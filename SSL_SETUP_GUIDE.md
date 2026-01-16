# Guida Rapida: Certificati SSL con Let's Encrypt

## Installazione Certbot su VPS

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install certbot

# CentOS/RHEL
sudo yum install certbot
```

## Opzione 1: Certbot con Nginx (Raccomandato)

### Passo 1: Fermare temporaneamente i container
```bash
cd /home/$USER/ShareLand
docker compose down
```

### Passo 2: Ottenere certificati
```bash
sudo certbot certonly --standalone \
  -d shareland.it \
  -d www.shareland.it \
  --email admin@shareland.it \
  --agree-tos \
  --no-eff-email
```

### Passo 3: Copiare certificati nella directory progetto
```bash
sudo mkdir -p /home/$USER/ShareLand/ssl
sudo cp /etc/letsencrypt/live/shareland.it/fullchain.pem /home/$USER/ShareLand/ssl/cert.pem
sudo cp /etc/letsencrypt/live/shareland.it/privkey.pem /home/$USER/ShareLand/ssl/key.pem
sudo chown -R $USER:$USER /home/$USER/ShareLand/ssl
sudo chmod 600 /home/$USER/ShareLand/ssl/*.pem
```

### Passo 4: Riavviare i container
```bash
cd /home/$USER/ShareLand
docker compose up -d
```

### Passo 5: Verificare HTTPS
```bash
curl -I https://shareland.it
```

## Opzione 2: Certificati Self-Signed (Solo per Test)

```bash
# Creare directory SSL
mkdir -p /home/$USER/ShareLand/ssl

# Generare certificato self-signed
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /home/$USER/ShareLand/ssl/key.pem \
  -out /home/$USER/ShareLand/ssl/cert.pem \
  -subj "/C=IT/ST=Italy/L=Rome/O=SHAReLAND/CN=shareland.it"

# Impostare permessi
chmod 600 /home/$USER/ShareLand/ssl/*.pem
```

**⚠️ Nota**: I certificati self-signed generano avvisi nel browser. Usare solo per sviluppo/test.

## Auto-Rinnovo Certificati Let's Encrypt

### Setup Cron Job per auto-rinnovo

```bash
# Creare script di rinnovo
sudo nano /usr/local/bin/renew-ssl.sh
```

Contenuto dello script:
```bash
#!/bin/bash

# Stop containers
cd /home/$USER/ShareLand
docker compose down

# Renew certificates
certbot renew --quiet

# Copy renewed certificates
cp /etc/letsencrypt/live/shareland.it/fullchain.pem /home/$USER/ShareLand/ssl/cert.pem
cp /etc/letsencrypt/live/shareland.it/privkey.pem /home/$USER/ShareLand/ssl/key.pem
chown -R $USER:$USER /home/$USER/ShareLand/ssl
chmod 600 /home/$USER/ShareLand/ssl/*.pem

# Restart containers
cd /home/$USER/ShareLand
docker compose up -d

# Log renewal
echo "$(date): SSL certificates renewed" >> /var/log/ssl-renewal.log
```

Rendere eseguibile:
```bash
sudo chmod +x /usr/local/bin/renew-ssl.sh
```

Aggiungere a crontab:
```bash
sudo crontab -e
```

Aggiungere questa riga (rinnovo ogni 2 mesi alle 3 AM):
```
0 3 1 */2 * /usr/local/bin/renew-ssl.sh
```

## Verifica Configurazione SSL

### Test validità certificato
```bash
openssl x509 -in /home/$USER/ShareLand/ssl/cert.pem -text -noout
```

### Test scadenza
```bash
openssl x509 -enddate -noout -in /home/$USER/ShareLand/ssl/cert.pem
```

### Test online
- [SSL Labs Test](https://www.ssllabs.com/ssltest/analyze.html?d=shareland.it)
- [SSL Checker](https://www.sslshopper.com/ssl-checker.html#hostname=shareland.it)

## Troubleshooting

### Errore: "Address already in use"
Il porto 80 o 443 è occupato. Fermare i container prima:
```bash
docker compose down
```

### Errore: "Permission denied"
Eseguire certbot con sudo:
```bash
sudo certbot certonly --standalone ...
```

### Certificato non valido dopo rinnovo
Riavviare nginx:
```bash
docker compose restart nginx
```

### Controllare log Certbot
```bash
sudo cat /var/log/letsencrypt/letsencrypt.log
```

## Configurazione Firewall

Se usi UFW:
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload
```

Se usi iptables:
```bash
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables-save
```

## Note Importanti

1. **Let's Encrypt ha rate limits**: Max 50 certificati per dominio per settimana
2. **Rinnovo automatico**: Certificati scadono dopo 90 giorni
3. **Backup certificati**: Fare backup di `/etc/letsencrypt/`
4. **DNS propagation**: Attendere propagazione DNS prima di richiedere certificato
5. **Wildcard certificates**: Richiedono DNS validation invece di standalone

## Alternative a Let's Encrypt

- **Cloudflare**: SSL/TLS gratuito con proxy
- **AWS Certificate Manager**: Se usi AWS
- **ZeroSSL**: Alternativa a Let's Encrypt
- **Commercial CA**: Per supporto enterprise (Sectigo, DigiCert)

---

Per ulteriori informazioni: https://letsencrypt.org/getting-started/
