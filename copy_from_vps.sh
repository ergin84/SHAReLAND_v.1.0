#!/bin/bash

# Script to copy ShareLAND site and database from Aruba VPS
# Usage: ./copy_from_vps.sh

VPS_HOST="root@89.36.211.235"
VPS_PROJECT_PATH="/path/to/shareland"  # Update this with actual path on VPS
LOCAL_DIR="./shareland_backup"
DB_NAME="shareland"  # Update with actual database name on VPS
DB_USER="postgres"   # Update with actual database user

echo "=== Copying ShareLAND from VPS ==="
echo "VPS: $VPS_HOST"
echo ""

# Create local backup directory
mkdir -p "$LOCAL_DIR"

# Step 1: Copy Django project files
echo "Step 1: Copying Django project files..."
echo "Please provide the path to the ShareLAND project on the VPS:"
read -p "VPS project path (e.g., /var/www/shareland or /home/user/shareland): " VPS_PROJECT_PATH

rsync -avz --exclude '*.pyc' --exclude '__pycache__' --exclude '*.sqlite3' \
    --exclude 'venv/' --exclude '.venv/' --exclude 'node_modules/' \
    "$VPS_HOST:$VPS_PROJECT_PATH/" "$LOCAL_DIR/"

if [ $? -eq 0 ]; then
    echo "✓ Project files copied successfully"
else
    echo "✗ Error copying project files"
    exit 1
fi

# Step 2: Copy media files
echo ""
echo "Step 2: Copying media files..."
if ssh "$VPS_HOST" "[ -d $VPS_PROJECT_PATH/media ]"; then
    rsync -avz "$VPS_HOST:$VPS_PROJECT_PATH/media/" "$LOCAL_DIR/media/"
    echo "✓ Media files copied"
else
    echo "⚠ Media directory not found on VPS"
fi

# Step 3: Copy static files
echo ""
echo "Step 3: Copying static files..."
if ssh "$VPS_HOST" "[ -d $VPS_PROJECT_PATH/static ]"; then
    rsync -avz "$VPS_HOST:$VPS_PROJECT_PATH/static/" "$LOCAL_DIR/static/"
    echo "✓ Static files copied"
else
    echo "⚠ Static directory not found on VPS"
fi

# Step 4: Export database
echo ""
echo "Step 4: Exporting database..."
echo "Please provide database credentials:"
read -p "Database name [$DB_NAME]: " input_db_name
DB_NAME=${input_db_name:-$DB_NAME}

read -p "Database user [$DB_USER]: " input_db_user
DB_USER=${input_db_user:-$DB_USER}

read -sp "Database password: " DB_PASSWORD
echo ""

DUMP_FILE="$LOCAL_DIR/database_$(date +%Y%m%d_%H%M%S).dump"

# Try to export database (adjust command based on PostgreSQL version)
ssh "$VPS_HOST" "PGPASSWORD=$DB_PASSWORD pg_dump -U $DB_USER -h localhost -Fc $DB_NAME" > "$DUMP_FILE"

if [ $? -eq 0 ] && [ -s "$DUMP_FILE" ]; then
    echo "✓ Database exported successfully: $DUMP_FILE"
else
    echo "✗ Error exporting database. Trying alternative method..."
    # Alternative: SQL dump
    DUMP_FILE_SQL="${DUMP_FILE%.dump}.sql"
    ssh "$VPS_HOST" "PGPASSWORD=$DB_PASSWORD pg_dump -U $DB_USER -h localhost $DB_NAME" > "$DUMP_FILE_SQL"
    if [ $? -eq 0 ] && [ -s "$DUMP_FILE_SQL" ]; then
        echo "✓ Database exported as SQL: $DUMP_FILE_SQL"
        DUMP_FILE="$DUMP_FILE_SQL"
    else
        echo "✗ Failed to export database"
        exit 1
    fi
fi

echo ""
echo "=== Copy Complete ==="
echo "Files copied to: $LOCAL_DIR"
echo "Database dump: $DUMP_FILE"
echo ""
echo "Next steps:"
echo "1. Review the copied files in $LOCAL_DIR"
echo "2. Update docker-compose.yml if needed"
echo "3. Run: ./setup_local_docker.sh"

















