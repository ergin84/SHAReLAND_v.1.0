# ShareLand VPS Deployment - Complete Guide

## Quick Deployment Options

### Option 1: Full Deployment with SSL (Recommended)
Deploy everything in one command:
```bash
cd /home/ergin/PycharmProjects/SHAReLAND_v.1.0
bash full_deploy.sh
```

This will:
1. Install and configure the application
2. Set up PostgreSQL database
3. Install and configure Nginx
4. Create SSL certificate from Let's Encrypt
5. Configure automatic HTTP → HTTPS redirect
6. Enable automatic certificate renewal

⏱️ **Duration**: 15-20 minutes

---

### Option 2: Application Only (No SSL)
```bash
bash quick_deploy.sh
```

Then later add SSL:
```bash
sshpass -p "Sh@r3l@nd2025/26" scp setup_ssl.sh root@5.249.148.147:/tmp/
sshpass -p "Sh@r3l@nd2025/26" ssh root@5.249.148.147 "bash /tmp/setup_ssl.sh"
```

---

### Option 3: Manual Step-by-Step
```bash
# Upload scripts
scp deploy_vps.sh root@5.249.148.147:/tmp/
scp setup_ssl.sh root@5.249.148.147:/tmp/

# SSH into VPS
ssh root@5.249.148.147
# Password: Sh@r3l@nd2025/26

# Run deployment
bash /tmp/deploy_vps.sh
bash /tmp/setup_ssl.sh
```

---

## What Gets Configured

### SSL Certificate
- **Provider**: Let's Encrypt
- **Domain**: shareland.it
- **Alternate**: www.shareland.it
- **Auto-renewal**: Enabled (checks daily)
- **Renewal email**: admin@shareland.it

### Nginx Configuration
```
HTTP (Port 80)  ──→ Automatically redirects to HTTPS (Port 443)
HTTPS (Port 443) ──→ Gunicorn Application
```

### Security Headers (Automatic)
```
Strict-Transport-Security: max-age=31536000
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: no-referrer-when-downgrade
```

### SSL Protocols
- **TLS 1.2** (minimum)
- **TLS 1.3** (preferred)
- Strong ciphers only
- Session caching enabled

---

## After Deployment

### 1. Create Admin User
```bash
sshpass -p "Sh@r3l@nd2025/26" ssh root@5.249.148.147

cd /var/www/shareland/repo
source ../venv/bin/activate
python manage.py createsuperuser --settings=shareland.settings_production
```

### 2. Access Your Site
- **Main Site**: https://shareland.it
- **Admin Panel**: https://shareland.it/admin/
- **Alternate Domain**: https://www.shareland.it (auto-redirect available)

### 3. Monitor Application
```bash
# Watch error logs
tail -f /var/log/shareland/gunicorn_error.log

# Check application status
supervisorctl status

# View Nginx logs
tail -f /var/log/shareland/nginx_error.log
```

---

## SSL Certificate Management

### View Certificate Details
```bash
ssh root@5.249.148.147
certbot certificates
```

### Manual Renewal (optional)
```bash
# Test renewal (doesn't actually renew)
sudo certbot renew --dry-run

# Actually renew
sudo certbot renew
```

### View Renewal Logs
```bash
tail -f /var/log/letsencrypt/letsencrypt.log
```

---

## File Locations

| Purpose | Location |
|---------|----------|
| Application Code | `/var/www/shareland/repo` |
| Static Files | `/var/www/shareland/static` |
| User Uploads | `/var/www/shareland/media` |
| Logs | `/var/log/shareland/` |
| Nginx Config | `/etc/nginx/sites-available/shareland` |
| SSL Cert | `/etc/letsencrypt/live/shareland.it/` |
| Environment | `/var/www/shareland/.env` |

---

## Troubleshooting

### SSL Certificate Not Working
```bash
# Check certificate status
certbot certificates

# Check Nginx config
nginx -t

# View Nginx error log
tail -20 /var/log/shareland/nginx_error.log
```

### HTTP Not Redirecting to HTTPS
```bash
# Verify Nginx config includes redirect
grep -A 5 "return 301" /etc/nginx/sites-available/shareland

# Reload Nginx
systemctl reload nginx
```

### Certificate Renewal Failed
```bash
# Check renewal logs
tail -50 /var/log/letsencrypt/letsencrypt.log

# Manual renewal
certbot renew --force-renewal
```

### Application Not Running
```bash
# Check Gunicorn status
supervisorctl status shareland

# View error log
tail -50 /var/log/shareland/gunicorn_error.log

# Restart
supervisorctl restart shareland
```

---

## Security Checklist

After deployment, verify:

- [ ] HTTPS is working: https://shareland.it
- [ ] HTTP redirects to HTTPS
- [ ] SSL certificate is valid (no warnings)
- [ ] Admin user created
- [ ] Can access admin panel
- [ ] Application loads without errors
- [ ] SSL Labs grade A or higher

### Check SSL Quality
Visit: https://www.ssllabs.com/ssltest/analyze.html?d=shareland.it

---

## Updating the Application

When you push updates to GitHub:

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

---

## Backup & Restore

### Database Backup
```bash
ssh root@5.249.148.147
sudo -u postgres pg_dump shareland_db > ~/shareland_backup.sql
```

### Download Backup Locally
```bash
sshpass -p "Sh@r3l@nd2025/26" scp root@5.249.148.147:~/shareland_backup.sql ./
```

### Restore from Backup
```bash
ssh root@5.249.148.147
sudo -u postgres psql shareland_db < ~/shareland_backup.sql
```

---

## Performance Optimization

### View Current Settings
```bash
# Check Gunicorn workers
grep "workers" /var/www/shareland/gunicorn_config.py

# Check system resources
ssh root@5.249.148.147
htop
```

### Increase Workers (if needed)
```bash
ssh root@5.249.148.147
# Edit /var/www/shareland/gunicorn_config.py
# Increase 'workers' value
supervisorctl restart shareland
```

---

## Support & Help

**Scripts Provided:**
- `full_deploy.sh` - Complete deployment with SSL (RECOMMENDED)
- `setup_ssl.sh` - SSL setup only
- `quick_deploy.sh` - Application only
- `deploy_vps.sh` - Raw deployment script
- `deploy_launcher.sh` - Alternative launcher

**Server Details:**
- VPS IP: 5.249.148.147
- Domain: shareland.it
- Repository: https://github.com/ergin84/ShareLand.git

**Contact:**
- For Django issues: https://docs.djangoproject.com/
- For Let's Encrypt: https://letsencrypt.org/
- For PostgreSQL: https://www.postgresql.org/docs/
