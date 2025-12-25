# Deploy Now - One Command Deployment

## Quick Deploy (from your local machine)

Run this single command to deploy everything:

```bash
./deploy-to-server.sh your-domain.com your-email@example.com
```

This will:
1. Transfer all files to the server
2. Set up Docker (if needed)
3. Configure environment
4. Obtain SSL certificates
5. Start all services

## Manual Deploy (if you prefer step-by-step)

### Step 1: Transfer files to server

```bash
rsync -avz --exclude 'node_modules' --exclude '__pycache__' --exclude '.git' \
  /home/ben/all_projects/spanish/ root@5.75.174.115:/opt/spanish-anki/
```

### Step 2: SSH into server and deploy

```bash
ssh root@5.75.174.115
cd /opt/spanish-anki
chmod +x deploy.sh
./deploy.sh your-domain.com your-email@example.com
```

## Important Notes

1. **Domain DNS**: Make sure your domain points to `5.75.174.115` before running
2. **Port Conflicts**: If mtank is using ports 80/443, the script will warn you
3. **Environment Variables**: You'll need to edit `.env.prod` with your Supabase credentials

## What You Need

- Domain name (e.g., `spanish-anki.example.com`)
- Email for Let's Encrypt
- Supabase credentials:
  - `SUPABASE_URL`
  - `SUPABASE_JWT_SECRET`
  - `SUPABASE_ANON_KEY`

## After Deployment

Check status:
```bash
ssh root@5.75.174.115
cd /opt/spanish-anki
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f
```

Visit: `https://your-domain.com`
