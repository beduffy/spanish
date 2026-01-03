# Dictionary Feature Usage Guide

## Overview

The dictionary integration provides rich word information when clicking on words in the reader. It shows:
- Multiple meanings/definitions
- Part of speech (noun, verb, adjective, etc.)
- Example sentences
- Pronunciation (when available)

## How It Works

1. **Automatic Lookup**: When you click on a word in the reader, the system automatically fetches dictionary information from Wiktionary
2. **Caching**: Dictionary entries are cached for 30 days to improve performance
3. **Fallback**: If dictionary lookup fails, the simple translation is still shown

## Using the Dictionary Feature

### In the Reader View

1. **Navigate to a lesson**: Go to `/reader` and select a lesson
2. **Click on a word**: Click any word in the lesson text
3. **View dictionary info**: The popover will show:
   - **Part of speech** (e.g., "noun", "verb") as a badge
   - **Definitions** as a bulleted list
   - **Example sentences** (if available)
   - **Translation** (fallback if dictionary unavailable)

### Example Popover Display

```
┌─────────────────────────────┐
│ Hola                        │
├─────────────────────────────┤
│ [noun]                      │
│ • A greeting               │
│ • Hello                     │
│                             │
│ Examples:                   │
│ ↳ ¡Hola! ¿Cómo estás?      │
│ ↳ Hola, buenos días         │
└─────────────────────────────┘
```

## Testing the Dictionary Feature

### Manual Testing

1. **Start the application**:
   ```bash
   docker-compose up
   ```

2. **Create/import a lesson**:
   - Go to `/reader/import`
   - Paste some Spanish text (e.g., "Hola mundo. ¿Cómo estás?")
   - Click "Import Lesson"

3. **Click on words**:
   - Click "Hola" - should show dictionary entry
   - Click "mundo" - should show dictionary entry
   - Click "estás" - should show dictionary entry

4. **Verify dictionary data**:
   - Check that part of speech is shown
   - Check that definitions are listed
   - Check that examples appear (if available)

### API Testing

Test the dictionary lookup via API:

```bash
# Get auth token first (login via frontend or API)
TOKEN="your-auth-token"

# Click on a token (this triggers dictionary lookup)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/flashcards/reader/tokens/1/click/

# Response includes dictionary_entry:
{
  "token": {
    "token_id": 1,
    "text": "Hola",
    "translation": "Hello",
    "dictionary_entry": {
      "meanings": [
        {
          "part_of_speech": "noun",
          "definitions": ["A greeting", "Hello"],
          "examples": ["¡Hola! ¿Cómo estás?"]
        }
      ]
    }
  }
}
```

### Running Tests

```bash
# Run all dictionary-related tests
docker-compose exec backend python manage.py test flashcards.tests_reader.DictionaryServiceTests

# Run integration tests
docker-compose exec backend python manage.py test flashcards.tests_reader.DictionaryIntegrationTests

# Run all reader tests
docker-compose exec backend python manage.py test flashcards.tests_reader
```

## Troubleshooting

### Dictionary Not Showing

1. **Check API response**: Look for errors in backend logs
   ```bash
   docker-compose logs backend | grep -i dictionary
   ```

2. **Check Wiktionary API**: The API might be rate-limited or blocked
   - Error: `403 Forbidden` - User-Agent header issue (should be fixed)
   - Error: `404 Not Found` - Word not in Wiktionary
   - Error: `Timeout` - Network issue

3. **Check cache**: Dictionary entries are cached. Clear cache if needed:
   ```python
   from django.core.cache import cache
   cache.clear()
   ```

### Dictionary Entry Empty

- The word might not exist in Wiktionary
- The word might be in a different language than expected
- The API might have returned an error (check logs)

## API Details

### Dictionary Service

**File**: `anki_web_app/flashcards/dictionary_service.py`

**Main Function**: `get_dictionary_entry(word, source_lang, target_lang)`

**Parameters**:
- `word`: The word to look up
- `source_lang`: Source language code (e.g., 'es', 'de')
- `target_lang`: Target language code (default: 'en')

**Returns**: Dictionary with structure:
```python
{
    "meanings": [
        {
            "part_of_speech": "noun",
            "definitions": ["definition1", "definition2"],
            "examples": ["example1", "example2"]
        }
    ],
    "pronunciation": "https://...",  # Optional
    "source": "wiktionary"
}
```

### Caching

- **Cache Key**: `dictionary:{word}:{source_lang}:{target_lang}`
- **Cache Duration**: 30 days
- **Cache Backend**: Django's default cache (configured in settings)

## Future Enhancements

- [ ] Add pronunciation audio playback
- [ ] Support multiple dictionary sources (DeepL, etc.)
- [ ] Add etymology information
- [ ] Add frequency/usage information
- [ ] Support for phrases (not just single words)
