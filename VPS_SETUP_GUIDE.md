# Guida: Preparare un VPS Aruba per SHAReLAND

Stack: **Ubuntu 24.04 LTS · Python 3.12 · PostgreSQL 16 + PostGIS · Gunicorn · Nginx · Certbot (SSL)**

---

## Indice

1. [Accesso iniziale e hardening SSH](#1-accesso-iniziale-e-hardening-ssh)
2. [Firewall UFW](#2-firewall-ufw)
3. [Aggiornamento sistema e dipendenze](#3-aggiornamento-sistema-e-dipendenze)
4. [Utente applicativo](#4-utente-applicativo)
5. [PostgreSQL + PostGIS](#5-postgresql--postgis)
6. [Python 3.12 e virtualenv](#6-python-312-e-virtualenv)
7. [Clonare il repository](#7-clonare-il-repository)
8. [Variabili d'ambiente (.env)](#8-variabili-dambiente-env)
9. [Migrazioni e static files](#9-migrazioni-e-static-files)
10. [Gunicorn come servizio systemd](#10-gunicorn-come-servizio-systemd)
11. [Nginx come reverse proxy](#11-nginx-come-reverse-proxy)
12. [DNS — collegare il dominio](#12-dns--collegare-il-dominio)
13. [SSL con Certbot (Let's Encrypt)](#13-ssl-con-certbot-lets-encrypt)
14. [Hardening sicurezza finale](#14-hardening-sicurezza-finale)
15. [CI/CD — deploy automatico da GitHub](#15-cicd--deploy-automatico-da-github)
16. [Manutenzione e backup](#16-manutenzione-e-backup)
17. [Checklist finale](#17-checklist-finale)

---

## 1. Accesso iniziale e hardening SSH

### 1.1 Prima connessione (root con password Aruba)

```bash
ssh root@<IP_VPS>
```

### 1.2 Creare un utente admin non-root

```bash
adduser shareland_admin
usermod -aG sudo shareland_admin
```

### 1.3 Configurare autenticazione con chiave SSH

Sul tuo computer locale:
```bash
ssh-keygen -t ed25519 -C "shareland-vps" -f ~/.ssh/shareland_vps
ssh-copy-id -i ~/.ssh/shareland_vps.pub shareland_admin@<IP_VPS>
```

### 1.4 Disabilitare accesso SSH con password e root login

```bash
sudo nano /etc/ssh/sshd_config
```

Modifica queste righe:
```
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
Port 2222          # cambia porta default (opzionale ma consigliato)
```

```bash
sudo systemctl restart ssh
```

> **Attenzione:** Prima di chiudere la sessione, apri un secondo terminale e verifica che il login con chiave funzioni.

---

## 2. Firewall UFW

```bash
sudo apt install -y ufw

# Policy di default: nega tutto in ingresso, permetti tutto in uscita
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Permetti SSH (usa la porta che hai impostato)
sudo ufw allow 2222/tcp comment 'SSH'

# HTTP e HTTPS (Nginx)
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'

# Attiva il firewall
sudo ufw enable
sudo ufw status verbose
```

> PostgreSQL (5432) NON deve essere esposto pubblicamente — è accessibile solo in localhost.

---

## 3. Aggiornamento sistema e dipendenze

```bash
sudo apt update && sudo apt upgrade -y

sudo apt install -y \
  git curl wget unzip \
  build-essential python3-dev \
  libpq-dev \
  gdal-bin libgdal-dev \
  libgeos-dev libproj-dev \
  nginx \
  certbot python3-certbot-nginx \
  postgresql-16 postgresql-16-postgis-3 \
  fail2ban
```

---

## 4. Utente applicativo

È buona pratica far girare l'app con un utente dedicato senza privilegi sudo:

```bash
sudo useradd --system --shell /bin/bash --home /opt/shareland --create-home shareland
```

---

## 5. PostgreSQL + PostGIS

### 5.1 Avviare PostgreSQL

```bash
sudo systemctl enable --now postgresql
```

### 5.2 Creare database e utente

```bash
sudo -u postgres psql
```

```sql
CREATE USER shareland_user WITH PASSWORD 'password_sicura_qui';
CREATE DATABASE shareland_db OWNER shareland_user;
\c shareland_db
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;
-- Concedi tutti i privilegi necessari
GRANT ALL PRIVILEGES ON DATABASE shareland_db TO shareland_user;
\q
```

### 5.3 Configurare autenticazione locale (pg_hba.conf)

```bash
sudo nano /etc/postgresql/16/main/pg_hba.conf
```

Aggiungi (o verifica che esista) questa riga:
```
local   shareland_db    shareland_user                  md5
host    shareland_db    shareland_user  127.0.0.1/32    md5
```

```bash
sudo systemctl restart postgresql
```

### 5.4 Test connessione

```bash
psql -h 127.0.0.1 -U shareland_user -d shareland_db -c "SELECT PostGIS_Version();"
```

---

## 6. Python 3.12 e virtualenv

```bash
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# Crea il virtualenv nella home dell'utente app
sudo -u shareland python3.12 -m venv /opt/shareland/venv
```

---

## 7. Clonare il repository

```bash
sudo -u shareland git clone https://github.com/ergin84/SHAReLAND_v.1.0.git \
  /opt/shareland/app

# Installa dipendenze Python
sudo -u shareland /opt/shareland/venv/bin/pip install --upgrade pip
sudo -u shareland /opt/shareland/venv/bin/pip install \
  -r /opt/shareland/app/shareland/requirements.txt
```

---

## 8. Variabili d'ambiente (.env)

```bash
sudo -u shareland nano /opt/shareland/app/shareland/.env
```

```env
# Django
SECRET_KEY=una-chiave-segreta-lunga-e-casuale-minimo-50-caratteri
DEBUG=False
ALLOWED_HOSTS=tuodominio.it,www.tuodominio.it

# Database
DB_NAME=shareland_db
DB_USER=shareland_user
DB_PASSWORD=password_sicura_qui
DB_HOST=127.0.0.1
DB_PORT=5432

# Gunicorn
PORT=8000
GUNICORN_WORKERS=3
GUNICORN_TIMEOUT=120
GUNICORN_LOG_LEVEL=info

# Media / Static
MEDIA_ROOT=/opt/shareland/media
STATIC_ROOT=/opt/shareland/static
```

```bash
# Proteggi il file: leggibile solo dall'utente app
sudo chmod 600 /opt/shareland/app/shareland/.env
sudo chown shareland:shareland /opt/shareland/app/shareland/.env
```

Verifica che `settings.py` carichi il file `.env` (già presente con `python-dotenv`):
```python
# shareland/ShareLand/settings.py — già configurato:
from dotenv import load_dotenv
load_dotenv()
```

---

## 9. Migrazioni e static files

```bash
cd /opt/shareland/app/shareland

sudo -u shareland /opt/shareland/venv/bin/python manage.py migrate --noinput
sudo -u shareland /opt/shareland/venv/bin/python manage.py collectstatic --noinput --clear
sudo -u shareland /opt/shareland/venv/bin/python manage.py createsuperuser
```

---

## 10. Gunicorn come servizio systemd

```bash
sudo nano /etc/systemd/system/shareland.service
```

```ini
[Unit]
Description=SHAReLAND Gunicorn Application Server
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=notify
User=shareland
Group=shareland
WorkingDirectory=/opt/shareland/app/shareland
EnvironmentFile=/opt/shareland/app/shareland/.env
ExecStart=/opt/shareland/venv/bin/gunicorn \
    --config /opt/shareland/app/shareland/gunicorn_config.py \
    ShareLand.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now shareland
sudo systemctl status shareland
```

### Comandi utili Gunicorn

```bash
sudo systemctl status shareland       # stato
sudo systemctl reload shareland       # reload graceful (zero-downtime)
sudo systemctl restart shareland      # restart completo
journalctl -u shareland -f            # log in tempo reale
journalctl -u shareland -n 100        # ultimi 100 log
```

---

## 11. Nginx come reverse proxy

```bash
sudo nano /etc/nginx/sites-available/shareland
```

```nginx
server {
    listen 80;
    server_name tuodominio.it www.tuodominio.it;

    # Redirect HTTP → HTTPS (verrà gestito da Certbot, sezione 13)
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name tuodominio.it www.tuodominio.it;

    # SSL — certificati inseriti da Certbot
    # ssl_certificate     /etc/letsencrypt/live/tuodominio.it/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/tuodominio.it/privkey.pem;
    # include /etc/letsencrypt/options-ssl-nginx.conf;
    # ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Sicurezza headers
    add_header X-Frame-Options           "SAMEORIGIN"   always;
    add_header X-Content-Type-Options    "nosniff"      always;
    add_header X-XSS-Protection          "1; mode=block" always;
    add_header Referrer-Policy           "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Dimensione massima upload (per backup/media)
    client_max_body_size 100M;

    # Static files — serviti direttamente da Nginx (più veloce di Django)
    location /static/ {
        alias /opt/shareland/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /opt/shareland/media/;
        expires 30d;
        add_header Cache-Control "public";
    }

    # Tutto il resto → Gunicorn
    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }
}
```

```bash
# Abilita il sito
sudo ln -s /etc/nginx/sites-available/shareland /etc/nginx/sites-enabled/

# Rimuovi il sito default
sudo rm -f /etc/nginx/sites-enabled/default

# Test configurazione
sudo nginx -t

# Avvia Nginx
sudo systemctl enable --now nginx
```

---

## 12. DNS — collegare il dominio

Nel pannello DNS del tuo registrar (o Aruba DNS):

| Tipo | Nome | Valore | TTL |
|------|------|---------|-----|
| `A` | `@` (o `tuodominio.it`) | `<IP_VPS>` | 3600 |
| `A` | `www` | `<IP_VPS>` | 3600 |

Verifica propagazione (dopo 5–30 minuti):
```bash
dig tuodominio.it +short
nslookup tuodominio.it
```

---

## 13. SSL con Certbot (Let's Encrypt)

```bash
# Ottieni e installa il certificato (modifica automatica nginx.conf)
sudo certbot --nginx -d tuodominio.it -d www.tuodominio.it

# Segui le istruzioni: inserisci email, accetta termini, scegli redirect 301
```

Certbot aggiorna automaticamente il blocco `server { listen 443 }` in Nginx con i path SSL corretti.

### Rinnovo automatico

Certbot installa un timer systemd che rinnova ogni 60 giorni:
```bash
sudo systemctl status certbot.timer    # verifica che sia attivo
sudo certbot renew --dry-run           # test rinnovo
```

---

## 14. Hardening sicurezza finale

### 14.1 Fail2Ban (protezione brute-force SSH)

```bash
sudo nano /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime  = 3600
findtime = 600
maxretry = 5

[sshd]
enabled  = true
port     = 2222
logpath  = /var/log/auth.log
```

```bash
sudo systemctl enable --now fail2ban
sudo fail2ban-client status sshd
```

### 14.2 Django settings di produzione

Verifica che in `.env` siano impostati:
```env
DEBUG=False
SECRET_KEY=<chiave lunga e unica>
ALLOWED_HOSTS=tuodominio.it,www.tuodominio.it
```

E in `settings.py` (già presenti, da verificare):
```python
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'SAMEORIGIN'
SESSION_COOKIE_SECURE = True        # richiede HTTPS
CSRF_COOKIE_SECURE = True           # richiede HTTPS
SECURE_SSL_REDIRECT = True          # forza HTTPS
SECURE_HSTS_SECONDS = 31536000
```

### 14.3 Permessi filesystem

```bash
# L'utente app possiede solo la sua home
sudo chown -R shareland:shareland /opt/shareland/
sudo chmod -R 750 /opt/shareland/app/
sudo chmod -R 755 /opt/shareland/static/
sudo chmod -R 755 /opt/shareland/media/
sudo chmod 600 /opt/shareland/app/shareland/.env
```

### 14.4 Aggiornamenti automatici di sicurezza

```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
# Seleziona "Yes" per installare aggiornamenti di sicurezza automaticamente
```

---

## 15. CI/CD — deploy automatico da GitHub

Consulta `.github/CICD_SETUP.md` per la configurazione completa.

Il deploy SSH esegue questi comandi sul VPS:

```bash
cd /opt/shareland/app
git fetch origin main && git reset --hard origin/main
source /opt/shareland/venv/bin/activate
pip install -q -r shareland/requirements.txt
cd shareland
python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear
sudo systemctl reload shareland
```

Aggiungi la sudoers rule per il reload senza password:
```bash
sudo visudo -f /etc/sudoers.d/shareland-cicd
```
```
shareland_admin ALL=(ALL) NOPASSWD: /bin/systemctl reload shareland, /bin/systemctl restart shareland
```

---

## 16. Manutenzione e backup

### Log applicazione
```bash
journalctl -u shareland -f              # log gunicorn live
journalctl -u nginx -f                  # log nginx live
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Backup database (cron giornaliero)

```bash
sudo -u shareland crontab -e
```

```cron
# Backup database ogni giorno alle 02:00
0 2 * * * pg_dump -U shareland_user -h 127.0.0.1 -Fc shareland_db \
  > /opt/shareland/backups/db_$(date +\%Y\%m\%d).dump \
  && find /opt/shareland/backups/ -name "db_*.dump" -mtime +30 -delete
```

```bash
mkdir -p /opt/shareland/backups
chown shareland:shareland /opt/shareland/backups
```

### Restore database

```bash
pg_restore -U shareland_user -h 127.0.0.1 -d shareland_db \
  /opt/shareland/backups/db_20250415.dump
```

---

## 17. Checklist finale

```
[ ] VPS accessibile solo via chiave SSH (password disabilitata)
[ ] Root login SSH disabilitato
[ ] UFW attivo: porte 80, 443, 2222 (SSH) aperte; 5432 chiusa
[ ] Fail2Ban attivo e monitorato
[ ] PostgreSQL: utente dedicato, estensioni PostGIS installate
[ ] .env con DEBUG=False, SECRET_KEY univoca, ALLOWED_HOSTS corretto
[ ] Gunicorn: servizio systemd attivo, si riavvia automaticamente
[ ] Nginx: configurato come reverse proxy, static/media serviti direttamente
[ ] SSL: certificato Let's Encrypt installato, rinnovo automatico attivo
[ ] Headers sicurezza in Nginx: X-Frame-Options, HSTS, ecc.
[ ] Django SECURE_* settings abilitati (richiede HTTPS)
[ ] DNS: record A punta al VPS, propagazione verificata
[ ] Backup cron attivo
[ ] CI/CD GitHub Actions configurato (secrets VPS_HOST, VPS_SSH_KEY, ecc.)
[ ] Health check /health/ risponde 200
[ ] Pagine errore custom (404, 500) visibili con DEBUG=False
```

---

*Guida specifica per SHAReLAND v1.0 — Django 5.2 · Python 3.12 · PostgreSQL 16 + PostGIS · Ubuntu 24.04*
