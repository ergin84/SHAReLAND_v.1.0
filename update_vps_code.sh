#!/bin/bash

################################################################################
# ShareLand VPS Code Update Script
# Updates code on VPS while preserving the database
# Usage: bash update_vps_code.sh
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
echo -e "${GREEN}ShareLand VPS Code Update${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}This will update code while preserving the database.${NC}"
echo ""

# Ask for confirmation
read -p "Continue with update? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Update cancelled."
    exit 1
fi

# Execute update on VPS
ssh ${VPS_USER}@${VPS_IP} << ENDSSH
set -e

echo -e "${YELLOW}[1/8] Creating database backup...${NC}"
mkdir -p /var/backups/shareland
BACKUP_FILE="/var/backups/shareland/shareland_backup_\$(date +%Y%m%d_%H%M%S).sql"
sudo -u postgres pg_dump ${DB_NAME} > \$BACKUP_FILE
echo -e "${GREEN}Backup created: \$BACKUP_FILE${NC}"

echo -e "${YELLOW}[2/8] Updating code from GitHub...${NC}"
# Check if repo directory exists, if not clone it
if [ ! -d "${APP_DIR}/repo" ]; then
    echo "Repository not found. Cloning from GitHub..."
    mkdir -p ${APP_DIR}
    cd ${APP_DIR}
    git clone ${REPO_URL} repo
    chown -R ${APP_USER}:${APP_USER} ${APP_DIR}/repo
else
    cd ${APP_DIR}/repo
    # Check if remote is set correctly
    if ! git remote get-url origin 2>/dev/null | grep -q "SHAReLAND_v.1.0"; then
        echo "Updating remote URL..."
        git remote set-url origin ${REPO_URL}
    fi
    sudo -u ${APP_USER} git fetch origin
    sudo -u ${APP_USER} git checkout ${REPO_BRANCH} 2>/dev/null || sudo -u ${APP_USER} git checkout -b ${REPO_BRANCH} origin/${REPO_BRANCH}
    sudo -u ${APP_USER} git pull origin ${REPO_BRANCH} || sudo -u ${APP_USER} git pull origin master
fi
cd ${APP_DIR}/repo/shareland
LATEST_COMMIT=\$(sudo -u ${APP_USER} git rev-parse --short HEAD)
echo -e "${GREEN}Code updated. Latest commit: \$LATEST_COMMIT${NC}"

echo -e "${YELLOW}[3/8] Updating Python dependencies...${NC}"
cd ${APP_DIR}/repo/shareland
source ${APP_DIR}/venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo -e "${GREEN}Dependencies updated${NC}"

echo -e "${YELLOW}[4/8] Updating Gunicorn configuration...${NC}"
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
    chown ${APP_USER}:${APP_USER} ${APP_DIR}/gunicorn_config.py
    echo -e "${GREEN}Gunicorn configuration updated (timeout increased to 120s)${NC}"
else
    echo -e "${YELLOW}Warning: gunicorn_config.py not found in repo, updating timeout in existing config...${NC}"
    # Update timeout in existing config if it exists
    if [ -f "${APP_DIR}/gunicorn_config.py" ]; then
        sed -i 's/^timeout = .*/timeout = 120/' ${APP_DIR}/gunicorn_config.py
        echo -e "${GREEN}Updated timeout in existing config${NC}"
    fi
fi

echo -e "${YELLOW}[5/8] Running database migrations...${NC}"
set -a
source ${APP_DIR}/.env
set +a
python manage.py migrate --settings=ShareLand.settings_production
echo -e "${GREEN}Migrations completed${NC}"

echo -e "${YELLOW}[6/8] Collecting static files...${NC}"
python manage.py collectstatic --noinput --settings=ShareLand.settings_production
echo -e "${GREEN}Static files collected${NC}"

echo -e "${YELLOW}[7/8] Verifying and preserving Nginx configuration...${NC}"
# Backup existing Nginx config if it exists
if [ -f "/etc/nginx/sites-available/shareland" ]; then
    echo "Nginx configuration found, preserving it..."
    # Test Nginx configuration
    if nginx -t 2>/dev/null; then
        echo -e "${GREEN}Nginx configuration is valid${NC}"
        # Reload Nginx to ensure it's using the current config
        systemctl reload nginx 2>/dev/null || echo "Nginx reload skipped (may not be needed)"
    else
        echo -e "${YELLOW}Warning: Nginx configuration test failed, but keeping existing config${NC}"
    fi
else
    echo -e "${YELLOW}Warning: Nginx configuration not found at /etc/nginx/sites-available/shareland${NC}"
    echo "This is normal if Nginx was configured differently. No changes will be made."
fi
echo -e "${GREEN}Nginx configuration preserved${NC}"

echo -e "${YELLOW}[8/8] Restarting application...${NC}"
supervisorctl restart shareland
sleep 3

# Verify
echo -e "${YELLOW}Verifying deployment...${NC}"
if supervisorctl status shareland | grep -q "RUNNING"; then
    echo -e "${GREEN}Application is running${NC}"
else
    echo -e "${RED}WARNING: Application may not be running properly${NC}"
    supervisorctl status shareland
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Update Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Backup location: \$BACKUP_FILE"
echo "Latest commit: \$LATEST_COMMIT"
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




