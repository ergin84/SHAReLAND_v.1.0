# Deploy New Version to VPS (Preserving Database)

This guide explains how to deploy the new version of ShareLand to your VPS while **preserving all existing database data**.

## What's New in This Version

- ✅ **Gunicorn timeout increased** from 30s to 120s (fixes worker timeout errors)
- ✅ **Multiple workers** for better performance
- ✅ **Optimized evidence API** endpoint
- ✅ **Improved Gunicorn configuration** file

## Quick Deploy

### Step 1: Run the Update Script

```bash
./update_vps_code.sh
```

The script will:
1. ✅ Create a database backup (safety first!)
2. ✅ Pull latest code from GitHub
3. ✅ Update Python dependencies
4. ✅ Update Gunicorn configuration (new timeout settings)
5. ✅ Run database migrations (schema only, data preserved)
6. ✅ Collect static files
7. ✅ Restart the application

### Step 2: Verify Deployment

```bash
# Check application status
ssh root@5.249.148.147 'supervisorctl status shareland'

# Monitor logs
ssh root@5.249.148.147 'tail -f /var/log/shareland/gunicorn_error.log'

# Test the application
curl -I http://5.249.148.147
```

## What Gets Updated

### ✅ Code Updates (No Data Loss)
- Python application code
- Static files (CSS, JS)
- Gunicorn configuration
- Dependencies

### ✅ Database Schema Updates Only
- Migrations run automatically
- **All existing data is preserved**
- Only table structure changes (if any)

### ❌ NOT Updated (Preserved)
- **All database data** (sites, evidences, users, etc.)
- Media files (uploaded images)
- Environment variables
- Database credentials

## Manual Deployment Steps

If you prefer to deploy manually:

### 1. Backup Database (Recommended)

```bash
ssh root@5.249.148.147
mkdir -p /var/backups/shareland
sudo -u postgres pg_dump shareland_db > /var/backups/shareland/shareland_backup_$(date +%Y%m%d_%H%M%S).sql
```

### 2. Update Code from GitHub

```bash
cd /var/www/shareland/repo
sudo -u shareland git fetch origin
sudo -u shareland git pull origin main
```

### 3. Update Dependencies

```bash
cd /var/www/shareland/repo/shareland
source /var/www/shareland/venv/bin/activate
pip install -r requirements.txt
```

### 4. Update Gunicorn Config

The new `gunicorn_config.py` will be automatically copied from the repository. It includes:
- Timeout: 120 seconds (was 30)
- Multiple workers
- Better logging configuration

### 5. Run Migrations

```bash
cd /var/www/shareland/repo/shareland
source /var/www/shareland/venv/bin/activate
set -a
source /var/www/shareland/.env
set +a
python manage.py migrate --settings=ShareLand.settings_production
```

### 6. Collect Static Files

```bash
python manage.py collectstatic --noinput --settings=ShareLand.settings_production
```

### 7. Restart Application

```bash
supervisorctl restart shareland
supervisorctl status shareland
```

## Troubleshooting

### Application Won't Start

```bash
# Check logs
ssh root@5.249.148.147 'tail -100 /var/log/shareland/gunicorn_error.log'

# Check supervisor status
ssh root@5.249.148.147 'supervisorctl status shareland'

# Restart
ssh root@5.249.148.147 'supervisorctl restart shareland'
```

### Gunicorn Timeout Still Occurring

If you still see timeout errors after deployment:

1. Check the config file:
```bash
ssh root@5.249.148.147 'grep timeout /var/www/shareland/gunicorn_config.py'
```

Should show: `timeout = 120`

2. Verify Gunicorn is using the config:
```bash
ssh root@5.249.148.147 'ps aux | grep gunicorn'
```

Should show: `-c /var/www/shareland/gunicorn_config.py`

### Database Connection Issues

```bash
# Test PostgreSQL
ssh root@5.249.148.147 'sudo -u postgres psql -c "SELECT 1;"'

# Check database exists
ssh root@5.249.148.147 'sudo -u postgres psql -l | grep shareland_db'
```

### Rollback (If Needed)

If something goes wrong, you can restore from backup:

```bash
ssh root@5.249.148.147
sudo -u postgres psql shareland_db < /var/backups/shareland/shareland_backup_YYYYMMDD_HHMMSS.sql
```

## Important Notes

1. **Database is Safe**: The deployment process only updates code and schema. All data remains intact.

2. **Backups**: The script automatically creates a backup before updating. Backups are stored in `/var/backups/shareland/`

3. **Downtime**: There will be a brief downtime (5-10 seconds) when restarting Gunicorn.

4. **GitHub Repository**: Make sure your code is pushed to `https://github.com/ergin84/SHAReLAND_v.1.0.git`

## Verification Checklist

After deployment, verify:

- [ ] Application is accessible: `http://5.249.148.147`
- [ ] No errors in logs: `tail -f /var/log/shareland/gunicorn_error.log`
- [ ] Database data is intact (check a few records)
- [ ] Gunicorn timeout is 120s: `grep timeout /var/www/shareland/gunicorn_config.py`
- [ ] Workers are running: `ps aux | grep gunicorn | wc -l` (should be > 1)

## Summary

**To deploy new version preserving database:**

```bash
./update_vps_code.sh
```

That's it! The script handles everything automatically while keeping your database safe. 🎉






