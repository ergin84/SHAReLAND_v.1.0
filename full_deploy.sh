#!/bin/bash

################################################################################
# ShareLand Complete Deployment with SSL
# Deploys application and sets up SSL in one command
# SSH connection with interactive support for password prompts
################################################################################

set -e

VPS_IP="${1:-5.249.148.147}"
VPS_USER="${2:-root}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ShareLand Complete Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Target VPS:${NC} ${VPS_IP}"
echo -e "${BLUE}User:${NC} ${VPS_USER}"
echo ""

# Function to execute SSH command
execute_remote() {
    local description="$1"
    local command="$2"
    
    echo -e "${YELLOW}${description}...${NC}"
    ssh -t ${VPS_USER}@${VPS_IP} "${command}"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ ${description} failed${NC}"
        return 1
    fi
    echo -e "${GREEN}✓ ${description} successful${NC}"
    echo ""
}

# Step 1: Upload deployment scripts to VPS
echo -e "${YELLOW}Step 1/3: Uploading deployment scripts to VPS...${NC}"
scp -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
    "${SCRIPT_DIR}/deploy_vps.sh" \
    "${SCRIPT_DIR}/setup_ssl.sh" \
    ${VPS_USER}@${VPS_IP}:/tmp/ 2>/dev/null

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to upload scripts${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Scripts uploaded${NC}"
echo ""

# Step 2: Run application deployment
execute_remote "Step 2/4: Deploying ShareLand application" \
    "cd /tmp && chmod +x deploy_vps.sh && bash deploy_vps.sh" || exit 1

# Step 3: Run database migrations
execute_remote "Step 3/4: Running Django migrations" \
    "cd /var/www/shareland/repo && source ../venv/bin/activate && export \$(cat /var/www/shareland/.env | xargs) && python manage.py migrate --settings=ShareLand.settings_production" || exit 1

# Step 4: Create superuser (if not exists)
echo -e "${YELLOW}Step 4/5: Creating Django superuser...${NC}"
ssh -t ${VPS_USER}@${VPS_IP} <<'SUPERUSER_EOF'
cd /var/www/shareland/repo
export $(cat /var/www/shareland/.env | xargs)
source ../venv/bin/activate

python << 'PYTHON_SCRIPT'
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ShareLand.settings_production')
django.setup()

from django.contrib.auth.models import User

username = 'admin'
email = 'admin@shareland.it'
password = 'ShareLand2025!'

if User.objects.filter(username=username).exists():
    print(f"Superuser '{username}' already exists.")
else:
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"Superuser '{username}' created successfully!")
PYTHON_SCRIPT
SUPERUSER_EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Superuser creation failed${NC}"
else
    echo -e "${GREEN}✓ Superuser ready${NC}"
fi
echo ""

# Step 5: Run SSL setup
execute_remote "Step 5/5: Setting up SSL certificate" \
    "cd /tmp && chmod +x setup_ssl.sh && bash setup_ssl.sh" || exit 1

# Cleanup
echo -e "${YELLOW}Cleaning up temporary files...${NC}"
ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_IP} \
    "rm -f /tmp/deploy_vps.sh /tmp/setup_ssl.sh" 2>/dev/null || true
echo ""

# Cleanup
echo -e "${YELLOW}Cleaning up temporary files...${NC}"
ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_IP} \
    "rm -f /tmp/deploy_vps.sh /tmp/setup_ssl.sh" 2>/dev/null || true
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Complete Deployment Successful!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Your ShareLand site is now live:${NC}"
echo "  🌐 https://shareland.it"
echo "  🔒 SSL Certificate: Active"
echo "  👤 Admin: admin / ShareLand2025!"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo "1. Access Admin Panel:"
echo "   https://shareland.it/admin/"
echo "   Username: admin"
echo "   Password: ShareLand2025!"
echo ""
echo "2. Import Database Backup:"
echo "   https://shareland.it/database-import/"
echo "   (Supports PostgreSQL 17 dump format 1.16)"
echo ""
echo "3. Monitor Application:"
echo "   ssh root@${VPS_IP} 'tail -f /var/log/shareland/gunicorn_error.log'"
echo ""
echo -e "${YELLOW}SSL Certificate Details:${NC}"
echo "  Domain: shareland.it"
echo "  Renewal: Automatic (Let's Encrypt)"
echo "  Auto-redirect: HTTP → HTTPS enabled"
echo ""
echo -e "${YELLOW}Security Features:${NC}"
echo "  ✓ HTTPS/TLS 1.2+"
echo "  ✓ HSTS (Strict-Transport-Security)"
echo "  ✓ Security headers configured"
echo "  ✓ HTTP to HTTPS auto-redirect"
echo ""
echo -e "${YELLOW}Deployment Usage:${NC}"
echo "  Basic:    bash full_deploy.sh"
echo "  Advanced: bash full_deploy.sh 5.249.148.147 root"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
echo ""
