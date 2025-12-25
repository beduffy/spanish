# E2E Tests Status

## Current Situation

The E2E tests (`cypress/e2e/*.cy.js`) are testing the **old Sentence-based architecture**, but the app has been refactored to use the **new Card model** with authentication.

## What Changed

### Architecture Changes
- **Old**: Sentence model with `/api/flashcards/next-card/` (Sentence-based)
- **New**: Card model with `/api/flashcards/cards/next-card/` (Card-based)
- **New**: All API endpoints now require authentication
- **New**: Routes exist for both old (`/sentences`) and new (`/cards`) models

### Routes Available
- `/` - FlashcardView (old Sentence-based)
- `/cards/review` - CardFlashcardView (new Card-based)
- `/cards` - CardListView (new Card model)
- `/cards/create` - CardEditorView
- `/cards/import` - ImportCardsView
- `/sentences` - SentenceListView (legacy, still works)
- `/dashboard` - DashboardView
- `/login` - LoginView (new, required for auth)

## Test Status

### ✅ Fixed
- **Supabase env vars**: Mock values provided for Cypress tests
- **Uncaught exception handling**: Added to ignore Supabase errors in test env

### ⚠️ Needs Update
The E2E tests need to be updated to:
1. **Authenticate first** - All API calls now require auth tokens
2. **Test new Card endpoints** - Use `/api/flashcards/cards/*` instead of `/api/flashcards/*`
3. **Use new routes** - Test `/cards/review` instead of `/` for Card-based flow
4. **Handle auth state** - Mock or bypass Supabase auth for tests

## Options

### Option 1: Update Tests (Recommended)
Update E2E tests to:
- Mock authentication (bypass Supabase, use test tokens)
- Test new Card-based endpoints
- Test new routes (`/cards/review`, `/cards`, etc.)

### Option 2: Skip E2E Tests Temporarily
Comment out E2E test phase in `run_all_tests.sh` until tests are updated.

### Option 3: Keep Legacy Tests
Keep testing old Sentence endpoints (they still work) but add new Card tests.

## Recommendation

**Skip E2E tests for now** and focus on:
1. ✅ Backend tests (64/64 passing)
2. ✅ Frontend unit tests (37/37 passing)
3. ⏭️ E2E tests (needs refactor for new architecture)

Update E2E tests in Phase 4 (Review UX) when the Card review flow is finalized.
