# GitHub Actions Analysis & Test Summary

## Test Count Summary

### Backend Tests (Django)
- **`tests.py`**: 64 tests
- **`tests_card_functionality.py`**: 15 tests  
- **`tests_reader.py`**: 46 tests (newly added)
- **Total Backend Tests: 125 tests**

### Frontend Tests
- **Jest Unit Tests**: ~10 tests (in `tests/unit/`)
- **Cypress E2E Tests**: Variable (runs against full app)

### Grand Total
**~135+ automated tests** across backend and frontend

---

## Build Time Analysis

### Estimated Time Breakdown Per Build

| Phase | Estimated Time | Notes |
|-------|---------------|-------|
| **Setup** | 2-3 min | Checkout, Python setup, dependencies |
| **Docker Build** | 3-5 min | Building images, pulling base images |
| **Service Startup** | ~1 min | Waiting for containers to be ready |
| **Backend Tests** | 2-3 min | 125 Django tests with coverage |
| **Database Seeding** | ~30 sec | E2E test data preparation |
| **Frontend Unit Tests** | 1-2 min | Jest tests |
| **Cypress E2E Tests** | 2-4 min | End-to-end browser tests |
| **Codecov Upload** | ~30 sec | Coverage report upload |
| **Cleanup** | ~30 sec | Docker services shutdown |
| **TOTAL** | **~10-17 minutes** | Per build |

**Note**: Actual times vary based on:
- Docker layer caching
- Network speed
- GitHub Actions runner load
- Test complexity

---

## GitHub Actions Usage & Limits

### Free Tier Limits (GitHub Free/Personal)
- **2,000 minutes/month** included
- **500 MB storage** for artifacts
- Resets at start of each month

### Build Capacity Calculation

**Per Build**: ~10-17 minutes (average ~13.5 minutes)

**Monthly Capacity**:
- **Minimum** (17 min builds): 2,000 ÷ 17 = **~117 builds/month**
- **Average** (13.5 min builds): 2,000 ÷ 13.5 = **~148 builds/month**
- **Maximum** (10 min builds): 2,000 ÷ 10 = **~200 builds/month**

### Usage Scenarios

| Scenario | Builds/Month | Minutes Used | Status |
|----------|--------------|--------------|--------|
| **Light usage** (1-2 pushes/day) | ~30-60 | ~400-800 | ✅ Well within limit |
| **Moderate usage** (5-10 pushes/day) | ~150-300 | ~2,000-4,000 | ⚠️ May exceed free tier |
| **Heavy usage** (20+ pushes/day) | ~600+ | ~8,000+ | ❌ Will exceed free tier |

### Cost if Exceeding Free Tier
- **$0.008 per minute** for GitHub-hosted runners (Linux)
- Example: 1,000 extra minutes = **$8/month**

---

## GitHub Actions Control & Access

### Can I See GitHub Action Logs?
✅ **Yes** - Through GitHub web interface:
1. Go to your repository
2. Click **"Actions"** tab
3. Select a workflow run
4. Click on the job to see detailed logs
5. Logs retained for **90 days** by default

### Can I Control GitHub Actions?
✅ **Yes** - Multiple ways:

1. **Workflow Files** (`.github/workflows/*.yml`):
   - Edit to add/remove/modify steps
   - Control when workflows run (push, PR, schedule, etc.)
   - Set environment variables and secrets

2. **Repository Settings**:
   - Enable/disable Actions
   - Set permissions
   - Configure secrets
   - Manage runners

3. **GitHub API**:
   - Programmatic control via REST API
   - Can cancel runs, trigger workflows, etc.
   - Requires authentication token

### Do You Need GitHub API Access?
**Not required** for basic operations. I can:
- ✅ Read and modify workflow files (`.github/workflows/*.yml`)
- ✅ View logs through web interface (if you share screenshots/links)
- ❌ Cannot directly access GitHub API without your token
- ❌ Cannot view real-time logs without API access

**For advanced monitoring**, you could:
- Set up GitHub Actions status badges
- Use GitHub CLI (`gh`) locally
- Create a monitoring script with API access

---

## Optimization Opportunities

### Reduce Build Time

1. **Docker Layer Caching**:
   - Already using `--build` flag
   - Could optimize Dockerfile for better caching

2. **Parallel Test Execution**:
   - Backend tests already run together
   - Could split into parallel jobs (uses more minutes but faster)

3. **Conditional Test Runs**:
   - Only run E2E tests on main branch
   - Skip tests if only docs changed

4. **Skip Codecov on Failures**:
   - Already implemented with `continue-on-error: true`

### Reduce Minutes Usage

1. **Skip Tests on Draft PRs**:
   ```yaml
   if: github.event.pull_request.draft == false
   ```

2. **Only Run on Changed Paths**:
   ```yaml
   paths:
     - 'anki_web_app/**'
     - '.github/workflows/**'
   ```

3. **Cache Dependencies**:
   - Cache `node_modules` between runs
   - Cache Docker layers

---

## Current Status

✅ **All tests included**: Fixed missing `tests_reader.py` in CI  
✅ **Codecov error handling**: Won't fail builds on upload errors  
✅ **Comprehensive coverage**: 125+ backend tests + frontend tests  

---

## Recommendations

1. **Monitor Usage**: Check GitHub billing page monthly
2. **Optimize if Needed**: Implement caching if approaching limits
3. **Consider Pro**: If consistently exceeding 2,000 min/month ($4/month)
4. **Test Locally**: Run `./run_all_tests.sh` before pushing to save minutes

---

## Quick Reference

- **Total Tests**: ~135+ (125 backend + 10+ frontend)
- **Build Time**: ~10-17 minutes average
- **Monthly Capacity**: ~117-200 builds (free tier)
- **Current Usage**: Monitor at `github.com/settings/billing`
