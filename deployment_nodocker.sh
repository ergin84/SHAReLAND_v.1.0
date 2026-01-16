#!/bin/bash
# Usage: ./deployment_nodocker.sh <ENV_FILE>

set -e

if [ $# -ne 1 ]; then
  echo "Usage: $0 <ENV_FILE>"
  exit 1
fi

ENV_FILE="$1"

# Load variables from .env
set -a
. "$ENV_FILE"
set +a

# Now all variables are available: $VPS_IP, $VPS_USER, $VPS_PASSWORD, $DOMAIN, $DB_NAME, $DB_USER, $DB_PASSWORD, $GDRIVE_FOLDER_ID

LOCAL_PROJECT_DIR="$(pwd)"
REMOTE_PROJECT_DIR="/home/$VPS_USER/ShareLand"

# Sync project files to VPS
sshpass -p "$VPS_PASSWORD" rsync -avz --delete "$LOCAL_PROJECT_DIR/" "$VPS_USER@$VPS_IP:$REMOTE_PROJECT_DIR/"

# Copy .env
sshpass -p "$VPS_PASSWORD" scp "$ENV_FILE" "$VPS_USER@$VPS_IP:$REMOTE_PROJECT_DIR/shareland/.env"

# Copy backup script
sshpass -p "$VPS_PASSWORD" scp "$LOCAL_PROJECT_DIR/db_backup_to_gdrive.sh" "$VPS_USER@$VPS_IP:$REMOTE_PROJECT_DIR/db_backup_to_gdrive.sh"
sshpass -p "$VPS_PASSWORD" ssh "$VPS_USER@$VPS_IP" "chmod +x $REMOTE_PROJECT_DIR/db_backup_to_gdrive.sh"

# Setup cron for nightly DB backup at 2am
sshpass -p "$VPS_PASSWORD" ssh "$VPS_USER@$VPS_IP" "(crontab -l 2>/dev/null; echo '0 2 * * * $REMOTE_PROJECT_DIR/db_backup_to_gdrive.sh $DB_NAME $DB_USER $DB_PASSWORD $GDRIVE_FOLDER_ID') | crontab -"

# Install system dependencies, Python, Nginx, Certbot, Supervisor
sshpass -p "$VPS_PASSWORD" ssh "$VPS_USER@$VPS_IP" "\
  sudo apt-get update && \
  sudo apt-get install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx certbot python3-certbot-nginx supervisor && \
  cd $REMOTE_PROJECT_DIR && \
  python3 -m venv venv && \
  source venv/bin/activate && \
  pip install --upgrade pip && \
  pip install -r shareland/requirements.txt && \
  python3 shareland/manage.py migrate && \
  python3 shareland/manage.py collectstatic --noinput\
"

# Gunicorn systemd service
sshpass -p "$VPS_PASSWORD" ssh "$VPS_USER@$VPS_IP" "cat > $REMOTE_PROJECT_DIR/gunicorn_shareland.service <<EOF
[Unit]
Description=gunicorn daemon for ShareLand
After=network.target

[Service]
User=$VPS_USER
Group=www-data
WorkingDirectory=$REMOTE_PROJECT_DIR/shareland
ExecStart=$REMOTE_PROJECT_DIR/venv/bin/gunicorn ShareLand.wsgi:application --bind unix:$REMOTE_PROJECT_DIR/shareland.sock
Restart=always

[Install]
WantedBy=multi-user.target
EOF
sudo mv $REMOTE_PROJECT_DIR/gunicorn_shareland.service /etc/systemd/system/gunicorn_shareland.service
sudo systemctl daemon-reload
sudo systemctl enable gunicorn_shareland
sudo systemctl restart gunicorn_shareland
"

# Nginx config
sshpass -p "$VPS_PASSWORD" ssh "$VPS_USER@$VPS_IP" "cat > $REMOTE_PROJECT_DIR/shareland_nginx <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root $REMOTE_PROJECT_DIR/shareland;
    }
    location /media/ {
        root $REMOTE_PROJECT_DIR/shareland;
    }
    location / {
        include proxy_params;
        proxy_pass http://unix:$REMOTE_PROJECT_DIR/shareland.sock;
    }
}
EOF
sudo mv $REMOTE_PROJECT_DIR/shareland_nginx /etc/nginx/sites-available/shareland_nginx
sudo ln -sf /etc/nginx/sites-available/shareland_nginx /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
"

# SSL with Let's Encrypt
sshpass -p "$VPS_PASSWORD" ssh "$VPS_USER@$VPS_IP" "sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN"

# Supervisor config for health check auto-restart
sshpass -p "$VPS_PASSWORD" ssh "$VPS_USER@$VPS_IP" "cat > $REMOTE_PROJECT_DIR/shareland_healthcheck.conf <<EOF
[program:shareland_healthcheck]
command=$REMOTE_PROJECT_DIR/venv/bin/python3 $REMOTE_PROJECT_DIR/shareland/manage.py site_health_check
directory=$REMOTE_PROJECT_DIR/shareland
autostart=true
autorestart=true
startsecs=10
startretries=3
stderr_logfile=/var/log/shareland_healthcheck.err.log
stdout_logfile=/var/log/shareland_healthcheck.out.log
user=$VPS_USER
environment=DJANGO_SETTINGS_MODULE='ShareLand.settings'

# Run every 5 minutes
stopsignal=INT
auto_start=true
auto_restart=true
EOF
sudo mv $REMOTE_PROJECT_DIR/shareland_healthcheck.conf /etc/supervisor/conf.d/shareland_healthcheck.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart shareland_healthcheck
"

echo "Deployment (no Docker) with Nginx, SSL, and health monitoring complete."
