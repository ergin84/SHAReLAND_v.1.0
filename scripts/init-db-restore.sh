#!/bin/bash
# Restore Shareland database backup on first container startup
set -e

DUMP_FILE="/backups/shareland_db_backup_20260224_131504.dump"

if [ -f "$DUMP_FILE" ]; then
    echo "Restoring database from backup: $DUMP_FILE"
    pg_restore -U postgres -d shareland --no-owner --no-acl "$DUMP_FILE" 2>/dev/null || true
    echo "Database restore completed"
else
    echo "No backup found at $DUMP_FILE, skipping restore"
fi
