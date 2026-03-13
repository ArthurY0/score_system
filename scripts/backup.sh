#!/bin/bash
# Database backup script — run via cron or manually
# Usage: ./scripts/backup.sh
# Cron example (daily at 3AM): 0 3 * * * /path/to/score_system/scripts/backup.sh

set -e

BACKUP_DIR="$(dirname "$0")/../backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/score_system_${TIMESTAMP}.sql.gz"
KEEP_DAYS=30

mkdir -p "$BACKUP_DIR"

echo "Backing up database to ${BACKUP_FILE}..."
docker exec score_db pg_dump -U postgres score_system | gzip > "$BACKUP_FILE"

echo "Backup complete: $(du -h "$BACKUP_FILE" | cut -f1)"

# Clean old backups
echo "Removing backups older than ${KEEP_DAYS} days..."
find "$BACKUP_DIR" -name "score_system_*.sql.gz" -mtime +${KEEP_DAYS} -delete

echo "Done."
