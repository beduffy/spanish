# Deployment Guide

Complete guide for deploying Spanish Anki to production (Hetzner server).

## Quick Start

### From Local Machine (Recommended)

```bash
./deploy-to-server.sh your-domain.com your-email@example.com
```

This single command:
1. Transfers files to server
2. Validates configuration
3. Sets up Docker (if needed)
4. Configures environment
5. Obtains SSL certificates
6. Starts all services

### From Server

```bash
ssh root@5.75.174.115
cd /opt/spanish-anki
./deploy.sh your-domain.com your-email@example.com
```

## Prerequisites

- Hetzner server with Ubuntu/Debian
- Domain name pointing to server IP (or use IP-only deployment)
- Docker and Docker Compose v2 installed
- Ports 80 and 443 open (or use IP-only on port 8080)

## Pre-Deployment Checklist

Run validation before deploying:

```bash
./scripts/validate-deployment.sh
```

This checks:
- ✅ `.env.prod` file exists with all required variables
- ✅ Environment variables are not placeholders
- ✅ TTS credentials file exists (if using Google TTS)
- ✅ Docker Compose configuration is correct
- ✅ Nginx configuration includes media file serving

## Required Environment Variables

Create `.env.prod` from `env.prod.example`:

```bash
cp env.prod.example .env.prod
nano .env.prod
```

### Critical (Required)
- `SECRET_KEY` - Django secret key (generate with: `python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_JWT_SECRET` - Supabase JWT secret
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `DEEPL_API_KEY` - DeepL translation API key
- `ALLOWED_HOSTS` - Your domain (e.g., `spanish-anki.example.com`)
- `CORS_ALLOWED_ORIGINS` - `https://your-domain.com` or `http://5.75.174.115:8080` for IP-only

### Optional but Recommended
- `GOOGLE_TTS_CREDENTIALS_PATH=/app/google-tts-credentials.json`
- `ELEVENLABS_API_KEY` - ElevenLabs API key (fallback TTS)

See `docs/ENVIRONMENT_VARIABLES.md` for complete reference.

## Deployment Steps

### Step 1: Transfer Files to Server

**Option A: Using deploy-to-server.sh (Recommended)**
```bash
./deploy-to-server.sh your-domain.com your-email@example.com
```

**Option B: Manual Transfer**
```bash
rsync -avz --exclude 'node_modules' --exclude '__pycache__' --exclude '.git' \
  --exclude '.env' --exclude '.env.prod' \
  /home/ben/all_projects/spanish/ root@5.75.174.115:/opt/spanish-anki/
```

### Step 2: Configure Environment

On the server:
```bash
ssh root@5.75.174.115
cd /opt/spanish-anki

# Copy credentials file (if using Google TTS)
# Ensure google-tts-credentials.json is in anki_web_app/ directory

# Edit environment variables
nano .env.prod
```

### Step 3: Deploy

```bash
# Make scripts executable
chmod +x deploy.sh scripts/validate-deployment.sh

# Run deployment
./deploy.sh your-domain.com your-email@example.com
```

The script will:
1. Validate configuration
2. Check Docker/Docker Compose
3. Create `.env.prod` from template (if missing)
4. Update Nginx configuration
5. Obtain SSL certificates (if domain provided)
6. Build and start all containers

### Step 4: Verify Deployment

```bash
# Check service status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Test endpoints
curl http://localhost:8080/health
curl http://localhost:8080/api/flashcards/cards/
```

## IP-Only Deployment (No Domain)

If you don't have a domain, deploy with IP-only access:

```bash
# On server
cd /opt/spanish-anki

# Edit .env.prod
nano .env.prod
# Set: ALLOWED_HOSTS=5.75.174.115,localhost,127.0.0.1
# Set: CORS_ALLOWED_ORIGINS=http://5.75.174.115:8080

# Deploy without SSL
docker compose -f docker-compose.prod.yml up -d --build
```

Access at: `http://5.75.174.115:8080`

## Frontend Rebuild (After Env Var Changes)

If you change Supabase credentials, rebuild frontend:

```bash
# On server
cd /opt/spanish-anki
./deploy-frontend-prod.sh
```

This ensures Supabase variables are baked into the frontend build.

## Common Issues & Solutions

### Issue 1: Environment Variables Not Loading

**Symptoms**: 403 Forbidden errors, "SUPABASE_URL configured: False" in logs

**Solution**:
1. Ensure `env_file: - .env.prod` is in `docker-compose.prod.yml`
2. **Do NOT** use `${VAR}` syntax in `environment` section
3. Restart: `docker compose -f docker-compose.prod.yml restart backend`

### Issue 2: Frontend Supabase Configuration Missing

**Symptoms**: "Supabase URL or Anon Key not configured" in browser console

**Solution**:
```bash
./deploy-frontend-prod.sh
```

### Issue 3: TTS Credentials Not Found

**Symptoms**: TTS generation fails with "Check API configuration" error

**Solution**:
1. Ensure `google-tts-credentials.json` exists in `anki_web_app/` directory
2. Verify mount path in `docker-compose.prod.yml`
3. Check file is not empty: `ls -lah anki_web_app/google-tts-credentials.json`

### Issue 4: Media Files Not Accessible

**Symptoms**: Audio files return 404, "NotSupportedError" in browser

**Solution**:
1. Ensure `nginx/production.conf` has `/media/` location block
2. Ensure `docker-compose.prod.yml` mounts media directory to nginx
3. Restart: `docker compose -f docker-compose.prod.yml restart nginx`

### Issue 5: Large Text TTS Fails

**Symptoms**: TTS works for small text but fails for large text (>5000 chars)

**Solution**: Fixed in code - text is automatically chunked. If still failing:
1. Check backend logs for specific error
2. Consider using ElevenLabs as fallback (no character limit)

### Issue 6: Port Conflicts

**Symptoms**: Port 80/443 already in use

**Solution**:
- Use IP-only deployment on port 8080
- Or stop conflicting service temporarily for cert setup

## Maintenance Commands

```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f
docker compose -f docker-compose.prod.yml logs backend --tail=100
docker compose -f docker-compose.prod.yml logs frontend --tail=100

# Restart services
docker compose -f docker-compose.prod.yml restart backend
docker compose -f docker-compose.prod.yml restart frontend
docker compose -f docker-compose.prod.yml restart nginx

# Update application
git pull
docker compose -f docker-compose.prod.yml up -d --build

# Run migrations
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Collect static files
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput

# Stop everything
docker compose -f docker-compose.prod.yml down

# Backup database
docker compose -f docker-compose.prod.yml exec backend python manage.py dumpdata > backup_$(date +%Y%m%d).json
```

## Post-Deployment Verification

- [ ] Can log in successfully
- [ ] Can view lessons/cards
- [ ] Can import new lessons
- [ ] TTS generation works
- [ ] Audio playback works
- [ ] No 403 errors in browser console
- [ ] No "SUPABASE_URL configured: False" in backend logs

## Quick Troubleshooting

```bash
# Check environment variables in container
docker compose -f docker-compose.prod.yml exec backend env | grep SUPABASE

# Check if credentials file exists
docker compose -f docker-compose.prod.yml exec backend ls -lah /app/google-tts-credentials.json

# Test media file serving
curl -I http://localhost:8080/media/tts/google_*.mp3

# View recent errors
docker compose -f docker-compose.prod.yml logs backend --tail=100 | grep -i error

# Restart all services
docker compose -f docker-compose.prod.yml restart
```

## Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Nginx    │ :8080 (or :80/:443 with SSL)
└──────┬──────┘
       │
       ├──► /api/* ──► Backend (Django/Gunicorn) :8000
       ├──► /media/* ─► Media files (TTS audio)
       └──► /* ──────► Frontend (Vue.js/Nginx) :8080
```

## Related Documentation

- `docs/ENVIRONMENT_VARIABLES.md` - Complete environment variable reference
- `docs/FRONTEND_DEPLOYMENT_FIX.md` - Frontend build process details
- `docs/API_USAGE_TRACKING.md` - API usage limits and monitoring
