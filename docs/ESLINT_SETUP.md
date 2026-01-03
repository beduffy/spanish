# ESLint Setup Guide

This guide explains how ESLint is configured and how to see errors faster.

## Quick Start

### See ESLint Errors in Your IDE

1. **Install ESLint Extension** (if using VS Code/Cursor):
   - Open Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
   - Type "Extensions: Install Extensions"
   - Search for "ESLint" by Microsoft
   - Install it

2. **Reload Window**:
   - Command Palette → "Developer: Reload Window"

3. **ESLint will now show errors:**
   - Red squiggles under errors
   - Yellow squiggles under warnings
   - Status bar shows error count
   - Problems panel lists all issues

### Auto-fix on Save

ESLint is configured to auto-fix issues when you save files. This is enabled in `.vscode/settings.json`.

## Pre-commit Hooks

### Setup (One-time)

```bash
./setup_precommit.sh
```

This will:
- Install `husky` and `lint-staged`
- Create a pre-commit hook that:
  1. Runs ESLint with auto-fix on staged files
  2. Runs quick unit tests
  3. Blocks commit if tests fail

### What Runs on Commit

1. **ESLint Auto-fix**: Fixes auto-fixable issues in staged files
2. **Quick Tests**: Runs unit tests with `--bail` (stops on first failure)

### Bypassing Hooks (Not Recommended)

```bash
git commit --no-verify
```

## NPM Scripts

### Linting

```bash
# Check for linting errors
npm run lint

# Auto-fix linting errors
npm run lint:fix

# Run from project root
cd anki_web_app/spanish_anki_frontend
npm run lint
```

### Testing

```bash
# Quick tests (stops on first failure)
npm run test:quick

# All unit tests
npm run test:unit

# Watch mode (re-runs on file changes)
npm run test:unit:watch
```

## ESLint Configuration

### Configuration Files

- `.eslintrc.js` - Main ESLint config (for IDE)
- `package.json` - ESLint config (for Vue CLI)

### Rules

- **Unused variables**: Variables/parameters starting with `_` are ignored
- **Console/Debugger**: Warnings in production, off in development
- **Vue 3**: Uses Vue 3 essential rules

### Customizing Rules

Edit `.eslintrc.js`:

```javascript
rules: {
  'no-unused-vars': ['error', { 
    argsIgnorePattern: '^_',
    varsIgnorePattern: '^_'
  }],
  // Add your custom rules here
}
```

## IDE Integration

### VS Code / Cursor

The `.vscode/settings.json` file configures:
- ESLint to run on file save
- Auto-fix on save
- Status bar integration
- Problems panel integration

### Other IDEs

- **WebStorm**: ESLint is built-in, enable it in Settings → Languages & Frameworks → JavaScript → Code Quality Tools → ESLint
- **Sublime Text**: Install "SublimeLinter-eslint" package
- **Atom**: Install "linter-eslint" package

## Troubleshooting

### ESLint Not Showing Errors

1. Check ESLint extension is installed and enabled
2. Reload window: `Ctrl+Shift+P` → "Developer: Reload Window"
3. Check ESLint is running: Look at status bar for ESLint status
4. Check output: View → Output → Select "ESLint" from dropdown

### Pre-commit Hook Not Running

1. Ensure husky is installed: `cd anki_web_app/spanish_anki_frontend && npm install`
2. Run setup script: `./setup_precommit.sh`
3. Check hook exists: `ls -la .husky/pre-commit`

### Tests Failing in Pre-commit

- Run tests manually: `npm run test:unit` to see full output
- Fix failing tests before committing
- Use `--no-verify` only if absolutely necessary

## Best Practices

1. **Fix errors as you code**: ESLint shows errors in real-time
2. **Use auto-fix**: Save files to auto-fix issues
3. **Don't bypass hooks**: They catch issues before they reach CI
4. **Run tests locally**: Don't rely only on pre-commit hooks
5. **Use `_` prefix**: For intentionally unused variables/parameters

## Example: Intentionally Unused Parameter

```javascript
// ❌ Bad - ESLint error
handleTouchEnd(event) {
  // event not used
}

// ✅ Good - No ESLint error
handleTouchEnd(_event) {
  // _event is intentionally unused
}

// ✅ Also Good - Remove if not needed
handleTouchEnd() {
  // No parameter needed
}
```
