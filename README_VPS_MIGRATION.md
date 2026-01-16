# Migrating ShareLAND from Aruba VPS to Local Docker

This guide helps you copy a ShareLAND site running on an Aruba VPS and run it locally in Docker.

## Prerequisites

- SSH access to the VPS (root@89.36.211.235)
- Docker and Docker Compose installed locally
- rsync installed locally
- PostgreSQL client tools installed locally

## Step 1: Copy Files from VPS

### Option A: Using the Automated Script

```bash
chmod +x copy_from_vps.sh
./copy_from_vps.sh
```

The script will:
- Ask for the project path on the VPS
- Copy Django project files
- Copy media and static files
- Export the database

### Option B: Manual Copy

#### 1. Copy Django Project

```bash
# Find the project path on VPS first
ssh root@89.36.211.235 "find / -name 'manage.py' -type f 2>/dev/null | grep shareland"

# Copy project (replace /path/to/shareland with actual path)
rsync -avz --exclude '*.pyc' --exclude '__pycache__' \
    --exclude 'venv/' --exclude '.venv/' \
    root@89.36.211.235:/path/to/shareland/ ./shareland_backup/
```

#### 2. Copy Media Files

```bash
rsync -avz root@89.36.211.235:/path/to/shareland/media/ ./shareland_backup/media/
```

#### 3. Copy Static Files

```bash
rsync -avz root@89.36.211.235:/path/to/shareland/static/ ./shareland_backup/static/
```

#### 4. Export Database

```bash
# Custom format dump (recommended)
ssh root@89.36.211.235 "PGPASSWORD=your_password pg_dump -U postgres -h localhost -Fc shareland" > ./shareland_backup/database.dump

# Or SQL format
ssh root@89.36.211.235 "PGPASSWORD=your_password pg_dump -U postgres -h localhost shareland" > ./shareland_backup/database.sql
```

## Step 2: Set Up Local Docker Environment

### Option A: Using the Automated Script

```bash
chmod +x setup_local_docker.sh
./setup_local_docker.sh [backup_directory]
```

### Option B: Manual Setup

#### 1. Copy Files to Project Directory

```bash
# Copy project files
cp -r ./shareland_backup/* ./shareland/

# Copy media
cp -r ./shareland_backup/media/* ./media/

# Copy static
cp -r ./shareland_backup/static/* ./static/

# Copy database dump
cp ./shareland_backup/database.dump ./open_landscapes2605.dump
```

#### 2. Update Settings

Check and update `shareland/shareland/settings.py`:
- Database name (should match your dump)
- Database credentials
- ALLOWED_HOSTS
- Static/Media paths

#### 3. Start Docker Services

```bash
docker-compose down -v
docker-compose up -d --build
```

#### 4. Load Database

Wait for PostgreSQL to be ready, then:

```bash
# For custom format dump
docker cp ./open_landscapes2605.dump shareland_postgres:/tmp/dump.dump
docker-compose exec -T postgres pg_restore -U postgres -d Open_Landscapes -v /tmp/dump.dump

# For SQL dump
docker cp ./open_landscapes2605.dump shareland_postgres:/tmp/dump.sql
docker-compose exec -T postgres psql -U postgres -d Open_Landscapes -f /tmp/dump.sql
```

#### 5. Run Migrations

```bash
docker-compose exec -T web python manage.py migrate --fake
```

## Step 3: Verify

1. Check services: `docker-compose ps`
2. Check logs: `docker-compose logs web`
3. Access site: http://localhost:8000
4. Access pgAdmin: http://localhost:5050

## Troubleshooting

### Database Connection Issues

- Check database name matches in settings.py and docker-compose.yml
- Verify PostgreSQL is healthy: `docker-compose ps`
- Check database exists: `docker-compose exec -T postgres psql -U postgres -c "\l"`

### Template Errors

- Ensure all templates are copied
- Check template paths in views.py match actual template locations

### Static/Media Files

- Verify files are copied to ./media and ./static
- Check volume mounts in docker-compose.yml
- Run collectstatic if needed: `docker-compose exec web python manage.py collectstatic --noinput`

### Migration Issues

- If migrations fail, use `--fake` flag
- Check Django version compatibility
- Review migration files for compatibility issues

## Quick Commands Reference

```bash
# View logs
docker-compose logs -f web

# Access Django shell
docker-compose exec web python manage.py shell

# Access PostgreSQL
docker-compose exec postgres psql -U postgres -d Open_Landscapes

# Restart services
docker-compose restart

# Stop everything
docker-compose down

# Stop and remove volumes
docker-compose down -v
```



















