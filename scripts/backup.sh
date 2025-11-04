#!/bin/bash
set -e
BACKUP_DIR="/app/backups"
DB_NAME="${DB_NAME:-pos_system}"
DB_USER="${DB_USER:-pos_user}"
DB_HOST="${DB_HOST:-db}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/pos_backup_$TIMESTAMP.sql.gz"
mkdir -p "$BACKUP_DIR"
echo "Starting database backup..."
PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"
echo "Backup successful: $BACKUP_FILE"
