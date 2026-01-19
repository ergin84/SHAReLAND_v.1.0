#!/bin/bash

################################################################################
# Setup GitHub Authentication for VPS
# Configures SSH keys or token for private repository access
# Usage: bash setup_vps_github_auth.sh
################################################################################

VPS_IP="5.249.148.147"
VPS_USER="root"
VPS_PASSWORD="Sh@r3l@nd2025/26"
APP_USER="shareland"
REPO_URL="https://github.com/ergin84/SHAReLAND_v.1.0.git"

echo "========================================"
echo "GitHub Authentication Setup for VPS"
echo "========================================"
echo ""
echo "Choose authentication method:"
echo "1. SSH Key (Recommended - most secure)"
echo "2. GitHub Personal Access Token"
echo "3. Deploy Key (SSH key for single repo)"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "=== SSH Key Method ==="
        echo ""
        echo "Step 1: Generate SSH key on VPS (if not exists)"
        sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_IP} << 'SSH_EOF'
# Check if SSH key exists for shareland user
if [ ! -f /home/shareland/.ssh/id_rsa ]; then
    echo "Generating SSH key for shareland user..."
    sudo -u shareland mkdir -p /home/shareland/.ssh
    sudo -u shareland ssh-keygen -t rsa -b 4096 -f /home/shareland/.ssh/id_rsa -N "" -C "shareland-vps"
    echo "SSH key generated!"
else
    echo "SSH key already exists"
fi

echo ""
echo "=== Your Public SSH Key ==="
cat /home/shareland/.ssh/id_rsa.pub
SSH_EOF

        echo ""
        echo "Step 2: Add this SSH key to GitHub"
        echo "  1. Go to: https://github.com/settings/keys"
        echo "  2. Click 'New SSH key'"
        echo "  3. Copy the public key shown above"
        echo "  4. Paste it and save"
        echo ""
        echo "Step 3: Update repository URL to use SSH"
        sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_IP} << 'SSH_EOF'
cd /var/www/shareland/repo
sudo -u shareland git remote set-url origin git@github.com:ergin84/SHAReLAND_v.1.0.git
sudo -u shareland git remote -v
echo ""
echo "Testing SSH connection to GitHub..."
sudo -u shareland ssh -T git@github.com 2>&1 | head -3
SSH_EOF
        ;;
        
    2)
        echo ""
        echo "=== GitHub Personal Access Token Method ==="
        echo ""
        echo "Step 1: Create a Personal Access Token on GitHub"
        echo "  1. Go to: https://github.com/settings/tokens"
        echo "  2. Click 'Generate new token (classic)'"
        echo "  3. Select scopes: 'repo' (full control of private repositories)"
        echo "  4. Generate and copy the token"
        echo ""
        read -sp "Step 2: Paste your GitHub token: " GITHUB_TOKEN
        echo ""
        
        if [ -z "$GITHUB_TOKEN" ]; then
            echo "Error: Token is required"
            exit 1
        fi
        
        echo ""
        echo "Step 3: Configuring git to use token..."
        sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_IP} << SSH_EOF
cd /var/www/shareland/repo
# Update remote URL to include token
sudo -u shareland git remote set-url origin https://${GITHUB_TOKEN}@github.com/ergin84/SHAReLAND_v.1.0.git
# Test connection
sudo -u shareland git ls-remote origin HEAD
SSH_EOF
        echo ""
        echo "Token configured! (Note: Token is visible in git config)"
        echo "Consider using SSH keys for better security."
        ;;
        
    3)
        echo ""
        echo "=== Deploy Key Method ==="
        echo ""
        echo "Step 1: Generate deploy key on VPS"
        sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_IP} << 'SSH_EOF'
# Generate deploy key
sudo -u shareland mkdir -p /home/shareland/.ssh
sudo -u shareland ssh-keygen -t ed25519 -f /home/shareland/.ssh/id_ed25519_deploy -N "" -C "shareland-deploy-key"
echo ""
echo "=== Deploy Key Public Key ==="
cat /home/shareland/.ssh/id_ed25519_deploy.pub
SSH_EOF

        echo ""
        echo "Step 2: Add Deploy Key to GitHub Repository"
        echo "  1. Go to: https://github.com/ergin84/SHAReLAND_v.1.0/settings/keys"
        echo "  2. Click 'Add deploy key'"
        echo "  3. Title: 'VPS Deploy Key'"
        echo "  4. Paste the public key shown above"
        echo "  5. Check 'Allow write access' (if needed)"
        echo "  6. Click 'Add key'"
        echo ""
        read -p "Press Enter after adding the deploy key to GitHub..."
        
        echo ""
        echo "Step 3: Configure SSH to use deploy key"
        sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_IP} << 'SSH_EOF'
# Create SSH config for GitHub
sudo -u shareland cat > /home/shareland/.ssh/config << 'SSH_CONFIG'
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_deploy
    IdentitiesOnly yes
SSH_CONFIG
chmod 600 /home/shareland/.ssh/config
chown shareland:shareland /home/shareland/.ssh/config

# Update remote URL
cd /var/www/shareland/repo
sudo -u shareland git remote set-url origin git@github.com:ergin84/SHAReLAND_v.1.0.git

# Test connection
echo "Testing SSH connection..."
sudo -u shareland ssh -T git@github.com 2>&1 | head -3
SSH_EOF
        ;;
        
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Test the connection:"
echo "  ssh root@${VPS_IP}"
echo "  cd /var/www/shareland/repo"
echo "  sudo -u shareland git pull origin master"





