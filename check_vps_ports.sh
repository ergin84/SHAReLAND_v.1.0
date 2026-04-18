#!/bin/bash

################################################################################
# Check Open Ports on VPS
# Scans common ports to see what's accessible
# Usage: bash check_vps_ports.sh
################################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

VPS_IP="5.249.148.147"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Port Scanner for VPS: ${VPS_IP}${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Function to check if port is open
check_port() {
    local port=$1
    local service=$2
    
    if timeout 2 bash -c "echo > /dev/tcp/$VPS_IP/$port" 2>/dev/null; then
        echo -e "${GREEN}✓ Port $port ($service) - OPEN${NC}"
        return 0
    else
        echo -e "${RED}✗ Port $port ($service) - CLOSED${NC}"
        return 1
    fi
}

# Function to check port with service detection
check_port_with_service() {
    local port=$1
    local service=$2
    
    if timeout 2 bash -c "echo > /dev/tcp/$VPS_IP/$port" 2>/dev/null; then
        # Try to get service banner/response
        local response=""
        case $port in
            22)
                response=$(timeout 2 ssh -o ConnectTimeout=2 -o StrictHostKeyChecking=no root@$VPS_IP "echo 'SSH OK'" 2>&1 | head -1)
                ;;
            80)
                response=$(curl -s -I --max-time 2 http://$VPS_IP 2>/dev/null | head -1)
                ;;
            443)
                response=$(curl -s -I --max-time 2 https://$VPS_IP 2>/dev/null | head -1)
                ;;
            3306)
                response=$(timeout 2 mysql -h $VPS_IP -u root -e "SELECT 1" 2>&1 | head -1)
                ;;
            5432)
                response=$(timeout 2 nc -zv $VPS_IP $port 2>&1 | head -1)
                ;;
        esac
        
        if [ -n "$response" ] && [ "$response" != "" ]; then
            echo -e "${GREEN}✓ Port $port ($service) - OPEN${NC} ${BLUE}[$response]${NC}"
        else
            echo -e "${GREEN}✓ Port $port ($service) - OPEN${NC}"
        fi
        return 0
    else
        echo -e "${RED}✗ Port $port ($service) - CLOSED${NC}"
        return 1
    fi
}

echo -e "${YELLOW}Checking common ports...${NC}"
echo ""

# Common ports to check
declare -A ports=(
    ["22"]="SSH"
    ["80"]="HTTP"
    ["443"]="HTTPS"
    ["21"]="FTP"
    ["25"]="SMTP"
    ["53"]="DNS"
    ["3306"]="MySQL"
    ["5432"]="PostgreSQL"
    ["8000"]="Django Dev"
    ["8001"]="Gunicorn"
    ["8080"]="HTTP Alt"
    ["8443"]="HTTPS Alt"
    ["2222"]="SSH Alt"
    ["22022"]="SSH Alt 2"
)

OPEN_PORTS=()
CLOSED_PORTS=()

echo -e "${BLUE}Standard Services:${NC}"
for port in 22 80 443; do
    if check_port_with_service $port "${ports[$port]}"; then
        OPEN_PORTS+=($port)
    else
        CLOSED_PORTS+=($port)
    fi
done

echo ""
echo -e "${BLUE}Database Ports:${NC}"
for port in 3306 5432; do
    if check_port $port "${ports[$port]}"; then
        OPEN_PORTS+=($port)
    else
        CLOSED_PORTS+=($port)
    fi
done

echo ""
echo -e "${BLUE}Application Ports:${NC}"
for port in 8000 8001 8080; do
    if check_port $port "${ports[$port]}"; then
        OPEN_PORTS+=($port)
    else
        CLOSED_PORTS+=($port)
    fi
done

echo ""
echo -e "${BLUE}Alternative SSH Ports:${NC}"
for port in 2222 22022; do
    if check_port $port "${ports[$port]}"; then
        OPEN_PORTS+=($port)
    else
        CLOSED_PORTS+=($port)
    fi
done

echo ""
echo -e "${BLUE}Other Common Ports:${NC}"
for port in 21 25 53 8443; do
    if check_port $port "${ports[$port]}"; then
        OPEN_PORTS+=($port)
    else
        CLOSED_PORTS+=($port)
    fi
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

if [ ${#OPEN_PORTS[@]} -gt 0 ]; then
    echo -e "${GREEN}Open Ports (${#OPEN_PORTS[@]}):${NC}"
    for port in "${OPEN_PORTS[@]}"; do
        echo "  - Port $port (${ports[$port]})"
    done
else
    echo -e "${RED}No open ports detected${NC}"
fi

echo ""
if [ ${#CLOSED_PORTS[@]} -gt 0 ]; then
    echo -e "${RED}Closed Ports (${#CLOSED_PORTS[@]}):${NC}"
    for port in "${CLOSED_PORTS[@]}"; do
        echo "  - Port $port (${ports[$port]})"
    done
fi

echo ""
echo -e "${BLUE}Detailed Service Information:${NC}"
echo ""

# Check HTTP service details
if [[ " ${OPEN_PORTS[@]} " =~ " 80 " ]]; then
    echo -e "${YELLOW}HTTP Service (Port 80):${NC}"
    HTTP_HEADERS=$(curl -s -I --max-time 3 http://$VPS_IP 2>/dev/null)
    if [ -n "$HTTP_HEADERS" ]; then
        echo "$HTTP_HEADERS" | head -5
    fi
    echo ""
fi

# Check HTTPS service details
if [[ " ${OPEN_PORTS[@]} " =~ " 443 " ]]; then
    echo -e "${YELLOW}HTTPS Service (Port 443):${NC}"
    HTTPS_HEADERS=$(curl -s -I --max-time 3 https://$VPS_IP 2>/dev/null)
    if [ -n "$HTTPS_HEADERS" ]; then
        echo "$HTTPS_HEADERS" | head -5
    fi
    echo ""
fi

# Check SSH service details
if [[ " ${OPEN_PORTS[@]} " =~ " 22 " ]]; then
    echo -e "${YELLOW}SSH Service (Port 22):${NC}"
    SSH_VERSION=$(timeout 2 ssh -o ConnectTimeout=2 -o StrictHostKeyChecking=no root@$VPS_IP "echo 'SSH accessible'" 2>&1 | grep -i "ssh" | head -1)
    if [ -n "$SSH_VERSION" ]; then
        echo "SSH is accessible"
    else
        echo "SSH port is open but connection may require authentication"
    fi
    echo ""
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Scan Complete${NC}"
echo -e "${GREEN}========================================${NC}"






