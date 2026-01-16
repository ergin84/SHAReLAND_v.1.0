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

echo -e "${YELLOW}[1/6] Creating database backup...${NC}"
mkdir -p /var/backups/shareland
BACKUP_FILE="/var/backups/shareland/shareland_backup_\$(date +%Y%m%d_%H%M%S).sql"
sudo -u postgres pg_dump ${DB_NAME} > \$BACKUP_FILE
echo -e "${GREEN}Backup created: \$BACKUP_FILE${NC}"

echo -e "${YELLOW}[2/6] Pulling latest code from Git...${NC}"
cd ${APP_DIR}/repo
sudo -u ${APP_USER} git fetch origin
sudo -u ${APP_USER} git pull origin main || sudo -u ${APP_USER} git pull origin master
LATEST_COMMIT=\$(sudo -u ${APP_USER} git rev-parse --short HEAD)
echo -e "${GREEN}Code updated. Latest commit: \$LATEST_COMMIT${NC}"

echo -e "${YELLOW}[3/6] Updating Python dependencies...${NC}"
cd ${APP_DIR}/repo
source ${APP_DIR}/venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo -e "${GREEN}Dependencies updated${NC}"

echo -e "${YELLOW}[4/6] Running database migrations...${NC}"
set -a
source ${APP_DIR}/.env
set +a
python manage.py migrate --settings=ShareLand.settings_production
echo -e "${GREEN}Migrations completed${NC}"

echo -e "${YELLOW}[5/6] Collecting static files...${NC}"
python manage.py collectstatic --noinput --settings=ShareLand.settings_production
echo -e "${GREEN}Static files collected${NC}"

echo -e "${YELLOW}[6/6] Restarting application...${NC}"
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




