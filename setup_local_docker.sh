#!/bin/bash

# Script to set up ShareLAND in Docker from VPS backup
# Usage: ./setup_local_docker.sh [backup_directory]

BACKUP_DIR="${1:-./shareland_backup}"
DUMP_FILE=$(find "$BACKUP_DIR" -name "*.dump" -o -name "*.sql" | head -1)

if [ ! -d "$BACKUP_DIR" ]; then
    echo "Error: Backup directory not found: $BACKUP_DIR"
    echo "Usage: ./setup_local_docker.sh [backup_directory]"
    exit 1
fi

if [ -z "$DUMP_FILE" ]; then
    echo "Error: Database dump file not found in $BACKUP_DIR"
    exit 1
fi

echo "=== Setting up ShareLAND in Docker ==="
echo "Backup directory: $BACKUP_DIR"
echo "Database dump: $DUMP_FILE"
echo ""

# Step 1: Copy project files to shareland directory
echo "Step 1: Copying project files..."
if [ -d "$BACKUP_DIR/shareland" ]; then
    cp -r "$BACKUP_DIR/shareland/"* ./shareland/
elif [ -d "$BACKUP_DIR" ]; then
    # If backup is the project root itself
    cp -r "$BACKUP_DIR/"* ./shareland/ 2>/dev/null || true
fi

# Copy media files
if [ -d "$BACKUP_DIR/media" ]; then
    echo "Copying media files..."
    cp -r "$BACKUP_DIR/media/"* ./media/ 2>/dev/null || mkdir -p ./media && cp -r "$BACKUP_DIR/media/"* ./media/
fi

# Copy static files
if [ -d "$BACKUP_DIR/static" ]; then
    echo "Copying static files..."
    cp -r "$BACKUP_DIR/static/"* ./static/ 2>/dev/null || mkdir -p ./static && cp -r "$BACKUP_DIR/static/"* ./static/
fi

# Step 2: Copy database dump
echo ""
echo "Step 2: Setting up database dump..."
cp "$DUMP_FILE" ./open_landscapes2605.dump
echo "✓ Database dump copied"

# Step 3: Update docker-compose.yml to use the dump
echo ""
echo "Step 3: Updating docker-compose.yml..."
if ! grep -q "open_landscapes2605.dump" docker-compose.yml; then
    # Update postgres service to include dump file
    sed -i '/volumes:/a\      - ./open_landscapes2605.dump:/docker-entrypoint-initdb.d/open_landscapes2605.dump:ro' docker-compose.yml
fi

# Step 4: Start Docker services
echo ""
echo "Step 4: Starting Docker services..."
docker-compose down -v 2>/dev/null
docker-compose up -d --build

echo ""
echo "Waiting for PostgreSQL to be ready..."
sleep 10

# Step 5: Load database
echo ""
echo "Step 5: Loading database..."

# Check if dump is custom format or SQL
if [[ "$DUMP_FILE" == *.dump ]]; then
    echo "Loading custom format dump..."
    docker-compose exec -T postgres pg_restore -U postgres -d Open_Landscapes -v /docker-entrypoint-initdb.d/open_landscapes2605.dump 2>&1 | tail -5
else
    echo "Loading SQL dump..."
    docker cp "$DUMP_FILE" shareland_postgres:/tmp/dump.sql
    docker-compose exec -T postgres psql -U postgres -d Open_Landscapes -f /tmp/dump.sql 2>&1 | tail -5
fi

# Step 6: Run migrations
echo ""
echo "Step 6: Running Django migrations..."
docker-compose exec -T web python manage.py migrate --fake 2>&1 | tail -5

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Services are running:"
echo "  - Django: http://localhost:8000"
echo "  - pgAdmin: http://localhost:5050"
echo "  - PostgreSQL: localhost:5433"
echo ""
echo "To view logs: docker-compose logs -f web"






















