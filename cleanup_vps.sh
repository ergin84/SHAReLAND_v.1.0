#!/bin/bash

# Cleanup existing deployment on VPS
echo "Cleaning up existing deployment..."

ssh root@5.249.148.147 << 'ENDSSH'
# Stop services if running
supervisorctl stop shareland 2>/dev/null || true
systemctl stop nginx 2>/dev/null || true

# Remove existing installation
rm -rf /var/www/shareland/repo
rm -rf /var/www/shareland/venv
rm -rf /var/www/shareland/static
rm -rf /var/www/shareland/media
rm -rf /var/log/shareland

# Drop database if exists
sudo -u postgres psql -c "DROP DATABASE IF EXISTS shareland_db;" 2>/dev/null || true
sudo -u postgres psql -c "DROP USER IF EXISTS shareland_user;" 2>/dev/null || true

# Remove configs
rm -f /etc/nginx/sites-enabled/shareland
rm -f /etc/nginx/sites-available/shareland
rm -f /etc/supervisor/conf.d/shareland.conf

# Restart nginx
systemctl start nginx

echo "✓ Cleanup complete - ready for fresh deployment"
ENDSSH

echo ""
echo "Now run: bash full_deploy.sh"
