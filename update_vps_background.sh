#!/bin/bash

################################################################################
# ShareLand VPS Background Image Update Script
# Uploads and updates the background image on VPS
# Usage: bash update_vps_background.sh [path_to_bg_image]
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
VPS_IP="5.249.148.147"
VPS_USER="root"
APP_DIR="/var/www/shareland"
APP_USER="shareland"

# Default background image path
BG_SOURCE="${1:-shareland/frontend/static/images/bg.jpg}"

# Check if source file exists
if [ ! -f "$BG_SOURCE" ]; then
    echo -e "${RED}Error: Background image not found at: $BG_SOURCE${NC}"
    echo "Usage: bash update_vps_background.sh [path_to_bg_image]"
    echo "Default: shareland/frontend/static/images/bg.jpg"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ShareLand VPS Background Update${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Source file: $BG_SOURCE${NC}"
echo -e "${YELLOW}Target: VPS static files directory${NC}"
echo ""

# Upload and update background on VPS
sshpass -p "Sh@r3l@nd2025/26" ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_IP} << ENDSSH
set -e

echo "[1/3] Creating backup of existing background..."
mkdir -p /var/backups/shareland/static
if [ -f "${APP_DIR}/static/images/bg.jpg" ]; then
    cp ${APP_DIR}/static/images/bg.jpg /var/backups/shareland/static/bg.jpg.backup.\$(date +%Y%m%d_%H%M%S)
    echo "Backup created"
else
    echo "No existing background found, skipping backup"
fi

echo "[2/3] Creating static/images directory if needed..."
mkdir -p ${APP_DIR}/static/images
chown -R ${APP_USER}:${APP_USER} ${APP_DIR}/static

ENDSSH

echo "[3/3] Uploading new background image..."
sshpass -p "Sh@r3l@nd2025/26" scp -o StrictHostKeyChecking=no "$BG_SOURCE" ${VPS_USER}@${VPS_IP}:${APP_DIR}/static/images/bg.jpg

# Set permissions and reload
sshpass -p "Sh@r3l@nd2025/26" ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_IP} << ENDSSH
set -e

chown ${APP_USER}:${APP_USER} ${APP_DIR}/static/images/bg.jpg
chmod 644 ${APP_DIR}/static/images/bg.jpg

echo "Background image updated successfully"
echo "File location: ${APP_DIR}/static/images/bg.jpg"
echo ""
echo "Note: Nginx may cache static files. Changes should be visible immediately,"
echo "      but you may need to hard-refresh (Ctrl+F5) in your browser."

ENDSSH

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Background Update Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "The background image has been uploaded to the VPS."
echo "Check the website: http://${VPS_IP}"
echo ""
echo "If you don't see changes, try:"
echo "  - Hard refresh: Ctrl+F5 (or Cmd+Shift+R on Mac)"
echo "  - Clear browser cache"

