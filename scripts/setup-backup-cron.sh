#!/bin/bash
# Setup automated daily backups via cron
# Usage: ./scripts/setup-backup-cron.sh [backup-dir]

set -e

BACKUP_DIR="${1:-./backups}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup-database.sh"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up automated daily backups...${NC}"

# Check if backup script exists
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo -e "${RED}Error: Backup script not found at $BACKUP_SCRIPT${NC}"
    exit 1
fi

# Make backup script executable
chmod +x "$BACKUP_SCRIPT"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create cron job (runs daily at 2 AM)
CRON_JOB="0 2 * * * cd $PROJECT_DIR && $BACKUP_SCRIPT $BACKUP_DIR >> $BACKUP_DIR/backup.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$BACKUP_SCRIPT"; then
    echo -e "${YELLOW}Cron job already exists. Updating...${NC}"
    # Remove existing cron job
    crontab -l 2>/dev/null | grep -v "$BACKUP_SCRIPT" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo -e "${GREEN}✓ Automated backup configured!${NC}"
echo -e "  Schedule: Daily at 2:00 AM"
echo -e "  Backup directory: $BACKUP_DIR"
echo -e "  Log file: $BACKUP_DIR/backup.log"
echo -e "\n${YELLOW}Current cron jobs:${NC}"
crontab -l | grep -A 1 "$BACKUP_SCRIPT" || echo "  (none found)"

echo -e "\n${YELLOW}To view all cron jobs:${NC} crontab -l"
echo -e "${YELLOW}To remove this cron job:${NC} crontab -e"
