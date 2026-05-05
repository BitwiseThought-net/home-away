import os
import time
import json
import logging
import shutil
import platform
from datetime import datetime
import requests
from git import Repo
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

ENV_PATH = ".env"
EXAMPLE_PATH = ".env.example"

def get_hosts_path():
    """Detects the hosts file path based on the operating system."""
    # When running in Docker, we typically mount the host's file to a known path.
    # However, if running natively or via specific mounts, this helps:
    if platform.system() == "Windows":
        return r"C:\Windows\System32\drivers\etc\hosts"
    return "/etc/hosts"

def validate_env():
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
    # In Docker, we will mount the host's file to /app/hosts_mount
    hosts_path = "/app/hosts_mount" 
    
    if not os.path.exists(hosts_path):
        logging.error(f"Hosts mount not found at {hosts_path}. Check docker-compose volumes.")
        return

    try:
        with open(hosts_path, 'r') as f:
            lines = f.readlines()
        
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
            
        with open(hosts_path, 'w') as f:
            f.writelines(new_lines)
        logging.info(f"Updated hosts: {hostname} -> {new_ip}")
    except Exception as e:
        logging.error(f"Failed to update hosts file: {e}")

# ... (push_to_github and pull_from_github remain the same) ...

def main():
    last_ip = None
    while True:
        if validate_env():
            is_client = os.getenv("CLIENT", "false").lower() == "true"
            if is_client:
                logging.info("Running in CLIENT mode.")
                data = pull_from_github()
                if data and data.get("IP") != last_ip:
                    update_hosts_file(data["IP"], os.getenv("HOME_HOSTNAME", "home.local"))
                    last_ip = data["IP"]
            else:
                logging.info("Running in SERVER mode.")
                try:
                    current_ip = requests.get('https://ipify.org', timeout=10).text
                    if current_ip != last_ip:
                        push_to_github(current_ip)
                        last_ip = current_ip
                except Exception as e:
                    logging.error(f"IP check failed: {e}")
        time.sleep(300)

if __name__ == '__main__':
    main()
