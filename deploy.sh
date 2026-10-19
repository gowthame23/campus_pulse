#!/usr/bin/env bash
# ==============================================================================
# CampusPulse — Production VPS Deployment Script (Ubuntu / Debian)
# ==============================================================================
# Usage:
#   chmod +x deploy.sh
#   sudo ./deploy.sh [YOUR_DOMAIN_OR_IP]
#
# Examples:
#   sudo ./deploy.sh 203.0.113.45
#   sudo ./deploy.sh campuspulse.edu
# ==============================================================================

set -euo pipefail

DOMAIN="${1:-_}"
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${INSTALL_DIR}/Backend"
FRONTEND_DIR="${INSTALL_DIR}/Frontend"
USER_NAME="${SUDO_USER:-$(whoami)}"

echo "=========================================================="
echo " Starting CampusPulse Production Deployment"
echo " Target Domain / IP: ${DOMAIN}"
echo " Install Directory:  ${INSTALL_DIR}"
echo " Service User:       ${USER_NAME}"
echo "=========================================================="

# 1. Update system packages
echo "--> [1/7] Updating system packages..."
apt-get update -y
apt-get install -y curl git build-essential nginx ufw python3 python3-pip python3-venv sqlite3

# 2. Install Node.js 20 LTS if missing
if ! command -v node >/dev/null 2>&1; then
    echo "--> [2/7] Installing Node.js 20 LTS..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi
echo "Node version: $(node -v)"
echo "NPM version:  $(npm -v)"

# 3. Setup Python Virtual Environment and Backend Dependencies
echo "--> [3/7] Setting up Python virtual environment and dependencies..."
cd "${BACKEND_DIR}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn uvicorn[standard]
deactivate

# 4. Build Frontend Assets
echo "--> [4/7] Building production frontend assets..."
cd "${FRONTEND_DIR}"
npm ci
npm run build

# 5. Configure Systemd Service for Backend
echo "--> [5/7] Creating systemd service: campuspulse-backend.service..."
cat <<EOF > /etc/systemd/system/campuspulse-backend.service
[Unit]
Description=CampusPulse FastAPI Backend Service
After=network.target

[Service]
User=${USER_NAME}
Group=www-data
WorkingDirectory=${BACKEND_DIR}
Environment="PATH=${BACKEND_DIR}/venv/bin:/usr/local/bin:/usr/bin"
Environment="PYTHONPATH=${BACKEND_DIR}"
Environment="ENV=production"
ExecStart=${BACKEND_DIR}/venv/bin/gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000 --timeout 120 --graceful-timeout 30
Restart=always
RestartSec=5
StandardOutput=append:${BACKEND_DIR}/logs/gunicorn.log
StandardError=append:${BACKEND_DIR}/logs/gunicorn_error.log

[Install]
WantedBy=multi-user.target
EOF

mkdir -p "${BACKEND_DIR}/logs"
chown -R "${USER_NAME}:www-data" "${INSTALL_DIR}"
chmod -R 775 "${BACKEND_DIR}/storage" "${BACKEND_DIR}/logs"

systemctl daemon-reload
systemctl enable campuspulse-backend
systemctl restart campuspulse-backend

# 6. Configure Nginx Reverse Proxy
echo "--> [6/7] Configuring Nginx reverse proxy..."
cat <<EOF > /etc/nginx/sites-available/campuspulse
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    client_max_body_size 50M;

    # Frontend Static Files
    root ${FRONTEND_DIR}/dist;
    index index.html;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml application/javascript application/json;
    gzip_disable "MSIE [1-6]\.";

    # Cache static assets
    location ~* \.(?:ico|css|js|gif|jpe?g|png|woff2?|eot|otf|ttf|svg|webp)$ {
        expires 6M;
        access_log off;
        add_header Cache-Control "public, max-age=15552000, immutable";
        try_files \$uri =404;
    }

    # API Endpoints
    location ~ ^/(auth|users|complaints|departments|locations|teams|leaves|safety-reports|emergency|lost-found|announcements|chat|notifications|push|analytics|reports|backups|settings|audit|search|api|docs|openapi.json) {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
        proxy_read_timeout 120s;
    }

    # WebSocket Endpoints
    location ~ ^/(notifications/ws|chat/ws) {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    # Single Page Application (SPA) routing fallback
    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF

ln -sf /etc/nginx/sites-available/campuspulse /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

# 7. Configure Firewall (UFW)
echo "--> [7/7] Configuring firewall..."
if command -v ufw >/dev/null 2>&1; then
    ufw allow 22/tcp || true
    ufw allow 80/tcp || true
    ufw allow 443/tcp || true
    ufw --force enable || true
fi

echo "=========================================================="
echo " ✅ CampusPulse is successfully deployed!"
echo " Web Application URL: http://${DOMAIN}"
echo " Backend Status:       systemctl status campuspulse-backend"
echo " Nginx Status:         systemctl status nginx"
echo "=========================================================="
