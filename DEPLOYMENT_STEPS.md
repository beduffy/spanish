# Deployment Steps for Hetzner Server

## Quick Summary

You're deploying to: `root@5.75.174.115`

**Important**: Check if `mtank` is using ports 80/443 before starting!

## Step-by-Step Deployment

### 1. On Your Local Machine - Prepare Files

```bash
cd /home/ben/all_projects/spanish

# Make sure all files are committed and pushed
git status
git add .
git commit -m "Prepare for deployment"
git push
```

### 2. On the Server - Initial Setup

```bash
# SSH into server
ssh root@5.75.174.115

# Check what's using ports 80 and 443
sudo lsof -i :80
sudo lsof -i :443

# If mtank is using these ports, you'll need to either:
# - Stop it temporarily for cert setup, OR
# - Configure a reverse proxy to handle both services
```

### 3. Install Docker (if not already installed)

```bash
# Check if Docker is installed
docker --version
docker compose version

# If not installed, run:
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install -y docker-compose-plugin

# Or use the setup script (copy from local first):
# scp server-setup.sh root@5.75.174.115:/root/
# chmod +x server-setup.sh
# ./server-setup.sh
```

### 4. Clone/Transfer Project to Server

**Option A: Clone from Git (recommended)**
```bash
cd /opt
git clone <your-repo-url> spanish-anki
cd spanish-anki
```

**Option B: Transfer from local**
```bash
# On local machine
rsync -avz --exclude 'node_modules' --exclude '__pycache__' --exclude '.git' \
  /home/ben/all_projects/spanish/ root@5.75.174.115:/opt/spanish-anki/
```

### 5. Configure Environment Variables

```bash
cd /opt/spanish-anki

# Copy template
cp env.prod.example .env.prod

# Edit with your values
nano .env.prod
```

**Required values:**
- `SECRET_KEY`: Generate with:
  ```bash
  python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
- `ALLOWED_HOSTS`: Your domain (comma-separated if multiple)
- `CORS_ALLOWED_ORIGINS`: `https://your-domain.com`
- `SUPABASE_URL`: From Supabase dashboard
- `SUPABASE_JWT_SECRET`: From Supabase project settings
- `SUPABASE_ANON_KEY`: From Supabase project settings
- `DOMAIN`: Your domain name

### 6. Run Deployment Script

```bash
# Make executable
chmod +x deploy.sh

# Run deployment (replace with your domain and email)
./deploy.sh your-domain.com your-email@example.com
```

The script will:
- Check prerequisites
- Set up SSL certificates (if needed)
- Build and start all containers
- Configure nginx

### 7. Verify Deployment

```bash
# Check all services are running
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Test endpoints
curl https://your-domain.com/health
```

### 8. Access Your Application

Open in browser: `https://your-domain.com`

## Troubleshooting

### Port Conflicts with mtank

If mtank is using ports 80/443:

1. **Temporary solution for initial cert:**
   ```bash
   # Stop mtank temporarily
   sudo systemctl stop mtank  # or whatever service
   
   # Get certificate
   docker run -it --rm -p 80:80 \
     -v "$(pwd)/nginx/ssl:/etc/letsencrypt" \
     certbot/certbot certonly --standalone \
     -d your-domain.com --email your-email@example.com --agree-tos
   
   # Restart mtank
   sudo systemctl start mtank
   ```

2. **Permanent solution:** Use a reverse proxy (nginx/traefik) to route to both services.

### Check Service Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f nginx
docker compose -f docker-compose.prod.yml logs -f frontend
```

### Backend Issues

```bash
# Run migrations
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Collect static files
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput

# Check Django settings
docker compose -f docker-compose.prod.yml exec backend python manage.py check --deploy
```

### SSL Certificate Issues

```bash
# Check certbot logs
docker compose -f docker-compose.prod.yml logs certbot

# Manually renew
docker compose -f docker-compose.prod.yml run --rm certbot renew
docker compose -f docker-compose.prod.yml restart nginx
```

## Maintenance

### Update Application

```bash
cd /opt/spanish-anki
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

### Restart Services

```bash
# All services
docker compose -f docker-compose.prod.yml restart

# Specific service
docker compose -f docker-compose.prod.yml restart backend
```

### Stop Services

```bash
docker compose -f docker-compose.prod.yml down
```

### Backup Database

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py dumpdata > backup_$(date +%Y%m%d).json
```

## Files Created/Modified

- `deploy.sh` - Main deployment script
- `server-setup.sh` - Server initialization script
- `docker-compose.prod.yml` - Production Docker Compose config
- `nginx/production.conf` - Nginx reverse proxy config (updated)
- `DEPLOYMENT_QUICKSTART.md` - Quick reference guide
- `DEPLOYMENT_STEPS.md` - This file

## Next Steps After Deployment

1. Set up automated backups (cron job)
2. Configure monitoring/alerting
3. Set up CI/CD for automated deployments
4. Configure log rotation
