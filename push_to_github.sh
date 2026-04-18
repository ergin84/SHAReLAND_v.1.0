#!/bin/bash

################################################################################
# Push to ShareLand.git (Public Repository)
# This script helps you push your code to GitHub
################################################################################

echo "=========================================="
echo "Push to ShareLand.git"
echo "=========================================="
echo ""

# Verify remote
echo "Checking remote configuration..."
REMOTE_URL=$(git remote get-url origin)
echo "Remote URL: $REMOTE_URL"
echo ""

if [[ "$REMOTE_URL" != *"ShareLand.git"* ]]; then
    echo "⚠️  Warning: Remote doesn't point to ShareLand.git"
    echo "Fixing remote..."
    git remote set-url origin https://github.com/ergin84/ShareLand.git
    echo "✅ Remote updated"
    echo ""
fi

# Check if there are commits to push
AHEAD=$(git rev-list --count origin/master..master 2>/dev/null || echo "0")
if [ "$AHEAD" = "0" ]; then
    echo "✅ No commits to push (already up to date)"
    exit 0
fi

echo "Commits ahead: $AHEAD"
echo ""

# Option 1: Try with stored credentials
echo "Attempting push with stored credentials..."
if git push origin master 2>&1; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    exit 0
fi

echo ""
echo "Authentication required. Choose an option:"
echo ""
echo "1. Push with Personal Access Token (Recommended)"
echo "   - Create token at: https://github.com/settings/tokens"
echo "   - Select 'repo' scope"
echo "   - Use token as password when prompted"
echo ""
echo "2. Use SSH (if you have SSH keys set up)"
echo ""
echo "3. Use GitHub CLI"
echo ""

read -p "Enter option (1/2/3) or 'q' to quit: " choice

case $choice in
    1)
        echo ""
        echo "Clearing old credentials..."
        git credential reject <<EOF
protocol=https
host=github.com
EOF
        echo ""
        echo "Pushing to GitHub..."
        echo "When prompted:"
        echo "  Username: ergin84 (or your GitHub username)"
        echo "  Password: [Your Personal Access Token]"
        echo ""
        git push origin master
        ;;
    2)
        echo ""
        echo "Switching to SSH..."
        git remote set-url origin git@github.com:ergin84/ShareLand.git
        echo "Attempting push with SSH..."
        git push origin master
        ;;
    3)
        echo ""
        if ! command -v gh &> /dev/null; then
            echo "Installing GitHub CLI..."
            sudo apt update && sudo apt install -y gh
        fi
        echo "Authenticating with GitHub..."
        gh auth login
        echo "Pushing..."
        git push origin master
        ;;
    q|Q)
        echo "Cancelled."
        exit 0
        ;;
    *)
        echo "Invalid option. Exiting."
        exit 1
        ;;
esac

echo ""
if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to GitHub!"
    echo ""
    echo "View your repository at:"
    echo "  https://github.com/ergin84/ShareLand"
else
    echo "❌ Push failed. Check the error messages above."
    echo ""
    echo "Common issues:"
    echo "  - Invalid credentials"
    echo "  - No SSH key configured (for SSH method)"
    echo "  - Network connectivity issues"
fi






