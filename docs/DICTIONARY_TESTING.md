# Dictionary Feature - Testing & Verification Guide

## Quick Test

### 1. Start the Application
```bash
cd /home/ben/all_projects/spanish
docker-compose up -d
```

### 2. Test Dictionary API Directly

```bash
# Get auth token (login first via frontend or create test user)
# Then test dictionary lookup:

curl -X GET "http://localhost:8000/api/flashcards/reader/tokens/1/click/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Expected response includes dictionary_entry:
{
  "token": {
    "token_id": 1,
    "text": "Hola",
    "translation": "Hello",
    "dictionary_entry": {
      "meanings": [
        {
          "part_of_speech": "interjection",
          "definitions": ["hello", "hi"],
          "examples": ["¡Hola! ¿Cómo estás?"]
        }
      ]
    }
  },
  "sentence": "...",
  "sentence_translation": "..."
}
```

### 3. Test in Frontend

1. **Open browser**: Navigate to `http://localhost:8080`
2. **Login**: Use your credentials
3. **Go to Reader**: Click "Reader" in navigation
4. **Import a lesson**: Click "Import Lesson", paste Spanish text:
   ```
   Hola mundo. ¿Cómo estás? Me llamo Juan.
   ```
5. **Click on words**: Click "Hola", "mundo", "estás" - each should show dictionary popover

### 4. Verify Dictionary Data

The popover should show:
- ✅ **Part of speech badge** (e.g., "noun", "verb")
- ✅ **Definitions** (bulleted list)
- ✅ **Example sentences** (if available)
- ✅ **Translation** (fallback if dictionary fails)

## Running Tests

### Run All Dictionary Tests
```bash
docker-compose exec backend python manage.py test flashcards.tests_reader.DictionaryServiceTests flashcards.tests_reader.DictionaryIntegrationTests -v 2
```

### Run Specific Test
```bash
# Test dictionary service
docker-compose exec backend python manage.py test flashcards.tests_reader.DictionaryServiceTests.test_get_dictionary_entry_success -v 2

# Test integration
docker-compose exec backend python manage.py test flashcards.tests_reader.DictionaryIntegrationTests.test_token_click_fetches_dictionary_entry -v 2
```

### Run All Tests
```bash
bash run_all_tests.sh
```

## Fixes Applied

### 1. Wiktionary API 403 Error
**Problem**: Wiktionary API was returning `403 Forbidden`

**Fix**: Added User-Agent header to requests:
```python
headers = {
    'User-Agent': 'SpanishAnkiApp/1.0 (Language Learning App; https://github.com/yourusername/spanish-anki)'
}
response = requests.get(url, headers=headers, timeout=10)
```

**File**: `anki_web_app/flashcards/dictionary_service.py`

### 2. Test Failure: test_token_status_user_scoping
**Problem**: Test was trying to access another user's lesson (which is forbidden)

**Fix**: Updated test to:
- Verify user2 gets 404 when accessing user1's lesson
- Create separate lesson for user2 to test status scoping properly

**File**: `anki_web_app/flashcards/tests_reader.py`

### 3. Frontend Performance
**Problem**: `getDictionaryEntry()` was called multiple times in template

**Fix**: Added `currentDictionaryEntry` computed property and watchers

**File**: `anki_web_app/spanish_anki_frontend/src/views/ReaderView.vue`

## Expected Test Results

After fixes, all tests should pass:

```
✅ DictionaryServiceTests.test_get_dictionary_entry_success
✅ DictionaryServiceTests.test_get_dictionary_entry_not_found
✅ DictionaryServiceTests.test_get_dictionary_entry_api_error
✅ DictionaryServiceTests.test_get_dictionary_entry_cache_hit
✅ DictionaryIntegrationTests.test_token_click_fetches_dictionary_entry
✅ DictionaryIntegrationTests.test_token_click_uses_cached_dictionary_entry
✅ DictionaryIntegrationTests.test_token_click_handles_dictionary_failure
✅ TokenStatusAPITests.test_token_status_user_scoping
```

## Troubleshooting

### Dictionary Not Showing

1. **Check backend logs**:
   ```bash
   docker-compose logs backend | grep -i dictionary
   ```

2. **Check for 403 errors**: Should be fixed with User-Agent header

3. **Check cache**: Dictionary entries cached for 30 days
   ```python
   from django.core.cache import cache
   cache.clear()  # Clear cache if needed
   ```

### Test Failures

1. **Run tests individually** to identify specific failure
2. **Check test database**: Tests use separate test database
3. **Check mock setup**: Dictionary tests use mocked API calls

## API Endpoints

### Token Click (triggers dictionary lookup)
```
GET /api/flashcards/reader/tokens/<token_id>/click/
```

**Response**:
```json
{
  "token": {
    "token_id": 1,
    "text": "Hola",
    "translation": "Hello",
    "dictionary_entry": {
      "meanings": [...]
    }
  },
  "sentence": "...",
  "sentence_translation": "..."
}
```

## Dictionary Entry Structure

```json
{
  "meanings": [
    {
      "part_of_speech": "noun",
      "definitions": ["definition1", "definition2"],
      "examples": ["example1", "example2"]
    }
  ],
  "pronunciation": "https://...",
  "source": "wiktionary"
}
```
