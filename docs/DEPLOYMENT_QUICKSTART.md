# Quick Deployment Guide - Hetzner Server

This is a quick reference for deploying the Spanish Anki app to your Hetzner server.

## Prerequisites

- Hetzner server with Ubuntu 22.04+ (you're already SSH'd in)
- Domain name pointing to your server's IP
- Ports 80 and 443 available (check if mtank is using them)

## Step 1: Check Current Server State

```bash
# Check what's running on ports 80 and 443
sudo lsof -i :80
sudo lsof -i :443

# Check if Docker is installed
docker --version
docker compose version
```

**If mtank is using port 80/443**, you have two options:
1. Run this app on different ports and use a reverse proxy (more complex)
2. Stop mtank temporarily for initial cert setup, then configure both to coexist

## Step 2: Server Setup (if needed)

If Docker isn't installed, run the setup script:

```bash
# On your local machine, copy the script to server
scp server-setup.sh root@5.75.174.115:/root/

# On the server
ssh root@5.75.174.115
chmod +x server-setup.sh
./server-setup.sh
```

Or install manually:
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose plugin
sudo apt-get install -y docker-compose-plugin

# Configure firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

## Step 3: Transfer Project to Server

**Option A: Clone from Git (recommended)**
```bash
# On server
cd /opt
git clone <your-repo-url> spanish-anki
cd spanish-anki
```

**Option B: Transfer from local machine**
```bash
# On your local machine
rsync -avz --exclude 'node_modules' --exclude '__pycache__' --exclude '.git' \
  /home/ben/all_projects/spanish/ root@5.75.174.115:/opt/spanish-anki/
```

## Step 4: Configure Environment

```bash
cd /opt/spanish-anki

# Copy and edit environment file
cp env.prod.example .env.prod
nano .env.prod
```

**Required settings in `.env.prod`:**
- `SECRET_KEY`: Generate with `python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `ALLOWED_HOSTS`: Your domain (e.g., `spanish-anki.example.com`)
- `CORS_ALLOWED_ORIGINS`: `https://your-domain.com`
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_JWT_SECRET`: From Supabase settings
- `SUPABASE_ANON_KEY`: From Supabase settings
- `DOMAIN`: Your domain name

## Step 5: Deploy

```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment (it will prompt for domain and email if not provided)
./deploy.sh your-domain.com your-email@example.com
```

The script will:
1. Check prerequisites
2. Set up SSL certificates (if needed)
3. Build and start all containers
4. Configure nginx

## Step 6: Verify Deployment

```bash
# Check service status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Test endpoints
curl https://your-domain.com/health
curl https://your-domain.com/api/flashcards/cards/
```

## Common Issues

### Port 80/443 Already in Use

If mtank or another service is using these ports:

1. **Temporary solution for cert setup:**
   ```bash
   # Stop the service temporarily
   sudo systemctl stop nginx  # or whatever is using port 80
   
   # Run certbot standalone
   docker run -it --rm -p 80:80 -v "$(pwd)/nginx/ssl:/etc/letsencrypt" \
     certbot/certbot certonly --standalone -d your-domain.com \
     --email your-email@example.com --agree-tos
   
   # Restart your service
   sudo systemctl start nginx
   ```

2. **Permanent solution:** Use a reverse proxy (nginx or traefik) to route traffic to both services.

### Certificate Issues

```bash
# Check certbot logs
docker compose -f docker-compose.prod.yml logs certbot

# Manually renew
docker compose -f docker-compose.prod.yml run --rm certbot renew
docker compose -f docker-compose.prod.yml restart nginx
```

### Backend Not Starting

```bash
# Check backend logs
docker compose -f docker-compose.prod.yml logs backend

# Run migrations manually
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Collect static files
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

## Maintenance Commands

```bash
# View all logs
docker compose -f docker-compose.prod.yml logs -f

# Restart a service
docker compose -f docker-compose.prod.yml restart backend

# Update application
git pull
docker compose -f docker-compose.prod.yml up -d --build

# Stop everything
docker compose -f docker-compose.prod.yml down

# Backup database
docker compose -f docker-compose.prod.yml exec backend python manage.py dumpdata > backup_$(date +%Y%m%d).json
```

## Next Steps

- Set up automated backups (cron job)
- Configure monitoring
- Set up CI/CD for automated deployments
