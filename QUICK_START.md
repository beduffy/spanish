# Quick Start: ESLint & Pre-commit Setup

## ✅ Already Done

1. ✅ ESLint configured with auto-fix on save
2. ✅ Pre-commit hook installed
3. ✅ VS Code/Cursor settings configured

## See ESLint Errors Faster

### In VS Code/Cursor:

1. **Install ESLint Extension** (if not already):
   - Press `Ctrl+Shift+X` (or `Cmd+Shift+X` on Mac)
   - Search "ESLint"
   - Install "ESLint" by Microsoft

2. **Reload Window**:
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P`)
   - Type "Reload Window"
   - Press Enter

3. **You'll now see:**
   - 🔴 Red squiggles = Errors
   - 🟡 Yellow squiggles = Warnings
   - Status bar shows error count
   - Problems panel (View → Problems) lists all issues

### Auto-fix on Save

ESLint will automatically fix issues when you save files. This is already configured in `.vscode/settings.json`.

## Pre-commit Hook

The pre-commit hook is already set up! It will automatically:

1. ✅ Run ESLint with auto-fix on staged files
2. ✅ Run quick unit tests
3. ✅ Block commit if tests fail

### Test It

```bash
# Make a change and commit
git add .
git commit -m "test commit"
# You'll see the hook run automatically!
```

### Manual Commands

```bash
# Lint check
cd anki_web_app/spanish_anki_frontend
npm run lint

# Auto-fix linting
npm run lint:fix

# Quick tests
npm run test:quick
```

## Bypass Hook (Not Recommended)

```bash
git commit --no-verify
```

## Files Created

- `.vscode/settings.json` - IDE ESLint configuration
- `.vscode/extensions.json` - Recommended extensions
- `.git/hooks/pre-commit` - Pre-commit hook
- `anki_web_app/spanish_anki_frontend/.eslintrc.js` - ESLint config
- `anki_web_app/spanish_anki_frontend/package.json` - Updated with scripts

## Documentation

- `docs/ESLINT_SETUP.md` - Full ESLint guide
- `docs/PRE_COMMIT_SETUP.md` - Pre-commit hook details
