# Nginx Configuration Preservation

This document explains how the deployment process preserves your existing Nginx configuration on the VPS.

## Current VPS Nginx Configuration

Based on the deployment script (`deploy_vps.sh`), the VPS uses the following Nginx configuration:

**Location**: `/etc/nginx/sites-available/shareland`

**Key Settings**:
- **Upstream**: `127.0.0.1:8001` (Gunicorn)
- **Server Name**: `5.249.148.147 shareland.it www.shareland.it`
- **Client Max Body Size**: `20M`
- **Static Files**: `/var/www/shareland/static/`
- **Media Files**: `/var/www/shareland/media/`
- **Logs**: `/var/log/shareland/nginx_access.log` and `/var/log/shareland/nginx_error.log`

## How It's Preserved

The `update_vps_code.sh` script **does NOT modify** the Nginx configuration. It:

1. ✅ **Checks** if Nginx config exists
2. ✅ **Validates** the configuration with `nginx -t`
3. ✅ **Preserves** the existing configuration
4. ✅ **Reloads** Nginx if needed (without changing config)

## Manual Backup (Recommended Before First Deployment)

Before deploying, you can manually backup the Nginx configuration:

```bash
# Option 1: Using the backup script
./preserve_nginx_config.sh

# Option 2: Manual backup
ssh root@5.249.148.147 'cat /etc/nginx/sites-available/shareland' > nginx_config_backup.conf
```

## Expected Nginx Configuration

The VPS should have a configuration similar to this:

```nginx
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
```

## SSL/HTTPS Configuration

If SSL certificates are configured (Let's Encrypt), they are also preserved. The deployment script does not modify SSL settings.

To check SSL configuration:
```bash
ssh root@5.249.148.147 'certbot certificates'
```

## Verification After Deployment

After running `update_vps_code.sh`, verify Nginx is still working:

```bash
# Check Nginx status
ssh root@5.249.148.147 'systemctl status nginx'

# Test Nginx configuration
ssh root@5.249.148.147 'nginx -t'

# Check if site is accessible
curl -I http://5.249.148.147
```

## What Gets Updated vs. Preserved

### ✅ Preserved (Not Modified)
- Nginx configuration files
- SSL certificates
- Nginx upstream settings
- Static/media file paths
- Log file locations

### ✅ Updated (Application Only)
- Gunicorn configuration (timeout, workers)
- Application code
- Static files content
- Database schema (migrations)

## Troubleshooting

### Nginx Configuration Test Fails

If you see a warning about Nginx configuration test failing:

```bash
# SSH to VPS and check the config
ssh root@5.249.148.147
nginx -t

# If there are errors, check the config file
cat /etc/nginx/sites-available/shareland

# Restore from backup if needed
cp nginx_config_backup.conf /etc/nginx/sites-available/shareland
nginx -t
systemctl reload nginx
```

### Nginx Not Reloading

If Nginx doesn't reload automatically:

```bash
ssh root@5.249.148.147 'systemctl reload nginx'
```

### Static Files Not Loading

Check that static files path is correct:

```bash
ssh root@5.249.148.147 'ls -la /var/www/shareland/static/'
```

## Summary

**The deployment process preserves your Nginx configuration completely.** No changes are made to:
- Nginx server blocks
- Upstream configuration
- SSL settings
- Static/media file paths
- Log locations

Only the application code and Gunicorn settings are updated.





