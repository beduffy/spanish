#!/bin/bash
# Setup script for pre-commit hooks

set -e

echo "Setting up pre-commit hooks..."
echo "------------------------------------"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "Error: Not in a git repository"
    exit 1
fi

FRONTEND_DIR="anki_web_app/spanish_anki_frontend"

# Navigate to frontend directory
cd "$FRONTEND_DIR"

# Install husky if not already installed
if ! grep -q "husky" package.json; then
    echo "Installing husky and lint-staged..."
    npm install --save-dev husky lint-staged
fi

# Initialize husky from git root (husky needs .git directory)
echo "Initializing husky..."
cd ../..
npx husky install "$FRONTEND_DIR/.husky" || echo "Husky already initialized"

# Create pre-commit hook
echo "Creating pre-commit hook..."
cd "$FRONTEND_DIR"
mkdir -p .husky
cat > .husky/pre-commit << 'EOF'
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"

cd anki_web_app/spanish_anki_frontend

# Run lint-staged (auto-fixes and stages fixes)
npx lint-staged

# Run quick tests (bail on first failure for speed)
npm run test:quick || {
    echo "❌ Quick tests failed. Commit aborted."
    echo "Run 'npm run test:unit' to see full test output."
    exit 1
}

echo "✅ Pre-commit checks passed!"
EOF

chmod +x .husky/pre-commit

cd ../..

echo ""
echo "✅ Pre-commit hooks setup complete!"
echo ""
echo "The pre-commit hook will now:"
echo "  1. Run ESLint with auto-fix on staged files"
echo "  2. Run quick unit tests (bails on first failure)"
echo ""
echo "To test it, make a commit and see it run automatically."
echo ""
echo "To bypass hooks (not recommended): git commit --no-verify"
