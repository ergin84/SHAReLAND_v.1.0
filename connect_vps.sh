#!/bin/bash

################################################################################
# Connect to VPS with Password
# Uses sshpass to connect with the stored password
# Usage: bash connect_vps.sh
################################################################################

VPS_IP="5.249.148.147"
VPS_USER="root"
VPS_PASSWORD="Sh@r3l@nd2025/26"

echo "========================================"
echo "Connecting to VPS: ${VPS_IP}"
echo "========================================"
echo ""

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo "Installing sshpass..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get install -y sshpass 2>/dev/null || {
            echo "Please install sshpass manually:"
            echo "  sudo apt-get install sshpass"
            echo ""
            echo "Or connect manually with:"
            echo "  ssh root@${VPS_IP}"
            echo "  Password: ${VPS_PASSWORD}"
            exit 1
        }
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Please install sshpass manually:"
        echo "  brew install sshpass"
        echo ""
        echo "Or connect manually with:"
        echo "  ssh root@${VPS_IP}"
        echo "  Password: ${VPS_PASSWORD}"
        exit 1
    fi
fi

echo "Attempting to connect..."
echo "Note: If SSH port 22 is closed, you'll need to restart SSH service via VPS console first"
echo ""

# Try to connect
sshpass -p "${VPS_PASSWORD}" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ${VPS_USER}@${VPS_IP}

if [ $? -ne 0 ]; then
    echo ""
    echo "========================================"
    echo "Connection failed!"
    echo "========================================"
    echo ""
    echo "Possible reasons:"
    echo "1. SSH port 22 is closed (SSH service not running)"
    echo "2. Firewall is blocking port 22"
    echo "3. VPS is down or unreachable"
    echo ""
    echo "Solutions:"
    echo "1. Access VPS via provider's web console"
    echo "2. Start SSH service: systemctl start ssh"
    echo "3. Check firewall: ufw status"
    echo ""
    echo "Manual connection:"
    echo "  ssh root@${VPS_IP}"
    echo "  Password: ${VPS_PASSWORD}"
fi





