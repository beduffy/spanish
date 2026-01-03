# Test Suite Quick Reference

## Test Suite Overview

**Total Tests: ~222 backend + ~10 E2E + ~5 frontend unit**

### Backend Tests (Django)
- `tests.py` - Legacy Sentence model, SRS logic, CSV import
- `tests_card_functionality.py` - Card CRUD, reviews, statistics
- `tests_reader.py` - Reader features (lessons, tokens, phrases, TTS)
- `tests_study_sessions.py` - Study session tracking

### Frontend Tests
- **Unit Tests (Jest)**: Component tests in `tests/unit/`
- **E2E Tests (Cypress)**: Browser tests in `cypress/e2e/`

---

## Quick Commands

### Run All Tests
```bash
./run_all_tests.sh
```

### Run Only Backend Tests
```bash
./run_backend_tests.sh
# Or specific test:
./run_backend_tests.sh flashcards.tests_study_sessions
```

### Run Only E2E Tests
```bash
./run_e2e_tests.sh
# Or specific test file:
./run_e2e_tests.sh cypress/e2e/card_flow.cy.js
```

### Run Specific Backend Test
```bash
# Test file
docker-compose exec -T backend python manage.py test flashcards.tests_study_sessions

# Test class
docker-compose exec -T backend python manage.py test flashcards.tests_study_sessions.StudySessionAPITests

# Single test method
docker-compose exec -T backend python manage.py test flashcards.tests_study_sessions.StudySessionAPITests.test_start_session
```

### Run Specific E2E Test
```bash
cd anki_web_app/spanish_anki_frontend

# All E2E tests
npx cypress run

# Specific file
npx cypress run --spec "cypress/e2e/card_flow.cy.js"

# Interactive mode (GUI)
npx cypress open
```

### Run Frontend Unit Tests
```bash
docker-compose exec -T frontend npm run test:unit
```

---

## Test Files Location

```
anki_web_app/
├── flashcards/
│   ├── tests.py                    # ~50 tests
│   ├── tests_card_functionality.py # ~60 tests
│   ├── tests_reader.py             # ~100 tests
│   └── tests_study_sessions.py     # ~12 tests
│
spanish_anki_frontend/
├── tests/unit/                     # Jest unit tests
│   ├── DashboardView.spec.js
│   └── example.spec.js
└── cypress/e2e/                    # Cypress E2E tests
    ├── card_flow.cy.js
    ├── card_navigation.cy.js
    ├── reader_flow.cy.js
    └── study_session.cy.js
```

---

## Common Patterns

### Backend: Run tests matching pattern
```bash
docker-compose exec -T backend python manage.py test flashcards.tests_study_sessions --keepdb
```

### Backend: Run with verbose output
```bash
docker-compose exec -T backend python manage.py test flashcards.tests_study_sessions --verbosity=2
```

### E2E: Run in specific browser
```bash
cd anki_web_app/spanish_anki_frontend
npx cypress run --browser chrome
```

### E2E: Run without video (faster)
```bash
npx cypress run --config video=false
```

---

See `docs/TESTING_GUIDE.md` for complete documentation.
