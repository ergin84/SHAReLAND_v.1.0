# Private Repository Authentication Guide

## Problem

If your GitHub repository is **private**, the deployment script cannot pull code without authentication. The current script uses HTTPS URLs which require credentials for private repos.

## Solutions

### Option 1: SSH Keys (Recommended ⭐)

**Best for**: Security and ease of use

#### Setup Steps:

1. **Generate SSH key on VPS:**
   ```bash
   ssh root@5.249.148.147
   sudo -u shareland ssh-keygen -t rsa -b 4096 -f /home/shareland/.ssh/id_rsa -N "" -C "shareland-vps"
   cat /home/shareland/.ssh/id_rsa.pub
   ```

2. **Add SSH key to GitHub:**
   - Go to: https://github.com/settings/keys
   - Click "New SSH key"
   - Paste the public key
   - Save

3. **Update repository URL to use SSH:**
   ```bash
   cd /var/www/shareland/repo
   sudo -u shareland git remote set-url origin git@github.com:ergin84/SHAReLAND_v.1.0.git
   sudo -u shareland git pull origin master
   ```

#### Use the automated script:
```bash
./setup_vps_github_auth.sh
# Choose option 1
```

---

### Option 2: GitHub Personal Access Token

**Best for**: Quick setup, but less secure (token visible in git config)

#### Setup Steps:

1. **Create Personal Access Token:**
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Name: "VPS Deployment"
   - Select scope: `repo` (full control of private repositories)
   - Generate and **copy the token** (you won't see it again!)

2. **Configure git to use token:**
   ```bash
   ssh root@5.249.148.147
   cd /var/www/shareland/repo
   sudo -u shareland git remote set-url origin https://YOUR_TOKEN@github.com/ergin84/SHAReLAND_v.1.0.git
   sudo -u shareland git pull origin master
   ```

3. **Store token securely (optional):**
   ```bash
   # Store in .env file (not in git!)
   echo "GITHUB_TOKEN=your_token_here" >> /var/www/shareland/.env
   ```

#### Use the automated script:
```bash
./setup_vps_github_auth.sh
# Choose option 2
```

---

### Option 3: Deploy Key (SSH for Single Repository)

**Best for**: Repository-specific access, most secure for single repo

#### Setup Steps:

1. **Generate deploy key on VPS:**
   ```bash
   ssh root@5.249.148.147
   sudo -u shareland ssh-keygen -t ed25519 -f /home/shareland/.ssh/id_ed25519_deploy -N "" -C "shareland-deploy"
   cat /home/shareland/.ssh/id_ed25519_deploy.pub
   ```

2. **Add Deploy Key to Repository:**
   - Go to: https://github.com/ergin84/SHAReLAND_v.1.0/settings/keys
   - Click "Add deploy key"
   - Title: "VPS Deploy Key"
   - Paste the public key
   - Check "Allow write access" (if you need to push)
   - Save

3. **Configure SSH config:**
   ```bash
   sudo -u shareland cat > /home/shareland/.ssh/config << 'EOF'
   Host github.com
       HostName github.com
       User git
       IdentityFile ~/.ssh/id_ed25519_deploy
       IdentitiesOnly yes
   EOF
   chmod 600 /home/shareland/.ssh/config
   ```

4. **Update remote URL:**
   ```bash
   cd /var/www/shareland/repo
   sudo -u shareland git remote set-url origin git@github.com:ergin84/SHAReLAND_v.1.0.git
   sudo -u shareland git pull origin master
   ```

#### Use the automated script:
```bash
./setup_vps_github_auth.sh
# Choose option 3
```

---

## Quick Setup Script

Run the automated setup:

```bash
chmod +x setup_vps_github_auth.sh
./setup_vps_github_auth.sh
```

This will guide you through the setup process.

---

## Update Deployment Script

After setting up authentication, the deployment script will work automatically. The `update_vps_code_auto.sh` script will be able to pull from the private repository.

---

## Verify Authentication

Test that authentication works:

```bash
ssh root@5.249.148.147
cd /var/www/shareland/repo
sudo -u shareland git pull origin master
```

If it works without asking for credentials, authentication is configured correctly!

---

## Security Notes

### ⚠️ SSH Keys (Option 1 & 3)
- ✅ Most secure
- ✅ No credentials in git config
- ✅ Can be revoked easily
- ✅ Recommended for production

### ⚠️ Personal Access Token (Option 2)
- ⚠️ Token visible in git remote URL
- ⚠️ Anyone with repo access can see it
- ⚠️ Must be kept secret
- ✅ Easy to set up
- ✅ Can be revoked on GitHub

### Best Practice
**Use SSH keys (Option 1 or 3)** for production deployments.

---

## Troubleshooting

### "Permission denied (publickey)"
- SSH key not added to GitHub
- Wrong SSH key being used
- Check: `ssh -T git@github.com` as shareland user

### "Authentication failed"
- Token expired or invalid
- Token doesn't have `repo` scope
- Check token at: https://github.com/settings/tokens

### "Repository not found"
- Repository is private and authentication failed
- Check authentication method is working
- Verify repository URL is correct

---

## Current Status

Your repository is currently using HTTPS:
```
origin  https://github.com/ergin84/SHAReLAND_v.1.0.git
```

After setting up authentication, it should be:
```
origin  git@github.com:ergin84/SHAReLAND_v.1.0.git  (for SSH)
```

or remain HTTPS with token embedded (less secure).





