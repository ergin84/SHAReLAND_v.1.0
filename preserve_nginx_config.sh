#!/bin/bash

################################################################################
# Preserve Nginx Configuration on VPS
# This script backs up and preserves the existing Nginx configuration
# Usage: bash preserve_nginx_config.sh
################################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VPS_IP="5.249.148.147"
VPS_USER="root"
BACKUP_DIR="./nginx_backups"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Preserve VPS Nginx Configuration${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Create backup directory
mkdir -p ${BACKUP_DIR}

echo -e "${YELLOW}Backing up Nginx configuration from VPS...${NC}"
echo ""
echo "You will be prompted for SSH password or use SSH key authentication."
echo ""

# Backup Nginx configuration
ssh ${VPS_USER}@${VPS_IP} << 'ENDSSH' > ${BACKUP_DIR}/nginx_config_$(date +%Y%m%d_%H%M%S).conf 2>&1
echo "=== ShareLand Nginx Configuration ==="
if [ -f "/etc/nginx/sites-available/shareland" ]; then
    cat /etc/nginx/sites-available/shareland
elif [ -f "/etc/nginx/sites-enabled/shareland" ]; then
    cat /etc/nginx/sites-enabled/shareland
else
    echo "# Nginx config not found at expected location"
    echo "# Checking for other configs..."
    if [ -f "/etc/nginx/sites-enabled/default" ]; then
        cat /etc/nginx/sites-enabled/default
    fi
fi
ENDSSH

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Nginx configuration backed up${NC}"
    echo ""
    echo "Backup saved to: ${BACKUP_DIR}/nginx_config_*.conf"
    echo ""
    echo -e "${BLUE}Current Nginx configuration:${NC}"
    cat ${BACKUP_DIR}/nginx_config_*.conf | tail -n +2
else
    echo -e "${RED}✗ Failed to backup Nginx configuration${NC}"
    echo "Please check SSH access and try again manually:"
    echo "  ssh ${VPS_USER}@${VPS_IP} 'cat /etc/nginx/sites-available/shareland' > nginx_config_backup.conf"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Backup Complete${NC}"
echo -e "${GREEN}========================================${NC}"





