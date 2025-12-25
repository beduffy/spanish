#!/bin/bash

# Script to configure Supabase and rebuild frontend
# Run this on the server

set -e

cd /opt/spanish-anki

echo "=========================================="
echo "Supabase Configuration"
echo "=========================================="
echo ""

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
  echo "Creating .env.prod from template..."
  cp env.prod.example .env.prod
fi

# Check current values
echo "Current Supabase configuration:"
grep "^SUPABASE" .env.prod | sed 's/=.*/=***/' || echo "  Not configured"

echo ""
echo "You need to edit .env.prod and set:"
echo "  - SUPABASE_URL (e.g., https://xxxxx.supabase.co)"
echo "  - SUPABASE_JWT_SECRET (from Supabase project settings)"
echo "  - SUPABASE_ANON_KEY (from Supabase project settings)"
echo ""
read -p "Press Enter to edit .env.prod, or Ctrl+C to cancel..."

# Open editor
nano .env.prod

# Source the file to check values
set -a
source .env.prod
set +a

# Validate
if [ -z "$SUPABASE_URL" ] || [ "$SUPABASE_URL" = "https://your-project.supabase.co" ]; then
  echo "Error: SUPABASE_URL not configured!"
  exit 1
fi

if [ -z "$SUPABASE_ANON_KEY" ] || [ "$SUPABASE_ANON_KEY" = "your-anon-key-from-supabase-project-settings" ]; then
  echo "Error: SUPABASE_ANON_KEY not configured!"
  exit 1
fi

echo ""
echo "Configuration looks good!"
echo "Rebuilding frontend with Supabase credentials..."

# Rebuild frontend
docker compose -f docker-compose.prod.yml build --no-cache \
  --build-arg SUPABASE_URL="$SUPABASE_URL" \
  --build-arg SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
  frontend

# Restart services
docker compose -f docker-compose.prod.yml up -d frontend backend

echo ""
echo "=========================================="
echo "Done! Frontend rebuilt with Supabase config."
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Add http://5.75.174.115:8080 to Supabase CORS settings"
echo "2. Test login at http://5.75.174.115:8080/login"
