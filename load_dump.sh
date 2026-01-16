#!/bin/bash

# Script to load PostgreSQL dump file into Docker container

echo "Starting PostgreSQL container..."
docker-compose up -d postgres

echo "Waiting for PostgreSQL to be ready..."
sleep 5

# Wait for PostgreSQL to be fully ready
until docker exec shareland_postgres pg_isready -U postgres > /dev/null 2>&1; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

echo "PostgreSQL is ready. Loading dump file..."

# Load the dump file using pg_restore
docker exec -i shareland_postgres pg_restore -U postgres -d shareland -v /docker-entrypoint-initdb.d/open_landscapes2605.dump

if [ $? -eq 0 ]; then
    echo "✓ Dump file loaded successfully!"
    echo ""
    echo "Connection details:"
    echo "  Host: localhost"
    echo "  Port: 5432"
    echo "  Database: shareland"
    echo "  User: postgres"
    echo "  Password: postgres"
else
    echo "✗ Error loading dump file. Trying alternative method..."
    
    # Alternative: copy dump to container and restore
    docker cp open_landscapes2605.dump shareland_postgres:/tmp/open_landscapes2605.dump
    docker exec shareland_postgres pg_restore -U postgres -d shareland -v /tmp/open_landscapes2605.dump
    
    if [ $? -eq 0 ]; then
        echo "✓ Dump file loaded successfully using alternative method!"
    else
        echo "✗ Failed to load dump file. Please check the dump file format."
        exit 1
    fi
fi





















