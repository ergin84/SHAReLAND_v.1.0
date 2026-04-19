# CI/CD Setup — GitHub Actions → Aruba VPS

---

## VPS First-Time Provisioning

All steps below are **manual, one-time setup** that must be completed on the VPS
**before** the first `git push` triggers the CI/CD pipeline.

Assumed OS: **Ubuntu 22.04 / 24.04** (Aruba VPS default).

---

### 1 — System packages

```bash
apt update && apt upgrade -y
apt install -y \
    git curl wget gnupg lsb-release ca-certificates \
    build-essential libpq-dev \
    nginx \
    python3.12 python3.12-venv python3.12-dev python3-pip \
    gdal-bin libgdal-dev    # required by geopandas / pyproj
```

> **Python 3.12 on Ubuntu 22.04** — if `python3.12` is not available, add the
> deadsnakes PPA first:
> ```bash
> add-apt-repository ppa:deadsnakes/ppa && apt update
> ```

---

### 2 — PostgreSQL installation

Pin a specific major version so local Docker and VPS stay in sync. The project
exports backups as plain SQL (`.sql.gz`), so minor version differences are fine;
**major versions must match**.

```bash
# Install the PostgreSQL APT repository (example: PostgreSQL 16)
curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
  | gpg --dearmor -o /usr/share/keyrings/postgresql.gpg
echo "deb [signed-by=/usr/share/keyrings/postgresql.gpg] \
  https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" \
  > /etc/apt/sources.list.d/pgdg.list
apt update
apt install -y postgresql-17
```

Check the installed version:
```bash
psql --version          # should print: psql (PostgreSQL) 16.x
pg_dump --version       # same major as local Docker
```

---

### 3 — PostGIS installation

PostGIS is not used by the current models (geometry is stored as plain text),
but install it now so the database is ready for spatial queries when needed.

```bash
apt install -y postgresql-17-postgis-3 postgis
```

Enable the extension inside the application database (do this **after** step 4):
```bash
sudo -u postgres psql -d shareland_db -c "CREATE EXTENSION IF NOT EXISTS postgis;"
sudo -u postgres psql -d shareland_db -c "CREATE EXTENSION IF NOT EXISTS postgis_topology;"
# Verify:
sudo -u postgres psql -d shareland_db -c "SELECT PostGIS_Full_Version();"
```

---

### 4 — PostgreSQL: create user and database

```bash
sudo -u postgres psql << 'EOF'
CREATE USER shareland_user WITH PASSWORD 'your-strong-password-here';
CREATE DATABASE shareland_db OWNER shareland_user;
GRANT ALL PRIVILEGES ON DATABASE shareland_db TO shareland_user;
-- Allow the user to create extensions (needed for PostGIS)
ALTER USER shareland_user CREATEDB;
EOF
```

Test the connection:
```bash
psql -U shareland_user -h localhost -d shareland_db -c "\dt"
# Should connect and show an empty table list (no tables yet)
```

---

### 5 — Project directory and .env

```bash
# Create project directory (matches VPS_PROJECT_PATH secret)
mkdir -p /var/www/shareland
git clone https://github.com/ergin84/SHAReLAND_v.1.0.git /var/www/shareland
cd /var/www/shareland

# Create the production .env (never commit this file)
cp shareland/.env.production.example shareland/.env
chmod 600 shareland/.env
nano shareland/.env          # fill in all values — see template below
```

**Minimum required `.env` values for VPS:**
```ini
SECRET_KEY=<generate with: python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
DEBUG=False
ALLOWED_HOSTS=shareland.it,www.shareland.it,<your-vps-ip>

# Database — DB_HOST must be localhost on VPS (not 'db' which is the Docker service name)
DB_NAME=shareland_db
DB_USER=shareland_user
DB_PASSWORD=your-strong-password-here
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_HOST=smtp.aruba.it
EMAIL_PORT=465
EMAIL_HOST_USER=noreply@shareland.it
EMAIL_HOST_PASSWORD=your-email-password
EMAIL_USE_TLS=False
EMAIL_USE_SSL=True
DEFAULT_FROM_EMAIL=noreply@shareland.it
ADMIN_EMAIL=admin@shareland.it
```

---

### 6 — Python virtualenv and dependencies

```bash
python3.12 -m venv /opt/venv
source /opt/venv/bin/activate
pip install --upgrade pip
pip install -r /var/www/shareland/shareland/requirements.txt
```

---

### 7 — Log directory

Django writes logs to `shareland/logs/django.log`:
```bash
mkdir -p /var/www/shareland/shareland/logs
chown -R ubuntu:ubuntu /var/www/shareland/shareland/logs
```

---

### 8 — Gunicorn systemd service (Unix socket)

The deploy pipeline checks health via `/run/gunicorn/gunicorn.sock`.
Create the socket directory and the systemd unit:

```bash
mkdir -p /run/gunicorn
chown ubuntu:www-data /run/gunicorn
```

Create `/etc/systemd/system/gunicorn.service`:
```ini
[Unit]
Description=SHAReLAND Gunicorn
After=network.target postgresql.service

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/var/www/shareland/shareland
EnvironmentFile=/var/www/shareland/shareland/.env
Environment=DJANGO_SETTINGS_MODULE=ShareLand.settings
Environment=DB_HOST=localhost

ExecStart=/opt/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/run/gunicorn/gunicorn.sock \
    --timeout 120 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --graceful-timeout 30 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    ShareLand.wsgi:application

ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=5
RuntimeDirectory=gunicorn
RuntimeDirectoryMode=0775

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
systemctl daemon-reload
systemctl enable gunicorn
systemctl start gunicorn
systemctl status gunicorn
```

Test the socket directly (same as the CI health check):
```bash
curl -s -o /dev/null -w "%{http_code}" \
  --unix-socket /run/gunicorn/gunicorn.sock \
  http://localhost/health/
# Expected: 200
```

---

### 9 — Nginx configuration

```bash
nano /etc/nginx/sites-available/shareland
```

Paste:
```nginx
# HTTP → HTTPS redirect (domain access only; IP access skips redirect)
server {
    listen 80;
    server_name shareland.it www.shareland.it;
    return 301 https://$host$request_uri;
}

# HTTPS — main site
server {
    listen 443 ssl;
    server_name shareland.it www.shareland.it;

    ssl_certificate     /etc/letsencrypt/live/shareland.it/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/shareland.it/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    # Health check — accessible over plain HTTP (exempted from Django SSL redirect)
    location /health/ {
        proxy_pass http://unix:/run/gunicorn/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/shareland/shareland/static/;
        expires 30d;
    }

    location /media/ {
        alias /var/www/shareland/shareland/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://unix:/run/gunicorn/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }
}

# Direct IP access — no SSL redirect, no cert required
server {
    listen 80 default_server;
    server_name _;

    location / {
        proxy_pass http://unix:/run/gunicorn/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto http;
        proxy_read_timeout 120s;
    }
}
```

Enable and test:
```bash
ln -s /etc/nginx/sites-available/shareland /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default       # remove default site
nginx -t                                   # must print: syntax is ok
systemctl reload nginx
```

---

### 10 — SSL certificate (Let's Encrypt)

> **Do this step only after DNS is fully propagated.**
> Certbot requires Let's Encrypt to reach your server on port 80 via the domain
> name — it will fail if DNS still points to the old IP or hasn't propagated yet.

#### 10a — Point DNS to the VPS

In your DNS provider (Aruba panel or external registrar) set:

| Record | Name | Value |
|--------|------|-------|
| A | `shareland.it` | `<your-vps-ip>` |
| A | `www` | `<your-vps-ip>` |

#### 10b — Verify DNS propagation before continuing

```bash
# Run from your local machine or any external host:
dig shareland.it +short          # must return your VPS IP
dig www.shareland.it +short      # same

# Or use an online checker: https://dnschecker.org
# Wait until both records resolve correctly worldwide before proceeding.
```

You can also verify from inside the VPS that port 80 is open and reachable:
```bash
# From the VPS — confirm nginx is listening on port 80:
ss -tlnp | grep :80

# From your local machine — confirm port 80 is reachable:
curl -I http://shareland.it      # should return nginx headers (not a timeout)
```

#### 10c — Issue the certificate

```bash
apt install -y certbot python3-certbot-nginx

certbot --nginx -d shareland.it -d www.shareland.it \
  --agree-tos \
  --email admin@shareland.it \
  --redirect           # certbot will update nginx to force HTTPS automatically
```

Certbot will:
1. Verify domain ownership via HTTP on port 80
2. Issue the certificate to `/etc/letsencrypt/live/shareland.it/`
3. Patch the nginx config to add the `ssl_certificate` lines and HTTP→HTTPS redirect

#### 10d — Verify auto-renewal

```bash
# Certbot installs a systemd timer — confirm it is active:
systemctl status certbot.timer

# Dry-run to confirm renewal works without actually renewing:
certbot renew --dry-run
```

The certificate expires every 90 days; the timer renews it automatically when
fewer than 30 days remain. No manual action needed after this point.

---

### 11 — Firewall

```bash
ufw allow OpenSSH
ufw allow 'Nginx Full'     # ports 80 and 443
ufw enable
ufw status
```

---

### 12 — Run Django migrations (first deploy only)

```bash
source /opt/venv/bin/activate
cd /var/www/shareland/shareland
export DB_HOST=localhost
export DJANGO_SETTINGS_MODULE=ShareLand.settings
python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear
python manage.py createsuperuser    # create the first admin account
```

---

### 13 — Verify everything before the first push

```bash
# Gunicorn running?
systemctl is-active gunicorn

# Nginx running?
systemctl is-active nginx

# Socket exists?
ls -la /run/gunicorn/gunicorn.sock

# Health check responds?
curl -s --unix-socket /run/gunicorn/gunicorn.sock http://localhost/health/

# Django can talk to the DB?
cd /var/www/shareland/shareland && \
  DB_HOST=localhost python manage.py dbshell -c "\dt" 2>&1 | head -5
```

Only push to `main` once all checks above pass — the CI/CD pipeline will then
handle all subsequent deploys automatically.

---

## Secrets da configurare

Vai su: **GitHub → repository → Settings → Secrets and variables → Actions → New repository secret**

| Secret | Esempio | Descrizione |
|---|---|---|
| `VPS_HOST` | `123.456.78.90` | IP o hostname del VPS Aruba |
| `VPS_USER` | `ubuntu` | Utente SSH |
| `VPS_SSH_KEY` | `-----BEGIN OPENSSH...` | Chiave privata SSH (contenuto intero) |
| `VPS_PORT` | `22` | Porta SSH (default 22, omettibile) |
| `VPS_PROJECT_PATH` | `/opt/SHAReLAND_v.1.0` | Path assoluto del progetto sul VPS |
| `VPS_VENV_PATH` | `/opt/venv` | Path del virtualenv Python |
| `VPS_GUNICORN_SERVICE` | `gunicorn` | Nome del servizio systemd |
| `VPS_APP_PORT` | `8000` | Porta su cui risponde gunicorn (health check) |

## Prerequisiti sul VPS

### 1. Clonare il repo (prima volta)
```bash
git clone https://github.com/ergin84/SHAReLAND_v.1.0.git /opt/SHAReLAND_v.1.0
```

### 2. Creare il virtualenv
```bash
python3.12 -m venv /opt/venv
source /opt/venv/bin/activate
pip install -r /opt/SHAReLAND_v.1.0/shareland/requirements.txt
```

### 3. Permettere a GitHub Actions di fare sudo systemctl reload
L'utente SSH deve poter ricaricare il servizio gunicorn senza password.
Aggiungi questa riga in `/etc/sudoers.d/cicd`:
```
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl reload gunicorn, /bin/systemctl restart gunicorn
```
(sostituisci `ubuntu` con il tuo utente e `gunicorn` con il nome del servizio)

### 4. Aggiungere la chiave SSH di GitHub Actions
Genera una coppia di chiavi dedicata per il deploy:
```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_actions -N ""
# Aggiungi la chiave pubblica al VPS:
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys
# Copia il contenuto della chiave PRIVATA nel secret VPS_SSH_KEY:
cat ~/.ssh/github_actions
```

## Flusso CI/CD

```
git push origin main
        │
        ▼
┌───────────────────────────────────┐
│  CI  (ci.yml)                     │
│  1. Lint ruff (E,W,F rules)       │
│  2. Django system check           │
│  3. Check migrazioni committed    │
└──────────────┬────────────────────┘
               │ verde?
               ▼
┌───────────────────────────────────┐
│  Deploy  (deploy.yml)             │
│  1. git reset --hard origin/main  │
│  2. pip install -r requirements   │
│  3. manage.py migrate             │
│  4. manage.py collectstatic       │
│  5. systemctl reload gunicorn     │
│  6. curl /health/ → 200?          │
│     NO → systemctl restart + exit │
└───────────────────────────────────┘
```

## Rollback manuale
Se un deploy rompe tutto:
```bash
ssh ubuntu@<VPS_HOST>
cd /opt/SHAReLAND_v.1.0
git log --oneline -5          # trova il commit buono
git reset --hard <commit>
source /opt/venv/bin/activate
python shareland/manage.py migrate  # se necessario
sudo systemctl restart gunicorn
```
