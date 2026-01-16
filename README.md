# 🏛️ SHAReLAND - Archaeological Research Database

**Version 2.0 - Production Ready**

SHAReLAND è una piattaforma completa per la gestione e catalogazione di ricerche archeologiche, siti e evidenze archeologiche.

---

## 🚀 Nuove Funzionalità v2.0 (Dicembre 2025)

### ✅ Stabilità e Affidabilità
- Sistema completo di error handling
- Rate limiting e protezione DDoS
- Health checks per monitoring
- Nginx ottimizzato con caching
- Gunicorn per gestione produzione
- Auto-restart e resource limits

### ✅ SEO e Indicizzazione
- Meta tags dinamici (Open Graph, Twitter Card)
- Sitemap XML automatica
- Robots.txt configurato
- Structured Data (Schema.org JSON-LD)
- Ottimizzazione per Google Search

### ✅ Sicurezza
- HTTPS enforced
- Security headers completi
- HSTS configurato
- Rate limiting a 2 livelli
- Logging avanzato

---

## 📚 Documentazione

| Documento | Descrizione |
|-----------|-------------|
| [HYPERSTAGE_SUMMARY.md](HYPERSTAGE_SUMMARY.md) | 📋 Riepilogo esecutivo per Hyperstage |
| [STABILITY_AND_SEO_GUIDE.md](STABILITY_AND_SEO_GUIDE.md) | 📖 Guida tecnica completa (48 pagine) |
| [SSL_SETUP_GUIDE.md](SSL_SETUP_GUIDE.md) | 🔐 Setup certificati SSL |

---

## 🛠️ Stack Tecnologico

- **Backend**: Django 5.2 + Python 3.12
- **Database**: PostgreSQL 16 + PostGIS
- **Server**: Gunicorn
- **Reverse Proxy**: Nginx
- **Container**: Docker + Docker Compose
- **Maps**: Leaflet + Folium
- **Frontend**: Bootstrap 5

---

## 🚀 Quick Start

### Prerequisiti
- Docker e Docker Compose
- Certificati SSL (Let's Encrypt raccomandato)

### Installazione

1. **Clone del repository**
```bash
git clone <repository-url>
cd SHAReLAND_v.1.0
```

2. **Configurazione environment**
```bash
cp deployment.env.example shareland/.env
# Modificare shareland/.env con le tue configurazioni
```

3. **Setup SSL**
```bash
# Vedere SSL_SETUP_GUIDE.md per istruzioni dettagliate
mkdir ssl
# Copiare cert.pem e key.pem in ./ssl/
```

4. **Build e avvio**
```bash
docker compose up -d --build
```

5. **Verifiche**
```bash
# Health check
curl http://localhost/health/

# Sitemap
curl http://localhost/sitemap.xml

# Robots.txt
curl http://localhost/robots.txt
```

---

## 📊 Health Checks

### Endpoints disponibili:

- **`/health/`** - Comprehensive health check
  - Database connectivity
  - Disk space
  - Memory usage
  - CPU usage

- **`/health/ready/`** - Readiness probe
  - Verifica disponibilità per traffico

- **`/health/live/`** - Liveness probe
  - Verifica processo attivo

### Esempio:
```bash
curl http://localhost/health/ | jq
```

Output:
```json
{
  "status": "healthy",
  "checks": {
    "database": {"status": "ok", "message": "Database connection successful"},
    "disk_space": {"status": "ok", "used_percent": 45.2, "available_gb": 120.5},
    "memory": {"status": "ok", "used_percent": 62.3, "available_gb": 3.2},
    "cpu": {"status": "ok", "used_percent": 15.7}
  }
}
```

---

## 🔍 SEO Features

### Sitemap XML
Generata automaticamente da:
- Pagine statiche (home, catalog)
- Ricerche archeologiche
- Siti archeologici

**URL**: `https://shareland.it/sitemap.xml`

### Robots.txt
Configurato per ottimale crawling.

**URL**: `https://shareland.it/robots.txt`

### Meta Tags
Ogni pagina include:
- Title e Description dinamici
- Open Graph tags (Facebook, LinkedIn)
- Twitter Card tags
- Canonical URLs

### Structured Data
JSON-LD Schema.org per:
- ScholarlyArticle (ricerche)
- Archaeological sites
- Authors e organizations

---

## 🔒 Sicurezza

### Security Headers Implementati
- `Strict-Transport-Security` (HSTS)
- `X-Frame-Options`
- `X-Content-Type-Options`
- `X-XSS-Protection`
- `Referrer-Policy`
- `Permissions-Policy`

### Rate Limiting
- **Nginx**: 10 req/s con burst 20
- **Django**: 100 req/min per IP

### HTTPS
- Redirect automatico HTTP → HTTPS
- HSTS con preload
- TLS 1.2+ only

---

## 📈 Performance

### Caching
- **Static files**: 1 anno
- **Media files**: 30 giorni
- **Dynamic content**: 5 minuti
- **Sitemap/Robots**: 1 ora/1 giorno

### Compression
- Gzip attivo per tutti i content types
- Riduzione bandwidth: 60-80%

### Resource Limits
Configurati per ogni servizio Docker:
- Web: 2 CPU, 2GB RAM
- Nginx: 1 CPU, 512MB RAM
- Postgres: 2 CPU, 2GB RAM

---

## 🐳 Docker Services

### Services disponibili:

| Service | Port | Description |
|---------|------|-------------|
| `web` | 8000 | Django + Gunicorn |
| `nginx` | 80, 443 | Reverse proxy |
| `postgres` | 5433 | PostgreSQL + PostGIS |
| `pgadmin` | 5050 | Database admin UI |

### Comandi utili:

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f web

# Restart service
docker compose restart web

# Execute command in container
docker compose exec web python manage.py shell

# Database migrations
docker compose exec web python manage.py migrate

# Collect static files
docker compose exec web python manage.py collectstatic --noinput
```

---

## 🔧 Configurazione

### Environment Variables

File: `shareland/.env`

```bash
# Django
DEBUG=False
SECRET_KEY=<your-secret-key>
ALLOWED_HOSTS=shareland.it,www.shareland.it

# Database
DB_NAME=Open_Landscapes
DB_USER=postgres
DB_PASSWORD=<secure-password>
DB_HOST=postgres
DB_PORT=5432

# Email
EMAIL_HOST=smtp.example.com
EMAIL_PORT=465
EMAIL_HOST_USER=noreply@shareland.it
EMAIL_HOST_PASSWORD=<password>
EMAIL_USE_SSL=True
DEFAULT_FROM_EMAIL=noreply@shareland.it
ADMIN_EMAIL=admin@shareland.it
```

---

## 📊 Monitoring

### Log Files
- **Application logs**: `shareland/logs/django.log`
- **Nginx logs**: Container logs
- **Database logs**: Container logs

### Viewing Logs
```bash
# Django application logs
docker compose logs -f web

# Nginx logs
docker compose logs -f nginx

# PostgreSQL logs
docker compose logs -f postgres

# All logs
docker compose logs -f
```

### External Monitoring
Integrabile con:
- UptimeRobot
- Datadog
- New Relic
- Prometheus + Grafana

---

## 🧪 Testing

### Health Check
```bash
curl http://localhost/health/ | jq
```

### SEO Check
```bash
# Sitemap
curl http://localhost/sitemap.xml

# Robots
curl http://localhost/robots.txt

# Meta tags
curl -s http://localhost/ | grep -i "meta"
```

### Performance Test
```bash
# Apache Bench
ab -n 1000 -c 10 http://localhost/

# Hey
hey -n 1000 -c 10 http://localhost/
```

---

## 🚢 Deployment

### Production Deployment

Vedere [STABILITY_AND_SEO_GUIDE.md](STABILITY_AND_SEO_GUIDE.md) per istruzioni complete.

**Quick deploy:**
```bash
./deployment.sh <VPS_IP> <VPS_USER> <VPS_PASSWORD>
```

### Post-Deploy Checklist
- [ ] Verificare HTTPS funzionante
- [ ] Controllare health checks
- [ ] Verificare sitemap.xml
- [ ] Testare robots.txt
- [ ] Registrare in Google Search Console
- [ ] Configurare monitoring esterno

---

## 🐛 Troubleshooting

### Service non avviato
```bash
docker compose ps
docker compose logs <service-name>
docker compose restart <service-name>
```

### Database connection error
```bash
docker compose restart postgres
docker compose exec postgres pg_isready -U postgres
```

### Static files non caricati
```bash
docker compose exec web python manage.py collectstatic --noinput
docker compose restart nginx
```

### SSL certificate error
Verificare presenza certificati in `./ssl/` e configurazione in `nginx/default.conf`.

---

## 📞 Support

Per assistenza tecnica:
1. Consultare la documentazione
2. Controllare i log: `docker compose logs`
3. Verificare health checks: `/health/`
4. Contattare il team di sviluppo

---

## 📝 Changelog

### v2.0 - Dicembre 2025
- ✅ Sistema completo error handling
- ✅ Rate limiting e protezione DDoS
- ✅ Health checks
- ✅ Nginx ottimizzato con caching
- ✅ Meta tags SEO dinamici
- ✅ Sitemap XML automatica
- ✅ Robots.txt
- ✅ Structured data (Schema.org)
- ✅ Security settings produzione
- ✅ Migrazione a Gunicorn
- ✅ Container Nginx
- ✅ Resource limits e health checks Docker

### v1.0 - 2024
- Versione iniziale
- Sistema base di gestione ricerche
- Database PostgreSQL + PostGIS
- Upload shapefile
- Mappe interattive

---

## 📄 License

Copyright © 2025 SHAReLAND. All rights reserved.

---

## 👥 Credits

- **Development Team**: Hyperstage
- **AI Assistant**: GitHub Copilot
- **GIS Libraries**: PostGIS, Leaflet, Folium
- **Framework**: Django

---

**Per informazioni dettagliate su stabilità e SEO, consultare [STABILITY_AND_SEO_GUIDE.md](STABILITY_AND_SEO_GUIDE.md)**
