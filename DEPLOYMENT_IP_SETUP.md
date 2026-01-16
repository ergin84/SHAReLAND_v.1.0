# ShareLand IP-Based Deployment Setup

## Overview
The deployment scripts have been updated to support access via IP address (5.249.148.147) before DNS is configured.

## Access During Setup

### Initial Phase (Before SSL)
- **IP Access**: `http://5.249.148.147`
- **Status**: HTTP only (no SSL)
- **Use**: Testing and setup

### After SSL Setup
- **Domain HTTPS**: `https://shareland.it` and `https://www.shareland.it`
- **IP Access**: `http://5.249.148.147` (still available for direct IP access)
- **Domain HTTP**: Automatically redirects to HTTPS
- **Status**: Full SSL/TLS encryption

## Configuration Changes

### Django Settings (`settings_production.py`)
```python
# ALLOWED_HOSTS includes both IP and domain
ALLOWED_HOSTS = ['5.249.148.147', 'shareland.it', 'www.shareland.it']

# SSL redirect can be toggled via environment variable
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False') == 'True'
```

### Initial Environment (`/.env`)
```
SECURE_SSL_REDIRECT=False
```

During initial setup, SSL redirect is **disabled** to allow testing via IP.

### After SSL Setup
The `setup_ssl.sh` script automatically updates:
```
SECURE_SSL_REDIRECT=True
```

This enables:
- Automatic HTTP → HTTPS redirect for domain access
- Secure cookies
- Secure CSRF tokens

### Nginx Configuration
- Listens on port 80 and 443
- Serves IP address via HTTP (port 80)
- Redirects domain HTTP traffic to HTTPS (port 443)
- Allows both domain names and IP in server block

## Deployment Steps

### 1. Initial Deployment (IP-based)
```bash
bash full_deploy.sh
```

This will:
1. Copy `deploy_vps.sh` to VPS
2. Execute deployment with PostgreSQL, Python 3.12, Gunicorn, Supervisor
3. Configure Nginx for IP + domain access
4. Configure Django with `SECURE_SSL_REDIRECT=False`
5. Application is accessible at `http://5.249.148.147`

### 2. Create Admin User
```bash
ssh root@5.249.148.147
cd /var/www/shareland/repo
source ../venv/bin/activate
python manage.py createsuperuser --settings=shareland.settings_production
```

### 3. Test Application via IP
```
http://5.249.148.147/admin/
```

Login with your admin credentials.

### 4. Configure DNS (Optional)
Point your DNS records to 5.249.148.147:
- `shareland.it` → 5.249.148.147
- `www.shareland.it` → 5.249.148.147

### 5. Setup SSL Certificate
Once DNS is configured, run:
```bash
ssh root@5.249.148.147
cd /tmp
bash setup_ssl.sh
```

This will:
1. Validate domain DNS
2. Generate Let's Encrypt certificate
3. Configure Nginx for HTTPS
4. Enable automatic certificate renewal
5. Update Django to enforce SSL redirect
6. Restart services

### 6. Access Secure Application
```
https://shareland.it/admin/
https://www.shareland.it/admin/
```

## Security Timeline

| Phase | Access | Protocol | SSL | Redirect |
|-------|--------|----------|-----|----------|
| Initial Setup | IP only | HTTP | ❌ | ❌ |
| Testing | IP + Domain | HTTP | ❌ | ❌ |
| Production | Domain only | HTTPS | ✅ | ✅ |
| Full Secure | IP + Domain | HTTP/HTTPS | ✅ | ✅* |

*IP continues to work with HTTP; domain redirects to HTTPS

## Troubleshooting

### Application not accessible via IP
```bash
# Check Nginx is running
systemctl status nginx

# Check Gunicorn is running
supervisorctl status shareland

# View Nginx errors
tail -f /var/log/nginx/error.log

# View Django errors
tail -f /var/log/shareland/django.log
```

### After DNS setup, IP still shows non-SSL version
This is expected. The IP access remains HTTP for development purposes.

### Domain shows security warning
- Verify DNS is pointing to correct IP
- Run `setup_ssl.sh` on VPS
- Certificate generation typically takes 2-5 minutes

## File Modifications

### deploy_vps.sh
- Added `deadsnakes` PPA for Python 3.12
- Updated `ALLOWED_HOSTS` with IP address
- Set `SECURE_SSL_REDIRECT=False` by default
- Created .env with `SECURE_SSL_REDIRECT=False`

### setup_ssl.sh
- Nginx configuration updated to handle both HTTP and HTTPS
- Added SSL redirect enablement in .env
- Automatic Gunicorn restart after SSL setup
- Updated security headers for HTTPS

### full_deploy.sh
- SSH-based deployment (no sshpass required)
- Interactive terminal support
- Support for custom VPS IP and username
- Better error handling

## Next Steps

1. Execute: `bash full_deploy.sh`
2. Wait for deployment to complete
3. Access: `http://5.249.148.147`
4. Create admin user
5. Configure DNS when ready
6. Run SSL setup
7. Access secure domain

---

**Deployment Date**: 2025-12-23  
**VPS Provider**: Aruba  
**OS**: Ubuntu 22.04 LTS  
**Python**: 3.12  
**Database**: PostgreSQL 15  
**Web Server**: Nginx  
**App Server**: Gunicorn + Supervisor
