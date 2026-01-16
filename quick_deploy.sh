#!/bin/bash

################################################################################
# ShareLand Quick Deploy Script
# All-in-one deployment for Aruba VPS
# Run this script to deploy everything automatically
################################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VPS_IP="5.249.148.147"
VPS_USER="root"

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v ssh &> /dev/null; then
    echo "❌ SSH client not found. Please install SSH."
    exit 1
fi

if ! command -v scp &> /dev/null; then
    echo "❌ SCP command not found. Please install openssh-client."
    exit 1
fi

# Install sshpass if needed
if ! command -v sshpass &> /dev/null; then
    echo "Installing sshpass..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update && sudo apt-get install -y sshpass
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if ! command -v brew &> /dev/null; then
            echo "❌ Homebrew not found. Please install Homebrew first."
            exit 1
        fi
        brew install sshpass
    else
        echo "❌ Unsupported OS. Please install sshpass manually."
        exit 1
    fi
fi

echo "✓ Prerequisites check passed"
echo ""
echo "=========================================="
echo "ShareLand VPS Deployment"
echo "=========================================="
echo "Target: ${VPS_IP}"
echo "User: ${VPS_USER}"
echo ""

# Confirm deployment
read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 1
fi

echo ""
echo "Starting deployment..."
echo ""

# Upload deployment script
echo "[1/3] Uploading deployment script..."
sshpass -p "Sh@r3l@nd2025/26" scp -o StrictHostKeyChecking=no \
    "${SCRIPT_DIR}/deploy_vps.sh" \
    ${VPS_USER}@${VPS_IP}:/tmp/deploy_shareland.sh

if [ $? -ne 0 ]; then
    echo "❌ Failed to upload script"
    exit 1
fi
echo "✓ Script uploaded"

echo ""
echo "[2/3] Running deployment on VPS..."
echo "This will take 10-15 minutes..."
echo ""

# Execute deployment
sshpass -p "Sh@r3l@nd2025/26" ssh -o StrictHostKeyChecking=no \
    ${VPS_USER}@${VPS_IP} \
    "chmod +x /tmp/deploy_shareland.sh && /tmp/deploy_shareland.sh"

DEPLOY_STATUS=$?

echo ""
echo "[3/3] Cleaning up..."
sshpass -p "Sh@r3l@nd2025/26" ssh -o StrictHostKeyChecking=no \
    ${VPS_USER}@${VPS_IP} \
    "rm /tmp/deploy_shareland.sh"

echo ""
echo "=========================================="
if [ ${DEPLOY_STATUS} -eq 0 ]; then
    echo "✅ Deployment completed successfully!"
    echo "=========================================="
    echo ""
    echo "Application is now running at:"
    echo "  http://${VPS_IP}"
    echo ""
    echo "Next steps:"
    echo "1. Create superuser:"
    echo "   ssh root@${VPS_IP}"
    echo "   cd /var/www/shareland/repo"
    echo "   source ../venv/bin/activate"
    echo "   python manage.py createsuperuser --settings=shareland.settings_production"
    echo ""
    echo "2. Configure SSL (recommended):"
    echo "   ssh root@${VPS_IP}"
    echo "   certbot --nginx -d shareland.it -d www.shareland.it"
    echo ""
    echo "3. Monitor logs:"
    echo "   ssh root@${VPS_IP}"
    echo "   tail -f /var/log/shareland/gunicorn_error.log"
else
    echo "❌ Deployment failed (exit code: ${DEPLOY_STATUS})"
    echo "=========================================="
    echo ""
    echo "Check the logs on the VPS:"
    echo "  ssh root@${VPS_IP}"
    echo "  tail -100 /var/log/shareland/gunicorn_error.log"
fi

echo ""
