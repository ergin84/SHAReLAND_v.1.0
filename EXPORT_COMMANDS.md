# Manual Export Commands from VPS

Since sshpass is not installed, here are manual commands. You'll need to enter password "ergin" when prompted.

## Option 1: Install sshpass (Recommended)

```bash
sudo apt-get install sshpass
```

Then run:
```bash
./export_from_vps_manual.sh
```

## Option 2: Manual Commands

### 1. Find the project path on VPS

```bash
ssh root@89.36.211.235
# Once connected, run:
find /var/www /home /opt /root -name "manage.py" -type f 2>/dev/null
# Note the directory path, then exit
exit
```

### 2. Copy project files

Replace `/path/to/shareland` with the actual path:

```bash
mkdir -p shareland_backup
rsync -avz --progress \
    --exclude '*.pyc' \
    --exclude '__pycache__' \
    --exclude '*.sqlite3' \
    --exclude 'venv/' \
    --exclude '.venv/' \
    root@89.36.211.235:/path/to/shareland/ ./shareland_backup/shareland/
# Enter password: ergin
```

### 3. Copy media files

```bash
rsync -avz --progress root@89.36.211.235:/path/to/shareland/media/ ./shareland_backup/media/
# Enter password: ergin
```

### 4. Copy static files

```bash
rsync -avz --progress root@89.36.211.235:/path/to/shareland/static/ ./shareland_backup/static/
# Enter password: ergin
```

### 5. Export database

First, find database name from settings.py:

```bash
ssh root@89.36.211.235 "grep -A 5 'DATABASES' /path/to/shareland/shareland/settings.py"
# Enter password: ergin
```

Then export (replace `shareland` with actual database name):

```bash
ssh root@89.36.211.235 "PGPASSWORD=ergin pg_dump -U postgres -h localhost -Fc shareland" > ./shareland_backup/database.dump
# Enter password: ergin
```

Or SQL format:

```bash
ssh root@89.36.211.235 "PGPASSWORD=ergin pg_dump -U postgres -h localhost shareland" > ./shareland_backup/database.sql
# Enter password: ergin
```

## Option 3: Quick One-Liner (if you know the path)

Replace `/var/www/shareland` with your actual path:

```bash
# Create backup dir
mkdir -p shareland_backup

# Copy everything at once
rsync -avz --progress \
    --exclude '*.pyc' --exclude '__pycache__' --exclude 'venv' \
    root@89.36.211.235:/var/www/shareland/ ./shareland_backup/shareland/

# Export database
ssh root@89.36.211.235 "PGPASSWORD=ergin pg_dump -U postgres -h localhost -Fc shareland" > ./shareland_backup/database.dump
```

## After Export

Once files are copied, run:

```bash
./setup_local_docker.sh shareland_backup
```






















