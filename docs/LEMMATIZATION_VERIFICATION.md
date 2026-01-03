# Lemmatization Verification Guide

This guide shows you how to verify that lemmatization is working correctly in your application.

## Quick Verification Methods

### Method 1: Run the Verification Script

The easiest way to verify everything is working:

```bash
# If running locally
cd anki_web_app
python3 verify_lemmatization.py

# If running in Docker
docker-compose exec backend python verify_lemmatization.py
```

This script will:
- ✅ Test basic tokenization with lemma field
- ✅ Check if spaCy models are available
- ✅ Test database integration
- ✅ Show API response format
- ✅ Test German verb forms

### Method 2: Test via Django Shell

```bash
# Start Django shell
docker-compose exec backend python manage.py shell

# Or locally
cd anki_web_app && python3 manage.py shell
```

Then run:

```python
from flashcards.tokenization import tokenize_text, lemmatize_token

# Test tokenization
text = "Ich sehe, du sahst, er gesehen"
tokens = tokenize_text(text, language='de')

# Check if lemma field exists
for token in tokens:
    print(f"{token['text']} -> lemma: {token.get('lemma')}")
```

Expected output:
```
Ich -> lemma: ich
sehe -> lemma: sehen  # or None if spaCy not installed
du -> lemma: du
sahst -> lemma: sehen  # or None if spaCy not installed
er -> lemma: er
gesehen -> lemma: sehen  # or None if spaCy not installed
```

### Method 3: Test via API

Create a lesson via the API and check the tokens:

```bash
# Create a lesson
curl -X POST http://localhost:8000/api/flashcards/reader/lessons/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Lesson",
    "text": "Ich sehe, du sahst, er gesehen",
    "language": "de",
    "source_type": "text"
  }'

# Get the lesson with tokens
curl http://localhost:8000/api/flashcards/reader/lessons/1/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Check the response - each token should have a `lemma` field:

```json
{
  "lesson_id": 1,
  "title": "Test Lesson",
  "text": "Ich sehe, du sahst, er gesehen",
  "tokens": [
    {
      "token_id": 1,
      "text": "Ich",
      "normalized": "ich",
      "lemma": "ich",  // ← This field should exist
      "start_offset": 0,
      "end_offset": 3
    },
    {
      "token_id": 2,
      "text": "sehe",
      "normalized": "sehe",
      "lemma": "sehen",  // ← Verb form lemmatized
      "start_offset": 4,
      "end_offset": 8
    },
    // ... more tokens
  ]
}
```

### Method 4: Check Database Directly

```bash
# Connect to database
docker-compose exec backend python manage.py dbshell

# Or use psql directly
docker-compose exec db psql -U your_user -d your_db
```

Then query:

```sql
SELECT token_id, text, normalized, lemma 
FROM flashcards_token 
WHERE lesson_id = 1 
LIMIT 10;
```

You should see:
- `text`: The surface form (e.g., "sah")
- `normalized`: Normalized form (e.g., "sah")
- `lemma`: Lemmatized form (e.g., "sehen") or NULL if spaCy not available

## What to Look For

### ✅ Working Correctly

1. **All tokens have `lemma` field**
   - Even if value is `None`, the field should exist
   - Check: `'lemma' in token` should be `True`

2. **spaCy installed and working**
   - Lemmas are populated (not None)
   - German verb forms are unified (sah/gesehen → sehen)
   - Check: `lemmatize_token("sah", language='de')` returns `"sehen"`

3. **Database has lemma column**
   - Migration applied successfully
   - Check: `SELECT lemma FROM flashcards_token LIMIT 1;` works

4. **API includes lemma**
   - TokenSerializer includes `lemma` in response
   - Check: API response has `lemma` field for each token

### ⚠️ Partial Functionality (spaCy Not Installed)

If spaCy models are not installed:
- ✅ Tokenization still works
- ✅ All tokens have `lemma` field (but value is `None`)
- ⚠️ Lemmas are not populated
- ✅ System functions normally, just without lemmatization

To install spaCy models:
```bash
docker-compose exec backend python -m spacy download de_core_news_sm  # German
docker-compose exec backend python -m spacy download es_core_news_sm  # Spanish
```

### ❌ Not Working

If you see errors:

1. **Migration not applied**
   ```bash
   docker-compose exec backend python manage.py migrate
   ```

2. **Import errors**
   - Check if `spacy` is in requirements.txt
   - Check if dependencies are installed: `pip list | grep spacy`

3. **Field doesn't exist**
   - Check migration was created: `ls flashcards/migrations/ | grep lemma`
   - Apply migration: `python manage.py migrate flashcards`

## Testing Specific Scenarios

### Test German Verb Forms

```python
from flashcards.tokenization import lemmatize_token

verbs = ["sehen", "sehe", "sah", "gesehen", "sieht"]
for verb in verbs:
    lemma = lemmatize_token(verb, language='de')
    print(f"{verb} -> {lemma}")
```

Expected (with spaCy):
```
sehen -> sehen
sehe -> sehen
sah -> sehen
gesehen -> sehen
sieht -> sehen
```

### Test Spanish Verb Forms

```python
verbs = ["ver", "veo", "vi", "visto"]
for verb in verbs:
    lemma = lemmatize_token(verb, language='es')
    print(f"{verb} -> {lemma}")
```

Expected (with spaCy):
```
ver -> ver
veo -> ver
vi -> ver
visto -> ver
```

## Troubleshooting

### Issue: Lemma is always None

**Possible causes:**
1. spaCy not installed → Install: `pip install spacy`
2. Language model not downloaded → Download: `python -m spacy download de_core_news_sm`
3. Wrong language code → Use 'de' for German, 'es' for Spanish

**Check:**
```python
from flashcards.tokenization import get_spacy_model
model = get_spacy_model('de')
print(model)  # Should not be None if installed
```

### Issue: Migration error

**Check migration exists:**
```bash
ls anki_web_app/flashcards/migrations/ | grep lemma
# Should show: 0009_add_lemma_to_token.py
```

**Apply migration:**
```bash
docker-compose exec backend python manage.py migrate flashcards
```

### Issue: API doesn't return lemma

**Check serializer:**
```python
from flashcards.serializers import TokenSerializer
print(TokenSerializer.Meta.fields)
# Should include 'lemma'
```

## Summary Checklist

- [ ] Run verification script: `python verify_lemmatization.py`
- [ ] Check tokens have `lemma` field (even if None)
- [ ] Verify migration applied: `python manage.py showmigrations flashcards`
- [ ] Test API response includes `lemma`
- [ ] (Optional) Install spaCy models for actual lemmatization
- [ ] Test with German/Spanish verb forms

If all checks pass, lemmatization is working correctly! 🎉
