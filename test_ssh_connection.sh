#!/bin/bash

################################################################################
# Test SSH Connection to VPS
# Quick test to verify SSH is working
# Usage: bash test_ssh_connection.sh
################################################################################

VPS_IP="5.249.148.147"
VPS_USER="root"
VPS_PASSWORD="Sh@r3l@nd2025/26"

echo "========================================"
echo "Testing SSH Connection to VPS"
echo "========================================"
echo ""

# Check if port 22 is open
echo "[1/3] Checking if port 22 is open..."
if timeout 2 bash -c "echo > /dev/tcp/$VPS_IP/22" 2>/dev/null; then
    echo "✓ Port 22 is OPEN"
else
    echo "✗ Port 22 is still CLOSED"
    echo "   SSH service may need a moment to fully start"
    exit 1
fi

echo ""
echo "[2/3] Testing SSH connection..."

# Try to connect and run a simple command
if command -v sshpass &> /dev/null; then
    echo "Using sshpass for password authentication..."
    sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 ${VPS_USER}@${VPS_IP} "echo 'SSH connection successful!' && hostname && uptime" 2>&1
else
    echo "sshpass not installed. Testing connection (will prompt for password)..."
    echo "You can install sshpass: sudo apt-get install sshpass"
    echo ""
    echo "Or connect manually:"
    echo "  ssh root@${VPS_IP}"
    echo "  Password: ${VPS_PASSWORD}"
    exit 0
fi

CONNECTION_STATUS=$?

echo ""
echo "[3/3] Connection test result:"
if [ $CONNECTION_STATUS -eq 0 ]; then
    echo "✓ SSH connection is working!"
    echo ""
    echo "You can now:"
    echo "  1. Connect via SSH: ssh root@${VPS_IP}"
    echo "  2. Run deployment: ./update_vps_code.sh"
else
    echo "✗ SSH connection failed"
    echo ""
    echo "Possible issues:"
    echo "  - Password might be incorrect"
    echo "  - SSH service might still be starting"
    echo "  - Firewall might be blocking"
    echo ""
    echo "Try connecting manually:"
    echo "  ssh root@${VPS_IP}"
fi





