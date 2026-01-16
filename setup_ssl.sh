#!/bin/bash

################################################################################
# ShareLand SSL Certificate Setup
# Creates Let's Encrypt certificate and configures HTTPS redirect
# Usage: bash setup_ssl.sh
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

DOMAIN="shareland.it"
ALTERNATE_DOMAIN="www.shareland.it"
EMAIL="admin@shareland.it"  # Change to your email

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ShareLand SSL Certificate Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Domain: ${DOMAIN}${NC}"
echo -e "${YELLOW}Alternate Domain: ${ALTERNATE_DOMAIN}${NC}"
echo -e "${YELLOW}Email: ${EMAIL}${NC}"
echo ""

# Step 1: Check if certbot is installed
echo -e "${YELLOW}[1/5] Checking Certbot installation...${NC}"
if ! command -v certbot &> /dev/null; then
    echo "Installing Certbot..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
else
    echo "✓ Certbot already installed"
fi

# Step 2: Stop Nginx temporarily if needed
echo -e "${YELLOW}[2/5] Checking Nginx status...${NC}"
if systemctl is-active --quiet nginx; then
    echo "Nginx is running"
else
    echo "Starting Nginx..."
    systemctl start nginx
fi

# Step 3: Create SSL certificate
echo -e "${YELLOW}[3/5] Creating SSL certificate...${NC}"
certbot certonly --nginx \
    -d ${DOMAIN} \
    -d ${ALTERNATE_DOMAIN} \
    -m ${EMAIL} \
    --agree-tos \
    --non-interactive \
    --keep-until-expiring

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ SSL certificate created successfully${NC}"
else
    echo -e "${RED}✗ SSL certificate creation failed${NC}"
    exit 1
fi

# Step 4: Update Nginx configuration with HTTPS and redirect
echo -e "${YELLOW}[4/5] Updating Nginx configuration...${NC}"

cat > /etc/nginx/sites-available/shareland << 'NGINX_CONFIG'
# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name shareland.it www.shareland.it 5.249.148.147;
    
    # Allow Let's Encrypt renewal
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name shareland.it www.shareland.it;
    
    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/shareland.it/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/shareland.it/privkey.pem;
    
    # SSL security settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # HSTS (HTTP Strict Transport Security)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # Logging
    access_log /var/log/shareland/nginx_access.log;
    error_log /var/log/shareland/nginx_error.log;
    
    # Client max body size for uploads
    client_max_body_size 20M;

    # Static files with caching
    location /static/ {
        alias /var/www/shareland/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files with caching
    location /media/ {
        alias /var/www/shareland/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Deny access to sensitive files
    location ~ /\. {
        deny all;
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        proxy_redirect off;
        proxy_buffering off;
        proxy_request_buffering off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

# Redirect www to non-www (optional - remove if you want to keep both)
# Uncomment the following block to redirect www.shareland.it to shareland.it
# server {
#     listen 443 ssl http2;
#     listen [::]:443 ssl http2;
#     server_name www.shareland.it;
#     
#     ssl_certificate /etc/letsencrypt/live/shareland.it/fullchain.pem;
#     ssl_certificate_key /etc/letsencrypt/live/shareland.it/privkey.pem;
#     
#     return 301 https://shareland.it$request_uri;
# }
NGINX_CONFIG

echo "✓ Nginx configuration updated"

# Step 5: Enable SSL redirect and reload services
echo -e "${YELLOW}[5/5] Enabling SSL redirect and reloading services...${NC}"

# Update .env file to enable SSL redirect
if [ -f /var/www/shareland/.env ]; then
    sed -i 's/SECURE_SSL_REDIRECT=False/SECURE_SSL_REDIRECT=True/' /var/www/shareland/.env
    echo -e "${GREEN}✓ SSL redirect enabled in .env${NC}"
    
    # Restart Gunicorn to apply changes
    if command -v supervisorctl &> /dev/null; then
        supervisorctl restart shareland 2>/dev/null || true
        echo -e "${GREEN}✓ Gunicorn restarted${NC}"
    fi
else
    echo -e "${YELLOW}⚠ .env file not found at /var/www/shareland/.env${NC}"
fi

# Test and reload Nginx
if nginx -t; then
    systemctl reload nginx
    echo -e "${GREEN}✓ Nginx reloaded successfully${NC}"
else
    echo -e "${RED}✗ Nginx configuration test failed${NC}"
    exit 1
fi

# Step 6: Set up automatic renewal
echo -e "${YELLOW}Setting up automatic certificate renewal...${NC}"
systemctl enable certbot.timer
systemctl start certbot.timer

# Verify the timer is running
if systemctl is-active --quiet certbot.timer; then
    echo -e "${GREEN}✓ Automatic renewal configured${NC}"
else
    echo -e "${YELLOW}⚠ Could not enable automatic renewal${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SSL Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Your site is now secure:${NC}"
echo "  🌐 https://shareland.it"
echo "  🌐 https://www.shareland.it"
echo "  🔒 HTTP redirects to HTTPS automatically"
echo ""
echo -e "${YELLOW}Access during setup (before DNS is configured):${NC}"
echo "  http://5.249.148.147 (HTTP access via IP)"
echo ""
echo -e "${YELLOW}Certificate Details:${NC}"
certbot certificates --non-interactive
echo ""
echo -e "${YELLOW}Certificate Renewal:${NC}"
echo "  Automatic renewal is enabled"
echo "  Renewal check runs daily"
echo "  Renewal logs: /var/log/letsencrypt/"
echo ""
echo -e "${YELLOW}Security Headers Added:${NC}"
echo "  ✓ HSTS (HTTP Strict Transport Security)"
echo "  ✓ X-Frame-Options"
echo "  ✓ X-Content-Type-Options"
echo "  ✓ X-XSS-Protection"
echo "  ✓ Referrer-Policy"
echo ""
echo -e "${YELLOW}Manual Renewal (if needed):${NC}"
echo "  sudo certbot renew --dry-run"
echo "  sudo certbot renew"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. Visit https://shareland.it to verify SSL is working"
echo "2. Check SSL rating: https://www.ssllabs.com/ssltest/"
echo "3. Update any external configurations with HTTPS URLs"
echo ""
