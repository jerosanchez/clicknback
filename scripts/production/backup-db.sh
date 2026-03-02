#!/bin/bash
# Backup the Postgres database to a gzipped file in backups/
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source /home/clicknback/app/.env; set +a
BACKUP_DIR="/home/clicknback/app/backups"
mkdir -p "$BACKUP_DIR"
docker exec app-clicknback-db-1 pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$BACKUP_DIR/clicknback-$(date +%F).sql.gz"
