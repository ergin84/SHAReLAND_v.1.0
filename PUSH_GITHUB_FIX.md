# Fix GitHub Push Issue

## Problem

The error shows it's trying to push to the old repository URL. This is likely a credential cache issue.

## Solution

### Option 1: Clear Credential Cache and Push

```bash
# Clear any cached credentials
git credential-cache exit 2>/dev/null || true
git credential reject <<EOF
protocol=https
host=github.com
EOF

# Try pushing again (will prompt for credentials)
git push origin master
```

When prompted:
- **Username**: `ergin84` (or your GitHub username)
- **Password**: Use a **Personal Access Token** (not your password)
  - Create at: https://github.com/settings/tokens
  - Select `repo` scope

### Option 2: Use SSH Instead

```bash
# Check if you have SSH key
ls -la ~/.ssh/id_*.pub

# If no key, generate one:
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub: https://github.com/settings/keys

# Switch to SSH
git remote set-url origin git@github.com:ergin84/ShareLand.git

# Push
git push origin master
```

### Option 3: Use GitHub CLI

```bash
# Install GitHub CLI
sudo apt install gh

# Login
gh auth login

# Push
git push origin master
```

### Option 4: Manual Credential Setup

```bash
# Set up credential helper
git config --global credential.helper store

# Push (will prompt once, then save)
git push origin master
# Enter: username
# Enter: personal_access_token
```

## Verify Remote

Make sure remote is correct:

```bash
git remote -v
```

Should show:
```
origin  https://github.com/ergin84/ShareLand.git (fetch)
origin  https://github.com/ergin84/ShareLand.git (push)
```

If it shows `SHAReLAND_v.1.0.git`, fix it:

```bash
git remote set-url origin https://github.com/ergin84/ShareLand.git
```

## Quick Fix (Recommended)

```bash
# 1. Verify remote
git remote -v

# 2. Clear credentials
git credential reject <<EOF
protocol=https
host=github.com
EOF

# 3. Push with explicit URL
git push https://github.com/ergin84/ShareLand.git master
```

This will prompt for credentials interactively.






