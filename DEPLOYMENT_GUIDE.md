# ShareLand VPS Deployment Guide

## Overview
This guide provides complete instructions for deploying the ShareLand application to an Aruba VPS without Docker.

## Prerequisites
- VPS IP: `5.249.148.147`
- VPS User: `root`
- VPS Password: `Sh@r3l@nd2025/26`
- Root access to the VPS
- Git repository: `https://github.com/ergin84/ShareLand.git`

## Architecture
```
Internet → Nginx (Reverse Proxy, Port 80/443) → Gunicorn (Port 8001) → Django App
                                              ↓
                                        PostgreSQL (Port 5432)
```

## Quick Start (One-Command Deployment)

### Option 1: Automated Deployment (Recommended)

From your local machine:

```bash
cd /path/to/SHAReLAND_v.1.0
bash deploy_launcher.sh
```

This will:
1. Upload the deployment script to the VPS
2. Run the complete installation automatically
3. Configure all services
4. Report results

### Option 2: Manual Deployment

If you prefer to run commands manually:

```bash
# 1. Copy the deployment script to VPS
scp deploy_vps.sh root@5.249.148.147:/tmp/

# 2. SSH into the VPS
ssh root@5.249.148.147
# Password: Sh@r3l@nd2025/26

# 3. Run the deployment script
cd /tmp
chmod +x deploy_vps.sh
bash deploy_vps.sh
```

## What Gets Installed

### System Packages
- Python 3.12 with development headers
- PostgreSQL 15
- Nginx
- Gunicorn (Python WSGI server)
- Supervisor (process manager)
- Certbot (SSL certificates)
- Redis (caching/sessions)
- Build tools and libraries

### Application Structure
```
/var/www/shareland/
├── repo/                    # GitHub repository
│   ├── shareland/          # Django project
│   ├── frontend/           # Frontend app
│   ├── manage.py
│   └── requirements.txt
├── venv/                   # Python virtual environment
├── static/                 # Collected static files
├── media/                  # User uploads
├── .env                    # Environment variables
└── gunicorn_config.py      # Gunicorn configuration
```

### Directories
- **App Dir**: `/var/www/shareland`
- **Static Files**: `/var/www/shareland/static`
- **Media Files**: `/var/www/shareland/media`
- **Logs**: `/var/log/shareland`
- **Database**: PostgreSQL on localhost:5432

## Configuration

### Generated Credentials
After deployment, save these securely:
- **Database User**: `shareland_user`
- **Database Password**: (random, shown in output)
- **Django Secret Key**: (random, shown in output)

### Environment Variables (.env)
Located at `/var/www/shareland/.env`:
```
DEBUG=False
SECRET_KEY=<generated>
DB_NAME=shareland_db
DB_USER=shareland_user
DB_PASSWORD=<generated>
DB_HOST=localhost
DB_PORT=5432
ALLOWED_HOSTS=5.249.148.147,shareland.example.com,www.shareland.example.com
```

### Django Settings
Production settings at: `/var/www/shareland/repo/shareland/settings_production.py`

Key configurations:
- Static files: `/var/www/shareland/static`
- Media files: `/var/www/shareland/media`
- Database: PostgreSQL
- Debug mode: OFF
- SSL: HTTPS enforced

## Post-Deployment Setup

### 1. Create Superuser
```bash
ssh root@5.249.148.147
cd /var/www/shareland/repo
source ../venv/bin/activate
python manage.py createsuperuser --settings=shareland.settings_production
```

### 2. Configure SSL (Highly Recommended)
```bash
ssh root@5.249.148.147
certbot --nginx -d shareland.it -d www.shareland.it
```

### 3. Update Domain (Already Set)
The domain shareland.it is configured in:
- `/etc/nginx/sites-available/shareland`
- `/var/www/shareland/repo/shareland/settings_production.py`

Then restart services:
```bash
systemctl reload nginx
supervisorctl restart shareland
```

### 4. Access the Application
- **Web**: `http://5.249.148.147` or `https://shareland.it`
- **Admin**: `/admin/`
- **API**: `/api/`

## Service Management

### Check Application Status
```bash
ssh root@5.249.148.147
supervisorctl status
```

### Restart Application
```bash
ssh root@5.249.148.147
supervisorctl restart shareland
```

### View Logs
```bash
# Gunicorn errors
tail -f /var/log/shareland/gunicorn_error.log

# Gunicorn access
tail -f /var/log/shareland/gunicorn_access.log

# Nginx errors
tail -f /var/log/shareland/nginx_error.log

# Django errors
tail -f /var/log/shareland/django.log
```

### Restart Services
```bash
# Restart Nginx
systemctl restart nginx

# Restart Gunicorn
supervisorctl restart shareland

# Restart both
systemctl restart nginx && supervisorctl restart shareland
```

## Database Management

### PostgreSQL Access
```bash
ssh root@5.249.148.147
sudo -u postgres psql
\c shareland_db
```

### Backup Database
```bash
sudo -u postgres pg_dump shareland_db > shareland_backup.sql
```

### Restore Database
```bash
sudo -u postgres psql shareland_db < shareland_backup.sql
```

## Updating the Application

### Pull Latest Changes
```bash
ssh root@5.249.148.147
cd /var/www/shareland/repo
sudo -u shareland git pull origin main
source ../venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --settings=shareland.settings_production
python manage.py collectstatic --noinput --settings=shareland.settings_production
supervisorctl restart shareland
```

## Troubleshooting

### Application Not Starting
```bash
# Check supervisor status
supervisorctl status

# Check gunicorn logs
tail -100 /var/log/shareland/gunicorn_error.log

# Restart
supervisorctl restart shareland
```

### Database Connection Issues
```bash
# Test PostgreSQL connection
sudo -u postgres psql -c "SELECT 1;"

# Check database exists
sudo -u postgres psql -l
```

### Static Files Not Loading
```bash
# Collect static files again
cd /var/www/shareland/repo
source ../venv/bin/activate
python manage.py collectstatic --noinput --settings=shareland.settings_production

# Check Nginx config
nginx -t
systemctl reload nginx
```

### Permission Issues
```bash
# Fix ownership
chown -R shareland:shareland /var/www/shareland
chown -R shareland:shareland /var/log/shareland
```

## Security Recommendations

### After Deployment
1. **Change Root Password**: Use a strong, unique password
2. **SSH Key Setup**: Replace password authentication with SSH keys
3. **Firewall**: Configure UFW or fail2ban
4. **SSL Certificates**: Install Let's Encrypt certificates
5. **Regular Backups**: Set up automated database backups
6. **Monitoring**: Configure server monitoring and alerts

### Example: Setup SSH Keys
```bash
# On your local machine
ssh-keygen -t ed25519 -C "shareland@example.com"

# Copy public key to VPS
ssh-copy-id -i ~/.ssh/id_ed25519.pub root@5.249.148.147

# SSH into VPS and disable password auth in /etc/ssh/sshd_config
ssh root@5.249.148.147
# Edit /etc/ssh/sshd_config:
# - Set PasswordAuthentication no
# - Set PubkeyAuthentication yes
systemctl restart ssh
```

## Maintenance

### Regular Tasks
- Monitor disk space
- Check application logs
- Monitor database size
- Verify SSL certificate expiry
- Test backups

### Monthly
- Update system packages: `apt-get update && apt-get upgrade`
- Review application logs
- Check for security updates

### Yearly
- Full security audit
- Test disaster recovery
- Review and optimize database indexes

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review application logs in `/var/log/shareland/`
3. Consult Django documentation: https://docs.djangoproject.com/
4. Check PostgreSQL documentation: https://www.postgresql.org/docs/

## Additional Resources

- Django Deployment: https://docs.djangoproject.com/en/stable/howto/deployment/
- Gunicorn: https://gunicorn.org/
- Nginx: https://nginx.org/en/docs/
- PostgreSQL: https://www.postgresql.org/docs/
- Supervisor: http://supervisord.org/

---

**Deployment Date**: [Current Date]
**VPS IP**: 5.249.148.147
**Domain**: shareland.it
**Repository**: https://github.com/ergin84/ShareLand.git
