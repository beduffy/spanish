#!/bin/bash

# Server setup script for Hetzner Ubuntu server
# Installs Docker, Docker Compose, and configures firewall
# Run this on your Hetzner server as root or with sudo

set -e

echo "=========================================="
echo "Hetzner Server Setup for Spanish Anki"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root or with sudo"
  exit 1
fi

# Update system
echo "Updating system packages..."
apt update && apt upgrade -y

# Install prerequisites
echo "Installing prerequisites..."
apt install -y \
  curl \
  git \
  ufw \
  python3 \
  python3-pip

# Install Docker
if ! command -v docker &> /dev/null; then
  echo "Installing Docker..."
  curl -fsSL https://get.docker.com -o get-docker.sh
  sh get-docker.sh
  rm get-docker.sh
else
  echo "Docker is already installed"
fi

# Install Docker Compose plugin
if ! docker compose version &> /dev/null; then
  echo "Installing Docker Compose plugin..."
  apt-get install -y docker-compose-plugin
else
  echo "Docker Compose is already installed"
fi

# Configure firewall
echo "Configuring firewall..."
ufw --force enable
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw status

# Add current user to docker group (if not root)
if [ "$SUDO_USER" ]; then
  usermod -aG docker "$SUDO_USER"
  echo "Added $SUDO_USER to docker group"
  echo "You may need to log out and back in for this to take effect"
fi

echo ""
echo "=========================================="
echo "Server setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Clone your repository:"
echo "   git clone <your-repo-url> /opt/spanish-anki"
echo "   cd /opt/spanish-anki"
echo ""
echo "2. Run the deployment script:"
echo "   ./deploy.sh your-domain.com your-email@example.com"
echo ""
echo "Note: Make sure your domain DNS points to this server's IP address!"
