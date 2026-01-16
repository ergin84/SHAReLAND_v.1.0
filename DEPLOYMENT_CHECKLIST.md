# ✅ CHECKLIST PRE-DEPLOYMENT - SHAReLAND

## Prima del Deployment

### 🔐 Certificati SSL
- [ ] Installato certbot sul VPS
- [ ] Ottenuti certificati per shareland.it e www.shareland.it
- [ ] Certificati copiati in `./ssl/cert.pem` e `./ssl/key.pem`
- [ ] Verificata scadenza certificati: `openssl x509 -enddate -noout -in ./ssl/cert.pem`
- [ ] Impostato cron job per auto-rinnovo

### ⚙️ Configurazione
- [ ] File `.env` creato da `.env.production.example`
- [ ] `SECRET_KEY` generata e unica
- [ ] `DEBUG=False` impostato
- [ ] `ALLOWED_HOSTS` aggiornato con dominio reale
- [ ] Password database sicure configurate
- [ ] Email SMTP configurato e testato
- [ ] Admin email configurato

### 🌐 DNS
- [ ] Record A per shareland.it punta a VPS IP
- [ ] Record A per www.shareland.it punta a VPS IP
- [ ] DNS propagato (verifica con `nslookup shareland.it`)
- [ ] TTL abbassato a 300 secondi prima del cambio

### 💾 Database
- [ ] Backup database esistente creato
- [ ] Dump PostgreSQL testato e funzionante
- [ ] Piano di rollback preparato

### 🔥 Firewall
- [ ] Porta 80 aperta
- [ ] Porta 443 aperta
- [ ] Porta 22 (SSH) aperta solo per IP fidati
- [ ] Altre porte bloccate

---

## Durante il Deployment

### 📦 Sync File
```bash
# 1. Dalla macchina locale
./deployment.sh <VPS_IP> <VPS_USER> <VPS_PASSWORD>
```
- [ ] File sincronizzati con successo
- [ ] Nessun errore durante rsync

### 🐳 Docker Build
```bash
# 2. Sul VPS
ssh user@vps_ip
cd ShareLand

# Stop containers esistenti
docker compose down

# Build e start
docker compose up -d --build
```
- [ ] Build completato senza errori
- [ ] Tutti i container avviati
- [ ] Health checks passano

### 🔍 Verifiche Iniziali
```bash
# 3. Verifica servizi
docker compose ps

# Output atteso: tutti i container "Up" e "healthy"
```
- [ ] Container `web` attivo
- [ ] Container `nginx` attivo
- [ ] Container `postgres` attivo e healthy
- [ ] Container `pgadmin` attivo (opzionale)

---

## Post-Deployment

### ✅ Verifiche Funzionali

#### Health Checks
```bash
# Da VPS
curl http://localhost/health/ | jq
curl http://localhost/health/live/
curl http://localhost/health/ready/
```
- [ ] `/health/` risponde con status 200
- [ ] Database check: OK
- [ ] Disk space check: OK
- [ ] Memory check: OK
- [ ] CPU check: OK

#### Accesso Web
```bash
# Da browser
https://shareland.it
```
- [ ] Homepage carica correttamente
- [ ] HTTPS attivo (lucchetto verde)
- [ ] Nessun warning certificato
- [ ] Redirect HTTP → HTTPS funziona
- [ ] Immagini e CSS caricati

#### Funzionalità Applicazione
- [ ] Login utente funziona
- [ ] Registrazione nuovo utente funziona
- [ ] Catalogo ricerche carica
- [ ] Dettaglio ricerca carica
- [ ] Mappe visualizzate correttamente
- [ ] Upload file funziona
- [ ] Creazione nuova ricerca funziona

### 🔍 Verifiche SEO

#### Sitemap
```bash
curl https://shareland.it/sitemap.xml
```
- [ ] Sitemap.xml accessibile
- [ ] Contiene URL delle ricerche
- [ ] Contiene URL dei siti
- [ ] Formato XML valido

#### Robots.txt
```bash
curl https://shareland.it/robots.txt
```
- [ ] Robots.txt accessibile
- [ ] Contiene link a sitemap
- [ ] Disallow corretti per /admin/, /api/, etc.

#### Meta Tags
```bash
curl -s https://shareland.it/ | grep -i "meta"
```
- [ ] Tag `<meta name="description">` presente
- [ ] Tag `<meta name="keywords">` presente
- [ ] Open Graph tags presenti
- [ ] Twitter Card tags presenti
- [ ] Canonical URL presente

#### Structured Data
- [ ] Apri https://search.google.com/test/rich-results
- [ ] Inserisci URL ricerca (es. https://shareland.it/public/research/1/)
- [ ] Verifica presenza ScholarlyArticle schema
- [ ] [ ] Nessun errore validazione

### 🔒 Verifiche Sicurezza

#### SSL/TLS
- [ ] Apri https://www.ssllabs.com/ssltest/
- [ ] Inserisci shareland.it
- [ ] Attendi scansione completa
- [ ] Score A o superiore

#### Security Headers
```bash
curl -I https://shareland.it/
```
- [ ] `Strict-Transport-Security` presente
- [ ] `X-Frame-Options` presente
- [ ] `X-Content-Type-Options` presente
- [ ] `X-XSS-Protection` presente

#### Rate Limiting
```bash
# Test rate limit (esegui più volte rapidamente)
for i in {1..30}; do curl -I https://shareland.it/; done
```
- [ ] Dopo ~10 richieste, ricevi 429 Too Many Requests
- [ ] Rate limiting funziona

### 📊 Verifiche Performance

#### PageSpeed
- [ ] Apri https://pagespeed.web.dev/
- [ ] Inserisci https://shareland.it
- [ ] Score Mobile > 80
- [ ] Score Desktop > 85

#### Load Time
```bash
curl -w "@-" -o /dev/null -s https://shareland.it/ <<'EOF'
    time_namelookup:  %{time_namelookup}\n
       time_connect:  %{time_connect}\n
    time_appconnect:  %{time_appconnect}\n
      time_redirect:  %{time_redirect}\n
   time_pretransfer:  %{time_pretransfer}\n
 time_starttransfer:  %{time_starttransfer}\n
                    ----------\n
         time_total:  %{time_total}\n
EOF
```
- [ ] time_total < 2 secondi
- [ ] time_starttransfer < 1 secondo

### 📝 Logging

#### Verifica Log
```bash
# Sul VPS
cd ShareLand

# Django logs
docker compose logs web --tail=50

# Nginx logs
docker compose logs nginx --tail=50

# Postgres logs
docker compose logs postgres --tail=50
```
- [ ] Nessun errore critico nei log
- [ ] Request logging attivo
- [ ] Log file creati in `./logs/`

---

## Registrazione Motori di Ricerca

### Google Search Console
1. [ ] Vai a https://search.google.com/search-console
2. [ ] Clicca "Aggiungi proprietà"
3. [ ] Inserisci `https://shareland.it`
4. [ ] Scegli metodo verifica (HTML file o DNS)
5. [ ] Completa verifica
6. [ ] Vai su "Sitemaps"
7. [ ] Aggiungi `https://shareland.it/sitemap.xml`
8. [ ] Attendi indicizzazione (24-48 ore)

### Bing Webmaster Tools
1. [ ] Vai a https://www.bing.com/webmasters
2. [ ] Aggiungi sito `https://shareland.it`
3. [ ] Completa verifica
4. [ ] Invia sitemap `https://shareland.it/sitemap.xml`

---

## Monitoring Setup

### UptimeRobot (Gratuito)
1. [ ] Vai a https://uptimerobot.com
2. [ ] Crea account gratuito
3. [ ] Aggiungi monitor:
   - Type: HTTPS
   - URL: https://shareland.it/health/live/
   - Interval: 5 minuti
4. [ ] Imposta alert email per downtime
5. [ ] Verifica test alert

### Email Alerts Django
```bash
# Test email alerts
docker compose exec web python manage.py shell

# In shell Python:
from django.core.mail import mail_admins
mail_admins('Test Alert', 'This is a test alert from SHAReLAND')
```
- [ ] Email ricevuta correttamente
- [ ] Formato email corretto

---

## Backup Setup

### Database Backup
```bash
# Creare script backup
sudo nano /usr/local/bin/backup-shareland-db.sh
```

Contenuto:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/$USER/backups"
mkdir -p $BACKUP_DIR

docker compose exec -T postgres pg_dump -U postgres Open_Landscapes > $BACKUP_DIR/shareland_$DATE.sql

# Keep only last 7 backups
ls -t $BACKUP_DIR/shareland_*.sql | tail -n +8 | xargs rm -f

echo "$(date): Database backup completed" >> /var/log/shareland-backup.log
```

- [ ] Script creato
- [ ] Reso eseguibile: `chmod +x /usr/local/bin/backup-shareland-db.sh`
- [ ] Testato manualmente
- [ ] Aggiunto a cron (daily 2 AM):

```bash
sudo crontab -e
# Aggiungere:
0 2 * * * /usr/local/bin/backup-shareland-db.sh
```

---

## Test Finali

### Stress Test (Opzionale)
```bash
# Installare apache bench
sudo apt install apache2-utils

# Test 1000 richieste, 10 concorrenti
ab -n 1000 -c 10 https://shareland.it/
```
- [ ] Tutte le richieste completate
- [ ] Failed requests: 0
- [ ] Requests per second > 50

### End-to-End Test
1. [ ] Registra nuovo utente
2. [ ] Login con nuovo utente
3. [ ] Crea nuova ricerca
4. [ ] Aggiungi sito archeologico
5. [ ] Upload shapefile
6. [ ] Visualizza mappa
7. [ ] Verifica salvataggio
8. [ ] Logout
9. [ ] Login come admin
10. [ ] Verifica audit logs

---

## Documentazione Post-Deploy

- [ ] Screenshot configurazione funzionante
- [ ] Note su eventuali problemi risolti
- [ ] Credenziali salvate in password manager sicuro
- [ ] Documentazione aggiornata con configurazione specifica
- [ ] Team informato del go-live

---

## Comunicazione

### Stakeholders
- [ ] Email a Hyperstage con conferma deployment
- [ ] Riepilogo funzionalità implementate
- [ ] Link al sito in produzione
- [ ] Credenziali accesso test (se richieste)
- [ ] Prossimi passi per SEO (tempi indicizzazione)

### Team
- [ ] Documento deployment condiviso
- [ ] Procedure rollback documentate
- [ ] Contatti on-call definiti
- [ ] Documentazione accessibile

---

## Rollback Plan (in caso di problemi)

```bash
# 1. Stop new version
docker compose down

# 2. Restore old version (se necessario)
git checkout <previous-commit>

# 3. Rebuild
docker compose up -d --build

# 4. Restore database backup (se necessario)
docker compose exec -T postgres psql -U postgres Open_Landscapes < backup.sql

# 5. Verify
curl http://localhost/health/
```

---

## Note

- ✅ = Task completato
- ⚠️ = Task con issue (documentare)
- ❌ = Task fallito (blocco deployment)

**Non procedere se ci sono task ❌**

---

**Data Deployment**: _______________
**Deployed By**: _______________
**Version**: v2.0
**Status**: ⬜ Success  ⬜ Issues  ⬜ Rollback

---

*Basato su STABILITY_AND_SEO_GUIDE.md*
