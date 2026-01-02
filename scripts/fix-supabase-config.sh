#!/bin/bash

# Script to rebuild frontend with Supabase credentials from .env.prod
# Run this on the server after configuring .env.prod

set -e

cd /opt/spanish-anki

# Check if .env.prod exists and has Supabase config
if [ ! -f .env.prod ]; then
  echo "Error: .env.prod not found!"
  exit 1
fi

# Source the .env.prod file to get variables
set -a
source .env.prod
set +a

# Check if Supabase vars are set
if [ -z "$SUPABASE_URL" ] || [ "$SUPABASE_URL" = "https://your-project.supabase.co" ]; then
  echo "Error: SUPABASE_URL not configured in .env.prod"
  echo "Please edit .env.prod and set your actual Supabase URL"
  exit 1
fi

if [ -z "$SUPABASE_ANON_KEY" ] || [ "$SUPABASE_ANON_KEY" = "your-anon-key-from-supabase-project-settings" ]; then
  echo "Error: SUPABASE_ANON_KEY not configured in .env.prod"
  echo "Please edit .env.prod and set your actual Supabase anon key"
  exit 1
fi

echo "Rebuilding frontend with Supabase credentials..."
echo "SUPABASE_URL: $SUPABASE_URL"
echo "SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY:0:20}..."

# Rebuild frontend with build args
docker compose -f docker-compose.prod.yml build --no-cache \
  --build-arg SUPABASE_URL="$SUPABASE_URL" \
  --build-arg SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
  frontend

# Restart frontend
docker compose -f docker-compose.prod.yml up -d frontend

echo "Frontend rebuilt and restarted!"
echo "The Supabase credentials are now baked into the build."
