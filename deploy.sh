#!/bin/bash

# Deployment script for Spanish Anki application on Hetzner
# Usage: ./deploy.sh [domain] [email]

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

# Get domain and email from arguments or prompt
DOMAIN=${1:-}
EMAIL=${2:-}

if [ -z "$DOMAIN" ]; then
  read -p "Enter your domain name (e.g., spanish-anki.example.com): " DOMAIN
fi

if [ -z "$EMAIL" ]; then
  read -p "Enter your email for Let's Encrypt: " EMAIL
fi

echo -e "${GREEN}✓ Domain: $DOMAIN${NC}"
echo -e "${GREEN}✓ Email: $EMAIL${NC}"

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
  
  # Update .env.prod with domain and secret key
  sed -i "s|your-secret-key-here-change-this-in-production|$SECRET_KEY|g" .env.prod
  sed -i "s|your-domain.com|$DOMAIN|g" .env.prod
  sed -i "s|https://your-project.supabase.co|${SUPABASE_URL:-https://your-project.supabase.co}|g" .env.prod
  
  echo -e "${YELLOW}⚠ Please edit .env.prod and fill in your Supabase credentials and other settings!${NC}"
  echo -e "${YELLOW}⚠ Press Enter to continue after editing, or Ctrl+C to abort...${NC}"
  read
else
  echo -e "${GREEN}✓ .env.prod exists${NC}"
fi

# Update nginx config with domain
echo -e "${GREEN}Updating nginx configuration...${NC}"
sed -i "s|your-domain.com|$DOMAIN|g" nginx/production.conf

# Create necessary directories
echo -e "${GREEN}Creating directories...${NC}"
mkdir -p nginx/ssl
mkdir -p data

# Check for port conflicts
echo -e "${GREEN}Checking for port conflicts...${NC}"
PORT_80_IN_USE=$(lsof -i :80 2>/dev/null | grep -v "COMMAND" | wc -l || echo "0")
PORT_443_IN_USE=$(lsof -i :443 2>/dev/null | grep -v "COMMAND" | wc -l || echo "0")

if [ "$PORT_80_IN_USE" -gt 0 ] || [ "$PORT_443_IN_USE" -gt 0 ]; then
  echo -e "${YELLOW}⚠ Port 80 or 443 is already in use!${NC}"
  echo "Services using these ports:"
  lsof -i :80 -i :443 2>/dev/null || echo "  (Could not determine - may need sudo)"
  echo ""
  echo "Options:"
  echo "  1. Stop the conflicting service temporarily for cert setup"
  echo "  2. Use existing certificates if you have them"
  echo "  3. Configure a reverse proxy to handle both services"
  echo ""
  read -p "Do you want to continue anyway? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

# Check if SSL certificates already exist
if [ -d "nginx/ssl/live/$DOMAIN" ] && [ -f "nginx/ssl/live/$DOMAIN/fullchain.pem" ]; then
  echo -e "${GREEN}✓ SSL certificates already exist${NC}"
  SKIP_CERT=true
else
  echo -e "${YELLOW}⚠ SSL certificates not found.${NC}"
  if [ "$PORT_80_IN_USE" -gt 0 ]; then
    echo -e "${YELLOW}⚠ Port 80 is in use. You may need to stop the service temporarily.${NC}"
    echo "  Or place existing certificates in: nginx/ssl/live/$DOMAIN/"
    read -p "Continue with cert setup? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      SKIP_CERT=true
      echo -e "${YELLOW}⚠ Skipping cert setup. Make sure certificates are in place before starting nginx.${NC}"
    else
      SKIP_CERT=false
    fi
  else
    SKIP_CERT=false
  fi
fi

# Stop any existing containers
echo -e "${GREEN}Stopping any existing containers...${NC}"
$DC_COMMAND -f docker-compose.prod.yml down 2>/dev/null || true

# Build and start services (without nginx first if we need certs)
if [ "$SKIP_CERT" = false ]; then
  echo -e "${GREEN}Building services...${NC}"
  $DC_COMMAND -f docker-compose.prod.yml build
  
  echo -e "${GREEN}Starting backend and frontend (without nginx for cert setup)...${NC}"
  $DC_COMMAND -f docker-compose.prod.yml up -d backend frontend
  
  echo -e "${YELLOW}Waiting for services to be ready...${NC}"
  sleep 5
  
  # Get initial certificate using standalone mode
  echo -e "${GREEN}Obtaining SSL certificate from Let's Encrypt...${NC}"
  echo -e "${YELLOW}Note: This requires port 80 to be free. If mtank or another service is using it,${NC}"
  echo -e "${YELLOW}      you may need to stop it temporarily.${NC}"
  
  # Check if port 80 is still in use
  if lsof -i :80 2>/dev/null | grep -v "COMMAND" | grep -q .; then
    echo -e "${RED}Port 80 is still in use. Please stop the conflicting service first.${NC}"
    echo "You can run: sudo systemctl stop <service-name>"
    echo "Or place existing certificates in: nginx/ssl/live/$DOMAIN/"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      SKIP_CERT=true
      echo -e "${YELLOW}Skipping cert setup. You'll need to configure certificates manually.${NC}"
    fi
  fi
  
  if [ "$SKIP_CERT" = false ]; then
    docker run -it --rm \
      -v "$(pwd)/nginx/ssl:/etc/letsencrypt" \
      -v "$(pwd)/nginx/ssl:/var/lib/letsencrypt" \
      -p 80:80 \
      certbot/certbot certonly --standalone \
      -d "$DOMAIN" \
      --email "$EMAIL" \
      --agree-tos \
      --rsa-key-size 4096 \
      --non-interactive || {
      echo -e "${RED}Failed to obtain certificate. Make sure:${NC}"
      echo "  1. Domain $DOMAIN points to this server's IP"
      echo "  2. Port 80 is accessible from the internet"
      echo "  3. No other service is using port 80"
      echo ""
      echo "You can manually obtain certificates later or place existing ones in:"
      echo "  nginx/ssl/live/$DOMAIN/fullchain.pem"
      echo "  nginx/ssl/live/$DOMAIN/privkey.pem"
      SKIP_CERT=true
    }
  fi
  
  # Verify certificates are in place
  echo -e "${GREEN}Setting up certificate paths...${NC}"
  mkdir -p "nginx/ssl/live/$DOMAIN"
  
  # Check if certs were created by certbot (they go to archive first, then we symlink)
  if [ -d "nginx/ssl/archive/$DOMAIN" ]; then
    # Certbot stores certs in archive, create symlinks
    if [ ! -f "nginx/ssl/live/$DOMAIN/fullchain.pem" ]; then
      ln -sf "../../archive/$DOMAIN/fullchain.pem" "nginx/ssl/live/$DOMAIN/fullchain.pem" 2>/dev/null || true
      ln -sf "../../archive/$DOMAIN/privkey.pem" "nginx/ssl/live/$DOMAIN/privkey.pem" 2>/dev/null || true
    fi
  fi
  
  if [ -f "nginx/ssl/live/$DOMAIN/fullchain.pem" ] && [ -f "nginx/ssl/live/$DOMAIN/privkey.pem" ]; then
    echo -e "${GREEN}✓ Certificates ready${NC}"
  else
    echo -e "${YELLOW}⚠ Certificate files not found.${NC}"
    echo "You can:"
    echo "  1. Place existing certificates in: nginx/ssl/live/$DOMAIN/"
    echo "  2. Run certbot manually later"
    echo "  3. Continue without HTTPS (not recommended for production)"
    read -p "Continue without certificates? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      exit 1
    fi
  fi
fi

# Start all services including nginx
echo -e "${GREEN}Starting all services...${NC}"
$DC_COMMAND -f docker-compose.prod.yml up -d --build

# Wait a moment for services to start
sleep 3

# Check service status
echo -e "${GREEN}Checking service status...${NC}"
$DC_COMMAND -f docker-compose.prod.yml ps

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Your application should be available at:"
echo -e "  ${GREEN}https://$DOMAIN${NC}"
echo ""
echo "Useful commands:"
echo "  View logs:        $DC_COMMAND -f docker-compose.prod.yml logs -f"
echo "  Restart services: $DC_COMMAND -f docker-compose.prod.yml restart"
echo "  Stop services:    $DC_COMMAND -f docker-compose.prod.yml down"
echo "  Update app:       git pull && $DC_COMMAND -f docker-compose.prod.yml up -d --build"
echo ""
echo -e "${YELLOW}Note: SSL certificates will auto-renew via the certbot container.${NC}"
