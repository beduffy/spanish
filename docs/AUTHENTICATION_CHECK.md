# Quick Authentication Check Guide

## How to Verify You're Logged In Correctly

### 1. Visual Check in Browser

After logging in at `http://5.75.174.115:8080/login`, you should see:
- **Navigation bar** shows: "Logged in as [your-email]"
- **Logout button** appears in the navigation

### 2. Browser Console Check

1. Open browser console (F12)
2. Go to the Console tab
3. Run this command:

```javascript
// Check Supabase session
(async () => {
  // Access the Supabase client from the app
  const { data: { session } } = await window.supabase?.auth.getSession() || { data: { session: null } };
  
  if (session) {
    console.log('✓ Logged in to Supabase');
    console.log('User:', session.user.email);
    console.log('User ID:', session.user.id);
    
    // Test backend API
    const response = await fetch('/api/flashcards/current-user/', {
      headers: {
        'Authorization': `Bearer ${session.access_token}`
      }
    });
    
    if (response.ok) {
      const userInfo = await response.json();
      console.log('✓ Backend authentication working');
      console.log('Backend user info:', userInfo);
    } else {
      console.error('✗ Backend authentication failed:', response.status);
    }
  } else {
    console.log('✗ Not logged in to Supabase');
  }
})();
```

### 3. Check Backend Logs

```bash
ssh root@5.75.174.115
cd /opt/spanish-anki
docker compose -f docker-compose.prod.yml logs backend | grep -i "middleware\|auth\|user" | tail -20
```

Look for:
- `[Middleware] Authentication successful for user: <user-id>`
- No authentication errors

### 4. Test API Endpoint Directly

If you have a Supabase access token (from browser console):

```bash
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  http://5.75.174.115:8080/api/flashcards/current-user/
```

Should return:
```json
{
  "id": 1,
  "username": "abc123...",
  "email": "your-email@example.com",
  "first_name": "",
  "last_name": "",
  "is_authenticated": true,
  "is_anonymous": false
}
```

### 5. Verify User Data Isolation

1. Login as User A
2. Create some cards
3. Logout
4. Login as User B  
5. Verify you only see User B's cards (not User A's)

## Common Issues

### "Not logged in" in navigation
- **Solution**: Go to `/login` and sign in
- Check browser console for Supabase errors
- Verify Supabase credentials in `.env.prod`

### "401 Unauthorized" when accessing API
- **Solution**: 
  - Check Supabase JWT_SECRET matches your project
  - Verify token is being sent (check Network tab in browser)
  - Check backend logs for authentication errors

### "CORS error"
- **Solution**: Add `http://5.75.174.115:8080` to Supabase CORS settings

### User shows but API calls fail
- **Solution**: 
  - Check API URL is correct (should be `/api/flashcards` in production)
  - Verify backend is receiving Authorization header
  - Check backend logs

## Quick Fixes

### Restart Services After Config Changes

```bash
ssh root@5.75.174.115
cd /opt/spanish-anki
docker compose -f docker-compose.prod.yml restart backend frontend
```

### Check Current Configuration

```bash
ssh root@5.75.174.115
cd /opt/spanish-anki
cat .env.prod | grep SUPABASE
```

Should show:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_JWT_SECRET=your-secret
SUPABASE_ANON_KEY=your-key
```
