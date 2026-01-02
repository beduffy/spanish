#!/bin/bash

# Interactive script to set up Supabase credentials and rebuild frontend
# Run this on the server

set -e

cd /opt/spanish-anki

echo "=========================================="
echo "Supabase Credentials Setup"
echo "=========================================="
echo ""
echo "You need your Supabase credentials from:"
echo "  https://app.supabase.com → Your Project → Settings → API"
echo ""
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
  echo "Creating .env.prod from template..."
  cp env.prod.example .env.prod
fi

# Get Supabase URL
echo ""
echo "Enter your Supabase Project URL:"
echo "  (e.g., https://abcdefghijklmnop.supabase.co)"
read -p "SUPABASE_URL: " SUPABASE_URL

if [ -z "$SUPABASE_URL" ]; then
  echo "Error: SUPABASE_URL cannot be empty"
  exit 1
fi

# Get Supabase Anon Key
echo ""
echo "Enter your Supabase Anon Key (anon public key):"
read -p "SUPABASE_ANON_KEY: " SUPABASE_ANON_KEY

if [ -z "$SUPABASE_ANON_KEY" ]; then
  echo "Error: SUPABASE_ANON_KEY cannot be empty"
  exit 1
fi

# Get Supabase JWT Secret
echo ""
echo "Enter your Supabase JWT Secret:"
echo "  (Scroll down in API settings to find JWT Secret)"
read -p "SUPABASE_JWT_SECRET: " SUPABASE_JWT_SECRET

if [ -z "$SUPABASE_JWT_SECRET" ]; then
  echo "Error: SUPABASE_JWT_SECRET cannot be empty"
  exit 1
fi

# Update .env.prod
echo ""
echo "Updating .env.prod..."

# Use sed to update or add the values
if grep -q "^SUPABASE_URL=" .env.prod; then
  sed -i "s|^SUPABASE_URL=.*|SUPABASE_URL=$SUPABASE_URL|g" .env.prod
else
  echo "SUPABASE_URL=$SUPABASE_URL" >> .env.prod
fi

if grep -q "^SUPABASE_ANON_KEY=" .env.prod; then
  sed -i "s|^SUPABASE_ANON_KEY=.*|SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY|g" .env.prod
else
  echo "SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY" >> .env.prod
fi

if grep -q "^SUPABASE_JWT_SECRET=" .env.prod; then
  sed -i "s|^SUPABASE_JWT_SECRET=.*|SUPABASE_JWT_SECRET=$SUPABASE_JWT_SECRET|g" .env.prod
else
  echo "SUPABASE_JWT_SECRET=$SUPABASE_JWT_SECRET" >> .env.prod
fi

echo "✓ .env.prod updated"

# Rebuild frontend
echo ""
echo "Rebuilding frontend with Supabase credentials..."
echo "This may take a few minutes..."

docker compose -f docker-compose.prod.yml build --no-cache \
  --build-arg SUPABASE_URL="$SUPABASE_URL" \
  --build-arg SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
  frontend

# Restart services
echo ""
echo "Restarting services..."
docker compose -f docker-compose.prod.yml up -d frontend backend

echo ""
echo "=========================================="
echo "✓ Setup Complete!"
echo "=========================================="
echo ""
echo "Your frontend is now configured with Supabase."
echo "Test it at: http://5.75.174.115:8080/login"
echo ""
echo "Note: Supabase CORS is handled automatically - no configuration needed!"
