# SHAReLAND - Misure di Stabilità e SEO

## Data: Dicembre 2025

Questo documento descrive tutte le misure implementate per migliorare la stabilità del front-end e l'indicizzazione SEO del progetto SHAReLAND.

---

## 📊 STABILITÀ DEL FRONT-END

### 1. Gestione Robusta degli Errori

**File**: `shareland/frontend/error_middleware.py`

#### ErrorHandlingMiddleware
Middleware personalizzato che intercetta e gestisce tutti gli errori non catturati:

- **404 (Not Found)**: Pagina di errore personalizzata
- **403 (Forbidden)**: Gestione permessi
- **400 (Bad Request)**: Richieste malformate
- **500 (Internal Server Error)**: Errori del server con logging completo

**Caratteristiche**:
- Logging dettagliato di ogni errore con traceback completo
- Supporto JSON per API (content negotiation)
- Pagine di errore user-friendly in HTML
- Informazioni di debug in modalità sviluppo

#### Pagine di Errore Personalizzate
Locate in: `shareland/frontend/templates/errors/`
- `400.html` - Bad Request
- `403.html` - Forbidden  
- `404.html` - Not Found
- `429.html` - Too Many Requests
- `500.html` - Server Error

### 2. Rate Limiting e Protezione DDoS

**File**: `shareland/frontend/error_middleware.py` - `RateLimitMiddleware`

**Configurazione**:
- Limite: 100 richieste per minuto per IP
- Protezione automatica contro attacchi flood
- Whitelist per percorsi statici e admin
- Risposta HTTP 429 quando superato il limite

**Nota**: In produzione, si raccomanda di usare Redis o Memcached invece della cache in-memory.

### 3. Health Checks e Monitoring

**File**: `shareland/frontend/health_views.py`

#### Endpoints disponibili:

1. **`/health/`** - Comprehensive Health Check
   - Verifica connessione database
   - Monitoraggio spazio disco
   - Controllo uso memoria
   - Verifica CPU
   - Risponde con status 200 (healthy) o 503 (unhealthy)

2. **`/health/ready/`** - Readiness Check
   - Verifica se l'applicazione è pronta a ricevere traffico
   - Usato dai load balancers

3. **`/health/live/`** - Liveness Check
   - Verifica se l'applicazione è in esecuzione
   - Usato da Kubernetes/Docker per restart automatici

**Vantaggi**:
- Monitoraggio proattivo dello stato del sistema
- Rilevamento precoce di problemi
- Integrazione con sistemi di alerting esterni

### 4. Nginx - Reverse Proxy Robusto

**File**: `shareland/nginx/default.conf`

**Caratteristiche implementate**:

#### Rate Limiting a livello Nginx
- 10 richieste/secondo con burst fino a 20
- Protezione aggiuntiva al middleware Django

#### Caching Intelligente
- Cache statica aggressiva (1 anno per CSS/JS/immagini)
- Cache breve per contenuti dinamici (5 minuti)
- Cache sitemap e robots.txt
- Bypass cache per utenti autenticati

#### Security Headers
- `Strict-Transport-Security` (HSTS)
- `X-Frame-Options`
- `X-Content-Type-Options`
- `X-XSS-Protection`
- `Referrer-Policy`
- `Permissions-Policy`

#### Compressione Gzip
- Riduzione bandwidth del 60-80%
- Compressione di HTML, CSS, JS, JSON, SVG

#### Load Balancing
- Algoritmo `least_conn` per distribuzione ottimale
- Health checks automatici del backend
- Failover automatico

#### Redirect HTTP → HTTPS
- Tutto il traffico HTTP reindirizzato a HTTPS
- Eccezione per health checks

### 5. Logging Avanzato

**File**: `shareland/ShareLand/settings.py` - sezione `LOGGING`

**Configurazione**:
- **Console**: Output in tempo reale (INFO level)
- **File**: Log rotanti (10 file x 10MB) per errori
- **Email**: Notifiche agli admin per errori critici

**Log files**: `shareland/logs/django.log`

**Logs per**:
- Richieste Django
- Errori dell'applicazione
- Frontend custom logs

---

## 🔍 INDICIZZAZIONE E SEO

### 1. Meta Tags Dinamici

**File**: `shareland/frontend/templates/frontend/base.html`

#### Meta Tags Implementati:

**Base SEO**:
- `<title>` dinamico per ogni pagina
- `description` - Descrizione della pagina
- `keywords` - Parole chiave rilevanti
- `canonical` - URL canonico per evitare contenuti duplicati
- `robots` - Indicazioni per i crawler (index, follow)

**Open Graph (Facebook, LinkedIn)**:
- `og:type` - Tipo di contenuto
- `og:url` - URL della pagina
- `og:title` - Titolo
- `og:description` - Descrizione
- `og:image` - Immagine di anteprima
- `og:site_name` - Nome del sito
- `article:published_time` - Data pubblicazione (per ricerche)
- `article:author` - Autore

**Twitter Card**:
- `twitter:card` - Tipo di card (summary_large_image)
- `twitter:title` - Titolo
- `twitter:description` - Descrizione
- `twitter:image` - Immagine di anteprima

**Context Processor SEO**:
File: `shareland/frontend/seo_utils.py`
- Fornisce valori SEO di default a tutti i template
- Classe `SEOMetaTags` per gestione centralizzata

### 2. Sitemap XML

**File**: `shareland/frontend/seo_views.py`

**Sitemaps implementate**:

1. **StaticViewSitemap**: Pagine statiche
   - Homepage
   - Research Catalog
   - Public Research List
   - Priority: 0.8, Changefreq: weekly

2. **ResearchSitemap**: Ricerche archeologiche
   - URL: `/public/research/<id>/`
   - Priority: 0.9, Changefreq: monthly
   - Include data ultima modifica

3. **SiteSitemap**: Siti archeologici
   - URL: `/site/<id>/`
   - Priority: 0.7, Changefreq: monthly

**URL**: `https://shareland.it/sitemap.xml`

**Registrazione**:
- Google Search Console
- Bing Webmaster Tools

### 3. Robots.txt

**File**: `shareland/frontend/seo_views.py` - `robots_txt()`

**Configurazione**:
```
User-agent: *
Allow: /
Disallow: /admin/
Disallow: /database-browser/
Disallow: /audit-logs/
Disallow: /api/
Disallow: /ajax/

Sitemap: https://shareland.it/sitemap.xml
Crawl-delay: 1
```

**URL**: `https://shareland.it/robots.txt`

### 4. Structured Data (Schema.org JSON-LD)

**File**: `shareland/frontend/templates/frontend/public_research_detail.html`

#### Schema Implementato: ScholarlyArticle

**Proprietà**:
- `headline` - Titolo della ricerca
- `datePublished` - Data di pubblicazione
- `description` - Abstract della ricerca
- `keywords` - Parole chiave
- `author` - Array di autori con nome e affiliazione
- `inLanguage` - Lingua del contenuto
- `publisher` - SHAReLAND

**Vantaggi**:
- Rich snippets nei risultati di ricerca Google
- Miglior comprensione del contenuto da parte dei motori
- Maggiore visibilità e CTR

### 5. URL Ottimizzati

**Best practices applicate**:
- URL descrittivi e leggibili
- Uso di slug invece di ID quando possibile
- Struttura gerarchica logica
- Canonical tags per evitare contenuti duplicati

---

## 🔒 SICUREZZA IN PRODUZIONE

**File**: `shareland/ShareLand/settings.py`

### Security Settings (solo in produzione - DEBUG=False):

```python
SECURE_SSL_REDIRECT = True              # Force HTTPS
SESSION_COOKIE_SECURE = True            # Cookie solo HTTPS
CSRF_COOKIE_SECURE = True               # CSRF token solo HTTPS
SECURE_BROWSER_XSS_FILTER = True        # XSS protection
SECURE_CONTENT_TYPE_NOSNIFF = True      # MIME sniffing protection
SECURE_HSTS_SECONDS = 31536000          # HSTS per 1 anno
SECURE_HSTS_INCLUDE_SUBDOMAINS = True   # HSTS anche per subdomain
SECURE_HSTS_PRELOAD = True              # HSTS preload list
X_FRAME_OPTIONS = 'SAMEORIGIN'          # Clickjacking protection
```

### Proxy Headers
```python
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
```

---

## 🐳 DOCKER COMPOSE - PRODUZIONE

**File**: `docker-compose.yml`

### Miglioramenti Implementati:

#### 1. Gunicorn invece di runserver
```bash
gunicorn ShareLand.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 60 \
  --max-requests 1000 \
  --max-requests-jitter 50
```

**Vantaggi**:
- 4 worker processes per gestire carico elevato
- Timeout di 60 secondi per richieste lunghe
- Auto-restart workers dopo 1000 richieste (memory leak prevention)
- Logging strutturato

#### 2. Health Checks Docker
Tutti i servizi hanno health checks:
- **Postgres**: `pg_isready`
- **Web**: `curl http://localhost:8000/health/live/`
- **Nginx**: `wget http://localhost/health/live/`

#### 3. Resource Limits
Prevenzione consumo eccessivo risorse:

**Web Service**:
- Limits: 2 CPU, 2GB RAM
- Reservations: 0.5 CPU, 512MB RAM

**Nginx**:
- Limits: 1 CPU, 512MB RAM
- Reservations: 0.25 CPU, 128MB RAM

**Postgres**:
- Limits: 2 CPU, 2GB RAM
- Reservations: 0.5 CPU, 512MB RAM

#### 4. Restart Policies
- `restart: unless-stopped` per tutti i servizi
- Restart automatico in caso di crash
- Sopravvivenza a riavvii del sistema

#### 5. Container Nginx
Aggiunto container nginx separato:
- Reverse proxy per web service
- Gestione SSL/TLS
- Caching statico
- Rate limiting
- Security headers

#### 6. Volumes Persistenti
- `postgres_data` - Database persistente
- `pgadmin_data` - Configurazione pgAdmin
- `nginx_cache` - Cache nginx
- `logs` - Log applicazione

---

## 📋 CHECKLIST DEPLOYMENT

### Pre-Deployment

- [ ] **Certificati SSL**
  - Ottenere certificati SSL (Let's Encrypt consigliato)
  - Posizionare in `./ssl/cert.pem` e `./ssl/key.pem`
  - Aggiornare percorsi in `nginx/default.conf`

- [ ] **Variabili d'Ambiente**
  - Copiare `.env.example` a `shareland/.env`
  - Configurare `SECRET_KEY` forte e unico
  - Impostare `DEBUG=False`
  - Aggiornare `ALLOWED_HOSTS` con dominio reale
  - Configurare database credentials
  - Configurare email settings

- [ ] **Database**
  - Verificare backup database esistente
  - Testare restore del dump PostgreSQL

- [ ] **DNS**
  - Puntare dominio a server VPS
  - Configurare record A per `shareland.it`
  - Configurare record A per `www.shareland.it`

### Deployment

```bash
# 1. Sincronizzare file su VPS
./deployment.sh <VPS_IP> <VPS_USER> <VPS_PASSWORD>

# 2. Collegarsi al VPS
ssh user@vps_ip

# 3. Navigare alla cartella progetto
cd ShareLand

# 4. Build e avvio containers
docker compose down
docker compose up -d --build

# 5. Verificare health
curl http://localhost/health/
curl https://shareland.it/health/

# 6. Collect static files (se necessario)
docker compose exec web python manage.py collectstatic --noinput

# 7. Migrazioni database (se necessario)
docker compose exec web python manage.py migrate
```

### Post-Deployment

- [ ] **Verifica Funzionamento**
  - Testare accesso homepage
  - Verificare login utente
  - Testare creazione research
  - Controllare visualizzazione mappe

- [ ] **Verifica SEO**
  - Accedere a `https://shareland.it/robots.txt`
  - Accedere a `https://shareland.it/sitemap.xml`
  - Verificare meta tags in sorgente pagina
  - Test con [Google Rich Results Test](https://search.google.com/test/rich-results)

- [ ] **Registrazione Motori di Ricerca**
  - [Google Search Console](https://search.google.com/search-console)
    - Aggiungere proprietà
    - Verificare proprietà
    - Inviare sitemap
  - [Bing Webmaster Tools](https://www.bing.com/webmasters)
    - Aggiungere sito
    - Inviare sitemap

- [ ] **Monitoring**
  - Configurare uptime monitoring (es. UptimeRobot)
  - Impostare alert email per errori
  - Monitorare `/health/` endpoint

- [ ] **Performance**
  - Test con [Google PageSpeed Insights](https://pagespeed.web.dev/)
  - Test con [GTmetrix](https://gtmetrix.com/)
  - Verificare tempo caricamento < 3s

- [ ] **Sicurezza**
  - Test con [Mozilla Observatory](https://observatory.mozilla.org/)
  - Test SSL con [SSL Labs](https://www.ssllabs.com/ssltest/)
  - Verificare tutti i security headers

### Manutenzione Continua

**Giornaliera**:
- Controllo log errori: `docker compose logs web --tail=100`
- Verifica health checks: `curl http://localhost/health/`

**Settimanale**:
- Review log completi
- Verifica spazio disco
- Controllo performance database

**Mensile**:
- Backup completo database
- Aggiornamento dipendenze (security patches)
- Review delle metriche SEO in Google Search Console

---

## 🔧 TROUBLESHOOTING

### Errori Comuni

#### 1. Errore 502 Bad Gateway (Nginx)
**Causa**: Web service non risponde
**Soluzione**:
```bash
docker compose logs web
docker compose restart web
```

#### 2. Database connection error
**Causa**: Postgres non disponibile
**Soluzione**:
```bash
docker compose ps postgres
docker compose restart postgres
# Attendere health check
```

#### 3. Static files non caricati
**Causa**: collectstatic non eseguito
**Soluzione**:
```bash
docker compose exec web python manage.py collectstatic --noinput
```

#### 4. Certificato SSL non valido
**Causa**: Percorsi certificati errati in nginx
**Soluzione**:
- Verificare presenza certificati in `./ssl/`
- Controllare percorsi in `nginx/default.conf`
- Riavviare nginx: `docker compose restart nginx`

#### 5. Rate Limit eccessivo
**Causa**: IP bloccato per troppe richieste
**Soluzione**:
- Aumentare limite in `nginx/default.conf` (rate=10r/s)
- Aumentare limite in `error_middleware.py` (100 req/min)

---

## 📊 METRICHE DI SUCCESSO

### Stabilità
- ✅ Uptime > 99.9%
- ✅ Tempo risposta medio < 500ms
- ✅ Error rate < 0.1%
- ✅ Zero downtime per traffico normale

### SEO
- ✅ Sitemap generata automaticamente
- ✅ Robots.txt configurato
- ✅ Meta tags su tutte le pagine
- ✅ Structured data implementato
- ✅ Mobile-friendly (responsive design)
- ✅ HTTPS obbligatorio
- ✅ Performance score > 85/100

### Sicurezza
- ✅ Security headers implementati
- ✅ Rate limiting attivo
- ✅ HTTPS enforced
- ✅ HSTS configurato
- ✅ XSS protection attiva
- ✅ CSRF protection attiva

---

## 📞 SUPPORTO

Per problemi o domande:
1. Consultare questa documentazione
2. Controllare i log: `docker compose logs`
3. Verificare health checks: `/health/`
4. Contattare il team di sviluppo

---

## 📝 CHANGELOG

**Dicembre 2025 - v2.0**
- ✅ Implementato error handling middleware
- ✅ Aggiunto rate limiting
- ✅ Implementati health checks
- ✅ Configurato nginx con caching e security
- ✅ Implementati meta tags SEO dinamici
- ✅ Creato sitemap.xml automatico
- ✅ Aggiunto robots.txt
- ✅ Implementato structured data (Schema.org)
- ✅ Configurate security settings per produzione
- ✅ Migrato a Gunicorn
- ✅ Aggiunto container Nginx
- ✅ Implementati resource limits e health checks Docker

---

**Fine Documentazione**
