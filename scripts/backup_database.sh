#!/bin/bash
# Database backup script for production deployment
# This script creates automated backups with rotation and compression

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/flask-blog}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DATABASE_URL="${DATABASE_URL:-}"
BACKUP_PREFIX="flask-blog-backup"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${BACKUP_DIR}/backup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running as root or with sudo
check_permissions() {
    if [[ $EUID -ne 0 ]] && [[ -z "${SUDO_USER:-}" ]]; then
        error "This script should be run as root or with sudo"
        exit 1
    fi
}

# Create backup directory if it doesn't exist
setup_backup_dir() {
    if [[ ! -d "$BACKUP_DIR" ]]; then
        log "Creating backup directory: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
        chmod 750 "$BACKUP_DIR"
    fi
}

# Parse database URL to extract connection details
parse_database_url() {
    if [[ -z "$DATABASE_URL" ]]; then
        error "DATABASE_URL environment variable is not set"
        exit 1
    fi
    
    # Extract database type, user, password, host, port, and database name
    if [[ $DATABASE_URL =~ ^postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+)$ ]]; then
        DB_TYPE="postgresql"
        DB_USER="${BASH_REMATCH[1]}"
        DB_PASS="${BASH_REMATCH[2]}"
        DB_HOST="${BASH_REMATCH[3]}"
        DB_PORT="${BASH_REMATCH[4]}"
        DB_NAME="${BASH_REMATCH[5]}"
    elif [[ $DATABASE_URL =~ ^mysql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+)$ ]]; then
        DB_TYPE="mysql"
        DB_USER="${BASH_REMATCH[1]}"
        DB_PASS="${BASH_REMATCH[2]}"
        DB_HOST="${BASH_REMATCH[3]}"
        DB_PORT="${BASH_REMATCH[4]}"
        DB_NAME="${BASH_REMATCH[5]}"
    else
        error "Unsupported or invalid DATABASE_URL format"
        exit 1
    fi
    
    log "Database type: $DB_TYPE"
    log "Database name: $DB_NAME"
    log "Database host: $DB_HOST:$DB_PORT"
}

# Create PostgreSQL backup
backup_postgresql() {
    local backup_file="${BACKUP_DIR}/${BACKUP_PREFIX}_${DB_NAME}_${TIMESTAMP}.sql"
    local compressed_file="${backup_file}.gz"
    
    log "Starting PostgreSQL backup..."
    
    # Set password for pg_dump
    export PGPASSWORD="$DB_PASS"
    
    # Create backup with pg_dump
    if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --verbose --clean --no-owner --no-privileges > "$backup_file" 2>>"$LOG_FILE"; then
        
        # Compress the backup
        log "Compressing backup file..."
        gzip "$backup_file"
        
        # Set appropriate permissions
        chmod 640 "$compressed_file"
        
        log "PostgreSQL backup completed: $compressed_file"
        echo "$compressed_file"
    else
        error "PostgreSQL backup failed"
        rm -f "$backup_file"
        exit 1
    fi
    
    unset PGPASSWORD
}

# Create MySQL backup
backup_mysql() {
    local backup_file="${BACKUP_DIR}/${BACKUP_PREFIX}_${DB_NAME}_${TIMESTAMP}.sql"
    local compressed_file="${backup_file}.gz"
    
    log "Starting MySQL backup..."
    
    # Create backup with mysqldump
    if mysqldump -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" \
        --single-transaction --routines --triggers --events \
        "$DB_NAME" > "$backup_file" 2>>"$LOG_FILE"; then
        
        # Compress the backup
        log "Compressing backup file..."
        gzip "$backup_file"
        
        # Set appropriate permissions
        chmod 640 "$compressed_file"
        
        log "MySQL backup completed: $compressed_file"
        echo "$compressed_file"
    else
        error "MySQL backup failed"
        rm -f "$backup_file"
        exit 1
    fi
}

# Clean up old backups
cleanup_old_backups() {
    log "Cleaning up backups older than $RETENTION_DAYS days..."
    
    local deleted_count=0
    while IFS= read -r -d '' file; do
        rm -f "$file"
        ((deleted_count++))
        log "Deleted old backup: $(basename "$file")"
    done < <(find "$BACKUP_DIR" -name "${BACKUP_PREFIX}_*.sql.gz" -type f -mtime +$RETENTION_DAYS -print0)
    
    if [[ $deleted_count -eq 0 ]]; then
        log "No old backups to clean up"
    else
        log "Cleaned up $deleted_count old backup(s)"
    fi
}

# Verify backup integrity
verify_backup() {
    local backup_file="$1"
    
    log "Verifying backup integrity..."
    
    if [[ ! -f "$backup_file" ]]; then
        error "Backup file not found: $backup_file"
        return 1
    fi
    
    # Check if file is a valid gzip file
    if ! gzip -t "$backup_file" 2>/dev/null; then
        error "Backup file is corrupted or not a valid gzip file"
        return 1
    fi
    
    # Check file size (should be > 1KB for a real database)
    local file_size=$(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file" 2>/dev/null)
    if [[ $file_size -lt 1024 ]]; then
        warn "Backup file seems unusually small ($file_size bytes)"
    fi
    
    log "Backup verification completed successfully"
    return 0
}

# Send notification (placeholder for integration with monitoring systems)
send_notification() {
    local status="$1"
    local message="$2"
    
    # This is a placeholder for notification integration
    # You can integrate with services like Slack, email, or monitoring systems
    log "Notification: [$status] $message"
    
    # Example: Send to webhook
    # curl -X POST -H 'Content-type: application/json' \
    #     --data "{\"text\":\"Database Backup [$status]: $message\"}" \
    #     "$WEBHOOK_URL"
}

# Main execution
main() {
    log "Starting database backup process..."
    
    check_permissions
    setup_backup_dir
    parse_database_url
    
    # Perform backup based on database type
    case "$DB_TYPE" in
        postgresql)
            backup_file=$(backup_postgresql)
            ;;
        mysql)
            backup_file=$(backup_mysql)
            ;;
        *)
            error "Unsupported database type: $DB_TYPE"
            exit 1
            ;;
    esac
    
    # Verify backup
    if verify_backup "$backup_file"; then
        cleanup_old_backups
        send_notification "SUCCESS" "Database backup completed successfully: $(basename "$backup_file")"
        log "Backup process completed successfully"
    else
        send_notification "FAILED" "Database backup verification failed"
        error "Backup process failed during verification"
        exit 1
    fi
}

# Handle script interruption
trap 'error "Backup process interrupted"; exit 1' INT TERM

# Run main function
main "$@"