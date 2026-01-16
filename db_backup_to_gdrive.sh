#!/bin/bash
# Usage: ./db_backup_to_gdrive.sh <DB_NAME> <DB_USER> <DB_PASSWORD> <GDRIVE_FOLDER_ID>
# Add to crontab: 0 2 * * * /path/to/db_backup_to_gdrive.sh ...

set -e

DB_NAME="$1"
DB_USER="$2"
DB_PASSWORD="$3"
GDRIVE_FOLDER_ID="$4"
BACKUP_DIR="/tmp/shareland_backups"
DATE=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_$DATE.sql.gz"

mkdir -p "$BACKUP_DIR"

# Dump the PostgreSQL database
PGPASSWORD="$DB_PASSWORD" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

# Upload to Google Drive using gdrive CLI (https://github.com/prasmussen/gdrive)
# Requires gdrive to be installed and authenticated on the server
if command -v gdrive >/dev/null 2>&1; then
    gdrive files upload --parent "$GDRIVE_FOLDER_ID" "$BACKUP_FILE"
else
    echo "gdrive CLI not found. Please install and authenticate gdrive."
    exit 1
fi

# Optional: Remove backups older than 7 days
find "$BACKUP_DIR" -type f -mtime +7 -delete

echo "Backup complete: $BACKUP_FILE uploaded to Google Drive."
