#!/bin/bash

# Script to start the ShareLAND Django project in Docker

echo "Building and starting Docker containers..."
docker-compose up -d --build

echo "Waiting for PostgreSQL to be ready..."
sleep 5

echo "Running Django migrations..."
docker-compose exec web python manage.py migrate

echo "Creating superuser (if needed)..."
echo "You can create a superuser manually with: docker-compose exec web python manage.py createsuperuser"

echo ""
echo "Services are running:"
echo "  - Django web app: http://localhost:8000"
echo "  - pgAdmin: http://localhost:5050"
echo "  - PostgreSQL: localhost:5433"
echo ""
echo "To view logs: docker-compose logs -f web"
echo "To stop: docker-compose down"






















