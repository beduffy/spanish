#!/bin/bash

# Deployment script for IP-only access (no domain, no SSL)
# Usage: ./deploy-ip-only.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for Docker Compose (plugin or standalone)
if docker compose version >/dev/null 2>&1; then
  DC_COMMAND="docker compose"
elif command -v docker-compose >/dev/null 2>&1 && docker-compose version >/dev/null 2>&1; then
  DC_COMMAND="docker-compose"
else
  echo -e "${RED}Error: Docker Compose is not installed.${NC}" >&2
  echo "Install Docker Compose v2:"
  echo "  sudo apt-get install -y docker-compose-plugin"
  exit 1
fi

echo -e "${GREEN}✓ Docker Compose found: $DC_COMMAND${NC}"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
  echo -e "${RED}Error: Docker is not running.${NC}" >&2
  echo "Start Docker with: sudo systemctl start docker"
  exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}' || echo "localhost")
echo -e "${GREEN}✓ Server IP: $SERVER_IP${NC}"

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
  echo -e "${YELLOW}⚠ .env.prod not found. Creating from template...${NC}"
  if [ ! -f env.prod.example ]; then
    echo -e "${RED}Error: env.prod.example not found!${NC}"
    exit 1
  fi
  
  cp env.prod.example .env.prod
  
  # Generate Django secret key
  SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 2>/dev/null || openssl rand -hex 32)
  
  # Update .env.prod with IP and secret key
  sed -i "s|your-secret-key-here-change-this-in-production|$SECRET_KEY|g" .env.prod
  sed -i "s|your-domain.com|$SERVER_IP|g" .env.prod
  sed -i "s|ALLOWED_HOSTS=.*|ALLOWED_HOSTS=$SERVER_IP,localhost,127.0.0.1|g" .env.prod
  sed -i "s|CORS_ALLOWED_ORIGINS=.*|CORS_ALLOWED_ORIGINS=http://$SERVER_IP:8080,http://localhost:8080|g" .env.prod
  
  echo -e "${YELLOW}⚠ Please edit .env.prod and fill in your Supabase credentials!${NC}"
  echo -e "${YELLOW}⚠ Required: SUPABASE_URL, SUPABASE_JWT_SECRET, SUPABASE_ANON_KEY${NC}"
  read -p "Press Enter to continue after editing, or Ctrl+C to abort..."
else
  echo -e "${GREEN}✓ .env.prod exists${NC}"
  # Update ALLOWED_HOSTS and CORS if needed
  if ! grep -q "$SERVER_IP" .env.prod 2>/dev/null; then
    sed -i "s|ALLOWED_HOSTS=.*|ALLOWED_HOSTS=$SERVER_IP,localhost,127.0.0.1|g" .env.prod || true
    sed -i "s|CORS_ALLOWED_ORIGINS=.*|CORS_ALLOWED_ORIGINS=http://$SERVER_IP:8080,http://localhost:8080|g" .env.prod || true
  fi
fi

# Create necessary directories
echo -e "${GREEN}Creating directories...${NC}"
mkdir -p data

# Stop any existing containers
echo -e "${GREEN}Stopping any existing containers...${NC}"
$DC_COMMAND -f docker-compose.prod.yml down 2>/dev/null || true

# Build and start services
echo -e "${GREEN}Building services...${NC}"
$DC_COMMAND -f docker-compose.prod.yml build

echo -e "${GREEN}Starting all services...${NC}"
$DC_COMMAND -f docker-compose.prod.yml up -d

# Wait a moment for services to start
sleep 5

# Check service status
echo -e "${GREEN}Checking service status...${NC}"
$DC_COMMAND -f docker-compose.prod.yml ps

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Your application is available at:"
echo -e "  ${GREEN}http://$SERVER_IP:8080${NC}"
echo ""
echo "Useful commands:"
echo "  View logs:        $DC_COMMAND -f docker-compose.prod.yml logs -f"
echo "  Restart services: $DC_COMMAND -f docker-compose.prod.yml restart"
echo "  Stop services:    $DC_COMMAND -f docker-compose.prod.yml down"
echo "  Update app:       git pull && $DC_COMMAND -f docker-compose.prod.yml up -d --build"
echo ""
echo -e "${YELLOW}Note: This deployment uses HTTP only (no SSL).${NC}"
echo -e "${YELLOW}      Make sure to configure your Supabase CORS settings to allow:${NC}"
echo -e "${YELLOW}      http://$SERVER_IP:8080${NC}"
