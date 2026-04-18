#!/bin/bash

################################################################################
# Check VPS Nginx Configuration
# Retrieves and displays the current Nginx configuration from VPS
# Usage: bash check_vps_nginx.sh
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

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Checking VPS Nginx Configuration${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check Nginx configuration files
echo -e "${YELLOW}[1/4] Checking Nginx configuration files...${NC}"
ssh ${VPS_USER}@${VPS_IP} << 'ENDSSH'
echo "=== Nginx Sites Available ==="
ls -la /etc/nginx/sites-available/ 2>/dev/null || echo "No sites-available directory"

echo ""
echo "=== Nginx Sites Enabled ==="
ls -la /etc/nginx/sites-enabled/ 2>/dev/null || echo "No sites-enabled directory"

echo ""
echo "=== ShareLand Nginx Configuration ==="
if [ -f "/etc/nginx/sites-available/shareland" ]; then
    echo "Found: /etc/nginx/sites-available/shareland"
    echo "--- Content ---"
    cat /etc/nginx/sites-available/shareland
elif [ -f "/etc/nginx/sites-enabled/shareland" ]; then
    echo "Found: /etc/nginx/sites-enabled/shareland"
    echo "--- Content ---"
    cat /etc/nginx/sites-enabled/shareland
else
    echo "ShareLand config not found. Checking default configs..."
    if [ -f "/etc/nginx/sites-enabled/default" ]; then
        echo "--- Default Config ---"
        cat /etc/nginx/sites-enabled/default
    fi
fi

echo ""
echo "=== Main Nginx Configuration ==="
if [ -f "/etc/nginx/nginx.conf" ]; then
    echo "--- nginx.conf (first 50 lines) ---"
    head -50 /etc/nginx/nginx.conf
fi

echo ""
echo "=== Nginx Status ==="
systemctl status nginx --no-pager -l | head -10 || echo "Nginx service not found"

echo ""
echo "=== Nginx Test ==="
nginx -t 2>&1 || echo "Nginx test failed"
ENDSSH

echo ""
echo -e "${YELLOW}[2/4] Checking Nginx logs location...${NC}"
ssh ${VPS_USER}@${VPS_IP} << 'ENDSSH'
echo "=== Nginx Log Files ==="
if [ -d "/var/log/shareland" ]; then
    echo "ShareLand log directory exists:"
    ls -lh /var/log/shareland/ | grep nginx || echo "No nginx logs found"
else
    echo "ShareLand log directory not found"
fi

if [ -d "/var/log/nginx" ]; then
    echo ""
    echo "Standard Nginx log directory:"
    ls -lh /var/log/nginx/ | head -10
fi
ENDSSH

echo ""
echo -e "${YELLOW}[3/4] Checking SSL certificates...${NC}"
ssh ${VPS_USER}@${VPS_IP} << 'ENDSSH'
echo "=== SSL Certificates ==="
if [ -d "/etc/letsencrypt/live" ]; then
    echo "Let's Encrypt certificates found:"
    ls -la /etc/letsencrypt/live/
else
    echo "No Let's Encrypt certificates found"
fi

echo ""
echo "=== Certbot Status ==="
certbot certificates 2>/dev/null || echo "Certbot not installed or no certificates"
ENDSSH

echo ""
echo -e "${YELLOW}[4/4] Checking active Nginx processes...${NC}"
ssh ${VPS_USER}@${VPS_IP} << 'ENDSSH'
echo "=== Nginx Processes ==="
ps aux | grep nginx | grep -v grep || echo "No Nginx processes running"

echo ""
echo "=== Listening Ports ==="
netstat -tlnp 2>/dev/null | grep nginx || ss -tlnp 2>/dev/null | grep nginx || echo "Cannot determine listening ports"
ENDSSH

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Configuration Check Complete${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Review the configuration above"
echo "2. Save the configuration if needed:"
echo "   ssh ${VPS_USER}@${VPS_IP} 'cat /etc/nginx/sites-available/shareland' > nginx_config_backup.conf"
echo "3. Update update_vps_code.sh to preserve these settings"






