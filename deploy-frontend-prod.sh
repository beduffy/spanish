#!/bin/bash

# Script to rebuild frontend with proper environment variables
# Usage: ./deploy-frontend-prod.sh

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Rebuilding frontend with Supabase credentials...${NC}"

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
  echo -e "${YELLOW}Error: .env.prod not found!${NC}"
  exit 1
fi

# Load environment variables from .env.prod
export $(cat .env.prod | grep -v '^#' | xargs)

# Verify Supabase vars are loaded
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_ANON_KEY" ]; then
  echo -e "${YELLOW}Error: SUPABASE_URL or SUPABASE_ANON_KEY not found in .env.prod${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Supabase variables loaded${NC}"
echo "  SUPABASE_URL: ${SUPABASE_URL:0:30}..."
echo "  SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY:0:30}..."

# Rebuild frontend with build args
echo -e "${GREEN}Building frontend...${NC}"
docker compose -f docker-compose.prod.yml build \
  --no-cache \
  --build-arg SUPABASE_URL="$SUPABASE_URL" \
  --build-arg SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
  frontend

# Restart frontend container
echo -e "${GREEN}Restarting frontend container...${NC}"
docker compose -f docker-compose.prod.yml up -d frontend

echo -e "${GREEN}✓ Frontend rebuilt and restarted${NC}"
echo ""
echo "Frontend should now have Supabase credentials baked in."
echo "Test login at: http://5.75.174.115:8080"
