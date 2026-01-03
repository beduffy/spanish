# Complete Testing Guide

This document describes the entire test suite and how to run different types of tests.

## Test Suite Overview

The project has **three types of tests**:

1. **Backend Django Tests** (Python) - Unit and integration tests for Django models, views, and API endpoints
2. **Frontend Unit Tests** (Jest) - Component-level tests for Vue.js components
3. **Frontend E2E Tests** (Cypress) - End-to-end browser tests that test the full application flow

---

## Test Structure

### Backend Tests (`anki_web_app/flashcards/`)

All backend tests are in the `flashcards` app:

```
anki_web_app/flashcards/
├── tests.py                          # Legacy Sentence model tests, SRS logic, CSV import
├── tests_card_functionality.py       # Card model CRUD, review, import, statistics
├── tests_reader.py                   # Reader feature: lessons, tokens, phrases, TTS, translation
└── tests_study_sessions.py          # Study session tracking, AFK detection, active time
```

**Total Backend Tests: ~222 tests** covering:
- SRS (Spaced Repetition System) algorithm logic
- Sentence and Card models
- API endpoints (CRUD, reviews, statistics)
- CSV import functionality
- Reader features (lessons, tokenization, translation, TTS)
- Study session tracking
- User isolation and security
- Error handling and edge cases

### Frontend Unit Tests (`anki_web_app/spanish_anki_frontend/tests/unit/`)

```
anki_web_app/spanish_anki_frontend/tests/unit/
├── DashboardView.spec.js            # Dashboard component tests
└── example.spec.js                   # Example test template
```

**Frontend Unit Tests: ~2-5 tests** (can be expanded)

### Frontend E2E Tests (`anki_web_app/spanish_anki_frontend/cypress/e2e/`)

```
anki_web_app/spanish_anki_frontend/cypress/e2e/
├── card_flow.cy.js                  # Card review flow, submission, navigation
├── card_navigation.cy.js            # Navigation, card list, card creation
├── reader_flow.cy.js                # Reader: lesson import, token clicks, translations
└── study_session.cy.js              # Study session tracking during reviews
```

**E2E Tests: ~10+ test scenarios** covering:
- Complete card review workflows
- Navigation between pages
- Dashboard statistics
- Reader functionality
- Study session tracking

---

## Running Tests

### Option 1: Run All Tests (Recommended for CI)

```bash
# From project root
./run_all_tests.sh
```

This script:
1. Builds and starts Docker containers
2. Runs backend Django tests with coverage
3. Seeds database for E2E tests
4. Runs frontend Jest unit tests
5. Runs Cypress E2E tests
6. Generates coverage report (`anki_web_app/coverage.xml`)

**Time:** ~2-5 minutes

---

### Option 2: Run Only Backend Tests

#### Inside Docker (Recommended)

```bash
# Start services first
docker-compose up -d

# Run all backend tests
docker-compose exec -T backend coverage run manage.py test flashcards.tests flashcards.tests_card_functionality flashcards.tests_reader flashcards.tests_study_sessions --noinput

# Generate coverage report
docker-compose exec -T backend coverage xml -o /app/coverage.xml

# View coverage report
docker-compose exec backend coverage report
```

#### Run Specific Backend Test File

```bash
# Run only study session tests
docker-compose exec -T backend python manage.py test flashcards.tests_study_sessions

# Run only reader tests
docker-compose exec -T backend python manage.py test flashcards.tests_reader

# Run only card functionality tests
docker-compose exec -T backend python manage.py test flashcards.tests_card_functionality

# Run only legacy sentence tests
docker-compose exec -T backend python manage.py test flashcards.tests
```

#### Run Specific Test Class

```bash
# Run only StudySessionModelTests
docker-compose exec -T backend python manage.py test flashcards.tests_study_sessions.StudySessionModelTests

# Run only PhraseAPITests
docker-compose exec -T backend python manage.py test flashcards.tests_reader.PhraseAPITests
```

#### Run Specific Test Method

```bash
# Run only one test method
docker-compose exec -T backend python manage.py test flashcards.tests_study_sessions.StudySessionAPITests.test_start_session

# Run tests matching a pattern
docker-compose exec -T backend python manage.py test flashcards.tests_study_sessions.StudySessionAPITests.test_heartbeat
```

#### Without Docker (Local Python)

```bash
cd anki_web_app
python manage.py test flashcards.tests_study_sessions
```

---

### Option 3: Run Only Frontend Unit Tests (Jest)

#### Inside Docker

```bash
# Start services first
docker-compose up -d

# Run Jest unit tests
docker-compose exec -T frontend npm run test:unit
```

#### Without Docker (Local Node.js)

```bash
cd anki_web_app/spanish_anki_frontend
npm install
npm run test:unit
```

#### Run Specific Jest Test File

```bash
# Run only DashboardView tests
docker-compose exec -T frontend npm run test:unit -- DashboardView.spec.js

# Or from frontend directory
cd anki_web_app/spanish_anki_frontend
npm run test:unit -- DashboardView.spec.js
```

---

### Option 4: Run Only E2E Tests (Cypress)

#### Prerequisites

1. **Start Docker services** (backend and frontend must be running):
   ```bash
   docker-compose up -d
   ```

2. **Wait for services to be ready** (check logs):
   ```bash
   docker-compose logs -f backend
   # Wait for "Starting Django development server..."
   ```

3. **Seed E2E test data** (optional, but recommended):
   ```bash
   docker-compose exec -T backend python manage.py seed_e2e_data
   ```

#### Run All E2E Tests (Headless Mode)

```bash
cd anki_web_app/spanish_anki_frontend
npx cypress run
```

#### Run Specific E2E Test File

```bash
cd anki_web_app/spanish_anki_frontend

# Run only card flow tests
npx cypress run --spec "cypress/e2e/card_flow.cy.js"

# Run only reader flow tests
npx cypress run --spec "cypress/e2e/reader_flow.cy.js"

# Run only study session tests
npx cypress run --spec "cypress/e2e/study_session.cy.js"

# Run only navigation tests
npx cypress run --spec "cypress/e2e/card_navigation.cy.js"
```

#### Run Specific E2E Test (by describe/it name)

```bash
cd anki_web_app/spanish_anki_frontend

# Run tests matching a pattern
npx cypress run --spec "cypress/e2e/card_flow.cy.js" --grep "successfully completes a review cycle"
```

#### Open Cypress Test Runner (Interactive Mode)

```bash
cd anki_web_app/spanish_anki_frontend
npx cypress open
```

This opens the Cypress GUI where you can:
- Click on specific test files to run them
- Watch tests run in a real browser
- Debug failing tests
- See screenshots and videos of test runs

#### Run E2E Tests in Specific Browser

```bash
cd anki_web_app/spanish_anki_frontend

# Chrome (default)
npx cypress run --browser chrome

# Firefox
npx cypress run --browser firefox

# Edge
npx cypress run --browser edge

# Electron (headless, default for CI)
npx cypress run --browser electron
```

---

## Quick Reference: Common Test Commands

### Backend Tests

```bash
# All backend tests
docker-compose exec -T backend python manage.py test flashcards

# Specific test file
docker-compose exec -T backend python manage.py test flashcards.tests_study_sessions

# Specific test class
docker-compose exec -T backend python manage.py test flashcards.tests_study_sessions.StudySessionAPITests

# Specific test method
docker-compose exec -T backend python manage.py test flashcards.tests_study_sessions.StudySessionAPITests.test_start_session

# With verbose output
docker-compose exec -T backend python manage.py test flashcards.tests_study_sessions --verbosity=2

# Keep test database (faster for debugging)
docker-compose exec -T backend python manage.py test flashcards.tests_study_sessions --keepdb
```

### Frontend Unit Tests

```bash
# All Jest tests
docker-compose exec -T frontend npm run test:unit

# Watch mode (re-runs on file changes)
docker-compose exec -T frontend npm run test:unit -- --watch

# Coverage report
docker-compose exec -T frontend npm run test:unit -- --coverage
```

### E2E Tests

```bash
# All E2E tests (headless)
cd anki_web_app/spanish_anki_frontend && npx cypress run

# Interactive mode
cd anki_web_app/spanish_anki_frontend && npx cypress open

# Specific test file
cd anki_web_app/spanish_anki_frontend && npx cypress run --spec "cypress/e2e/card_flow.cy.js"

# With video recording (default)
npx cypress run --spec "cypress/e2e/card_flow.cy.js"

# Without video (faster)
npx cypress run --spec "cypress/e2e/card_flow.cy.js" --config video=false
```

---

## Test Coverage

### Backend Coverage

Coverage report is generated at: `anki_web_app/coverage.xml`

View coverage:
```bash
docker-compose exec backend coverage report
```

Coverage is uploaded to Codecov in CI/CD.

### Current Coverage Areas

- ✅ **SRS Logic**: ~95% coverage
- ✅ **Card Model & API**: ~90% coverage
- ✅ **Study Sessions**: ~95% coverage
- ✅ **Reader Features**: ~85% coverage
- ✅ **Phrase API**: ~90% coverage
- ✅ **Translation Service**: ~80% coverage
- ✅ **TTS Service**: ~75% coverage

---

## Test Data Setup

### E2E Test Data Seeding

Before running E2E tests, seed test data:

```bash
docker-compose exec -T backend python manage.py seed_e2e_data
```

This creates:
- Test user (`testuser`)
- Sample cards for review
- Sample lessons for reader

### Manual Test Data

For manual testing, you can import CSV data:

```bash
# Via web UI: Navigate to /cards/import
# Or via management command:
docker-compose exec -T backend python manage.py import_csv data/your_file.csv
```

---

## Debugging Tests

### Backend Tests

```bash
# Run with pdb debugger
docker-compose exec -T backend python manage.py test flashcards.tests_study_sessions.StudySessionAPITests.test_start_session --pdb

# Run with verbose output
docker-compose exec -T backend python manage.py test flashcards.tests_study_sessions --verbosity=2

# Keep test database for inspection
docker-compose exec -T backend python manage.py test flashcards.tests_study_sessions --keepdb
# Then inspect: docker-compose exec backend python manage.py dbshell
```

### E2E Tests

```bash
# Open Cypress GUI for interactive debugging
cd anki_web_app/spanish_anki_frontend
npx cypress open

# Run with browser devtools open
npx cypress run --headed --browser chrome

# View screenshots on failure
ls anki_web_app/spanish_anki_frontend/cypress/screenshots/

# View videos
ls anki_web_app/spanish_anki_frontend/cypress/videos/
```

---

## Test Files Reference

### Backend Test Files

| File | Tests | Coverage |
|------|-------|----------|
| `tests.py` | Legacy Sentence model, SRS logic, CSV import, API endpoints | ~90% |
| `tests_card_functionality.py` | Card CRUD, reviews, import, statistics | ~90% |
| `tests_reader.py` | Lessons, tokens, phrases, translation, TTS, reading progress | ~85% |
| `tests_study_sessions.py` | Study sessions, heartbeats, AFK detection, active time | ~95% |

### Frontend E2E Test Files

| File | Tests |
|------|-------|
| `card_flow.cy.js` | Card review flow, submission, next card |
| `card_navigation.cy.js` | Navigation, card list, card creation, dashboard |
| `reader_flow.cy.js` | Lesson import, token clicks, translations |
| `study_session.cy.js` | Session tracking, statistics, history |

---

## CI/CD Integration

Tests run automatically on:
- Push to `master` branch
- Pull requests targeting `master`

See `.github/workflows/ci.yml` for CI configuration.

---

## Troubleshooting

### Tests Fail with "No migrations to apply" Warning

```bash
# Create missing migrations
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
```

### E2E Tests Fail - Services Not Ready

```bash
# Check if services are running
docker-compose ps

# Check backend logs
docker-compose logs backend

# Wait longer for services to start
# Edit run_all_tests.sh SLEEP_SECONDS if needed
```

### Cypress Can't Connect to Frontend

```bash
# Verify frontend is accessible
curl http://localhost:8080

# Check frontend logs
docker-compose logs frontend

# Verify baseUrl in cypress.config.js matches your setup
```

### Coverage File Not Found

```bash
# Coverage is generated inside container, copy it out:
docker cp spanish_anki_backend:/app/coverage.xml ./anki_web_app/coverage.xml
```

---

## Best Practices

1. **Run backend tests frequently** during development (fastest)
2. **Run E2E tests before committing** (catches integration issues)
3. **Run all tests before pushing** to catch regressions
4. **Use `--keepdb` for faster iteration** during development
5. **Use Cypress GUI** for debugging E2E test failures
6. **Check coverage reports** to identify untested code paths

---

## Adding New Tests

### Backend Test Template

```python
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status

class MyFeatureTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(...)
        self.client.force_authenticate(user=self.user)
    
    def test_my_feature(self):
        response = self.client.get('/api/flashcards/my-endpoint/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
```

### E2E Test Template

```javascript
describe('My Feature', () => {
    beforeEach(() => {
        cy.visitAsAuthenticated('/');
    });

    it('does something', () => {
        cy.get('.my-element').should('be.visible');
        cy.get('button').click();
        cy.url().should('include', '/expected-page');
    });
});
```

---

## Summary

- **All tests**: `./run_all_tests.sh`
- **Backend only**: `docker-compose exec -T backend python manage.py test flashcards`
- **E2E only**: `cd anki_web_app/spanish_anki_frontend && npx cypress run`
- **Specific backend test**: `docker-compose exec -T backend python manage.py test flashcards.tests_study_sessions.StudySessionAPITests.test_start_session`
- **Specific E2E test**: `npx cypress run --spec "cypress/e2e/card_flow.cy.js"`
