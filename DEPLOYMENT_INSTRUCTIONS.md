# Deployment Instructions

## Quick Deploy

Since direct SSH access from this machine may be restricted, you have two options:

### Option 1: Run from Your Local Machine (Recommended)

If you have SSH access to the VPS from your local machine:

```bash
# Make sure you're in the project directory
cd /home/ergin/PycharmProjects/SHAReLAND_v.1.0

# Run the deployment script
./update_vps_code.sh
```

When prompted, type `y` and press Enter to continue.

### Option 2: Run Non-Interactive Version

```bash
./update_vps_code_auto.sh
```

This version doesn't require confirmation and starts automatically.

### Option 3: Manual Deployment via SSH

If you prefer to deploy manually, SSH into the VPS and run these commands:

```bash
# 1. SSH to VPS
ssh root@5.249.148.147

# 2. Create database backup
mkdir -p /var/backups/shareland
BACKUP_FILE="/var/backups/shareland/shareland_backup_$(date +%Y%m%d_%H%M%S).sql"
sudo -u postgres pg_dump shareland_db > $BACKUP_FILE
echo "Backup created: $BACKUP_FILE"

# 3. Update code from GitHub
cd /var/www/shareland/repo
sudo -u shareland git fetch origin
sudo -u shareland git pull origin main

# 4. Update Python dependencies
cd /var/www/shareland/repo/shareland
source /var/www/shareland/venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 5. Update Gunicorn configuration
cat > /var/www/shareland/gunicorn_config.py << 'EOF'
import multiprocessing
import os

bind = "127.0.0.1:8001"
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
worker_connections = 1000
timeout = int(os.getenv('GUNICORN_TIMEOUT', '120'))
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
preload_app = True
accesslog = "/var/log/shareland/gunicorn_access.log"
errorlog = "/var/log/shareland/gunicorn_error.log"
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')
proc_name = "shareland"
graceful_timeout = 30
EOF
chown shareland:shareland /var/www/shareland/gunicorn_config.py

# 6. Run database migrations
set -a
source /var/www/shareland/.env
set +a
python manage.py migrate --settings=ShareLand.settings_production

# 7. Collect static files
python manage.py collectstatic --noinput --settings=ShareLand.settings_production

# 8. Verify Nginx configuration (preserved, no changes)
nginx -t
systemctl reload nginx

# 9. Restart application
supervisorctl restart shareland
sleep 3

# 10. Verify deployment
supervisorctl status shareland
```

## What the Deployment Does

1. ✅ **Creates database backup** - Safety first!
2. ✅ **Pulls latest code** from GitHub
3. ✅ **Updates dependencies** - Installs/updates Python packages
4. ✅ **Updates Gunicorn config** - Sets timeout to 120s, multiple workers
5. ✅ **Runs migrations** - Updates database schema (data preserved)
6. ✅ **Collects static files** - Updates CSS/JS files
7. ✅ **Preserves Nginx config** - No changes to Nginx
8. ✅ **Restarts application** - Applies all changes

## Verification After Deployment

```bash
# Check application status
ssh root@5.249.148.147 'supervisorctl status shareland'

# Monitor logs
ssh root@5.249.148.147 'tail -f /var/log/shareland/gunicorn_error.log'

# Test the application
curl -I http://5.249.148.147

# Check Gunicorn timeout
ssh root@5.249.148.147 'grep timeout /var/www/shareland/gunicorn_config.py'
```

## Troubleshooting

### SSH Connection Refused

If you get "Connection refused":
1. Check if the VPS IP is correct: `5.249.148.147`
2. Verify SSH is running on the VPS
3. Check firewall settings
4. Try from a different network

### Permission Denied

If you get "Permission denied":
1. Make sure you're using the correct user: `root`
2. Check if SSH keys are set up
3. You may need to use password authentication

### Application Won't Start

```bash
# Check logs
ssh root@5.249.148.147 'tail -100 /var/log/shareland/gunicorn_error.log'

# Check supervisor
ssh root@5.249.148.147 'supervisorctl status shareland'

# Restart manually
ssh root@5.249.148.147 'supervisorctl restart shareland'
```

## Important Notes

- ✅ **Database is safe** - All data is preserved
- ✅ **Nginx config preserved** - No changes to web server
- ✅ **Backup created** - Located in `/var/backups/shareland/`
- ⚠️ **Brief downtime** - 5-10 seconds during restart

## Next Steps After Deployment

1. Verify the application is accessible
2. Check that Gunicorn timeout errors are resolved
3. Monitor logs for any issues
4. Test key functionality (evidence API, etc.)





