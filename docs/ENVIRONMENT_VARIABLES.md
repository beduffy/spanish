# Environment Variables Guide

This document lists all required and optional environment variables for the Spanish Anki application.

## Quick Setup

### Local Development

1. Copy `.env.example` to `.env` in the project root
2. Fill in your Supabase credentials (required)
3. Fill in DeepL API key (required for reader feature)
4. Optionally configure TTS services

### Production Deployment

1. Copy `env.prod.example` to `.env.prod` in the project root
2. Fill in all required values
3. Ensure `.env.prod` is NOT committed to git (it's in .gitignore)

## Required Variables

### Supabase Configuration (REQUIRED)

**Purpose**: User authentication and authorization

**Where to get**:
- Go to: https://app.supabase.com/project/YOUR_PROJECT/settings/api
- Copy the values from "Project URL" and "API keys" sections

**Variables**:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_JWT_SECRET=your-jwt-secret-from-supabase-project-settings
SUPABASE_ANON_KEY=your-anon-key-from-supabase-project-settings
```

**Used by**:
- Backend: Django authentication middleware
- Frontend: Vue.js authentication service
- Both: JWT token verification

**Note**: Frontend needs these at BUILD TIME (for production) because Vue CLI bakes env vars into the static build.

### DeepL Translation API (REQUIRED for Reader Feature)

**Purpose**: Translate words and sentences in the reader

**Where to get**:
- Sign up at: https://www.deepl.com/pro-api
- Free tier: 500,000 characters/month

**Variables**:
```bash
DEEPL_API_KEY=your_deepl_api_key_here
```

**Used by**:
- Backend: `flashcards/translation_service.py`
- API endpoint: `/api/flashcards/reader/translate/`

**Free Tier Limits**:
- 500,000 characters/month
- Monitor usage in DeepL dashboard

## Optional Variables

### Google Cloud Text-to-Speech (Recommended)

**Purpose**: Generate audio for lessons

**Where to get**:
1. Go to: https://console.cloud.google.com/apis/credentials
2. Create a service account
3. Download JSON credentials file
4. Place at: `~/.google-cloud/google-tts-credentials.json`
5. Enable Text-to-Speech API: https://console.cloud.google.com/apis/library/texttospeech.googleapis.com

**Variables**:
```bash
GOOGLE_TTS_CREDENTIALS_PATH=/app/google-tts-credentials.json
```

**Used by**:
- Backend: `flashcards/tts_service.py`
- API endpoint: `/api/flashcards/reader/generate-tts/`

**Free Tier Limits**:
- Standard voices: 1,000,000 characters/month
- WaveNet voices: 4,000,000 characters/month

**Docker Setup**:
- Mount credentials file in `docker-compose.yml`:
  ```yaml
  volumes:
    - ~/.google-cloud/google-tts-credentials.json:/app/google-tts-credentials.json:ro
  ```

### ElevenLabs TTS (Alternative/Fallback)

**Purpose**: Alternative TTS service (used as fallback if Google TTS fails)

**Where to get**:
- Sign up at: https://elevenlabs.io
- Get API key from: https://elevenlabs.io/app/settings/api-keys

**Variables**:
```bash
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM  # Default German voice
```

**Used by**:
- Backend: `flashcards/tts_service.py` (fallback)
- Automatically used if Google TTS fails

**Pricing**:
- Starter: $11/month (~200 minutes)
- Creator: $99/month (~1000 minutes)

## Django Settings

### SECRET_KEY (REQUIRED)

**Purpose**: Django secret key for cryptographic signing

**Generate**:
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Variables**:
```bash
SECRET_KEY=your-generated-secret-key-here
```

### DEBUG (Production: REQUIRED)

**Purpose**: Enable/disable Django debug mode

**Variables**:
```bash
DEBUG=False  # Production
DEBUG=True   # Development
```

### ALLOWED_HOSTS (Production: REQUIRED)

**Purpose**: List of allowed hostnames for the Django app

**Variables**:
```bash
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,5.75.174.115
```

### CORS_ALLOWED_ORIGINS (Production: REQUIRED)

**Purpose**: List of allowed origins for CORS requests

**Variables**:
```bash
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

## Environment Variable Files

### Local Development (`.env`)

Located at project root: `/home/ben/all_projects/spanish/.env`

**Template**: `.env.example` (create this if it doesn't exist)

**Required**:
- `SUPABASE_URL`
- `SUPABASE_JWT_SECRET`
- `SUPABASE_ANON_KEY`
- `DEEPL_API_KEY`

**Optional**:
- `GOOGLE_TTS_CREDENTIALS_PATH`
- `ELEVENLABS_API_KEY`
- `ELEVENLABS_VOICE_ID`

### Production (`.env.prod`)

Located at project root: `/home/ben/all_projects/spanish/.env.prod`

**Template**: `env.prod.example`

**Required**:
- All Supabase variables
- `DEEPL_API_KEY`
- `SECRET_KEY`
- `DEBUG=False`
- `ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`

**Optional**:
- `GOOGLE_TTS_CREDENTIALS_PATH`
- `ELEVENLABS_API_KEY`
- `ELEVENLABS_VOICE_ID`

## Docker Compose Configuration

### Development (`docker-compose.yml`)

Environment variables are passed directly:
```yaml
environment:
  - SUPABASE_URL=${SUPABASE_URL}
  - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
  - VUE_APP_SUPABASE_URL=${SUPABASE_URL}
  - VUE_APP_SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
```

**Note**: Reads from `.env` file in project root (if exists) or from shell environment.

### Production (`docker-compose.prod.yml`)

Uses `env_file` directive:
```yaml
env_file:
  - .env.prod
```

**Frontend Build Args**:
```yaml
build:
  args:
    SUPABASE_URL: ${SUPABASE_URL}
    SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY}
```

**Important**: Frontend build args must be available when building the Docker image. Docker Compose automatically loads `.env.prod` before building.

## Troubleshooting

### Frontend: "Supabase URL or Anon Key not configured"

**Cause**: Frontend build didn't receive Supabase variables at build time.

**Fix**:
1. Ensure `.env.prod` exists with `SUPABASE_URL` and `SUPABASE_ANON_KEY`
2. Rebuild frontend: `docker compose -f docker-compose.prod.yml build --no-cache frontend`
3. Restart: `docker compose -f docker-compose.prod.yml up -d`

### Backend: 403 Forbidden after login

**Cause**: Supabase JWT secret mismatch or missing.

**Fix**:
1. Verify `SUPABASE_JWT_SECRET` in `.env.prod` matches Supabase project settings
2. Restart backend: `docker compose -f docker-compose.prod.yml restart backend`

### Translation not working

**Cause**: DeepL API key missing or invalid.

**Fix**:
1. Verify `DEEPL_API_KEY` in `.env` or `.env.prod`
2. Check API key is valid: https://www.deepl.com/pro-api
3. Check usage limits (free tier: 500k chars/month)

### TTS not working

**Cause**: Missing credentials or API not enabled.

**Fix**:
1. **Google TTS**: 
   - Verify credentials file exists: `~/.google-cloud/google-tts-credentials.json`
   - Enable API: https://console.cloud.google.com/apis/library/texttospeech.googleapis.com
   - Check `GOOGLE_TTS_CREDENTIALS_PATH` in `.env.prod`
2. **ElevenLabs**: 
   - Verify `ELEVENLABS_API_KEY` is set
   - Check API key is valid at: https://elevenlabs.io/app/settings/api-keys

## Verification Commands

### Check environment variables are loaded:

```bash
# Local development
docker-compose exec backend env | grep SUPABASE
docker-compose exec frontend env | grep SUPABASE

# Production
docker compose -f docker-compose.prod.yml exec backend env | grep SUPABASE
```

### Verify Supabase connection:

```bash
# Test backend authentication
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/flashcards/cards/

# Check frontend build (production)
docker compose -f docker-compose.prod.yml exec frontend cat /usr/share/nginx/html/index.html | grep -i supabase
```

### Check API keys are working:

```bash
# Test DeepL (backend)
docker-compose exec backend python manage.py shell -c "from flashcards.translation_service import translate_text; print(translate_text('Hallo', 'de', 'en'))"

# Test TTS (backend)
docker-compose exec backend python manage.py shell -c "from flashcards.tts_service import generate_tts_audio; print(generate_tts_audio('Test', 'de-DE'))"
```

## Security Notes

1. **Never commit `.env` or `.env.prod` to git** - they contain secrets
2. **Use different keys for development and production**
3. **Rotate API keys regularly**
4. **Monitor API usage** to avoid unexpected charges
5. **Use environment-specific Supabase projects** if possible

## Related Documentation

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment guide
- [LINGQ_READER_IMPLEMENTATION.md](./LINGQ_READER_IMPLEMENTATION.md) - Reader feature details
- [API_USAGE_TRACKING.md](./API_USAGE_TRACKING.md) - Monitor API usage
