#!/bin/bash

################################################################################
# QUICK DEPLOYMENT REFERENCE - ShareLand VPS
# Reference: 5.249.148.147 (shareland.it)
################################################################################

# STEP 1: Deploy to VPS (10-15 minutes)
# This script uploads and executes deployment on remote VPS via SSH
bash full_deploy.sh

# Expected output: ✅ Complete Deployment Successful!
# Access at: http://5.249.148.147


# STEP 2: Create Admin User
# After deployment, create a superuser to access admin panel
ssh root@5.249.148.147

# Once connected to VPS, run:
cd /var/www/shareland/repo
source ../venv/bin/activate
python manage.py createsuperuser --settings=shareland.settings_production
# Follow prompts to create admin user


# STEP 3: Access Admin Panel (Before DNS setup)
# Open in browser: http://5.249.148.147/admin/
# Login with credentials created in Step 2


# STEP 4: Configure DNS (When ready)
# Point DNS records to 5.249.148.147:
# A Record: shareland.it     → 5.249.148.147
# A Record: www.shareland.it → 5.249.148.147
# Wait 15-30 minutes for DNS propagation
# Test: ping shareland.it (should resolve to 5.249.148.147)


# STEP 5: Setup SSL Certificate (After DNS is working)
# SSH into VPS and run SSL setup script
ssh root@5.249.148.147

# Once connected, run:
cd /tmp
bash setup_ssl.sh
# The script will:
# - Generate Let's Encrypt certificate
# - Configure Nginx for HTTPS
# - Enable automatic renewal
# - Enable SSL redirect in Django
# - Restart services


# STEP 6: Access Secure Application
# Now available at: https://shareland.it/admin/


################################################################################
# VERIFICATION COMMANDS
################################################################################

# Check deployment status
ssh root@5.249.148.147 'supervisorctl status shareland'

# View application logs
ssh root@5.249.148.147 'tail -f /var/log/shareland/gunicorn_error.log'

# View Nginx logs
ssh root@5.249.148.147 'tail -f /var/log/nginx/error.log'

# Test SSL certificate (after setup)
ssh root@5.249.148.147 'certbot certificates'

# Check SSL grade (online)
# https://www.ssllabs.com/ssltest/?d=shareland.it


################################################################################
# CONFIGURATION DETAILS
################################################################################

# VPS Details
# IP: 5.249.148.147
# User: root
# OS: Ubuntu 22.04 LTS
# Python: 3.12
# Database: PostgreSQL 15
# Web Server: Nginx
# App Server: Gunicorn
# Process Manager: Supervisor

# Important Paths on VPS
# App: /var/www/shareland/repo
# Venv: /var/www/shareland/venv
# Config: /var/www/shareland/.env
# Logs: /var/log/shareland/
# Nginx: /etc/nginx/sites-available/shareland
# Supervisor: /etc/supervisor/conf.d/shareland.conf

# Initial Access (Before SSL)
# URL: http://5.249.148.147
# SSL: No
# Redirect: No

# Production Access (After SSL)
# URL: https://shareland.it
# SSL: Yes (Let's Encrypt)
# Redirect: HTTP → HTTPS automatically


################################################################################
# TROUBLESHOOTING
################################################################################

# If deployment fails, check:
# 1. SSH connection: ssh root@5.249.148.147
# 2. Nginx status: systemctl status nginx
# 3. Gunicorn status: supervisorctl status shareland
# 4. PostgreSQL: systemctl status postgresql

# If IP access not working:
# 1. Check firewall: ufw status
# 2. Restart Nginx: systemctl restart nginx
# 3. Restart Gunicorn: supervisorctl restart shareland

# If DNS not working:
# 1. Verify DNS records: nslookup shareland.it
# 2. Wait for propagation (5-30 minutes)
# 3. Flush local DNS cache if needed

# If SSL certificate fails:
# 1. Verify DNS is working first
# 2. Check ports 80 and 443 are open
# 3. Review certbot logs: tail -f /var/log/letsencrypt/letsencrypt.log
