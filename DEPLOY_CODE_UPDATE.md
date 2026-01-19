# Deploy Code Updates to VPS (Preserving Database)

This guide explains how to push code updates to your VPS while **keeping the existing database intact**.

## ⚠️ Important: Database Safety

The database will **NOT** be affected by code updates. However, it's always recommended to backup before major updates.

## Prerequisites

- VPS IP: `5.249.148.147`
- VPS User: `root`
- SSH access to VPS
- Your code changes committed and pushed to Git repository

## Method 1: Quick Update (Recommended)

### Step 1: Backup Database (Optional but Recommended)

```bash
ssh root@5.249.148.147

# Create backup directory
mkdir -p /var/backups/shareland
cd /var/backups/shareland

# Backup database
sudo -u postgres pg_dump shareland_db > shareland_backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh shareland_backup_*.sql
```

### Step 2: Update Code from Git

```bash
ssh root@5.249.148.147
cd /var/www/shareland/repo

# Pull latest changes
sudo -u shareland git pull origin main

# Verify you're on the correct branch
git branch
git log -1 --oneline
```

### Step 3: Update Python Dependencies (if requirements.txt changed)

```bash
cd /var/www/shareland/repo
source ../venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt
```

### Step 4: Run Database Migrations (Schema Changes Only)

**⚠️ Important**: Migrations only change database schema (tables, columns, indexes), **NOT** existing data.

```bash
cd /var/www/shareland/repo
source ../venv/bin/activate

# Load environment variables
set -a
source /var/www/shareland/.env
set +a

# Run migrations (this only updates schema, preserves all data)
python manage.py migrate --settings=ShareLand.settings_production
```

### Step 5: Collect Static Files

```bash
cd /var/www/shareland/repo
source ../venv/bin/activate

# Load environment variables
set -a
source /var/www/shareland/.env
set +a

# Collect static files
python manage.py collectstatic --noinput --settings=ShareLand.settings_production
```

### Step 6: Restart Application

```bash
# Restart Gunicorn (Django application)
supervisorctl restart shareland

# Verify it's running
supervisorctl status shareland

# Reload Nginx (if needed)
systemctl reload nginx
```

### Step 7: Verify Deployment

```bash
# Check application logs
tail -f /var/log/shareland/gunicorn_error.log

# Check if application is responding
curl -I http://localhost:8001

# Check supervisor status
supervisorctl status
```

## Method 2: One-Command Update Script

Create a script for easier updates:

```bash
# On your local machine, create update_vps.sh
cat > update_vps.sh << 'EOF'
#!/bin/bash

VPS_IP="5.249.148.147"
APP_DIR="/var/www/shareland"

echo "Updating ShareLand on VPS..."

ssh root@${VPS_IP} << 'ENDSSH'
set -e

cd /var/www/shareland/repo

# Backup database
echo "Creating database backup..."
mkdir -p /var/backups/shareland
sudo -u postgres pg_dump shareland_db > /var/backups/shareland/shareland_backup_$(date +%Y%m%d_%H%M%S).sql

# Pull latest code
echo "Pulling latest code..."
sudo -u shareland git pull origin main

# Update dependencies
echo "Updating dependencies..."
cd /var/www/shareland/repo
source ../venv/bin/activate
pip install -r requirements.txt

# Run migrations
echo "Running migrations..."
set -a
source /var/www/shareland/.env
set +a
python manage.py migrate --settings=ShareLand.settings_production

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --settings=ShareLand.settings_production

# Restart application
echo "Restarting application..."
supervisorctl restart shareland

# Verify
echo "Verifying deployment..."
sleep 2
supervisorctl status shareland

echo "Update complete!"
ENDSSH

echo "Deployment finished!"
EOF

chmod +x update_vps.sh
```

Then run:
```bash
./update_vps.sh
```

## Method 3: Using Docker (If VPS Uses Docker)

If your VPS uses Docker Compose:

```bash
ssh root@5.249.148.147
cd /path/to/shareland

# Backup database
docker-compose exec db pg_dump -U postgres shareland_v1 > backup_$(date +%Y%m%d_%H%M%S).sql

# Pull latest code
git pull origin main

# Rebuild and restart containers (database volume persists)
docker-compose down
docker-compose build
docker-compose up -d

# Run migrations
docker-compose exec django python manage.py migrate

# Collect static files
docker-compose exec django python manage.py collectstatic --noinput
```

## What Gets Updated vs. What Stays the Same

### ✅ Updated (Code Changes)
- Python code (views, models, templates, etc.)
- Static files (CSS, JS, images)
- Configuration files
- Dependencies (if requirements.txt changed)

### ✅ Updated (Schema Only - Data Preserved)
- Database migrations (adds/modifies tables/columns)
- **All existing data remains intact**

### ❌ NOT Updated (Preserved)
- **All database data** (sites, evidences, users, etc.)
- Media files (uploaded images, documents)
- Database credentials
- Environment variables (unless you change them)

## Troubleshooting

### Application Won't Start

```bash
# Check logs
tail -100 /var/log/shareland/gunicorn_error.log

# Check supervisor
supervisorctl status shareland

# Restart
supervisorctl restart shareland
```

### Migration Errors

```bash
# Check migration status
cd /var/www/shareland/repo
source ../venv/bin/activate
python manage.py showmigrations --settings=ShareLand.settings_production

# If migration fails, you can rollback using the backup
sudo -u postgres psql shareland_db < /var/backups/shareland/shareland_backup_YYYYMMDD_HHMMSS.sql
```

### Static Files Not Loading

```bash
# Re-collect static files
cd /var/www/shareland/repo
source ../venv/bin/activate
set -a
source /var/www/shareland/.env
set +a
python manage.py collectstatic --noinput --settings=ShareLand.settings_production

# Reload Nginx
systemctl reload nginx
```

### Database Connection Issues

```bash
# Test PostgreSQL
sudo -u postgres psql -c "SELECT 1;"

# Check database exists
sudo -u postgres psql -l | grep shareland_db

# Verify .env file has correct credentials
cat /var/www/shareland/.env
```

## Best Practices

1. **Always backup before major updates**
2. **Test migrations locally first** if possible
3. **Update during low-traffic periods**
4. **Monitor logs after deployment**
5. **Keep backups for at least 7 days**

## Quick Reference Commands

```bash
# SSH to VPS
ssh root@5.249.148.147

# Navigate to app
cd /var/www/shareland/repo

# Pull code
sudo -u shareland git pull origin main

# Activate venv
source ../venv/bin/activate

# Load env vars
set -a && source /var/www/shareland/.env && set +a

# Run migrations
python manage.py migrate --settings=ShareLand.settings_production

# Collect static
python manage.py collectstatic --noinput --settings=ShareLand.settings_production

# Restart app
supervisorctl restart shareland

# Check status
supervisorctl status shareland
tail -f /var/log/shareland/gunicorn_error.log
```

## Summary

**To update code without touching database:**

1. Backup database (optional but recommended)
2. `git pull` latest code
3. `pip install -r requirements.txt` (if needed)
4. `python manage.py migrate` (schema only, data preserved)
5. `python manage.py collectstatic` (static files)
6. `supervisorctl restart shareland` (restart app)

**Your database data will remain completely intact!** 🎉








