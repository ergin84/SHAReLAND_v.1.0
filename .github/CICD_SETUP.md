# CI/CD Setup — GitHub Actions → Aruba VPS

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
