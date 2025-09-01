#!/bin/bash
#
# PostgreSQL Backup Script for SkyRide Production
# Performs daily backups with retention policy
#

set -e

# Configuration
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-skyride}"
DB_USER="${POSTGRES_USER:-skyride_user}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/skyride}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
S3_BUCKET="${S3_BUCKET:-skyride-backups}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/skyride_backup_$TIMESTAMP.sql"
COMPRESSED_FILE="$BACKUP_FILE.gz"

echo "🗄️ Starting PostgreSQL backup: $TIMESTAMP"

# Create database dump
echo "📦 Creating database dump..."
pg_dump \
  --host="$DB_HOST" \
  --port="$DB_PORT" \
  --username="$DB_USER" \
  --dbname="$DB_NAME" \
  --no-password \
  --verbose \
  --clean \
  --if-exists \
  --create \
  --format=plain \
  --file="$BACKUP_FILE"

# Compress backup
echo "🗜️ Compressing backup..."
gzip "$BACKUP_FILE"

# Verify backup
if [ -f "$COMPRESSED_FILE" ]; then
    BACKUP_SIZE=$(du -h "$COMPRESSED_FILE" | cut -f1)
    echo "✅ Backup created: $COMPRESSED_FILE ($BACKUP_SIZE)"
else
    echo "❌ Backup failed: File not created"
    exit 1
fi

# Upload to S3 (if configured)
if [ -n "$S3_BUCKET" ] && command -v aws &> /dev/null; then
    echo "☁️ Uploading to S3..."
    aws s3 cp "$COMPRESSED_FILE" "s3://$S3_BUCKET/postgres/" --storage-class STANDARD_IA
    if [ $? -eq 0 ]; then
        echo "✅ S3 upload successful"
    else
        echo "⚠️ S3 upload failed"
    fi
fi

# Clean up old backups
echo "🧹 Cleaning up old backups (keeping last $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "skyride_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete

# Count remaining backups
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "skyride_backup_*.sql.gz" -type f | wc -l)
echo "📁 Local backups retained: $BACKUP_COUNT files"

# Redis backup (if running locally)
if command -v redis-cli &> /dev/null && redis-cli ping &> /dev/null; then
    echo "🔴 Creating Redis backup..."
    REDIS_BACKUP="$BACKUP_DIR/redis_backup_$TIMESTAMP.rdb"
    redis-cli --rdb "$REDIS_BACKUP"
    
    if [ -f "$REDIS_BACKUP" ]; then
        gzip "$REDIS_BACKUP"
        echo "✅ Redis backup created: $REDIS_BACKUP.gz"
        
        # Upload Redis backup to S3
        if [ -n "$S3_BUCKET" ] && command -v aws &> /dev/null; then
            aws s3 cp "$REDIS_BACKUP.gz" "s3://$S3_BUCKET/redis/"
        fi
    fi
fi

# Generate backup report
cat > "$BACKUP_DIR/last_backup_report.txt" << EOF
SkyRide Backup Report
Generated: $(date)

Database Backup:
- File: $(basename "$COMPRESSED_FILE")
- Size: $BACKUP_SIZE
- Status: SUCCESS
- Host: $DB_HOST:$DB_PORT
- Database: $DB_NAME

Retention:
- Local files: $BACKUP_COUNT backups
- Retention policy: $RETENTION_DAYS days
- S3 bucket: ${S3_BUCKET:-"Not configured"}

Next backup: $(date -d "tomorrow" +"%Y-%m-%d %H:%M")
EOF

echo "📊 Backup report generated"
echo "🎉 Backup completed successfully!"

# Exit with success
exit 0
