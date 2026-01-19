#!/bin/bash

################################################################################
# Deployment Script for VPS Console
# Run this directly in the VPS console (copy and paste)
# Usage: Copy the commands below and paste into VPS console
################################################################################

cat << 'DEPLOY_SCRIPT'
#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

APP_DIR="/var/www/shareland"
APP_USER="shareland"
DB_NAME="shareland_db"
REPO_URL="https://github.com/ergin84/SHAReLAND_v.1.0.git"
REPO_BRANCH="main"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ShareLand VPS Code Update${NC}"
echo -e "${GREEN}========================================${NC}"

# Step 1: Database backup
echo -e "${YELLOW}[1/8] Creating database backup...${NC}"
mkdir -p /var/backups/shareland
BACKUP_FILE="/var/backups/shareland/shareland_backup_$(date +%Y%m%d_%H%M%S).sql"
sudo -u postgres pg_dump ${DB_NAME} > $BACKUP_FILE
echo -e "${GREEN}Backup created: $BACKUP_FILE${NC}"

# Step 2: Update code
echo -e "${YELLOW}[2/8] Updating code from GitHub...${NC}"
if [ ! -d "${APP_DIR}/repo" ]; then
    echo "Repository not found. Cloning..."
    mkdir -p ${APP_DIR}
    cd ${APP_DIR}
    git clone ${REPO_URL} repo
    chown -R ${APP_USER}:${APP_USER} ${APP_DIR}/repo
else
    cd ${APP_DIR}/repo
    if ! git remote get-url origin 2>/dev/null | grep -q "SHAReLAND_v.1.0"; then
        git remote set-url origin ${REPO_URL}
    fi
    sudo -u ${APP_USER} git fetch origin
    sudo -u ${APP_USER} git checkout ${REPO_BRANCH} 2>/dev/null || sudo -u ${APP_USER} git checkout -b ${REPO_BRANCH} origin/${REPO_BRANCH}
    sudo -u ${APP_USER} git pull origin ${REPO_BRANCH} || sudo -u ${APP_USER} git pull origin master
fi
cd ${APP_DIR}/repo/shareland
LATEST_COMMIT=$(sudo -u ${APP_USER} git rev-parse --short HEAD)
echo -e "${GREEN}Code updated. Latest commit: $LATEST_COMMIT${NC}"

# Step 3: Update dependencies
echo -e "${YELLOW}[3/8] Updating Python dependencies...${NC}"
cd ${APP_DIR}/repo/shareland
source ${APP_DIR}/venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo -e "${GREEN}Dependencies updated${NC}"

# Step 4: Update Gunicorn config
echo -e "${YELLOW}[4/8] Updating Gunicorn configuration...${NC}"
cat > ${APP_DIR}/gunicorn_config.py << 'GUNICORN_CONFIG'
import multiprocessing
import os

bind = "127.0.0.1:8001"
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
worker_connections = 1000
timeout = int(os.getenv('GUNICORN_TIMEOUT', '120'))
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
preload_app = True
accesslog = "/var/log/shareland/gunicorn_access.log"
errorlog = "/var/log/shareland/gunicorn_error.log"
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')
proc_name = "shareland"
graceful_timeout = 30
GUNICORN_CONFIG
chown ${APP_USER}:${APP_USER} ${APP_DIR}/gunicorn_config.py
echo -e "${GREEN}Gunicorn configuration updated (timeout: 120s)${NC}"

# Step 5: Run migrations
echo -e "${YELLOW}[5/8] Running database migrations...${NC}"
set -a
source ${APP_DIR}/.env
set +a
python manage.py migrate --settings=ShareLand.settings_production
echo -e "${GREEN}Migrations completed${NC}"

# Step 6: Collect static files
echo -e "${YELLOW}[6/8] Collecting static files...${NC}"
python manage.py collectstatic --noinput --settings=ShareLand.settings_production
echo -e "${GREEN}Static files collected${NC}"

# Step 7: Verify Nginx
echo -e "${YELLOW}[7/8] Verifying Nginx configuration...${NC}"
nginx -t && systemctl reload nginx
echo -e "${GREEN}Nginx configuration verified${NC}"

# Step 8: Restart application
echo -e "${YELLOW}[8/8] Restarting application...${NC}"
supervisorctl restart shareland
sleep 3

# Verify
if supervisorctl status shareland | grep -q "RUNNING"; then
    echo -e "${GREEN}Application is running${NC}"
else
    echo -e "${YELLOW}WARNING: Check application status${NC}"
    supervisorctl status shareland
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Backup: $BACKUP_FILE"
echo "Commit: $LATEST_COMMIT"
DEPLOY_SCRIPT

echo ""
echo "========================================"
echo "Instructions:"
echo "========================================"
echo ""
echo "1. Copy the script above (between the DEPLOY_SCRIPT markers)"
echo "2. In VPS console, create a file:"
echo "   nano /tmp/deploy.sh"
echo ""
echo "3. Paste the script content and save (Ctrl+X, Y, Enter)"
echo ""
echo "4. Make it executable:"
echo "   chmod +x /tmp/deploy.sh"
echo ""
echo "5. Run it:"
echo "   bash /tmp/deploy.sh"
echo ""
echo "========================================"





