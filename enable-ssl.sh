#!/usr/bin/env bash
# ==============================================================================
# CampusPulse — Free Let's Encrypt SSL Activation Script
# ==============================================================================
# Usage:
#   chmod +x enable-ssl.sh
#   sudo ./enable-ssl.sh yourdomain.com [admin_email@domain.com]
# ==============================================================================

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Error: Domain name is required."
    echo "Usage: sudo ./enable-ssl.sh yourdomain.com [email@domain.com]"
    exit 1
fi

DOMAIN="$1"
EMAIL="${2:-admin@${DOMAIN}}"

echo "Installing Certbot and Python Nginx plugin..."
apt-get update -y
apt-get install -y certbot python3-certbot-nginx

echo "Requesting Let's Encrypt certificate for ${DOMAIN}..."
certbot --nginx -d "${DOMAIN}" --non-interactive --agree-tos -m "${EMAIL}" --redirect

echo "Testing Nginx configuration..."
nginx -t
systemctl reload nginx

echo "Testing automated SSL renewal..."
certbot renew --dry-run

echo "=========================================================="
echo " ✅ HTTPS is active on https://${DOMAIN}"
echo " Certificates will automatically renew via certbot.timer."
echo "=========================================================="
