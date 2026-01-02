#!/bin/bash
# Backup script for SQLite database
# Usage: ./scripts/backup-database.sh [backup-dir]

set -e

# Configuration
BACKUP_DIR="${1:-./backups}"
DB_PATH="${DB_PATH:-./anki_web_app/db.sqlite3}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/db_backup_${TIMESTAMP}.sqlite3"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting database backup...${NC}"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo -e "${RED}Error: Database file not found at $DB_PATH${NC}"
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create backup using SQLite's backup command (safer than cp for active databases)
if command -v sqlite3 &> /dev/null; then
    echo -e "${YELLOW}Using sqlite3 backup command (recommended)...${NC}"
    sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"
else
    echo -e "${YELLOW}sqlite3 not found, using cp (may cause issues if DB is in use)...${NC}"
    cp "$DB_PATH" "$BACKUP_FILE"
fi

# Compress the backup
echo -e "${YELLOW}Compressing backup...${NC}"
gzip "$BACKUP_FILE"
BACKUP_FILE="${BACKUP_FILE}.gz"

# Get file size
FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

echo -e "${GREEN}✓ Backup created successfully!${NC}"
echo -e "  Location: ${BACKUP_FILE}"
echo -e "  Size: ${FILE_SIZE}"

# Clean up old backups (keep last 30 days)
echo -e "${YELLOW}Cleaning up old backups (keeping last 30 days)...${NC}"
find "$BACKUP_DIR" -name "db_backup_*.sqlite3.gz" -type f -mtime +30 -delete
REMAINING=$(find "$BACKUP_DIR" -name "db_backup_*.sqlite3.gz" -type f | wc -l)
echo -e "${GREEN}  Kept ${REMAINING} backup(s)${NC}"

# List recent backups
echo -e "\n${YELLOW}Recent backups:${NC}"
ls -lh "$BACKUP_DIR"/db_backup_*.sqlite3.gz 2>/dev/null | tail -5 || echo "  No backups found"
