#!/bin/bash
# Deployment Validation Script
# Checks that all required environment variables and files are present before deployment

set -e

echo "🔍 Validating deployment configuration..."
echo ""

ERRORS=0
WARNINGS=0

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
    echo "❌ ERROR: .env.prod file not found!"
    echo "   Create it from env.prod.example and fill in your values"
    ERRORS=$((ERRORS + 1))
else
    echo "✓ .env.prod file exists"
fi

# Check required environment variables
REQUIRED_VARS=(
    "SECRET_KEY"
    "SUPABASE_URL"
    "SUPABASE_JWT_SECRET"
    "SUPABASE_ANON_KEY"
    "DEEPL_API_KEY"
)

echo ""
echo "Checking required environment variables in .env.prod:"
for var in "${REQUIRED_VARS[@]}"; do
    if grep -q "^${var}=" .env.prod 2>/dev/null; then
        value=$(grep "^${var}=" .env.prod | cut -d'=' -f2- | tr -d ' ')
        if [ -z "$value" ] || [ "$value" = "your-${var,,}-here" ] || [ "$value" = "your_${var,,}_here" ]; then
            echo "⚠️  WARNING: ${var} is set but appears to be a placeholder"
            WARNINGS=$((WARNINGS + 1))
        else
            echo "✓ ${var} is configured"
        fi
    else
        echo "❌ ERROR: ${var} not found in .env.prod"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check TTS credentials (at least one should be configured)
echo ""
echo "Checking TTS configuration:"
if grep -q "^GOOGLE_TTS_CREDENTIALS_PATH=" .env.prod 2>/dev/null; then
    creds_path=$(grep "^GOOGLE_TTS_CREDENTIALS_PATH=" .env.prod | cut -d'=' -f2- | tr -d ' ')
    if [ -f "$creds_path" ] || [ -f "anki_web_app/google-tts-credentials.json" ]; then
        echo "✓ Google TTS credentials file found"
    else
        echo "⚠️  WARNING: Google TTS credentials path configured but file not found"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

if grep -q "^ELEVENLABS_API_KEY=" .env.prod 2>/dev/null; then
    elevenlabs_key=$(grep "^ELEVENLABS_API_KEY=" .env.prod | cut -d'=' -f2- | tr -d ' ')
    if [ -n "$elevenlabs_key" ] && [ "$elevenlabs_key" != "your_elevenlabs_api_key_here" ]; then
        echo "✓ ElevenLabs API key configured"
    fi
fi

# Check Docker Compose file
echo ""
echo "Checking Docker Compose configuration:"
if [ ! -f docker-compose.prod.yml ]; then
    echo "❌ ERROR: docker-compose.prod.yml not found!"
    ERRORS=$((ERRORS + 1))
else
    echo "✓ docker-compose.prod.yml exists"
    
    # Check that env_file is configured
    if grep -q "env_file:" docker-compose.prod.yml && grep -q ".env.prod" docker-compose.prod.yml; then
        echo "✓ env_file configured correctly"
    else
        echo "⚠️  WARNING: env_file may not be configured correctly in docker-compose.prod.yml"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# Check nginx config
echo ""
echo "Checking Nginx configuration:"
if [ ! -f nginx/production.conf ]; then
    echo "❌ ERROR: nginx/production.conf not found!"
    ERRORS=$((ERRORS + 1))
else
    echo "✓ nginx/production.conf exists"
    
    # Check that /media/ location is configured
    if grep -q "location /media/" nginx/production.conf; then
        echo "✓ Media files location configured in nginx"
    else
        echo "⚠️  WARNING: /media/ location not found in nginx config"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# Summary
echo ""
echo "=========================================="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ All checks passed! Ready to deploy."
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "⚠️  Validation complete with $WARNINGS warning(s)"
    echo "   Deployment can proceed, but please review warnings above"
    exit 0
else
    echo "❌ Validation failed with $ERRORS error(s) and $WARNINGS warning(s)"
    echo "   Please fix errors before deploying"
    exit 1
fi
