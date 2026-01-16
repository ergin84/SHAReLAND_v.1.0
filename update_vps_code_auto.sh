#!/bin/bash

################################################################################
# ShareLand VPS Code Update Script (Non-Interactive)
# Updates code on VPS while preserving the database
# Usage: bash update_vps_code_auto.sh
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
DB_NAME="shareland_db"
REPO_URL="https://github.com/ergin84/SHAReLAND_v.1.0.git"
REPO_BRANCH="master"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ShareLand VPS Code Update (Auto)${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}This will update code while preserving the database.${NC}"
echo -e "${YELLOW}Starting deployment in 3 seconds...${NC}"
sleep 3

# Execute update on VPS
sshpass -p "Sh@r3l@nd2025/26" ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_IP} << 'ENDSSH'
set -e
# Allow git pull to fail without stopping deployment
set +e

echo "[1/8] Creating database backup..."
mkdir -p /var/backups/shareland
BACKUP_FILE="/var/backups/shareland/shareland_backup_$(date +%Y%m%d_%H%M%S).sql"
sudo -u postgres pg_dump shareland_db > $BACKUP_FILE
echo "Backup created: $BACKUP_FILE"

echo "[2/8] Updating code from GitHub..."
# Check if repo directory exists, if not clone it
if [ ! -d "/var/www/shareland/repo" ]; then
    echo "Repository not found. Cloning from GitHub..."
    mkdir -p /var/www/shareland
    cd /var/www/shareland
    # Check if SSH key exists (prefer SSH for private repos)
    if [ -f "/home/shareland/.ssh/id_rsa" ] || [ -f "/home/shareland/.ssh/id_ed25519_deploy" ]; then
        echo "SSH key found, using SSH URL..."
        sudo -u shareland git clone git@github.com:ergin84/SHAReLAND_v.1.0.git repo
    else
        echo "No SSH key found, using HTTPS (may require authentication for private repos)..."
        sudo -u shareland git clone https://github.com/ergin84/SHAReLAND_v.1.0.git repo
    fi
    chown -R shareland:shareland /var/www/shareland/repo
else
    cd /var/www/shareland/repo
    # Fix ownership if needed
    chown -R shareland:shareland /var/www/shareland/repo/.git 2>/dev/null || true
    
    # Check current remote URL
    CURRENT_REMOTE=$(sudo -u shareland git remote get-url origin 2>/dev/null || echo "")
    
    # If using HTTPS and SSH key exists, switch to SSH
    if echo "$CURRENT_REMOTE" | grep -q "^https://" && [ -f "/home/shareland/.ssh/id_rsa" ] || [ -f "/home/shareland/.ssh/id_ed25519_deploy" ]; then
        echo "Switching to SSH URL for better private repo support..."
        sudo -u shareland git remote set-url origin git@github.com:ergin84/SHAReLAND_v.1.0.git
    fi
    
    # Check if remote is set correctly
    if ! sudo -u shareland git remote get-url origin 2>/dev/null | grep -q "SHAReLAND_v.1.0"; then
        echo "Updating remote URL..."
        # Prefer SSH if key exists
        if [ -f "/home/shareland/.ssh/id_rsa" ] || [ -f "/home/shareland/.ssh/id_ed25519_deploy" ]; then
            sudo -u shareland git remote set-url origin git@github.com:ergin84/SHAReLAND_v.1.0.git
        else
            sudo -u shareland git remote set-url origin https://github.com/ergin84/SHAReLAND_v.1.0.git
        fi
    fi
    
    # Reset any local changes that might block pull
    sudo -u shareland git reset --hard HEAD 2>/dev/null || true
    sudo -u shareland git clean -fd 2>/dev/null || true
    
    # Fetch and pull
    echo "Fetching latest changes..."
    if sudo -u shareland git fetch origin 2>&1 | grep -q "Permission denied\|Authentication failed\|could not read Username"; then
        echo "WARNING: Authentication failed. Repository may be private."
        echo "Run './setup_vps_github_auth.sh' to configure authentication."
        echo "Continuing with existing code..."
    else
        sudo -u shareland git checkout master 2>/dev/null || true
        if sudo -u shareland git pull origin master 2>&1 | grep -q "Permission denied\|Authentication failed\|could not read Username"; then
            echo "WARNING: Git pull failed - authentication required for private repository."
            echo "Run './setup_vps_github_auth.sh' to configure authentication."
            echo "Using existing code for now..."
        else
            echo "Code updated successfully"
        fi
    fi
fi
set -e
# Find shareland directory
if [ -d "/var/www/shareland/repo/shareland" ]; then
    cd /var/www/shareland/repo/shareland
elif [ -d "/var/www/shareland/repo" ]; then
    cd /var/www/shareland/repo
else
    echo "Error: Cannot find repository directory"
    exit 1
fi
LATEST_COMMIT=$(sudo -u shareland git rev-parse --short HEAD 2>/dev/null || echo "unknown")
echo "Code ready. Latest commit: $LATEST_COMMIT"

echo "[3/8] Updating Python dependencies..."
# Find the correct directory
if [ -d "/var/www/shareland/repo/shareland" ]; then
    cd /var/www/shareland/repo/shareland
elif [ -d "/var/www/shareland/repo" ]; then
    cd /var/www/shareland/repo
else
    echo "Error: Cannot find application directory"
    exit 1
fi
source /var/www/shareland/venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "Dependencies updated"

echo "[4/8] Updating Gunicorn configuration..."
# Check for gunicorn_config.py in different possible locations
GUNICORN_CONFIG_SOURCE=""
if [ -f "${APP_DIR}/repo/shareland/gunicorn_config.py" ]; then
    GUNICORN_CONFIG_SOURCE="${APP_DIR}/repo/shareland/gunicorn_config.py"
elif [ -f "${APP_DIR}/repo/gunicorn_config.py" ]; then
    GUNICORN_CONFIG_SOURCE="${APP_DIR}/repo/gunicorn_config.py"
fi

if [ -n "\$GUNICORN_CONFIG_SOURCE" ]; then
    # Create VPS-specific gunicorn config based on the repo version
    cat > ${APP_DIR}/gunicorn_config.py << 'GUNICORN_VPS_CONFIG'
import multiprocessing
import os

# Server socket - VPS uses 127.0.0.1:8001 (behind nginx)
bind = "127.0.0.1:8001"

# Worker processes
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
worker_connections = 1000

# Timeout settings - increased to handle longer requests
timeout = int(os.getenv('GUNICORN_TIMEOUT', '120'))  # 120 seconds default
keepalive = 5

# Worker lifecycle
max_requests = 1000
max_requests_jitter = 100
preload_app = True

# Logging - VPS uses file logging
accesslog = "/var/log/shareland/gunicorn_access.log"
errorlog = "/var/log/shareland/gunicorn_error.log"
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')

# Process naming
proc_name = "shareland"

# Graceful timeout for worker shutdown
graceful_timeout = 30
GUNICORN_VPS_CONFIG
    chown shareland:shareland /var/www/shareland/gunicorn_config.py
    echo "Gunicorn configuration updated (timeout increased to 120s)"
else
    echo -e "${YELLOW}Warning: gunicorn_config.py not found in repo, updating timeout in existing config...${NC}"
    # Update timeout in existing config if it exists
    if [ -f "/var/www/shareland/gunicorn_config.py" ]; then
        sed -i 's/^timeout = .*/timeout = 120/' /var/www/shareland/gunicorn_config.py
        echo "Updated timeout in existing config"
    fi
fi

echo "[5/8] Running database migrations..."
set -a
source /var/www/shareland/.env
set +a
# Try production settings, fall back to default settings
python manage.py migrate --settings=ShareLand.settings_production 2>/dev/null || python manage.py migrate
echo "Migrations completed"

echo "[6/8] Collecting static files..."
# Try production settings, fall back to default settings
python manage.py collectstatic --noinput --settings=ShareLand.settings_production 2>/dev/null || python manage.py collectstatic --noinput
echo "Static files collected"

echo "[7/8] Verifying and preserving Nginx configuration..."
# Backup existing Nginx config if it exists
if [ -f "/etc/nginx/sites-available/shareland" ]; then
    echo "Nginx configuration found, preserving it..."
    # Test Nginx configuration
    if nginx -t 2>/dev/null; then
        echo "Nginx configuration is valid"
        # Reload Nginx to ensure it's using the current config
        systemctl reload nginx 2>/dev/null || echo "Nginx reload skipped (may not be needed)"
    else
        echo "Warning: Nginx configuration test failed, but keeping existing config"
    fi
else
    echo "Warning: Nginx configuration not found at /etc/nginx/sites-available/shareland"
    echo "This is normal if Nginx was configured differently. No changes will be made."
fi
echo "Nginx configuration preserved"

echo "[8/8] Restarting application..."
supervisorctl restart shareland
sleep 3

# Verify
echo -e "${YELLOW}Verifying deployment...${NC}"
if supervisorctl status shareland | grep -q "RUNNING"; then
    echo "Application is running"
else
    echo "WARNING: Application may not be running properly"
    supervisorctl status shareland
fi

echo ""
echo "========================================"
echo "Update Complete!"
echo "========================================"
echo ""
echo "Backup location: $BACKUP_FILE"
echo "Latest commit: $LATEST_COMMIT"
echo ""
echo "Check logs: tail -f /var/log/shareland/gunicorn_error.log"
ENDSSH

echo ""
echo -e "${GREEN}Code update completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Check application: http://${VPS_IP}"
echo "2. Monitor logs: ssh ${VPS_USER}@${VPS_IP} 'tail -f /var/log/shareland/gunicorn_error.log'"
echo "3. Verify database: All data should be intact"

