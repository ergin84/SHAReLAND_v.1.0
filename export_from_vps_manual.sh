#!/bin/bash

# Manual export script - you'll need to enter password when prompted
# Or install sshpass: sudo apt-get install sshpass

VPS_HOST="root@89.36.211.235"
VPS_PASSWORD="ergin"
LOCAL_BACKUP_DIR="./shareland_backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=== Exporting ShareLAND from VPS ==="
echo "VPS: $VPS_HOST"
echo "Password: ergin"
echo ""

mkdir -p "$LOCAL_BACKUP_DIR"

# Check if sshpass is available
if command -v sshpass &> /dev/null; then
    SSH_CMD="sshpass -p '$VPS_PASSWORD' ssh -o StrictHostKeyChecking=no"
    RSYNC_CMD="sshpass -p '$VPS_PASSWORD' rsync -avz --progress"
else
    echo "Note: sshpass not installed. You'll be prompted for password."
    echo "To install: sudo apt-get install sshpass"
    echo ""
    SSH_CMD="ssh -o StrictHostKeyChecking=no"
    RSYNC_CMD="rsync -avz --progress"
fi

# Step 1: Find project path
echo "Step 1: Finding ShareLAND project..."
PROJECT_PATH=$(eval "$SSH_CMD" "$VPS_HOST" "find /var/www /home /opt /root -name 'manage.py' -type f 2>/dev/null | grep -i shareland | head -1 | xargs dirname 2>/dev/null || find /var/www /home /opt /root -name 'manage.py' -type f 2>/dev/null | head -1 | xargs dirname")

if [ -z "$PROJECT_PATH" ]; then
    echo "Please enter the project path manually:"
    read -p "Project path on VPS: " PROJECT_PATH
else
    echo "Found: $PROJECT_PATH"
    read -p "Use this? (y/n) [y]: " confirm
    if [ "$confirm" = "n" ] || [ "$confirm" = "N" ]; then
        read -p "Enter path: " PROJECT_PATH
    fi
fi

# Step 2: Copy project
echo ""
echo "Step 2: Copying project files..."
eval "$RSYNC_CMD" \
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

# Step 3: Copy media
echo ""
echo "Step 3: Copying media files..."
eval "$RSYNC_CMD" "$VPS_HOST:$PROJECT_PATH/media/" "$LOCAL_BACKUP_DIR/media/" 2>/dev/null || echo "Media directory not found"

# Step 4: Copy static
echo ""
echo "Step 4: Copying static files..."
eval "$RSYNC_CMD" "$VPS_HOST:$PROJECT_PATH/static/" "$LOCAL_BACKUP_DIR/static/" 2>/dev/null || echo "Static directory not found"

# Step 5: Export database
echo ""
echo "Step 5: Exporting database..."
DB_NAME=$(eval "$SSH_CMD" "$VPS_HOST" "grep -oP \"'NAME':\s*'\K[^']+\" $PROJECT_PATH/shareland/settings.py 2>/dev/null | head -1 || echo 'shareland'")
DB_USER=$(eval "$SSH_CMD" "$VPS_HOST" "grep -oP \"'USER':\s*'\K[^']+\" $PROJECT_PATH/shareland/settings.py 2>/dev/null | head -1 || echo 'postgres'")

echo "Database: $DB_NAME, User: $DB_USER"

DUMP_FILE="$LOCAL_BACKUP_DIR/database_${TIMESTAMP}.dump"

# Export database
if command -v sshpass &> /dev/null; then
    sshpass -p "$VPS_PASSWORD" ssh "$VPS_HOST" "PGPASSWORD=$VPS_PASSWORD pg_dump -U $DB_USER -h localhost -Fc $DB_NAME" > "$DUMP_FILE"
else
    echo "Enter password 'ergin' when prompted:"
    ssh "$VPS_HOST" "PGPASSWORD=$VPS_PASSWORD pg_dump -U $DB_USER -h localhost -Fc $DB_NAME" > "$DUMP_FILE"
fi

if [ -s "$DUMP_FILE" ]; then
    echo "✓ Database exported: $DUMP_FILE ($(du -h "$DUMP_FILE" | cut -f1))"
else
    echo "Trying SQL format..."
    DUMP_FILE_SQL="${DUMP_FILE%.dump}.sql"
    if command -v sshpass &> /dev/null; then
        sshpass -p "$VPS_PASSWORD" ssh "$VPS_HOST" "PGPASSWORD=$VPS_PASSWORD pg_dump -U $DB_USER -h localhost $DB_NAME" > "$DUMP_FILE_SQL"
    else
        ssh "$VPS_HOST" "PGPASSWORD=$VPS_PASSWORD pg_dump -U $DB_USER -h localhost $DB_NAME" > "$DUMP_FILE_SQL"
    fi
    [ -s "$DUMP_FILE_SQL" ] && DUMP_FILE="$DUMP_FILE_SQL" && echo "✓ Database exported as SQL"
fi

echo ""
echo "=== Export Complete ==="
echo "Backup: $LOCAL_BACKUP_DIR"
echo "Database: $DUMP_FILE"



















