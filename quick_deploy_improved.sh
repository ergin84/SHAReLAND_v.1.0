#!/bin/bash

################################################################################
# ShareLand Quick Deploy Script (Improved)
# All-in-one deployment for Aruba VPS
# Supports both initial deployment and updates
################################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VPS_IP="5.249.148.147"
VPS_USER="root"
VPS_PASSWORD="Sh@r3l@nd2025/26"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v ssh &> /dev/null; then
    echo -e "${RED}❌ SSH client not found. Please install SSH.${NC}"
    exit 1
fi

if ! command -v scp &> /dev/null; then
    echo -e "${RED}❌ SCP command not found. Please install openssh-client.${NC}"
    exit 1
fi

# Install sshpass if needed
if ! command -v sshpass &> /dev/null; then
    echo "Installing sshpass..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update && sudo apt-get install -y sshpass 2>/dev/null || {
            echo -e "${RED}❌ Failed to install sshpass. Please install manually.${NC}"
            exit 1
        }
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if ! command -v brew &> /dev/null; then
            echo -e "${RED}❌ Homebrew not found. Please install Homebrew first.${NC}"
            exit 1
        fi
        brew install sshpass
    else
        echo -e "${RED}❌ Unsupported OS. Please install sshpass manually.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

# Check if VPS already has deployment
echo "Checking VPS status..."
EXISTING_DEPLOYMENT=$(sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
    ${VPS_USER}@${VPS_IP} \
    "test -d /var/www/shareland/repo && echo 'yes' || echo 'no'" 2>/dev/null)

if [ "$EXISTING_DEPLOYMENT" = "yes" ]; then
    echo -e "${YELLOW}⚠️  Existing deployment detected on VPS!${NC}"
    echo ""
    echo "You have two options:"
    echo "  1. Update existing deployment (preserves database)"
    echo "  2. Full redeployment (⚠️  will overwrite everything)"
    echo ""
    read -p "Choose option (1 or 2): " choice
    
    if [ "$choice" = "1" ]; then
        echo ""
        echo -e "${BLUE}Using update script instead...${NC}"
        echo ""
        # Check if GitHub auth is set up
        HAS_SSH_KEY=$(sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no \
            ${VPS_USER}@${VPS_IP} \
            "test -f /home/shareland/.ssh/id_rsa && echo 'yes' || echo 'no'" 2>/dev/null)
        
        if [ "$HAS_SSH_KEY" = "no" ]; then
            echo -e "${YELLOW}⚠️  No SSH key found for GitHub authentication${NC}"
            echo "Private repositories require authentication."
            echo ""
            read -p "Set up GitHub authentication now? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                if [ -f "./setup_vps_github_auth.sh" ]; then
                    ./setup_vps_github_auth.sh
                else
                    echo -e "${RED}setup_vps_github_auth.sh not found${NC}"
                    echo "Please set up GitHub authentication manually."
                fi
            fi
        fi
        
        if [ -f "./update_vps_code_auto.sh" ]; then
            echo ""
            echo "Running update script..."
            ./update_vps_code_auto.sh
        else
            echo -e "${RED}update_vps_code_auto.sh not found${NC}"
            exit 1
        fi
        exit 0
    elif [ "$choice" = "2" ]; then
        echo -e "${RED}⚠️  WARNING: Full redeployment will:${NC}"
        echo "  - Remove existing repository"
        echo "  - Drop and recreate database (⚠️  DATA LOSS!)"
        echo "  - Reinstall all packages"
        echo ""
        read -p "Are you ABSOLUTELY SURE? Type 'yes' to continue: " confirm
        if [ "$confirm" != "yes" ]; then
            echo "Deployment cancelled."
            exit 1
        fi
    else
        echo "Invalid choice. Deployment cancelled."
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ShareLand VPS Full Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Target: ${VPS_IP}"
echo "User: ${VPS_USER}"
echo ""

# Confirm deployment
read -p "Continue with FULL deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 1
fi

echo ""
echo "Starting deployment..."
echo ""

# Check if deploy_vps.sh exists
if [ ! -f "${SCRIPT_DIR}/deploy_vps.sh" ]; then
    echo -e "${RED}❌ deploy_vps.sh not found in ${SCRIPT_DIR}${NC}"
    exit 1
fi

# Upload deployment script
echo "[1/3] Uploading deployment script..."
sshpass -p "$VPS_PASSWORD" scp -o StrictHostKeyChecking=no \
    "${SCRIPT_DIR}/deploy_vps.sh" \
    ${VPS_USER}@${VPS_IP}:/tmp/deploy_shareland.sh

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to upload script${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Script uploaded${NC}"

echo ""
echo "[2/3] Running deployment on VPS..."
echo -e "${YELLOW}This will take 10-15 minutes...${NC}"
echo ""

# Execute deployment
sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no \
    ${VPS_USER}@${VPS_IP} \
    "chmod +x /tmp/deploy_shareland.sh && /tmp/deploy_shareland.sh"

DEPLOY_STATUS=$?

echo ""
echo "[3/3] Cleaning up..."
sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no \
    ${VPS_USER}@${VPS_IP} \
    "rm -f /tmp/deploy_shareland.sh" 2>/dev/null

echo ""
echo -e "${GREEN}========================================${NC}"
if [ ${DEPLOY_STATUS} -eq 0 ]; then
    echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Application is now running at:"
    echo "  http://${VPS_IP}"
    echo ""
    echo "Next steps:"
    echo "1. Set up GitHub authentication (for private repo):"
    echo "   ./setup_vps_github_auth.sh"
    echo ""
    echo "2. Create superuser:"
    echo "   ssh root@${VPS_IP}"
    echo "   cd /var/www/shareland/repo"
    echo "   source ../venv/bin/activate"
    echo "   python manage.py createsuperuser"
    echo ""
    echo "3. Configure SSL (recommended):"
    echo "   ssh root@${VPS_IP}"
    echo "   certbot --nginx -d shareland.it -d www.shareland.it"
else
    echo -e "${RED}❌ Deployment failed (exit code: ${DEPLOY_STATUS})${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Check the logs on the VPS:"
    echo "  ssh root@${VPS_IP}"
    echo "  tail -100 /var/log/shareland/gunicorn_error.log"
fi

echo ""





