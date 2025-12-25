#!/bin/bash
# Script to rebuild frontend on production server with Supabase credentials
set -e

cd /opt/spanish-anki

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
  echo "Error: .env.prod not found!"
  exit 1
fi

# Source .env.prod to get variables
set -a
source .env.prod
set +a

# Check if Supabase vars are set
if [ -z "$SUPABASE_URL" ] || [ "$SUPABASE_URL" = "https://your-project.supabase.co" ]; then
  echo "Error: SUPABASE_URL not configured in .env.prod"
  exit 1
fi

if [ -z "$SUPABASE_ANON_KEY" ]; then
  echo "Error: SUPABASE_ANON_KEY not configured in .env.prod"
  exit 1
fi

echo "Rebuilding frontend with Supabase credentials..."
echo "SUPABASE_URL: $SUPABASE_URL"

# Export variables for docker-compose
export SUPABASE_URL
export SUPABASE_ANON_KEY

# Rebuild frontend with build args from environment
docker compose -f docker-compose.prod.yml build --no-cache frontend

# Restart frontend
docker compose -f docker-compose.prod.yml up -d frontend

echo "Frontend rebuilt and restarted!"
