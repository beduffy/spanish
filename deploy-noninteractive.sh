#!/bin/bash

# Non-interactive deployment script
# Usage: ./deploy-noninteractive.sh <domain> <email>

set -e

DOMAIN=$1
EMAIL=$2

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
  echo "Usage: $0 <domain> <email>"
  echo "Example: $0 spanish-anki.example.com admin@example.com"
  exit 1
fi

cd /opt/spanish-anki

# Make sure deploy.sh is executable
chmod +x deploy.sh

# Run deployment with provided domain and email
# The script will handle everything including cert setup
./deploy.sh "$DOMAIN" "$EMAIL"
