# Dictionary Feature Troubleshooting

## Issue: Dictionary Entry Shows as `{}` (Empty Object)

### Root Cause
When a word is not found in Wiktionary, the `dictionary_entry` field defaults to `{}` (empty dict), which was being returned in the API response.

### Fix Applied
1. **Serializer Fix**: `TokenSerializer.get_dictionary_entry()` now returns `None` instead of `{}` for empty dictionary entries
2. **Frontend Fix**: Frontend checks for empty objects and null values
3. **Lemma Fallback**: If word lookup fails, try the lemma (base form) instead

### Verification

**Before Fix:**
```json
{
  "token": {
    "dictionary_entry": {}  // Empty object
  }
}
```

**After Fix:**
```json
{
  "token": {
    "dictionary_entry": null  // Null when no entry found
  }
}
```

### Testing

1. **Clear browser cache** and reload page
2. **Click on a word** that exists in Wiktionary (e.g., "vorgeschlagen")
   - Should show dictionary entry with meanings
3. **Click on a word** that doesn't exist (e.g., "selbstschließende")
   - Should show `null` or `undefined` in console
   - Should fall back to simple translation

### Debug Steps

1. **Check browser console**:
   ```javascript
   // Should see:
   Dictionary entry received: {meanings: [...]}  // If found
   // OR
   Dictionary entry received: null  // If not found (after fix)
   ```

2. **Check backend logs**:
   ```bash
   docker-compose logs backend | grep -i "dictionary\|lookup"
   ```

3. **Test API directly**:
   ```bash
   curl -H "Authorization: Bearer TOKEN" \
     http://localhost:8000/api/flashcards/reader/tokens/TOKEN_ID/click/
   ```

### Common Issues

1. **Word not in Wiktionary**: Some words (especially compound words, proper nouns, slang) may not be in Wiktionary
   - **Solution**: Falls back to simple translation
   - **Future**: Could try alternative dictionary sources

2. **Inflected forms**: German words like "selbstschließende" (inflected) may not be in Wiktionary
   - **Solution**: Now tries lemma (base form) if available
   - **Example**: "selbstschließende" → tries "selbstschließend"

3. **Cached empty dict**: Old tokens may have `{}` saved in database
   - **Solution**: Serializer now returns `None` even if database has `{}`
   - **Cleanup**: Can run migration to clear empty dicts if needed

### Expected Behavior

✅ **Word found in Wiktionary**: Shows dictionary entry with meanings, part of speech, examples  
✅ **Word not found**: Shows `null` in API, falls back to translation in UI  
✅ **Lemma fallback**: Tries lemma if word form not found  
✅ **Empty dict in DB**: Serializer returns `None` instead of `{}`
