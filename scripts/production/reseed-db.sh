#!/bin/bash
# Reset and reseed the Postgres database for demo state
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source /home/clicknback/app/.env; set +a
docker exec app-clicknback-db-1 psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker compose -f /home/clicknback/app/docker-compose.yml run --rm migrate
docker exec -i app-clicknback-db-1 psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < /home/clicknback/app/seed.sql
