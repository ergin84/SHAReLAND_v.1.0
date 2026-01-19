#!/bin/bash

################################################################################
# Backup Database from Docker Local and Restore to VPS
# Creates backup from local Docker PostgreSQL and restores it to VPS
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Local Docker database credentials
LOCAL_DB_NAME="shareland_v1"
LOCAL_DB_USER="postgres"
LOCAL_DB_PASSWORD="postgres"
LOCAL_DB_HOST="localhost"
LOCAL_DB_PORT="5433"
LOCAL_DB_CONTAINER="shareland_db_1"

# VPS credentials
VPS_IP="5.249.148.147"
VPS_USER="root"
VPS_PASSWORD="Sh@r3l@nd2025/26"
VPS_DB_NAME="shareland_db"
VPS_DB_USER="shareland_user"

# Backup file
BACKUP_FILE="shareland_backup_$(date +%Y%m%d_%H%M%S).sql"
BACKUP_DIR="/tmp"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Database Backup and Restore${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Step 1: Check if Docker container is running
echo -e "${YELLOW}[1/5] Checking Docker database container...${NC}"
if ! docker ps | grep -q "$LOCAL_DB_CONTAINER"; then
    echo -e "${RED}Error: Docker container $LOCAL_DB_CONTAINER is not running${NC}"
    echo "Starting Docker containers..."
    cd shareland
    docker-compose up -d db
    sleep 5
    cd ..
fi
echo -e "${GREEN}✓ Docker container is running${NC}"

# Step 2: Create backup from Docker database
echo -e "${YELLOW}[2/5] Creating backup from local Docker database...${NC}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILE}"

# Try to get password from environment or use default
export PGPASSWORD="$LOCAL_DB_PASSWORD"

# Check if database exists, if not try Open_Landscapes
if docker exec $LOCAL_DB_CONTAINER psql -U $LOCAL_DB_USER -lqt | cut -d \| -f 1 | grep -qw "$LOCAL_DB_NAME"; then
    echo "Backing up database: $LOCAL_DB_NAME"
    docker exec $LOCAL_DB_CONTAINER pg_dump -U $LOCAL_DB_USER -d $LOCAL_DB_NAME --clean --if-exists > "$BACKUP_PATH"
elif docker exec $LOCAL_DB_CONTAINER psql -U $LOCAL_DB_USER -lqt | cut -d \| -f 1 | grep -qw "Open_Landscapes"; then
    echo "Database $LOCAL_DB_NAME not found, using Open_Landscapes"
    LOCAL_DB_NAME="Open_Landscapes"
    docker exec $LOCAL_DB_CONTAINER pg_dump -U $LOCAL_DB_USER -d $LOCAL_DB_NAME --clean --if-exists > "$BACKUP_PATH"
else
    echo -e "${RED}Error: Could not find database to backup${NC}"
    echo "Available databases:"
    docker exec $LOCAL_DB_CONTAINER psql -U $LOCAL_DB_USER -l
    exit 1
fi

if [ $? -eq 0 ] && [ -f "$BACKUP_PATH" ] && [ -s "$BACKUP_PATH" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_PATH" | cut -f1)
    echo -e "${GREEN}✓ Backup created: $BACKUP_FILE (${BACKUP_SIZE})${NC}"
else
    echo -e "${RED}✗ Backup failed${NC}"
    exit 1
fi

# Step 3: Transfer backup to VPS
echo -e "${YELLOW}[3/5] Transferring backup to VPS...${NC}"
sshpass -p "$VPS_PASSWORD" scp -o StrictHostKeyChecking=no "$BACKUP_PATH" ${VPS_USER}@${VPS_IP}:/tmp/${BACKUP_FILE}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backup transferred to VPS${NC}"
else
    echo -e "${RED}✗ Transfer failed${NC}"
    exit 1
fi

# Step 4: Get VPS database password
echo -e "${YELLOW}[4/5] Getting VPS database password...${NC}"
VPS_DB_PASSWORD=$(sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_IP} "grep DB_PASSWORD /var/www/shareland/.env | cut -d'=' -f2")

if [ -z "$VPS_DB_PASSWORD" ]; then
    echo -e "${YELLOW}⚠ Could not get password from .env, you may need to enter it manually${NC}"
    read -sp "Enter VPS database password: " VPS_DB_PASSWORD
    echo
fi

# Step 5: Restore backup to VPS database
echo -e "${YELLOW}[5/5] Restoring backup to VPS database...${NC}"
echo -e "${YELLOW}⚠ WARNING: This will replace all data in the VPS database!${NC}"

# Check if running non-interactively
if [ -t 0 ]; then
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Restore cancelled."
        exit 1
    fi
else
    echo "Running in non-interactive mode, proceeding with restore..."
fi

# Restore on VPS
sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_IP} << EOF
    # Drop existing connections
    sudo -u postgres psql -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$VPS_DB_NAME' AND pid <> pg_backend_pid();" 2>/dev/null || true
    
    # Drop and recreate database
    sudo -u postgres dropdb $VPS_DB_NAME 2>/dev/null || true
    sudo -u postgres createdb $VPS_DB_NAME
    
    # Restore backup
    sudo -u postgres psql -d $VPS_DB_NAME < /tmp/$BACKUP_FILE
    
    # Grant permissions
    sudo -u postgres psql -d $VPS_DB_NAME -c "GRANT ALL PRIVILEGES ON DATABASE $VPS_DB_NAME TO $VPS_DB_USER;"
    sudo -u postgres psql -d $VPS_DB_NAME -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $VPS_DB_USER;"
    sudo -u postgres psql -d $VPS_DB_NAME -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $VPS_DB_USER;"
    sudo -u postgres psql -d $VPS_DB_NAME -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $VPS_DB_USER;"
    sudo -u postgres psql -d $VPS_DB_NAME -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $VPS_DB_USER;"
    
    # Clean up
    rm /tmp/$BACKUP_FILE
    
    echo "✓ Database restored successfully"
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database restored to VPS${NC}"
else
    echo -e "${RED}✗ Restore failed${NC}"
    exit 1
fi

# Clean up local backup
if [ -t 0 ]; then
    read -p "Delete local backup file? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm "$BACKUP_PATH"
        echo -e "${GREEN}✓ Local backup deleted${NC}"
    else
        echo "Backup saved at: $BACKUP_PATH"
    fi
else
    echo "Backup saved at: $BACKUP_PATH"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Backup and Restore Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Local database: $LOCAL_DB_NAME"
echo "VPS database: $VPS_DB_NAME"
echo ""
echo "Next steps:"
echo "1. Restart Django application on VPS:"
echo "   ssh root@$VPS_IP 'supervisorctl restart shareland'"
echo "2. Verify data:"
echo "   ssh root@$VPS_IP 'psql -U $VPS_DB_USER -d $VPS_DB_NAME -c \"\\dt\"'"
echo ""

