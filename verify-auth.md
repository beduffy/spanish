# Verifying Authentication Setup

This guide helps you verify that authentication is working correctly and you're logged in as the right user.

## Step 1: Configure Supabase Credentials

On the server, edit `.env.prod`:

```bash
ssh root@5.75.174.115
cd /opt/spanish-anki
nano .env.prod
```

Add your Supabase credentials:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_JWT_SECRET=your-jwt-secret-here
SUPABASE_ANON_KEY=your-anon-key-here
```

Then restart the backend:
```bash
docker compose -f docker-compose.prod.yml restart backend
```

## Step 2: Update Supabase CORS Settings

In your Supabase dashboard:
1. Go to **Settings > API**
2. Scroll to **CORS Configuration**
3. Add `http://5.75.174.115:8080` to allowed origins
4. Save

## Step 3: Verify Frontend Can Connect to Supabase

1. Open browser console (F12)
2. Visit `http://5.75.174.115:8080`
3. Check console for any Supabase connection errors
4. You should see the login page if not authenticated

## Step 4: Create/Login with Your Account

1. Go to `http://5.75.174.115:8080/login`
2. Sign up with your email (or login if you already have an account)
3. After login, you should see "Logged in as [your-email]" in the navigation bar

## Step 5: Verify Backend Authentication

### Option A: Using Browser Console

1. Open browser console (F12)
2. Run this JavaScript:
```javascript
// Get current session
const { data: { session } } = await supabase.auth.getSession();
console.log('Session:', session);
console.log('User:', session?.user);

// Test API call
const token = session?.access_token;
const response = await fetch('/api/flashcards/current-user/', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
const userInfo = await response.json();
console.log('Backend user info:', userInfo);
```

### Option B: Using curl (from server)

```bash
# First, get a token from Supabase (you'll need to login via browser first)
# Then test the endpoint:
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  http://localhost:8000/api/flashcards/current-user/
```

### Option C: Check Backend Logs

```bash
ssh root@5.75.174.115
cd /opt/spanish-anki
docker compose -f docker-compose.prod.yml logs -f backend | grep -i "auth\|middleware\|user"
```

You should see:
- `[Middleware] Authentication successful for user: <supabase-sub>`
- No authentication errors

## Step 6: Verify User Data Isolation

1. Login as user A
2. Create some cards
3. Logout
4. Login as user B
5. Verify you only see user B's cards

## Troubleshooting

### "No access token available" in console
- Check Supabase credentials in `.env.prod`
- Verify Supabase URL is correct
- Check browser console for Supabase connection errors

### "401 Unauthorized" errors
- Verify JWT_SECRET matches Supabase project settings
- Check backend logs for authentication errors
- Ensure token is being sent in Authorization header

### "CORS error" in browser
- Add `http://5.75.174.115:8080` to Supabase CORS settings
- Check nginx is proxying `/api` correctly

### User not showing in navigation
- Check browser console for errors
- Verify `App.vue` is calling `checkUser()` on mount
- Check Supabase session is valid

## Quick Test Script

Save this as `test-auth.html` and open it in your browser (after logging in):

```html
<!DOCTYPE html>
<html>
<head>
    <title>Auth Test</title>
</head>
<body>
    <h1>Authentication Test</h1>
    <div id="results"></div>
    <script>
        async function testAuth() {
            const results = document.getElementById('results');
            results.innerHTML = '<p>Testing...</p>';
            
            try {
                // Get Supabase session (assuming you're logged in)
                const { createClient } = await import('https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm');
                const supabaseUrl = 'YOUR_SUPABASE_URL';
                const supabaseKey = 'YOUR_SUPABASE_ANON_KEY';
                const supabase = createClient(supabaseUrl, supabaseKey);
                
                const { data: { session }, error: sessionError } = await supabase.auth.getSession();
                
                if (sessionError || !session) {
                    results.innerHTML = '<p style="color:red">Not logged in. Please login first.</p>';
                    return;
                }
                
                results.innerHTML += `<p>✓ Supabase session found</p>`;
                results.innerHTML += `<p>User: ${session.user.email}</p>`;
                
                // Test backend API
                const token = session.access_token;
                const response = await fetch('/api/flashcards/current-user/', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (response.ok) {
                    const userInfo = await response.json();
                    results.innerHTML += `<p style="color:green">✓ Backend authentication successful</p>`;
                    results.innerHTML += `<pre>${JSON.stringify(userInfo, null, 2)}</pre>`;
                } else {
                    results.innerHTML += `<p style="color:red">✗ Backend authentication failed: ${response.status}</p>`;
                }
            } catch (error) {
                results.innerHTML += `<p style="color:red">Error: ${error.message}</p>`;
            }
        }
        
        testAuth();
    </script>
</body>
</html>
```
