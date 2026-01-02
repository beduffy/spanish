#!/bin/bash
# Backup script for remote SQLite database on Hetzner server
# Usage: ./scripts/backup-database-remote.sh [server] [backup-dir]

set -e

# Configuration
SERVER="${1:-root@5.75.174.115}"
REMOTE_DB_PATH="${REMOTE_DB_PATH:-/opt/spanish-anki/anki_web_app/db.sqlite3}"
LOCAL_BACKUP_DIR="${2:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${LOCAL_BACKUP_DIR}/db_backup_remote_${TIMESTAMP}.sqlite3"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting remote database backup from ${SERVER}...${NC}"

# Create backup directory if it doesn't exist
mkdir -p "$LOCAL_BACKUP_DIR"

# Check if remote database exists
if ! ssh "$SERVER" "[ -f $REMOTE_DB_PATH ]"; then
    echo -e "${RED}Error: Remote database file not found at $REMOTE_DB_PATH${NC}"
    exit 1
fi

# Create backup on remote server first (safer for active databases)
echo -e "${YELLOW}Creating backup on remote server...${NC}"
REMOTE_BACKUP="/tmp/db_backup_${TIMESTAMP}.sqlite3"
if ssh "$SERVER" "command -v sqlite3 &> /dev/null"; then
    ssh "$SERVER" "sqlite3 $REMOTE_DB_PATH \".backup '$REMOTE_BACKUP'\""
else
    echo -e "${YELLOW}sqlite3 not found on remote, using cp...${NC}"
    ssh "$SERVER" "cp $REMOTE_DB_PATH $REMOTE_BACKUP"
fi

# Copy backup from remote to local
echo -e "${YELLOW}Downloading backup...${NC}"
scp "${SERVER}:${REMOTE_BACKUP}" "$BACKUP_FILE"

# Clean up remote temporary file
ssh "$SERVER" "rm -f $REMOTE_BACKUP"

# Compress the backup
echo -e "${YELLOW}Compressing backup...${NC}"
gzip "$BACKUP_FILE"
BACKUP_FILE="${BACKUP_FILE}.gz"

# Get file size
FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

echo -e "${GREEN}✓ Remote backup created successfully!${NC}"
echo -e "  Location: ${BACKUP_FILE}"
echo -e "  Size: ${FILE_SIZE}"

# Clean up old backups (keep last 30 days)
echo -e "${YELLOW}Cleaning up old backups (keeping last 30 days)...${NC}"
find "$LOCAL_BACKUP_DIR" -name "db_backup_remote_*.sqlite3.gz" -type f -mtime +30 -delete
REMAINING=$(find "$LOCAL_BACKUP_DIR" -name "db_backup_remote_*.sqlite3.gz" -type f | wc -l)
echo -e "${GREEN}  Kept ${REMAINING} backup(s)${NC}"

# List recent backups
echo -e "\n${YELLOW}Recent remote backups:${NC}"
ls -lh "$LOCAL_BACKUP_DIR"/db_backup_remote_*.sqlite3.gz 2>/dev/null | tail -5 || echo "  No backups found"
