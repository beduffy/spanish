# Supabase CORS Configuration

## Important: Supabase CORS Settings Removed

**Supabase removed CORS settings from the dashboard in 2024/2025.** CORS is now handled automatically by Supabase's REST API and Auth services.

## What This Means

- **Supabase Auth** (login/signup) works cross-origin by default
- **Supabase REST API** includes CORS headers automatically
- **No configuration needed** in the Supabase dashboard

## If You're Getting CORS Errors

The CORS errors you're seeing are likely because:

1. **Frontend is using mock URL** - The frontend build doesn't have your real Supabase credentials
2. **Solution**: Rebuild the frontend with your actual Supabase credentials (see below)

## How to Fix

### Step 1: Configure Supabase Credentials

On the server:
```bash
ssh root@5.75.174.115
cd /opt/spanish-anki
nano .env.prod
```

Set your actual Supabase values:
```
SUPABASE_URL=https://your-actual-project-id.supabase.co
SUPABASE_JWT_SECRET=your-actual-jwt-secret
SUPABASE_ANON_KEY=your-actual-anon-key
```

### Step 2: Rebuild Frontend

The frontend needs Supabase credentials at BUILD time (they're baked into the JavaScript):

```bash
source .env.prod
docker compose -f docker-compose.prod.yml build --no-cache \
  --build-arg SUPABASE_URL="$SUPABASE_URL" \
  --build-arg SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
  frontend

docker compose -f docker-compose.prod.yml up -d frontend
```

Or use the helper script:
```bash
./configure-supabase.sh
```

### Step 3: Verify

After rebuilding, check the browser console. You should see:
- No "mock.supabase.co" errors
- No CORS errors
- Successful connection to your Supabase project

## Where to Find Your Supabase Credentials

1. Go to https://app.supabase.com
2. Select your project
3. Go to **Settings** (gear icon) → **API**
4. You'll find:
   - **Project URL** → This is your `SUPABASE_URL`
   - **anon public** key → This is your `SUPABASE_ANON_KEY`
   - **JWT Secret** (scroll down) → This is your `SUPABASE_JWT_SECRET`

## Testing

After configuring and rebuilding:

1. Visit `http://5.75.174.115:8080/login`
2. Try to sign up or log in
3. Check browser console (F12) - should see no CORS errors
4. Should connect to your actual Supabase project (not mock.supabase.co)
