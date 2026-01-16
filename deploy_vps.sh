#!/bin/bash

################################################################################
# ShareLand VPS Deployment Script
# Deploys to Aruba VPS with PostgreSQL
# Usage: bash deploy_vps.sh
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
VPS_IP="5.249.148.147"
APP_DIR="/var/www/shareland"
APP_USER="shareland"
APP_GROUP="shareland"
REPO_URL="https://github.com/ergin84/ShareLand.git"
PYTHON_VERSION="3.12"
DOMAIN="shareland.it"
DB_NAME="shareland_db"
DB_USER="shareland_user"
DB_PASSWORD="$(openssl rand -base64 32)"  # Generate secure password
SECRET_KEY="$(openssl rand -base64 48)"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ShareLand VPS Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Step 1: Update system
echo -e "${YELLOW}[1/12] Updating system packages...${NC}"
apt-get update
apt-get upgrade -y
apt-get install -y curl wget gnupg2 lsb-release ca-certificates

# Step 1.5: Add deadsnakes PPA for Python 3.12
echo -e "${YELLOW}[1.5/12] Adding deadsnakes PPA for Python 3.12...${NC}"
apt-get install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update

# Step 2: Install Python and dependencies
echo -e "${YELLOW}[2/12] Installing Python ${PYTHON_VERSION}, development tools, and GIS libraries...${NC}"
apt-get install -y \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-venv \
    python${PYTHON_VERSION}-dev \
    python3-pip \
    build-essential \
    libpq-dev \
    git \
    curl \
    wget \
    nano \
    htop \
    gdal-bin \
    libgdal-dev \
    python3-gdal \
    binutils \
    libproj-dev \
    libgeos-dev

# Step 3: Install PostgreSQL
echo -e "${YELLOW}[3/12] Installing PostgreSQL...${NC}"
sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
apt-get update
apt-get install -y postgresql-15 postgresql-contrib-15

# Step 4: Install Nginx
echo -e "${YELLOW}[4/12] Installing Nginx...${NC}"
apt-get install -y nginx
systemctl start nginx
systemctl enable nginx

# Step 5: Install additional system packages
echo -e "${YELLOW}[5/12] Installing additional packages...${NC}"
apt-get install -y \
    supervisor \
    certbot \
    python3-certbot-nginx \
    redis-server

# Step 6: Create application user and directories
echo -e "${YELLOW}[6/12] Creating application user and directories...${NC}"
useradd -m -s /bin/bash ${APP_USER} || true
mkdir -p ${APP_DIR}
chown -R ${APP_USER}:${APP_GROUP} ${APP_DIR}

# Step 7: Clone repository
echo -e "${YELLOW}[7/13] Cloning repository...${NC}"
# Remove existing repo if it exists
if [ -d "${APP_DIR}/repo" ]; then
    echo "Removing existing repository..."
    rm -rf ${APP_DIR}/repo
fi
sudo -u ${APP_USER} git clone ${REPO_URL} ${APP_DIR}/repo
chown -R ${APP_USER}:${APP_GROUP} ${APP_DIR}/repo
# Add safe directory globally
git config --global --add safe.directory ${APP_DIR}/repo
sudo -u ${APP_USER} git config --global --add safe.directory ${APP_DIR}/repo
cd ${APP_DIR}/repo
LATEST_COMMIT=$(git rev-parse --short HEAD)
echo "Repository cloned. Latest commit: ${LATEST_COMMIT}"

# Step 8: Create PostgreSQL database
echo -e "${YELLOW}[8/12] Setting up PostgreSQL database...${NC}"
# Drop existing database and user if they exist
sudo -u postgres psql <<EOF
DROP DATABASE IF EXISTS ${DB_NAME};
DROP USER IF EXISTS ${DB_USER};
CREATE DATABASE ${DB_NAME};
CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';
ALTER ROLE ${DB_USER} SET client_encoding TO 'utf8';
ALTER ROLE ${DB_USER} SET default_transaction_isolation TO 'read committed';
ALTER ROLE ${DB_USER} SET default_transaction_deferrable TO on;
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
\c ${DB_NAME}
GRANT ALL PRIVILEGES ON SCHEMA public TO ${DB_USER};
EOF

# Step 9: Set up Python virtual environment and install dependencies
echo -e "${YELLOW}[9/13] Setting up Python virtual environment...${NC}"
sudo -u ${APP_USER} python${PYTHON_VERSION} -m venv ${APP_DIR}/venv
source ${APP_DIR}/venv/bin/activate

# Upgrade pip
sudo -u ${APP_USER} ${APP_DIR}/venv/bin/pip install --upgrade pip setuptools wheel

# Install Django and dependencies
cd ${APP_DIR}/repo
sudo -u ${APP_USER} ${APP_DIR}/venv/bin/pip install -r requirements.txt
sudo -u ${APP_USER} ${APP_DIR}/venv/bin/pip install gunicorn psycopg2-binary redis

# Step 10: Configure Django settings
echo -e "${YELLOW}[10/13] Configuring Django application...${NC}"

# Create production settings
cat > ${APP_DIR}/repo/ShareLand/settings_production.py << 'DJANGO_SETTINGS'
from ShareLand.settings import *
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from application directory
env_path = Path('/var/www/shareland/.env')
load_dotenv(dotenv_path=env_path)

DEBUG = False
ALLOWED_HOSTS = ['5.249.148.147', 'shareland.it', 'www.shareland.it']

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'shareland_db'),
        'USER': os.environ.get('DB_USER', 'shareland_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'disable',
        },
    }
}

# Static and media files
STATIC_ROOT = '/var/www/shareland/static'
STATIC_URL = '/static/'
MEDIA_ROOT = '/var/www/shareland/media'
MEDIA_URL = '/media/'

# Security settings
# Allow HTTP for IP, HTTPS for domain (will be enforced by SSL setup)
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False') == 'True'
SESSION_COOKIE_SECURE = os.environ.get('SECURE_SSL_REDIRECT', 'False') == 'True'
CSRF_COOKIE_SECURE = os.environ.get('SECURE_SSL_REDIRECT', 'False') == 'True'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ("'self'",),
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/shareland/django.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
DJANGO_SETTINGS

chown ${APP_USER}:${APP_GROUP} ${APP_DIR}/repo/ShareLand/settings_production.py

# Create .env file
cat > ${APP_DIR}/.env << ENV_FILE
DEBUG=False
SECRET_KEY='${SECRET_KEY}'
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=localhost
DB_PORT=5432
ALLOWED_HOSTS=5.249.148.147,shareland.it,www.shareland.it
SECURE_SSL_REDIRECT=False
ENV_FILE

chown ${APP_USER}:${APP_GROUP} ${APP_DIR}/.env
chmod 600 ${APP_DIR}/.env

# Create directories for logs and media
mkdir -p /var/log/shareland
mkdir -p ${APP_DIR}/static
mkdir -p ${APP_DIR}/media
chown -R ${APP_USER}:${APP_GROUP} /var/log/shareland
chown -R ${APP_USER}:${APP_GROUP} ${APP_DIR}/static
chown -R ${APP_USER}:${APP_GROUP} ${APP_DIR}/media

# Collect static files
echo -e "${YELLOW}Collecting static files...${NC}"
cd ${APP_DIR}/repo
# Export environment variables from .env file and run with sudo -E to preserve env
set -a
source ${APP_DIR}/.env
set +a
sudo -E -u ${APP_USER} ${APP_DIR}/venv/bin/python manage.py collectstatic --noinput --settings=ShareLand.settings_production

# Run migrations
echo -e "${YELLOW}Running migrations...${NC}"
# Export environment variables from .env file and run with sudo -E to preserve env
set -a
source ${APP_DIR}/.env
set +a
sudo -E -u ${APP_USER} ${APP_DIR}/venv/bin/python manage.py migrate --settings=ShareLand.settings_production

# Step 11: Configure Gunicorn
echo -e "${YELLOW}[11/13] Configuring Gunicorn and Supervisor...${NC}"

# Create Gunicorn configuration
cat > ${APP_DIR}/gunicorn_config.py << 'GUNICORN_CONFIG'
import multiprocessing

bind = "127.0.0.1:8001"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True

# Logging
accesslog = "/var/log/shareland/gunicorn_access.log"
errorlog = "/var/log/shareland/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "shareland"
GUNICORN_CONFIG

chown ${APP_USER}:${APP_GROUP} ${APP_DIR}/gunicorn_config.py

# Create Gunicorn startup script that loads environment variables
cat > ${APP_DIR}/start_gunicorn.sh << 'START_SCRIPT'
#!/bin/bash
set -a
source /var/www/shareland/.env
set +a
cd /var/www/shareland/repo
exec /var/www/shareland/venv/bin/gunicorn -c /var/www/shareland/gunicorn_config.py ShareLand.wsgi:application
START_SCRIPT

chmod +x ${APP_DIR}/start_gunicorn.sh
chown ${APP_USER}:${APP_GROUP} ${APP_DIR}/start_gunicorn.sh

# Create Supervisor configuration
cat > /etc/supervisor/conf.d/shareland.conf << 'SUPERVISOR_CONFIG'
[program:shareland]
directory=/var/www/shareland/repo
command=/var/www/shareland/start_gunicorn.sh
user=shareland
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/shareland/gunicorn_error.log

[group:shareland]
programs=shareland
SUPERVISOR_CONFIG

# Start Supervisor
systemctl enable supervisor || true
systemctl restart supervisor

# Wait for Supervisor to be ready (socket available)
SUP_SOCK="/var/run/supervisor.sock"
for i in {1..10}; do
    if [ -S "$SUP_SOCK" ]; then
        break
    fi
    echo "Waiting for Supervisor socket... ($i/10)"
    sleep 1
done

# Reread and start program via supervisorctl
supervisorctl reread || true
supervisorctl update || true
supervisorctl start shareland || true
supervisorctl status shareland || true

# Step 12: Configure Nginx
echo -e "${YELLOW}[12/13] Configuring Nginx...${NC}"

# Remove default config
rm -f /etc/nginx/sites-enabled/default

# Create Nginx configuration
cat > /etc/nginx/sites-available/shareland << 'NGINX_CONFIG'
upstream shareland_app {
    server 127.0.0.1:8001;
}

server {
    listen 80;
    server_name 5.249.148.147 shareland.it www.shareland.it;
    client_max_body_size 20M;

    # Logging
    access_log /var/log/shareland/nginx_access.log;
    error_log /var/log/shareland/nginx_error.log;

    # Static files
    location /static/ {
        alias /var/www/shareland/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /var/www/shareland/media/;
        expires 7d;
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass http://shareland_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;
    }

    # Deny access to .htaccess and other sensitive files
    location ~ /\. {
        deny all;
    }
}
NGINX_CONFIG

# Enable site
ln -sf /etc/nginx/sites-available/shareland /etc/nginx/sites-enabled/shareland

# Test Nginx configuration
nginx -t

# Reload Nginx
systemctl reload nginx

# Print summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Important Information:${NC}"
echo "VPS IP: ${VPS_IP}"
echo "App Directory: ${APP_DIR}"
echo "Database: ${DB_NAME}"
echo "Database User: ${DB_USER}"
echo ""
echo -e "${YELLOW}Database Credentials (save in secure location):${NC}"
echo "DB Password: ${DB_PASSWORD}"
echo ""
echo -e "${YELLOW}Django Secret Key:${NC}"
echo "${SECRET_KEY}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Update DOMAIN variable in script to your actual domain"
echo "2. Update ALLOWED_HOSTS in settings_production.py"
echo "3. Configure SSL certificates: sudo certbot --nginx -d shareland.it -d www.shareland.it"
echo "4. Create superuser: cd ${APP_DIR}/repo && ../venv/bin/python manage.py createsuperuser --settings=ShareLand.settings_production"
echo "5. Check application status: supervisorctl status"
echo "6. View logs: tail -f /var/log/shareland/gunicorn_error.log"
echo ""
echo -e "${GREEN}Application running on:${NC}"
echo "http://${VPS_IP}"
echo ""
