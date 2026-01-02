# Database Backup Guide

## Overview

The application uses SQLite for the database (`anki_web_app/db.sqlite3`). **Important**: The database file is different on your local machine vs. the Hetzner production server. Each environment has its own separate database.

## Why Backup?

- **Data Loss Prevention**: Protect against accidental deletion, corruption, or server failures
- **Migration Safety**: Safe to test migrations or updates
- **Recovery**: Restore to a previous state if needed
- **Compliance**: Keep historical records of your data

## Backup Methods

### Method 1: Local Backup Script (Recommended for Development)

Use the provided script to backup your local database:

```bash
# Basic usage
./scripts/backup-database.sh

# Specify custom backup directory
./scripts/backup-database.sh ./my-backups
```

**Features:**
- Uses SQLite's `.backup` command (safer than `cp` for active databases)
- Automatically compresses backups with gzip
- Keeps last 30 days of backups automatically
- Shows backup location and size

**Example Output:**
```
Starting database backup...
Using sqlite3 backup command (recommended)...
Compressing backup...
✓ Backup created successfully!
  Location: ./backups/db_backup_20260102_221500.sqlite3.gz
  Size: 2.3M
```

### Method 2: Remote Backup Script (For Production Server)

Backup the database from your Hetzner server to your local machine:

```bash
# Backup from default server (root@5.75.174.115)
./scripts/backup-database-remote.sh

# Backup from custom server
./scripts/backup-database-remote.sh user@example.com

# Custom backup directory
./scripts/backup-database-remote.sh root@5.75.174.115 ./production-backups
```

**Features:**
- Creates backup on remote server first (safer)
- Downloads compressed backup to local machine
- Cleans up temporary files automatically
- Keeps last 30 days of backups

**Prerequisites:**
- SSH access to the server
- SSH key configured (or password access)
- `sqlite3` installed on remote server (optional, falls back to `cp`)

### Method 3: Manual Backup

#### Local Database
```bash
# Simple copy (works when database is not in use)
cp anki_web_app/db.sqlite3 backups/db_backup_$(date +%Y%m%d_%H%M%S).sqlite3

# Using SQLite backup (safer, works even when DB is in use)
sqlite3 anki_web_app/db.sqlite3 ".backup backups/db_backup_$(date +%Y%m%d_%H%M%S).sqlite3"
```

#### Remote Database (Hetzner Server)
```bash
# SSH into server
ssh root@5.75.174.115

# Navigate to project directory
cd /opt/spanish-anki

# Create backup
sqlite3 anki_web_app/db.sqlite3 ".backup backups/db_backup_$(date +%Y%m%d_%H%M%S).sqlite3"

# Or download directly to local machine
scp root@5.75.174.115:/opt/spanish-anki/anki_web_app/db.sqlite3 ./backups/
```

## Automated Backups (Cron)

Set up daily automated backups on your local machine or server:

```bash
# Setup daily backups at 2 AM
./scripts/setup-backup-cron.sh

# Custom backup directory
./scripts/setup-backup-cron.sh ./my-backups
```

**What it does:**
- Creates a cron job that runs daily at 2:00 AM
- Backs up to specified directory
- Logs to `backups/backup.log`
- Automatically cleans up backups older than 30 days

**View cron jobs:**
```bash
crontab -l
```

**Remove automated backups:**
```bash
crontab -e  # Then delete the backup line
```

## Restoring from Backup

### Local Database
```bash
# Stop the application first (if running)
docker-compose down

# Restore from backup
gunzip -c backups/db_backup_20260102_221500.sqlite3.gz > anki_web_app/db.sqlite3

# Or if backup is not compressed
cp backups/db_backup_20260102_221500.sqlite3 anki_web_app/db.sqlite3

# Restart application
docker-compose up -d
```

### Remote Database (Hetzner Server)
```bash
# SSH into server
ssh root@5.75.174.115

# Stop services
cd /opt/spanish-anki
docker-compose -f docker-compose.prod.yml down

# Restore backup
gunzip -c backups/db_backup_20260102_221500.sqlite3.gz > anki_web_app/db.sqlite3

# Set correct permissions
chown root:root anki_web_app/db.sqlite3
chmod 644 anki_web_app/db.sqlite3

# Restart services
docker-compose -f docker-compose.prod.yml up -d
```

## Best Practices

### 1. Backup Frequency
- **Development**: Before major changes or migrations
- **Production**: Daily automated backups (recommended)
- **Before Updates**: Always backup before deploying updates

### 2. Backup Storage
- **Local**: Keep backups in `./backups/` directory (already in .gitignore)
- **Remote**: Store production backups separately (cloud storage, external drive)
- **Multiple Locations**: Don't keep all backups in one place

### 3. Backup Retention
- Keep daily backups for 30 days
- Keep weekly backups for 3 months
- Keep monthly backups for 1 year
- The scripts automatically clean up old backups (30+ days)

### 4. Testing Backups
- Periodically test restoring from backups
- Verify backup integrity (check file size, try to open)
- Document restore procedures

### 5. Database Location

**Local Development:**
- Path: `./anki_web_app/db.sqlite3`
- Volume mounted in Docker: `./data:/app/data`

**Production (Hetzner):**
- Path: `/opt/spanish-anki/anki_web_app/db.sqlite3`
- Volume mounted in Docker: `./anki_web_app:/app`

**Important**: These are **separate databases**. Backing up one doesn't affect the other.

## Troubleshooting

### "Database is locked" Error
- Stop the application before backing up
- Use SQLite's `.backup` command instead of `cp`
- Wait for active transactions to complete

### Backup File is Empty
- Check database file exists and has content
- Verify file permissions
- Check disk space

### Cannot Connect to Remote Server
- Verify SSH access: `ssh root@5.75.174.115`
- Check SSH key is configured
- Ensure server is accessible

## Backup Scripts Location

All backup scripts are in `scripts/` directory:
- `backup-database.sh` - Local database backup
- `backup-database-remote.sh` - Remote database backup
- `setup-backup-cron.sh` - Setup automated backups

## Additional Resources

- [SQLite Backup Documentation](https://www.sqlite.org/backup.html)
- [Docker Volume Backup](https://docs.docker.com/storage/volumes/#backup-restore-or-migrate-data-volumes)
