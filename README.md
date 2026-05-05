# 🌍 Docker External IP Tracker & Remote Client

### 🚀 What is this all about??
A universal Docker utility for maintaining connectivity to dynamic networks. Deploy it as a **Server** to track your home's changing IP and log it to GitHub, or as a **Client** to automatically update your local `hosts` file so your "Home" hostname always points to the right place—no matter where you are in the world.

---

## ✨ Features
*   **Dual-Mode Toggle**: Switch between Server (Tracker) and Client (Updater) via a single `.env` variable.
*   **Automated Tracking**: Periodically checks external IP using `ipify`.
*   **Git Integration**: Uses a GitHub repository as a "Source of Truth" for your IP data.
*   **JSON Logging**: Stores data in a structured `{ "IP": "...", "Last_Modified": "..." }` format.
*   **Self-Healing**: Integrated with `autoheal` to restart the service if it becomes unhealthy.
*   **OS-Agnostic**: Compatible with Linux and Windows hosts.

---

## 🛠 Prerequisites
*   [Docker](https://docker.com) and [Docker Compose](https://docker.com)
*   A GitHub Personal Access Token (PAT) with `repo` scope.

---

## 📦 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com
cd home-away
```

### 2. Launch the Service
```bash
docker compose up -d
```

### 3. Configure the `.env` File
The service will automatically generate a `.env` file from the template on its first run. Open it and update:


| Variable | Description |
| :--- | :--- |
| `CLIENT` | `false` for Server mode (Home), `true` for Client mode (Remote). |
| `HOME_HOSTNAME` | The hostname you want to use (e.g., `home.local`). |
| `GITHUB_USERNAME` | Your GitHub username. |
| `GITHUB_PASSWORD` | Your Personal Access Token. |
| `GITHUB_REPO_URL` | The URL of the repo to store/read the IP JSON. |
| `IP_LOG_FILE` | The filename (e.g., `external_ip.json`). |

### 4. OS-Specific Host Mounting
If running in **CLIENT** mode, you must ensure your `docker-compose.yml` mounts the correct hosts file to `/app/hosts_mount`:

*   **Linux**: `- /etc/hosts:/app/hosts_mount`
*   **Windows**: `- C:\Windows\System32\drivers\etc\hosts:/app/hosts_mount`

---

## 🔍 Monitoring & Health
```bash
# Check if the service is 'healthy'
docker compose ps

# Follow logs (useful for checking .env update alerts)
docker compose logs -f
```

## 🧪 Testing
The project includes a suite of unit tests that mock network and filesystem operations.
```bash
pip install -r requirements.txt
python -m unittest test_tracker.py
```

---

## 📄 License
This work is licensed under the [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](LICENSE.md).
