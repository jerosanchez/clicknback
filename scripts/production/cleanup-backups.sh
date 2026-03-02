#!/bin/bash
# Remove database backups older than 7 days from backups/
set -euo pipefail
cd "$(dirname "$0")/.."
BACKUP_DIR="/home/clicknback/app/backups"
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete
