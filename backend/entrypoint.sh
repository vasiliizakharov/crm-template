#!/usr/bin/env bash
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL is required}"
: "${ADMIN_EMAIL:=admin@example.com}"
: "${ADMIN_PASSWORD:?ADMIN_PASSWORD is required}"

# Wait for Postgres
echo "[entrypoint] waiting for postgres..."
for i in $(seq 1 60); do
    if PGPASSWORD="${PG_PASS:-}" psql "${DATABASE_URL}" -c 'SELECT 1' >/dev/null 2>&1; then
        echo "[entrypoint] postgres reachable"
        break
    fi
    sleep 1
done

# Apply migrations idempotently
echo "[entrypoint] applying migrations..."
psql "${DATABASE_URL}" -v ON_ERROR_STOP=1 -f /app/migrations/001_init.sql 2>&1 | grep -v "already exists" || true
psql "${DATABASE_URL}" -v ON_ERROR_STOP=1 -f /app/migrations/002_seed.sql

# Bootstrap admin
python -m app.bootstrap

exec "$@"
