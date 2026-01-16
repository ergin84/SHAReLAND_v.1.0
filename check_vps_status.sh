#!/bin/bash

################################################################################
# Check VPS Status and Connectivity
# Troubleshoots connection issues to the VPS
# Usage: bash check_vps_status.sh
################################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

VPS_IP="5.249.148.147"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}VPS Connectivity Check${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

echo -e "${YELLOW}[1/5] Checking if VPS is reachable (ping)...${NC}"
if ping -c 3 -W 2 $VPS_IP > /dev/null 2>&1; then
    echo -e "${GREEN}✓ VPS is reachable via ping${NC}"
else
    echo -e "${RED}✗ VPS is NOT reachable via ping${NC}"
    echo "   This could mean:"
    echo "   - VPS is down"
    echo "   - IP address has changed"
    echo "   - Network connectivity issues"
fi

echo ""
echo -e "${YELLOW}[2/5] Checking if SSH port (22) is open...${NC}"
if timeout 3 bash -c "echo > /dev/tcp/$VPS_IP/22" 2>/dev/null; then
    echo -e "${GREEN}✓ Port 22 is open${NC}"
else
    echo -e "${RED}✗ Port 22 is closed or filtered${NC}"
    echo "   This could mean:"
    echo "   - SSH service is not running"
    echo "   - Firewall is blocking port 22"
    echo "   - SSH might be on a different port"
fi

echo ""
echo -e "${YELLOW}[3/5] Checking if HTTP port (80) is open...${NC}"
if timeout 3 bash -c "echo > /dev/tcp/$VPS_IP/80" 2>/dev/null; then
    echo -e "${GREEN}✓ Port 80 is open${NC}"
    echo "   Testing HTTP response..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://$VPS_IP 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" != "000" ]; then
        echo -e "${GREEN}✓ HTTP server is responding (Status: $HTTP_CODE)${NC}"
    else
        echo -e "${YELLOW}⚠ Port 80 is open but not responding${NC}"
    fi
else
    echo -e "${RED}✗ Port 80 is closed${NC}"
fi

echo ""
echo -e "${YELLOW}[4/5] Checking if HTTPS port (443) is open...${NC}"
if timeout 3 bash -c "echo > /dev/tcp/$VPS_IP/443" 2>/dev/null; then
    echo -e "${GREEN}✓ Port 443 is open${NC}"
else
    echo -e "${YELLOW}⚠ Port 443 is closed (may not have SSL configured)${NC}"
fi

echo ""
echo -e "${YELLOW}[5/5] Testing alternative SSH ports...${NC}"
for port in 2222 22022 2200; do
    if timeout 2 bash -c "echo > /dev/tcp/$VPS_IP/$port" 2>/dev/null; then
        echo -e "${GREEN}✓ Port $port is open (SSH might be here)${NC}"
        echo "   Try: ssh -p $port root@$VPS_IP"
    fi
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Diagnosis Complete${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Possible Solutions:${NC}"
echo ""
echo "1. If VPS is not reachable:"
echo "   - Check VPS provider dashboard"
echo "   - Verify VPS is running"
echo "   - Check if IP address has changed"
echo ""
echo "2. If port 22 is closed but VPS is reachable:"
echo "   - SSH service might be stopped"
echo "   - Check VPS provider console/control panel"
echo "   - Try accessing via VPS provider's web console"
echo ""
echo "3. If HTTP is working but SSH is not:"
echo "   - VPS is running but SSH service needs restart"
echo "   - Use VPS provider's console to restart SSH"
echo ""
echo "4. Alternative access methods:"
echo "   - Use VPS provider's web console/terminal"
echo "   - Check if SSH is on a different port"
echo "   - Contact VPS provider support"



