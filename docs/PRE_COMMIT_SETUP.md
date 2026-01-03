# Pre-commit Hooks Setup

## Quick Setup

Run the setup script once:

```bash
./setup_precommit.sh
```

This will:
- Install `husky` and `lint-staged` as dev dependencies
- Create a pre-commit hook that runs:
  1. ESLint with auto-fix on staged files
  2. Quick unit tests (stops on first failure)

## What Happens on Commit

When you run `git commit`, the pre-commit hook automatically:

1. **Runs ESLint** on staged `.js` and `.vue` files
   - Auto-fixes issues where possible
   - Stages the fixes automatically
   - Blocks commit if unfixable errors exist

2. **Runs Quick Tests**
   - Runs unit tests with `--bail` (stops on first failure)
   - Blocks commit if tests fail
   - Fast execution for quick feedback

## Manual Commands

### Run linting manually:
```bash
cd anki_web_app/spanish_anki_frontend
npm run lint          # Check for errors
npm run lint:fix      # Auto-fix errors
```

### Run quick tests manually:
```bash
cd anki_web_app/spanish_anki_frontend
npm run test:quick    # Quick tests (stops on first failure)
npm run test:unit     # All unit tests
```

## Bypassing Hooks (Not Recommended)

Only use this if absolutely necessary:

```bash
git commit --no-verify
```

## Troubleshooting

### Hook not running
1. Check hook exists: `ls -la .git/hooks/pre-commit`
2. Check hook is executable: `chmod +x .git/hooks/pre-commit`
3. Re-run setup: `./setup_precommit.sh`

### Tests failing in hook
- Run tests manually to see full output: `npm run test:unit`
- Fix failing tests before committing
- Check test output for specific errors

### ESLint errors
- Run `npm run lint:fix` to auto-fix issues
- Check `.eslintrc.js` for rule configuration
- See `docs/ESLINT_SETUP.md` for more details

## Configuration Files

- `.husky/pre-commit` - Pre-commit hook script
- `package.json` - Contains `lint-staged` config
- `.git/hooks/pre-commit` - Git hook (symlink to husky)

## Disabling Pre-commit Hooks

To temporarily disable:

```bash
# Rename the hook
mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled

# Re-enable later
mv .git/hooks/pre-commit.disabled .git/hooks/pre-commit
```
