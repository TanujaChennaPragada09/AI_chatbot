# 🚀 TanujaChennaPragada AI Chatbot – Full Deployment Guide (AWS + Flask + Nginx + Ollama + Prometheus + Grafana)

This README explains the *complete* end‑to‑end setup of the AI Chatbot Application, including:

* Frontend UI (HTML/CSS/JS)
* Flask Backend running on AWS EC2
* Ollama LLM model (LLaMA3)
* Nginx reverse proxy
* Monitoring using Prometheus + Grafana
* Node Exporter on all servers

---

# 📌 Project Overview

This project deploys a full AI chatbot system with:

* 🧠 **Backend:** Python Flask API + SQLite + PDF export
* 🤖 **LLM:** Ollama – Llama3.2:1b model
* 🎨 **Frontend:** Beautiful HTML/CSS UI
* 🌐 **Reverse Proxy:** Nginx
* 📊 **Monitoring:** Prometheus + Grafana + Node Exporter
* 🔒 **Security:** AWS WAF (optional)

You will have **3 EC2 Servers**:

1. **Frontend Server (Nginx serving HTML)**
2. **Backend Server (Flask + Ollama)**
3. **Monitoring Server (Prometheus + Grafana)**

---

# 🟩 1. Launch EC2 Instances

Launch 3 EC2 Instances (Ubuntu 22.04 recommended):

| Server            | Purpose              | Ports                |
| ----------------- | -------------------- | -------------------- |
| Frontend Server   | Host UI using Nginx  | 80                   |
| Backend Server    | Flask API + Ollama   | 8080, 11434 (Ollama) |
| Monitoring Server | Prometheus + Grafana | 9090, 3000           |

---

# 🟩 2. Setup Backend Server

## Install Dependencies

```
sudo apt update -y
sudo apt install -y python3 python3-pip python3-venv nginx
```

## Install Ollama

```
curl -fsSL https://ollama.com/install.sh | sh
```

## Pull Llama Model

```
ollama pull llama3.2:1b
```

## Create Python Virtual Environment

```
sudo apt install python3.12-venv -y
python3 -m venv myenv
source myenv/bin/activate
```

## Install Python Packages

```
pip install flask flask-cors fpdf
```

*(sqlite3 is built-in — no need to install)*

---

# 🟩 3. Flask Backend Code

Create file `/home/ubuntu/backend/app.py`

(**Your full Flask code goes here — exact code added in your backend server**)

Run the backend:

```
python app.py
```

It runs on:
👉 `http://<backend-ip>:8080/chat`

---

# 🟩 4. Setup Frontend Server (Nginx)

## Install Nginx

```
sudo apt install nginx -y
```

## Replace default HTML

Place your `index.html` inside:

```
/var/www/html/index.html
```

🚨 **Update API URL inside index.html:**

```
const API_URL = "http://<BACKEND_PUBLIC_IP>:8080/chat";
```

Restart Nginx:

```
sudo systemctl restart nginx
```

Frontend now loads at:
👉 `http://<frontend-ip>`

---

# 🟩 5. Setup Prometheus + Grafana (Monitoring Server)

```
sudo apt update -y
sudo useradd --no-create-home --shell /bin/false prometheus
```

Download Prometheus:

```
wget https://github.com/prometheus/prometheus/releases/download/v2.47.0/prometheus-2.47.0.linux-amd64.tar.gz
tar -xvf prometheus-2.47.0.linux-amd64.tar.gz
sudo mv prometheus-2.47.0.linux-amd64 /etc/prometheus
```

## Prometheus Config `/etc/prometheus/prometheus.yml`

```
global:
  scrape_interval: 5s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'monitoring-server'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'backend-server'
    static_configs:
      - targets: ['<backend-ip>:9100']

  - job_name: 'frontend-server'
    static_configs:
      - targets: ['<frontend-ip>:9100']
```

Start Prometheus:

```
sudo systemctl start prometheus
sudo systemctl enable prometheus
```

Prometheus UI:
👉 `http://<monitor-ip>:9090/targets`

---

# 🟩 6. Install Node Exporter on All Servers

Repeat these steps on **frontend, backend, and monitoring** servers.

```
wget https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
tar -xvf node_exporter*.tar.gz
sudo mv node_exporter* /usr/local/bin/node_exporter
```

Start Node Exporter:

```
sudo nohup /usr/local/bin/node_exporter &
```

Metrics available at:
👉 `http://<server-ip>:9100/metrics`

---

# 🟩 7. Install Grafana

```
wget https://dl.grafana.com/oss/release/grafana_11.0.0_amd64.deb
sudo dpkg -i grafana_11.0.0_amd64.deb
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

Grafana UI:
👉 `http://<monitor-ip>:3000`

Default Login:

* **user:** admin
* **pass:** admin

### Add Prometheus as Data Source

Use URL:

```
http://localhost:9090
```

### Recommended Dashboards

* Node Exporter Full
* EC2 Monitoring Dashboard

---


