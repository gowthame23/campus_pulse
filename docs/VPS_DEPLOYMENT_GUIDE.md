# CampusPulse — Production VPS Deployment Guide

This guide explains how to deploy **CampusPulse** to any Linux Cloud VPS (DigitalOcean, AWS EC2, Hetzner, Linode, Hostinger, GCP, or Azure) in under 5 minutes.

---

## 1. Prerequisites: Provision a VPS
- **OS:** Ubuntu 22.04 LTS or Ubuntu 24.04 LTS (recommended)
- **Specs:** 1 vCPU, 1 GB RAM minimum (2 GB RAM recommended)
- **Ports to Open (Security Group / Firewall):**
  - `22` (SSH)
  - `80` (HTTP)
  - `443` (HTTPS)

---

## 2. Transfer Code to Your VPS

### Option A: Via Git (Recommended)
On your local machine, push the code to your GitHub / GitLab repository:
```bash
git add .
git commit -m "Deploy: production-ready CampusPulse"
git push origin main
```
Then SSH into your VPS and clone:
```bash
ssh root@<YOUR_SERVER_IP>
git clone <YOUR_GIT_REPO_URL> /var/www/campuspulse
cd /var/www/campuspulse
```

### Option B: Direct Copy via SCP / Rsync (Without Git)
From your local terminal, copy the project directly to your VPS:
```bash
scp -r CampusPulse_co root@<YOUR_SERVER_IP>:/var/www/campuspulse
ssh root@<YOUR_SERVER_IP>
cd /var/www/campuspulse
```

---

## 3. Run the Automated 1-Click Deployment Script

On your VPS terminal, execute:
```bash
chmod +x deploy.sh enable-ssl.sh
sudo ./deploy.sh <YOUR_SERVER_IP_OR_DOMAIN>
```

*Example with Server IP:*
```bash
sudo ./deploy.sh 159.65.120.45
```

*Example with Domain Name:*
```bash
sudo ./deploy.sh campuspulse.edu
```

### What `deploy.sh` automatically does:
1. Installs system packages: Python 3, Nginx, Node.js 20 LTS, Gunicorn, UFW.
2. Creates an isolated Python virtual environment and installs backend dependencies.
3. Compiles the React 19 frontend into optimized production PWA assets (`npm run build`).
4. Configures a persistent `systemd` service (`campuspulse-backend.service`) with 4 Gunicorn/Uvicorn workers, automatic restart on failure, and boot persistence.
5. Configures Nginx with reverse proxy, SPA fallback, WebSocket upgrade headers for real-time notifications/chat, static asset caching, and gzip compression.
6. Configures the firewall (UFW) to allow traffic on ports 22, 80, and 443.

---

## 4. (Optional) Enable Free HTTPS / SSL

If you pointed a domain name to your server's IP address:
```bash
sudo ./enable-ssl.sh yourdomain.com your_email@domain.com
```
This automatically obtains a Let's Encrypt SSL certificate, updates Nginx, forces HTTPS redirection, and configures auto-renewal.

---

## 5. Useful Management Commands on VPS

| Action | Command |
| :--- | :--- |
| **Check Backend Status** | `sudo systemctl status campuspulse-backend` |
| **Restart Backend** | `sudo systemctl restart campuspulse-backend` |
| **View Live Backend Logs** | `sudo journalctl -u campuspulse-backend -f` or `tail -f Backend/logs/gunicorn.log` |
| **Check Nginx Status** | `sudo systemctl status nginx` |
| **Test Nginx Config** | `sudo nginx -t` |
| **Reload Nginx** | `sudo systemctl reload nginx` |

---

## 6. How to Deploy Future Code Updates

When you make changes to the codebase later:
```bash
cd /var/www/campuspulse
git pull origin main
sudo ./deploy.sh <YOUR_SERVER_IP_OR_DOMAIN>
```
The script rebuilds the frontend, updates backend dependencies, and performs a zero-downtime reload of the services.
