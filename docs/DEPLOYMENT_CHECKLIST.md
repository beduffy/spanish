# Deployment Checklist

This checklist ensures smooth deployments and prevents common issues.

## Pre-Deployment Validation

Run the validation script before deploying:

```bash
./scripts/validate-deployment.sh
```

This checks:
- ✅ `.env.prod` file exists and has all required variables
- ✅ Environment variables are not placeholders
- ✅ TTS credentials file exists (if using Google TTS)
- ✅ Docker Compose configuration is correct
- ✅ Nginx configuration includes media file serving

## Required Environment Variables

All of these must be set in `.env.prod`:

### Critical (Required)
- `SECRET_KEY` - Django secret key
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_JWT_SECRET` - Supabase JWT secret
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `DEEPL_API_KEY` - DeepL translation API key

### Optional but Recommended
- `GOOGLE_TTS_CREDENTIALS_PATH` - Path to Google TTS credentials JSON
- `ELEVENLABS_API_KEY` - ElevenLabs API key (fallback TTS)

## Common Deployment Issues & Solutions

### Issue 1: Environment Variables Not Loading

**Symptoms**: 403 Forbidden errors, "SUPABASE_URL configured: False" in logs

**Cause**: Docker Compose not loading `.env.prod` correctly

**Solution**:
1. Ensure `env_file: - .env.prod` is in `docker-compose.prod.yml`
2. **Do NOT** use `${VAR}` syntax in `environment` section - let `env_file` handle it
3. Restart containers: `docker compose -f docker-compose.prod.yml restart backend`

### Issue 2: Frontend Supabase Configuration Missing

**Symptoms**: "Supabase URL or Anon Key not configured" in browser console

**Cause**: Frontend build didn't include Supabase variables

**Solution**:
1. Use `deploy-frontend-prod.sh` script to rebuild frontend
2. Or manually: `export $(cat .env.prod | grep -v '^#' | xargs) && docker compose -f docker-compose.prod.yml build frontend`

### Issue 3: TTS Credentials Not Found

**Symptoms**: TTS generation fails with "Check API configuration" error

**Cause**: Credentials file not mounted or empty

**Solution**:
1. Ensure `google-tts-credentials.json` exists in `anki_web_app/` directory
2. Verify mount path in `docker-compose.prod.yml`: `./anki_web_app/google-tts-credentials.json:/app/google-tts-credentials.json:ro`
3. Check file is not empty: `ls -lah anki_web_app/google-tts-credentials.json`

### Issue 4: Media Files Not Accessible

**Symptoms**: Audio files return 404, "NotSupportedError" in browser

**Cause**: Nginx not configured to serve `/media/` directory

**Solution**:
1. Ensure `nginx/production.conf` has `/media/` location block
2. Ensure `docker-compose.prod.yml` mounts media directory to nginx
3. Restart nginx: `docker compose -f docker-compose.prod.yml restart nginx`

### Issue 5: Large Text TTS Fails

**Symptoms**: TTS works for small text but fails for large text (>5000 chars)

**Cause**: Google TTS has a 5000 character limit per request

**Solution**: Fixed in code - text is automatically chunked. If still failing:
1. Check backend logs for specific error
2. Consider using ElevenLabs as fallback (no character limit)

## Deployment Steps

1. **Validate Configuration**
   ```bash
   ./scripts/validate-deployment.sh
   ```

2. **Pull Latest Code**
   ```bash
   git pull origin main
   ```

3. **Update Environment Variables** (if needed)
   ```bash
   # Edit .env.prod
   nano .env.prod
   ```

4. **Rebuild Frontend** (if Supabase vars changed)
   ```bash
   ./deploy-frontend-prod.sh
   ```

5. **Restart Services**
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

6. **Check Logs**
   ```bash
   docker compose -f docker-compose.prod.yml logs backend --tail=50
   docker compose -f docker-compose.prod.yml logs frontend --tail=50
   docker compose -f docker-compose.prod.yml logs nginx --tail=50
   ```

7. **Verify**
   - Test login
   - Test TTS generation
   - Test audio playback
   - Check API endpoints return 200 (not 403)

## Post-Deployment Verification

- [ ] Can log in successfully
- [ ] Can view lessons/cards
- [ ] Can import new lessons
- [ ] TTS generation works
- [ ] Audio playback works
- [ ] No 403 errors in browser console
- [ ] No "SUPABASE_URL configured: False" in backend logs

## Quick Troubleshooting Commands

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
