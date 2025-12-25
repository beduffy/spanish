#!/bin/bash

# Script to initialize Let's Encrypt certificates
# Usage: ./init-letsencrypt.sh <domain> <email>

# Check for Docker Compose (plugin or standalone)
if docker compose version >/dev/null 2>&1; then
  DC_COMMAND="docker compose"
elif command -v docker-compose >/dev/null 2>&1 && docker-compose version >/dev/null 2>&1; then
  DC_COMMAND="docker-compose"
else
  echo 'Error: Docker Compose is not installed.' >&2
  echo 'Install Docker Compose v2:'
  echo '  - Standalone: https://docs.docker.com/compose/install/'
  echo '  - Plugin: sudo apt-get install -y docker-compose-plugin'
  exit 1
fi

DOMAIN=$1
EMAIL=$2

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
  echo "Usage: $0 <domain> <email>"
  echo "Example: $0 example.com admin@example.com"
  exit 1
fi

echo "### Creating directory for certbot challenges..."
mkdir -p ./nginx/ssl

echo "### Requesting Let's Encrypt certificate for $DOMAIN ..."
# Note: This uses the standalone authenticator which requires port 80 to be available
$DC_COMMAND -f docker-compose.prod.yml run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    --email $EMAIL \
    -d $DOMAIN \
    --rsa-key-size 4096 \
    --agree-tos \
    --force-renewal" certbot

echo "### Certificate obtained! Updating nginx configuration..."
# Replace domain placeholder in production.conf
sed -i "s/your-domain.com/$DOMAIN/g" ./nginx/production.conf

echo "### Reloading nginx..."
$DC_COMMAND -f docker-compose.prod.yml restart nginx

echo "### Done! Your site should now be accessible at https://$DOMAIN"
