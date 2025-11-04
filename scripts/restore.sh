#!/bin/bash
set -e
DB_NAME="${DB_NAME:-pos_system}"
DB_USER="${DB_USER:-pos_user}"
DB_HOST="${DB_HOST:-db}"
if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    exit 1
fi
BACKUP_FILE="$1"
echo "Starting database restore..."
gunzip -c "$BACKUP_FILE" | PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME"
echo "Restore successful!"
