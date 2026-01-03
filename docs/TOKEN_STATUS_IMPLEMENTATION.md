# TokenStatus Feature Implementation

## Overview
Implemented Known/Unknown Highlighting feature for the LingQ-style Reader, allowing users to mark words as known or unknown while reading, with visual highlighting and persistent storage.

## Implementation Summary

### Backend Changes

#### 1. Model (`anki_web_app/flashcards/models.py`)
- **TokenStatus Model**: New model to track known/unknown status per user per token
  - Fields: `user`, `token`, `status` ('known' or 'unknown'), `created_at`, `updated_at`
  - Unique constraint: (user, token) - each user can have one status per token
  - Indexes: (user, status) and (token, status) for efficient queries

#### 2. Migration (`anki_web_app/flashcards/migrations/0011_add_token_status.py`)
- Creates TokenStatus table with all fields and constraints
- Adds indexes for performance
- Dependencies: `0010_add_lesson_progress_tracking`

#### 3. API Endpoints (`anki_web_app/flashcards/views.py`)
- **TokenStatusAPIView**:
  - `POST /api/flashcards/reader/tokens/<token_id>/status/` - Mark token as known/unknown
    - Body: `{"status": "known"}` or `{"status": "unknown"}`
    - Returns: `{"token_id": int, "status": str, "created": bool}`
  - `DELETE /api/flashcards/reader/tokens/<token_id>/status/` - Remove status
    - Returns: `{"token_id": int, "message": str}`

#### 4. Serializer (`anki_web_app/flashcards/serializers.py`)
- **TokenSerializer**: Added `status` field (SerializerMethodField)
  - Automatically includes user's status for token when request context is available
  - Returns `'known'`, `'unknown'`, or `None` if no status exists

#### 5. Admin (`anki_web_app/flashcards/admin.py`)
- Registered TokenStatus in Django admin
- List display: status_id, user, token, status, updated_at
- Filters: status, updated_at
- Search: user username, token text/normalized

### Frontend Changes

#### 1. API Service (`spanish_anki_frontend/src/services/ApiService.js`)
- `updateTokenStatus(tokenId, status)` - POST to update status
- `removeTokenStatus(tokenId)` - DELETE to remove status

#### 2. Reader View (`spanish_anki_frontend/src/views/ReaderView.vue`)
- **Visual Highlighting**:
  - `.token-known` - Green background for known words
  - `.token-unknown` - Red background for unknown words
  - Applied via `getTokenClass()` method
  
- **UI Controls**:
  - Status buttons in token popover:
    - "Mark as Known" / "✓ Known" (shows active state)
    - "Mark as Unknown" / "✗ Unknown" (shows active state)
    - "Clear Status" (shown when status exists)
  
- **Methods**:
  - `markTokenAsKnown()` - Marks token as known
  - `markTokenAsUnknown()` - Marks token as unknown
  - `removeTokenStatus()` - Removes status
  - All methods update local state immediately for responsive UI

#### 3. Styling
- Status buttons with active states and hover effects
- Color-coded highlighting for visual feedback
- Responsive design

## Testing

### Test Coverage (`anki_web_app/flashcards/tests_reader.py`)

#### TokenStatusModelTests (4 tests)
- ✅ Create known status
- ✅ Create unknown status
- ✅ Unique constraint per user/token
- ✅ Multiple users can have different statuses for same token

#### TokenStatusAPITests (13 tests)
- ✅ Mark token as known
- ✅ Mark token as unknown
- ✅ Update existing status
- ✅ Missing status validation
- ✅ Invalid status validation
- ✅ Token not found handling
- ✅ User scoping (cannot mark other users' tokens)
- ✅ Remove status
- ✅ Remove nonexistent status
- ✅ Serializer includes status
- ✅ Serializer returns None when no status
- ✅ User scoping in serializer (users see only their statuses)

### Running Tests
```bash
# Run all TokenStatus tests
python manage.py test flashcards.tests_reader.TokenStatusModelTests
python manage.py test flashcards.tests_reader.TokenStatusAPITests

# Run all reader tests
python manage.py test flashcards.tests_reader
```

## Usage

### For Users
1. Open a lesson in the Reader
2. Click on any word to open the translation popover
3. Use the status buttons to mark words:
   - Click "Mark as Known" for words you know
   - Click "Mark as Unknown" for words you're learning
   - Click "Clear Status" to remove the status
4. Words are highlighted with colors:
   - Green = Known
   - Red = Unknown

### For Developers
```python
# Create a status
TokenStatus.objects.create(
    user=user,
    token=token,
    status='known'
)

# Get status for a token
status = TokenStatus.objects.filter(
    user=user,
    token=token
).first()

# Query tokens by status
known_tokens = Token.objects.filter(
    statuses__user=user,
    statuses__status='known'
)
```

## API Examples

### Mark Token as Known
```bash
POST /api/flashcards/reader/tokens/123/status/
Content-Type: application/json

{
  "status": "known"
}
```

### Mark Token as Unknown
```bash
POST /api/flashcards/reader/tokens/123/status/
Content-Type: application/json

{
  "status": "unknown"
}
```

### Remove Status
```bash
DELETE /api/flashcards/reader/tokens/123/status/
```

## Database Schema

```sql
CREATE TABLE flashcards_tokenstatus (
    status_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    token_id INTEGER NOT NULL,
    status VARCHAR(10) NOT NULL CHECK (status IN ('known', 'unknown')),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    UNIQUE(user_id, token_id)
);

CREATE INDEX flashcards__user_id_status_idx ON flashcards_tokenstatus(user_id, status);
CREATE INDEX flashcards__token_id_status_idx ON flashcards_tokenstatus(token_id, status);
```

## Migration

To apply the migration:
```bash
python manage.py migrate flashcards
```

## Future Enhancements

Potential improvements:
1. Bulk status updates (mark multiple tokens at once)
2. Status statistics (count of known/unknown words per lesson)
3. Export vocabulary lists filtered by status
4. Status-based filtering in lesson view
5. Progress tracking based on known words percentage
