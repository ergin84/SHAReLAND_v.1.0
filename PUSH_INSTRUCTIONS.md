# Push Code to ShareLand.git

## ✅ All Scripts Updated

All deployment scripts have been updated to use the **public ShareLand.git** repository:

- ✅ `deploy_vps.sh` → `https://github.com/ergin84/ShareLand.git`
- ✅ `update_vps_code_auto.sh` → `https://github.com/ergin84/ShareLand.git`
- ✅ `update_vps_code.sh` → `https://github.com/ergin84/ShareLand.git`

## 📤 Push to GitHub

Your code is committed locally. To push to GitHub, run:

```bash
git push origin master
```

**Authentication Options:**

1. **Personal Access Token** (Recommended for HTTPS):
   - Go to: https://github.com/settings/tokens
   - Create a new token with `repo` permissions
   - Use token as password when prompted

2. **SSH Key** (For future use):
   ```bash
   # Generate key
   ssh-keygen -t ed25519 -C "your_email@example.com"
   
   # Add to GitHub: https://github.com/settings/keys
   
   # Switch to SSH
   git remote set-url origin git@github.com:ergin84/ShareLand.git
   git push origin master
   ```

## 🚀 After Pushing

Once pushed, you can deploy to VPS:

```bash
./update_vps_code_auto.sh
```

This will now pull from the public `ShareLand.git` repository (no authentication needed for cloning).

## 📝 Current Commit

```
Fix Gunicorn timeout (120s), add multiple workers, optimize evidence API, update deployment scripts to use ShareLand.git
```



