# Deployment Guide - Hetzner Server

This guide covers deploying the Spanish Anki application to a Hetzner server using Docker Compose, Nginx reverse proxy, and Let's Encrypt TLS certificates.

## Prerequisites

- Hetzner server with Ubuntu/Debian
- Domain name pointing to your server's IP address
- Docker and Docker Compose v2 installed
- Ports 80 and 443 open in firewall

## Step 1: Server Setup

### Install Docker and Docker Compose

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose v2 (choose one):
# Option 1: Plugin form (recommended)
sudo apt-get install -y docker-compose-plugin
# Option 2: Standalone binary (also works fine)
# Follow: https://docs.docker.com/compose/install/linux/

# Add your user to docker group (optional, to run without sudo)
sudo usermod -aG docker $USER
newgrp docker
```

### Configure Firewall

```bash
# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # SSH
sudo ufw enable
```

## Step 2: Clone Repository

```bash
# Clone your repository
git clone <your-repo-url> /opt/spanish-anki
cd /opt/spanish-anki

# Or if you're deploying from your local machine, transfer files via rsync/scp
```

## Step 3: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.prod.example .env.prod

# Edit with your actual values
nano .env.prod
```

Required variables:
- `SECRET_KEY`: Generate a secure Django secret key
- `ALLOWED_HOSTS`: Your domain name(s)
- `CORS_ALLOWED_ORIGINS`: Your domain URL(s) with https://
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_JWT_SECRET`: From Supabase project settings
- `SUPABASE_ANON_KEY`: From Supabase project settings
- `DOMAIN`: Your domain name for Let's Encrypt

### Generate Django Secret Key

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Step 4: Update Nginx Configuration

Edit `nginx/production.conf` and replace `your-domain.com` with your actual domain name:

```bash
sed -i 's/your-domain.com/your-actual-domain.com/g' nginx/production.conf
```

## Step 5: Initial Let's Encrypt Certificate

Before starting the full stack, we need to obtain the SSL certificate. The initial certificate request requires port 80 to be available.

### Option A: Standalone Certbot (Recommended for first-time setup)

```bash
# Stop any existing nginx/web server
sudo systemctl stop nginx 2>/dev/null || true

# Run certbot standalone
sudo docker run -it --rm \
  -v "$(pwd)/nginx/ssl:/etc/letsencrypt" \
  -v "$(pwd)/nginx/ssl:/var/lib/letsencrypt" \
  -p 80:80 \
  certbot/certbot certonly --standalone \
  -d your-domain.com \
  --email your-email@example.com \
  --agree-tos \
  --rsa-key-size 4096

# Copy certificates to the expected location
sudo mkdir -p nginx/ssl/live/your-domain.com
sudo cp -r nginx/ssl/live/your-domain.com/* nginx/ssl/live/your-domain.com/ 2>/dev/null || true
```

### Option B: Use the init script (after initial setup)

After the first certificate is obtained, you can use the renewal script:

```bash
./nginx/init-letsencrypt.sh your-domain.com your-email@example.com
```

## Step 6: Start Production Services

```bash
# Build and start all services
# Use 'docker-compose' if you have standalone binary, or 'docker compose' if plugin
docker-compose -f docker-compose.prod.yml up -d --build
# OR
docker compose -f docker-compose.prod.yml up -d --build

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Check service status
docker compose -f docker-compose.prod.yml ps
```

## Step 7: Verify Deployment

1. **Check backend health**: `curl https://your-domain.com/health`
2. **Check API**: `curl https://your-domain.com/api/flashcards/cards/` (requires auth)
3. **Visit frontend**: Open `https://your-domain.com` in your browser

## Step 8: SSL Certificate Renewal

The certbot container runs automatically and renews certificates every 12 hours. The nginx container reloads every 6 hours to pick up renewed certificates.

To manually renew:

```bash
docker compose -f docker-compose.prod.yml run --rm certbot renew
docker compose -f docker-compose.prod.yml restart nginx
```

## Maintenance Commands

### View Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f nginx
```

### Restart Services

```bash
# Restart all
docker compose -f docker-compose.prod.yml restart

# Restart specific service
docker compose -f docker-compose.prod.yml restart backend
```

### Stop Services

```bash
docker compose -f docker-compose.prod.yml down
```

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build

# Run migrations (if needed)
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

### Database Backups

```bash
# Backup SQLite database
docker compose -f docker-compose.prod.yml exec backend python manage.py dumpdata > backup_$(date +%Y%m%d).json

# Or if using PostgreSQL, use pg_dump
docker compose -f docker-compose.prod.yml exec db pg_dump -U postgres dbname > backup_$(date +%Y%m%d).sql
```

## Troubleshooting

### Certificate Issues

If certificates fail to renew:

```bash
# Check certbot logs
docker compose -f docker-compose.prod.yml logs certbot

# Manually test renewal
docker compose -f docker-compose.prod.yml run --rm certbot renew --dry-run
```

### Nginx Not Starting

```bash
# Check nginx configuration
docker compose -f docker-compose.prod.yml exec nginx nginx -t

# View nginx error logs
docker compose -f docker-compose.prod.yml logs nginx
```

### Backend Not Responding

```bash
# Check backend logs
docker compose -f docker-compose.prod.yml logs backend

# Test backend directly (bypass nginx)
docker compose -f docker-compose.prod.yml exec backend curl http://localhost:8000/health
```

### Port Conflicts

If ports 80/443 are already in use:

```bash
# Find what's using the ports
sudo lsof -i :80
sudo lsof -i :443

# Stop conflicting services
sudo systemctl stop nginx  # if system nginx is running
sudo systemctl stop apache2  # if apache is running
```

## Security Checklist

- [ ] Strong `SECRET_KEY` set in `.env.prod`
- [ ] `DEBUG=False` in production
- [ ] `ALLOWED_HOSTS` includes only your domain(s)
- [ ] `CORS_ALLOWED_ORIGINS` restricted to your domain(s)
- [ ] Firewall configured (ports 80, 443, 22 only)
- [ ] Regular backups scheduled
- [ ] SSL certificates auto-renewing
- [ ] Supabase credentials secured (not in git)

## Next Steps

- Set up automated backups (cron job)
- Configure monitoring/alerting (optional)
- Set up CI/CD for automated deployments (optional)
- Configure log rotation
