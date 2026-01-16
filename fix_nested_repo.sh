#!/bin/bash

################################################################################
# Fix Nested Repository Issue
# This script removes the nested .git directory from shareland and commits
# all files to the main repository
################################################################################

set -e

REPO_ROOT="/home/ergin/PycharmProjects/SHAReLAND_v.1.0"
SHARELAND_DIR="${REPO_ROOT}/shareland"

echo "=========================================="
echo "Fixing Nested Repository Issue"
echo "=========================================="
echo ""

if [ ! -d "${SHARELAND_DIR}" ]; then
    echo "Error: shareland directory not found at ${SHARELAND_DIR}"
    exit 1
fi

if [ ! -d "${SHARELAND_DIR}/.git" ]; then
    echo "✓ shareland is not a nested repository. No action needed."
    exit 0
fi

echo "Found nested .git directory in shareland/"
echo ""
echo "This will:"
echo "1. Remove the nested .git directory"
echo "2. Add all shareland files to the main repository"
echo "3. Commit the changes"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

cd "${REPO_ROOT}"

# Remove nested .git directory
echo "Removing nested .git directory..."
rm -rf "${SHARELAND_DIR}/.git"
echo "✓ Removed"

# Add all shareland files to main repository
echo "Adding shareland files to main repository..."
git add shareland/
echo "✓ Added"

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "No changes to commit. Files may already be tracked."
else
    echo "Committing changes..."
    git commit -m "Fix: Remove nested repository from shareland directory

- Removed nested .git directory from shareland/
- Committed all shareland files to main repository
- This fixes deployment issues where shareland directory was empty"
    echo "✓ Committed"
fi

echo ""
echo "=========================================="
echo "✓ Repository structure fixed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Push to GitHub: git push origin master"
echo "2. Deploy to VPS: ./quick_deploy.sh"
echo ""

