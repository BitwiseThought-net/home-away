import os
import time
import json
import logging
import shutil
import platform
import requests
from git import Repo
from dotenv import load_dotenv

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

ENV_PATH = ".env"
EXAMPLE_PATH = ".env.example"

def validate_env():
    """Ensures the .env file exists and is configured by the user."""
    if not os.path.exists(ENV_PATH):
        shutil.copy(EXAMPLE_PATH, ENV_PATH)
        logging.warning(".env not found. Created from template. UPDATE THE .env FILE.")
        return False
    load_dotenv(ENV_PATH)
    if os.getenv("GITHUB_USERNAME") == "your_username":
        logging.warning("Default values detected. PLEASE UPDATE YOUR .env FILE.")
        return False
    return True

def update_hosts_file(new_ip, hostname):
    """Updates the mounted hosts file with the new IP address."""
    hosts_path = "/app/hosts_mount"
    if not os.path.exists(hosts_path):
        logging.error("Hosts mount not found at %s. Check docker-compose.", hosts_path)
        return
    try:
        with open(hosts_path, 'r', encoding="utf-8") as file:
            lines = file.readlines()
        new_lines = []
        found = False
        for line in lines:
            if f" {hostname}" in line or line.endswith(f" {hostname}\n"):
                new_lines.append(f"{new_ip} {hostname}\n")
                found = True
            else:
                new_lines.append(line)
        if not found:
            new_lines.append(f"{new_ip} {hostname}\n")
        with open(hosts_path, 'w', encoding="utf-8") as file:
            file.writelines(new_lines)
        logging.info("Updated hosts: %s -> %s", hostname, new_ip)
    except Exception as err:
        logging.error("Failed to update hosts file: %s", err)

def push_to_github(new_ip):
    """Saves the IP to a JSON file and pushes to the GitHub repository."""
    user = os.getenv("GITHUB_USERNAME")
    pw = os.getenv("GITHUB_PASSWORD")
    repo_url = os.getenv("GITHUB_REPO_URL", "")
    url = repo_url.replace("https://", f"https://{user}:{pw}@")
    log_file = os.getenv("IP_LOG_FILE", "ip_log.json")
    
    tmp_dir = "/tmp/repo_sync"
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    
    repo = Repo.clone_from(url, tmp_dir)
    payload = {
        "IP": new_ip,
        "Last_Modified": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(os.path.join(tmp_dir, log_file), 'w', encoding="utf-8") as file:
        json.dump(payload, file, indent=4)
    
    repo.index.add([log_file])
    repo.index.commit(f"Automated IP Update: {new_ip}")
    repo.remotes.origin.push()
    logging.info("Pushed new IP to GitHub: %s", new_ip)

def pull_from_github():
    """Clones the repo and reads the current IP from the JSON log."""
    user = os.getenv("GITHUB_USERNAME")
    pw = os.getenv("GITHUB_PASSWORD")
    repo_url = os.getenv("GITHUB_REPO_URL", "")
    url = repo_url.replace("https://", f"https://{user}:{pw}@")
    log_file = os.getenv("IP_LOG_FILE", "ip_log.json")
    
    tmp_dir = "/tmp/repo_pull"
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    
    Repo.clone_from(url, tmp_dir)
    file_path = os.path.join(tmp_dir, log_file)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding="utf-8") as file:
            return json.load(file)
    return None

def main():
    """Main loop to toggle between Server (Tracker) and Client modes."""
    last_ip = None
    logging.info("Starting Service (OS Detected: %s)", platform.system())
    
    while True:
        if validate_env():
            is_client = os.getenv("CLIENT", "false").lower() == "true"
            if is_client:
                data = pull_from_github()
                if data and data.get("IP") != last_ip:
                    update_hosts_file(data["IP"], os.getenv("HOME_HOSTNAME", "home.local"))
                    last_ip = data["IP"]
            else:
                try:
                    current_ip = requests.get('https://ipify.org', timeout=10).text
                    if current_ip != last_ip:
                        push_to_github(current_ip)
                        last_ip = current_ip
                except Exception as err:
                    logging.error("IP check failed: %s", err)
        
        # Check every 5 minutes
        time.sleep(300)

if __name__ == '__main__':
    main()
