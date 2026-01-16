#!/bin/bash
# Usage: ./deployment.sh <VPS_IP> <VPS_USER> <VPS_PASSWORD>

set -e

if [ $# -ne 3 ]; then
  echo "Usage: $0 <VPS_IP> <VPS_USER> <VPS_PASSWORD>"
  exit 1
fi

VPS_IP="$1"
VPS_USER="$2"
VPS_PASSWORD="$3"

LOCAL_PROJECT_DIR="$(pwd)"
REMOTE_PROJECT_DIR="/home/$VPS_USER/ShareLand"

# Sync project files to VPS
sshpass -p "$VPS_PASSWORD" rsync -avz --delete "$LOCAL_PROJECT_DIR/" "$VPS_USER@$VPS_IP:$REMOTE_PROJECT_DIR/"

# Copy .env (edit password before running or prompt for it)
sshpass -p "$VPS_PASSWORD" scp "$LOCAL_PROJECT_DIR/shareland/.env" "$VPS_USER@$VPS_IP:$REMOTE_PROJECT_DIR/shareland/.env"

# Restart Docker Compose on VPS
sshpass -p "$VPS_PASSWORD" ssh "$VPS_USER@$VPS_IP" "cd $REMOTE_PROJECT_DIR && docker compose down && docker compose up -d --build"

echo "Deployment complete. Check your site and email functionality."
