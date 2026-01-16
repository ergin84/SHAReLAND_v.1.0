#!/bin/bash

################################################################################
# SSH Tunnel & Deployment Launcher
# Connects to VPS and runs deployment
################################################################################

VPS_IP="5.249.148.147"
VPS_USER="root"
VPS_PASSWORD="Sh@r3l@nd2025/26"  # Note: using password-based auth (not recommended for production)
REPO_URL="https://github.com/ergin84/ShareLand.git"
LOCAL_SCRIPT="deploy_vps.sh"
REMOTE_SCRIPT="/tmp/deploy_shareland.sh"

echo "========================================"
echo "ShareLand VPS Deployment Launcher"
echo "========================================"
echo ""
echo "Target VPS: ${VPS_IP}"
echo ""

# Check if deploy script exists
if [ ! -f "${LOCAL_SCRIPT}" ]; then
    echo "Error: ${LOCAL_SCRIPT} not found!"
    echo "Make sure you're in the correct directory."
    exit 1
fi

# Install sshpass if not available (for password-based SSH)
if ! command -v sshpass &> /dev/null; then
    echo "Installing sshpass for password-based SSH..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get install -y sshpass
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install sshpass
    fi
fi

echo ""
echo "Uploading deployment script to VPS..."
sshpass -p "${VPS_PASSWORD}" scp -o StrictHostKeyChecking=no "${LOCAL_SCRIPT}" ${VPS_USER}@${VPS_IP}:${REMOTE_SCRIPT}

if [ $? -ne 0 ]; then
    echo "Error: Failed to upload script to VPS"
    exit 1
fi

echo "Script uploaded successfully!"
echo ""
echo "Running deployment script on VPS (this will take 10-15 minutes)..."
echo ""

# Execute the deployment script on the VPS
sshpass -p "${VPS_PASSWORD}" ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_IP} << 'SSH_COMMANDS'
#!/bin/bash
chmod +x /tmp/deploy_shareland.sh
/tmp/deploy_shareland.sh
SSH_COMMANDS

DEPLOY_STATUS=$?

echo ""
echo "========================================"
if [ ${DEPLOY_STATUS} -eq 0 ]; then
    echo "✓ Deployment completed successfully!"
else
    echo "✗ Deployment encountered errors (exit code: ${DEPLOY_STATUS})"
    echo "Check the logs on the VPS for details"
fi
echo "========================================"
echo ""
echo "Connect to VPS with:"
echo "ssh root@${VPS_IP}"
echo ""
echo "After deployment, secure SSH access:"
echo "1. Use SSH keys instead of passwords"
echo "2. Disable root login"
echo "3. Change default SSH port"
echo ""
