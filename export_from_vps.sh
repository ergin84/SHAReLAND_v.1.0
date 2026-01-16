#!/bin/bash

# Script to export ShareLAND from Aruba VPS
# Password: ergin

VPS_HOST="root@89.36.211.235"
VPS_PASSWORD="ergin"
LOCAL_BACKUP_DIR="./shareland_backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=== Exporting ShareLAND from VPS ==="
echo "VPS: $VPS_HOST"
echo ""

# Create backup directory
mkdir -p "$LOCAL_BACKUP_DIR"

# Function to run SSH command with password
ssh_with_password() {
    if command -v sshpass &> /dev/null; then
        sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no "$@"
    else
        echo "Warning: sshpass not installed. You'll need to enter password manually."
        ssh -o StrictHostKeyChecking=no "$@"
    fi
}

# Function to run rsync with password
rsync_with_password() {
    if command -v sshpass &> /dev/null; then
        sshpass -p "$VPS_PASSWORD" rsync -avz --progress "$@"
    else
        echo "Warning: sshpass not installed. You'll need to enter password manually."
        rsync -avz --progress "$@"
    fi
}

# Step 1: Find the ShareLAND project on VPS
echo "Step 1: Finding ShareLAND project on VPS..."
PROJECT_PATH=$(ssh_with_password "$VPS_HOST" "find /var/www /home /opt /root -name 'manage.py' -type f 2>/dev/null | grep -i shareland | head -1 | xargs dirname 2>/dev/null || find /var/www /home /opt /root -name 'manage.py' -type f 2>/dev/null | head -1 | xargs dirname")

if [ -z "$PROJECT_PATH" ]; then
    echo "Could not auto-detect project path. Please enter it manually:"
    read -p "Project path on VPS (e.g., /var/www/shareland): " PROJECT_PATH
else
    echo "Found project at: $PROJECT_PATH"
    read -p "Use this path? (y/n) [y]: " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "" ]; then
        read -p "Enter project path: " PROJECT_PATH
    fi
fi

if [ -z "$PROJECT_PATH" ]; then
    echo "Error: Project path is required"
    exit 1
fi

# Step 2: Copy Django project files
echo ""
echo "Step 2: Copying Django project files..."
rsync_with_password \
    --exclude '*.pyc' \
    --exclude '__pycache__' \
    --exclude '*.sqlite3' \
    --exclude 'venv/' \
    --exclude '.venv/' \
    --exclude 'env/' \
    --exclude '.env' \
    --exclude 'node_modules/' \
    --exclude '.git/' \
    "$VPS_HOST:$PROJECT_PATH/" "$LOCAL_BACKUP_DIR/shareland/"

if [ $? -eq 0 ]; then
    echo "✓ Project files copied"
else
    echo "✗ Error copying project files"
    exit 1
fi

# Step 3: Copy media files
echo ""
echo "Step 3: Copying media files..."
if ssh_with_password "$VPS_HOST" "[ -d $PROJECT_PATH/media ]"; then
    rsync_with_password "$VPS_HOST:$PROJECT_PATH/media/" "$LOCAL_BACKUP_DIR/media/"
    echo "✓ Media files copied"
else
    echo "⚠ Media directory not found, skipping"
fi

# Step 4: Copy static files
echo ""
echo "Step 4: Copying static files..."
if ssh_with_password "$VPS_HOST" "[ -d $PROJECT_PATH/static ]"; then
    rsync_with_password "$VPS_HOST:$PROJECT_PATH/static/" "$LOCAL_BACKUP_DIR/static/"
    echo "✓ Static files copied"
else
    echo "⚠ Static directory not found, skipping"
fi

# Step 5: Export database
echo ""
echo "Step 5: Exporting database..."

# Try to detect database name from settings.py
DB_NAME=$(ssh_with_password "$VPS_HOST" "grep -o \"'NAME':\s*'[^']*'\" $PROJECT_PATH/shareland/settings.py 2>/dev/null | grep -o \"'[^']*'\" | tail -1 | tr -d \"'\" || echo 'shareland'")
DB_USER=$(ssh_with_password "$VPS_HOST" "grep -o \"'USER':\s*'[^']*'\" $PROJECT_PATH/shareland/settings.py 2>/dev/null | grep -o \"'[^']*'\" | tail -1 | tr -d \"'\" || echo 'postgres'")

echo "Detected database: $DB_NAME"
echo "Detected user: $DB_USER"

DUMP_FILE="$LOCAL_BACKUP_DIR/database_${TIMESTAMP}.dump"

# Export database (custom format)
echo "Exporting database (custom format)..."
if command -v sshpass &> /dev/null; then
    sshpass -p "$VPS_PASSWORD" ssh "$VPS_HOST" "PGPASSWORD=$VPS_PASSWORD pg_dump -U $DB_USER -h localhost -Fc $DB_NAME" > "$DUMP_FILE"
else
    ssh "$VPS_HOST" "PGPASSWORD=$VPS_PASSWORD pg_dump -U $DB_USER -h localhost -Fc $DB_NAME" > "$DUMP_FILE"
fi

if [ $? -eq 0 ] && [ -s "$DUMP_FILE" ]; then
    echo "✓ Database exported: $DUMP_FILE"
    DUMP_SIZE=$(du -h "$DUMP_FILE" | cut -f1)
    echo "  Size: $DUMP_SIZE"
else
    echo "⚠ Custom format failed, trying SQL format..."
    DUMP_FILE_SQL="${DUMP_FILE%.dump}.sql"
    if command -v sshpass &> /dev/null; then
        sshpass -p "$VPS_PASSWORD" ssh "$VPS_HOST" "PGPASSWORD=$VPS_PASSWORD pg_dump -U $DB_USER -h localhost $DB_NAME" > "$DUMP_FILE_SQL"
    else
        ssh "$VPS_HOST" "PGPASSWORD=$VPS_PASSWORD pg_dump -U $DB_USER -h localhost $DB_NAME" > "$DUMP_FILE_SQL"
    fi
    
    if [ $? -eq 0 ] && [ -s "$DUMP_FILE_SQL" ]; then
        echo "✓ Database exported as SQL: $DUMP_FILE_SQL"
        DUMP_FILE="$DUMP_FILE_SQL"
    else
        echo "✗ Failed to export database"
        exit 1
    fi
fi

# Step 6: Create info file
echo ""
echo "Step 6: Creating backup info..."
cat > "$LOCAL_BACKUP_DIR/backup_info.txt" << EOF
ShareLAND Backup Information
============================
Date: $(date)
VPS: $VPS_HOST
Project Path: $PROJECT_PATH
Database: $DB_NAME
Database User: $DB_USER
Database Dump: $(basename "$DUMP_FILE")
EOF

echo ""
echo "=== Export Complete ==="
echo "Backup location: $LOCAL_BACKUP_DIR"
echo "Database dump: $DUMP_FILE"
echo ""
echo "Next steps:"
echo "1. Review files in $LOCAL_BACKUP_DIR"
echo "2. Run: ./setup_local_docker.sh $LOCAL_BACKUP_DIR"
echo "   Or manually copy files and load database"



















