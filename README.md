# \# 🌍 Docker External IP Tracker

# \### 🚀 Elevator Pitch

Never lose track of your home or office network's external IP address again. This lightweight Docker service monitors your internet-facing IP and automatically "checks it in" to a GitHub repository the moment it changes. It's a self-healing, DIY Dynamic DNS alternative that keeps a timestamped JSON history of your connectivity.
But wait! There's more!
It's also universal Docker utility for maintaining connectivity to dynamic networks. Deploy as a Server to track and log your home's changing IP to GitHub, .... OR.... as a Client to automatically update your local /etc/hosts file so your "Home" hostname always points to the right place—no matter where you are in the world.
===

# 

# \---

# 

# \## ✨ Features

# \*   \*\*Automated Tracking\*\*: Periodically checks external IP using `ipify`.

# \*   \*\*Git Integration\*\*: Commits and pushes changes automatically to your chosen repo.

# \*   \*\*JSON Logging\*\*: Saves data in a clean `{ "IP": "...", "Last\_Modified": "..." }` format.

# \*   \*\*Self-Generating Config\*\*: Automatically creates a `.env` template if one is missing.

# \*   \*\*Health Monitored\*\*: Integrated with `autoheal` to ensure the service stays alive 24/7.

# \*   \*\*CI/CD Ready\*\*: Includes unit tests and quality linting via GitHub Actions.

# 

# \---

# 

# \## 🛠 Prerequisites

# \*   \[Docker](https://docker.com) and \[Docker Compose](https://docker.com)

# \*   A GitHub account and a \*\*Personal Access Token (PAT)\*\*. 

# &#x20;   \*   \*Note: Using a PAT is required for the service to push updates to your repository.\*

# 

# \---

# 

# \## 📦 Installation \& Setup

# 

# \### 1. Clone the Repository

# ```bash

# git clone https://github.com

# cd YOUR\_REPO

# ```

# \### 🖥 OS-Specific Configuration

# If running in \*\*CLIENT\*\* mode, you must uncomment the correct volume line in `docker-compose.yml`:

# 

# \*   \*\*Linux\*\*: `- /etc/hosts:/app/hosts\_mount`

# \*   \*\*Windows\*\*: `- C:\\Windows\\System32\\drivers\\etc\\hosts:/app/hosts\_mount`

# 

# > \*\*Note\*\*: On Windows, you may need to grant Docker Desktop permission to access the `C:\\Windows\\System32` directory in the Docker Desktop settings (File Sharing).





# \### 2. Launch the Service

# Run the following command to build the image and start the container:

# ```bash

# docker compose up -d

# ```

# 

# \### 3. Configure Credentials

# The first time the service runs, it will detect that a `.env` file is missing and create one for you using the `.env.example` template. 

# 

# 1\.  Open the newly created `.env` file in your root directory.

# 2\.  Update the following variables:

# &#x20;   \*   `GITHUB\_USERNAME`: Your GitHub handle.

# &#x20;   \*   `GITHUB\_PASSWORD`: Your GitHub Personal Access Token.

# &#x20;   \*   `GITHUB\_REPO\_URL`: The URL of the repo where the IP should be logged.

# &#x20;   \*   `IP\_LOG\_FILE`: The filename (e.g., `current\_ip.json`).

# 

# \### 4. Apply Changes

# After saving your `.env` file, restart the service to apply the configuration:

# ```bash

# docker compose restart ip-tracker

# ```

# 

# \---

# 

# \## 🔍 Monitoring \& Logs

# You can monitor the service in real-time to see IP checks and GitHub push confirmations:

# 

# ```bash

# \# View live logs

# docker compose logs -f

# 

# \# Check health status

# docker compose ps

# ```

# 

# \## 🧪 Running Tests

# If you are developing or modifying the tracker, you can run the unit tests locally:

# ```bash

# pip install -r requirements.txt

# python -m unittest test\_tracker.py

# ```

# 

# \---

# 

# \## 📄 License

# This work is licensed under the \[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](LICENSE.md).

