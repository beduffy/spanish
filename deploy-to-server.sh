#!/bin/bash

# Master deployment script - runs on your LOCAL machine
# This script transfers files to server and executes deployment
# Usage: ./deploy-to-server.sh [domain] [email] [server_user] [server_ip]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

DOMAIN=${1:-}
EMAIL=${2:-}
SERVER_USER=${3:-root}
SERVER_IP=${4:-5.75.174.115}
SERVER_PATH="/opt/spanish-anki"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Spanish Anki - Full Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Get domain and email if not provided
if [ -z "$DOMAIN" ]; then
  read -p "Enter your domain name (e.g., spanish-anki.example.com): " DOMAIN
fi

if [ -z "$EMAIL" ]; then
  read -p "Enter your email for Let's Encrypt: " EMAIL
fi

echo ""
echo -e "${GREEN}Deployment Configuration:${NC}"
echo "  Domain: $DOMAIN"
echo "  Email: $EMAIL"
echo "  Server: $SERVER_USER@$SERVER_IP"
echo "  Path: $SERVER_PATH"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  exit 1
fi

# Check SSH access
echo -e "${GREEN}Testing SSH connection...${NC}"
if ! ssh -o ConnectTimeout=5 "$SERVER_USER@$SERVER_IP" "echo 'SSH connection successful'" 2>/dev/null; then
  echo -e "${RED}Error: Cannot connect to server. Check SSH access.${NC}"
  exit 1
fi

# Transfer files to server
echo -e "${GREEN}Transferring files to server...${NC}"
rsync -avz --progress \
  --exclude 'node_modules' \
  --exclude '__pycache__' \
  --exclude '.git' \
  --exclude '*.pyc' \
  --exclude '.env' \
  --exclude '.env.prod' \
  --exclude 'db.sqlite3' \
  --exclude 'coverage.xml' \
  --exclude '*.log' \
  /home/ben/all_projects/spanish/ "$SERVER_USER@$SERVER_IP:$SERVER_PATH/"

# Execute deployment on server
echo -e "${GREEN}Executing deployment on server...${NC}"
ssh "$SERVER_USER@$SERVER_IP" << EOF
set -e
cd $SERVER_PATH

# Make scripts executable
chmod +x deploy.sh server-setup.sh 2>/dev/null || true

# Run deployment
./deploy.sh "$DOMAIN" "$EMAIL"
EOF

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Your application should be available at:"
echo -e "  ${GREEN}https://$DOMAIN${NC}"
echo ""
echo "To check status on server:"
echo "  ssh $SERVER_USER@$SERVER_IP"
echo "  cd $SERVER_PATH"
echo "  docker compose -f docker-compose.prod.yml ps"
