# Frontend Deployment Fix - Supabase Environment Variables

## Problem

The frontend production build wasn't receiving Supabase environment variables, causing login failures with errors:
- "Supabase URL or Anon Key not configured"
- "Failed to fetch" errors when trying to authenticate

## Root Cause

Docker Compose doesn't automatically load `env_file` (`.env.prod`) for **build arguments**. Build args are evaluated before `env_file` is processed, so `${SUPABASE_URL}` and `${SUPABASE_ANON_KEY}` were empty strings during the build.

Vue CLI builds are **static** - environment variables must be baked into the build at build time, not runtime.

## Solution

### Option 1: Use the Deployment Script (Recommended)

```bash
cd /opt/spanish-anki
./deploy-frontend-prod.sh
```

This script:
1. Loads `.env.prod` into shell environment
2. Verifies Supabase variables are present
3. Rebuilds frontend with proper build args
4. Restarts the frontend container

### Option 2: Manual Rebuild

```bash
cd /opt/spanish-anki

# Load environment variables from .env.prod
export $(cat .env.prod | grep -v '^#' | xargs)

# Verify variables are loaded
echo "SUPABASE_URL: $SUPABASE_URL"
echo "SUPABASE_ANON_KEY: $SUPABASE_ANON_KEY"

# Rebuild frontend with build args
docker compose -f docker-compose.prod.yml build \
  --no-cache \
  --build-arg SUPABASE_URL="$SUPABASE_URL" \
  --build-arg SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
  frontend

# Restart frontend
docker compose -f docker-compose.prod.yml up -d frontend
```

## Why This Happens

1. **Vue CLI Static Builds**: Vue CLI bakes environment variables into the JavaScript bundle at build time
2. **Docker Build Args**: Build arguments must be explicitly passed during `docker build`
3. **Docker Compose Limitation**: `env_file` is only loaded for runtime environment variables, not build args

## Verification

After rebuilding, verify the frontend has Supabase credentials:

```bash
# Check if Supabase URL is in the built files
docker compose -f docker-compose.prod.yml exec frontend \
  grep -r "supabase.co" /usr/share/nginx/html/ | head -1

# Or check browser console - should NOT see "Supabase URL or Anon Key not configured"
```

## When to Rebuild Frontend

Rebuild the frontend whenever:
- Supabase credentials change
- `.env.prod` is updated with new Supabase values
- After initial deployment
- If login fails with "Supabase URL or Anon Key not configured"

## Future Improvements

Consider:
1. Using a build script that always loads `.env.prod` before building
2. Using Docker secrets for sensitive values
3. Using a CI/CD pipeline that handles environment variable injection
4. Documenting this requirement in deployment docs

## Related Files

- `deploy-frontend-prod.sh` - Deployment script that handles this automatically
- `docker-compose.prod.yml` - Production Docker Compose configuration
- `anki_web_app/spanish_anki_frontend/Dockerfile` - Frontend Dockerfile with build args
