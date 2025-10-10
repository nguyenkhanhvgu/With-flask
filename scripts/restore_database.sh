#!/bin/bash
# Database restore script for production deployment
# This script restores database from backup files with safety checks

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/flask-blog}"
DATABASE_URL="${DATABASE_URL:-}"
FLASK_APP="${FLASK_APP:-wsgi.py}"
LOG_FILE="${LOG_FILE:-/var/log/flask-blog/restore.log}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1" | tee -a "$LOG_FILE"
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

# List available backup files
list_backups() {
    log "Available backup files in $BACKUP_DIR:"
    
    if [[ ! -d "$BACKUP_DIR" ]]; then
        error "Backup directory not found: $BACKUP_DIR"
        exit 1
    fi
    
    local backup_files=()
    while IFS= read -r -d '' file; do
        backup_files+=("$file")
    done < <(find "$BACKUP_DIR" -name "flask-blog-backup_*.sql.gz" -type f -print0 | sort -z)
    
    if [[ ${#backup_files[@]} -eq 0 ]]; then
        error "No backup files found in $BACKUP_DIR"
        exit 1
    fi
    
    for i in "${!backup_files[@]}"; do
        local file="${backup_files[$i]}"
        local basename=$(basename "$file")
        local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
        local date=$(stat -f%Sm -t "%Y-%m-%d %H:%M:%S" "$file" 2>/dev/null || stat -c%y "$file" 2>/dev/null | cut -d'.' -f1)
        printf "%3d) %s (%s bytes, %s)\n" $((i+1)) "$basename" "$size" "$date"
    done
    
    echo "${backup_files[@]}"
}

# Select backup file
select_backup() {
    local backup_files=($1)
    local selected_file=""
    
    if [[ ${#backup_files[@]} -eq 1 ]]; then
        selected_file="${backup_files[0]}"
        log "Using the only available backup: $(basename "$selected_file")"
    else
        echo
        read -p "Select backup file number (1-${#backup_files[@]}): " selection
        
        if [[ ! "$selection" =~ ^[0-9]+$ ]] || [[ $selection -lt 1 ]] || [[ $selection -gt ${#backup_files[@]} ]]; then
            error "Invalid selection: $selection"
            exit 1
        fi
        
        selected_file="${backup_files[$((selection-1))]}"
        log "Selected backup: $(basename "$selected_file")"
    fi
    
    echo "$selected_file"
}

# Verify backup file
verify_backup() {
    local backup_file="$1"
    
    log "Verifying backup file: $(basename "$backup_file")"
    
    if [[ ! -f "$backup_file" ]]; then
        error "Backup file not found: $backup_file"
        exit 1
    fi
    
    # Check if file is a valid gzip file
    if ! gzip -t "$backup_file" 2>/dev/null; then
        error "Backup file is corrupted or not a valid gzip file"
        exit 1
    fi
    
    # Check file size
    local file_size=$(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file" 2>/dev/null)
    if [[ $file_size -lt 1024 ]]; then
        warn "Backup file seems unusually small ($file_size bytes)"
        read -p "Continue anyway? (y/N): " confirm
        if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
            log "Restore cancelled by user"
            exit 0
        fi
    fi
    
    log "Backup file verification completed"
}

# Create safety backup of current database
create_safety_backup() {
    log "Creating safety backup of current database..."
    
    local safety_backup_script="$(dirname "$0")/backup_database.sh"
    if [[ -f "$safety_backup_script" ]]; then
        if BACKUP_DIR="${BACKUP_DIR}/safety" "$safety_backup_script"; then
            log "Safety backup completed successfully"
        else
            error "Safety backup failed"
            read -p "Continue without safety backup? (y/N): " confirm
            if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
                log "Restore cancelled by user"
                exit 0
            fi
        fi
    else
        warn "Safety backup script not found: $safety_backup_script"
        warn "Proceeding without safety backup"
    fi
}

# Restore PostgreSQL database
restore_postgresql() {
    local backup_file="$1"
    
    log "Starting PostgreSQL database restore..."
    
    # Set password for psql
    export PGPASSWORD="$DB_PASS"
    
    # Drop existing connections to the database
    log "Terminating existing connections to database..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "
        SELECT pg_terminate_backend(pid) 
        FROM pg_stat_activity 
        WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();
    " 2>>"$LOG_FILE" || warn "Could not terminate all connections"
    
    # Restore database
    log "Restoring database from backup..."
    if zcat "$backup_file" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" 2>>"$LOG_FILE"; then
        log "PostgreSQL database restore completed successfully"
    else
        error "PostgreSQL database restore failed"
        unset PGPASSWORD
        exit 1
    fi
    
    unset PGPASSWORD
}

# Restore MySQL database
restore_mysql() {
    local backup_file="$1"
    
    log "Starting MySQL database restore..."
    
    # Restore database
    log "Restoring database from backup..."
    if zcat "$backup_file" | mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" 2>>"$LOG_FILE"; then
        log "MySQL database restore completed successfully"
    else
        error "MySQL database restore failed"
        exit 1
    fi
}

# Verify database after restore
verify_restore() {
    log "Verifying database after restore..."
    
    # Check database connectivity
    if ! python -c "
from $FLASK_APP import app
from app.extensions import db
with app.app_context():
    result = db.engine.execute('SELECT COUNT(*) as count FROM information_schema.tables WHERE table_schema = DATABASE()' if '$DB_TYPE' == 'mysql' else 'SELECT COUNT(*) as count FROM information_schema.tables WHERE table_catalog = current_database()')
    count = result.fetchone()[0]
    print(f'Found {count} tables in database')
    if count == 0:
        raise Exception('No tables found in database')
" 2>>"$LOG_FILE"; then
        error "Database verification failed"
        return 1
    fi
    
    # Check if Flask-Migrate tables exist
    if python -c "
from $FLASK_APP import app
from app.extensions import db
with app.app_context():
    result = db.engine.execute(\"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'alembic_version'\")
    count = result.fetchone()[0]
    if count == 0:
        print('Warning: alembic_version table not found - migrations may need to be reinitialized')
    else:
        print('Migration table found')
" 2>>"$LOG_FILE"; then
        log "Database structure verification completed"
    else
        warn "Could not verify migration table"
    fi
    
    log "Database restore verification completed successfully"
    return 0
}

# Show help
show_help() {
    cat << EOF
Database Restore Script for Flask Blog Enhanced

Usage: $0 [OPTIONS] [BACKUP_FILE]

Options:
    --list              List available backup files
    --no-safety-backup  Skip creating safety backup before restore
    --backup-dir DIR    Specify backup directory (default: /var/backups/flask-blog)
    --log-file FILE     Set log file path
    -h, --help          Show this help message

Arguments:
    BACKUP_FILE         Specific backup file to restore (optional)

Environment Variables:
    DATABASE_URL        Database connection URL
    BACKUP_DIR          Backup directory path
    FLASK_APP           Flask application module (default: wsgi.py)
    LOG_FILE            Log file path

Examples:
    $0                                          # Interactive restore from available backups
    $0 --list                                   # List available backup files
    $0 backup.sql.gz                           # Restore from specific backup file
    $0 --no-safety-backup backup.sql.gz        # Restore without creating safety backup

WARNING: This operation will replace all data in the target database!
Make sure you have a recent backup before proceeding.

EOF
}

# Parse command line arguments
parse_arguments() {
    BACKUP_FILE=""
    LIST_ONLY=false
    CREATE_SAFETY_BACKUP=true
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --list)
                LIST_ONLY=true
                shift
                ;;
            --no-safety-backup)
                CREATE_SAFETY_BACKUP=false
                shift
                ;;
            --backup-dir)
                BACKUP_DIR="$2"
                shift 2
                ;;
            --log-file)
                LOG_FILE="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            -*)
                error "Unknown option: $1"
                show_help
                exit 1
                ;;
            *)
                if [[ -z "$BACKUP_FILE" ]]; then
                    BACKUP_FILE="$1"
                else
                    error "Multiple backup files specified"
                    exit 1
                fi
                shift
                ;;
        esac
    done
}

# Main execution
main() {
    # Create log directory if it doesn't exist
    mkdir -p "$(dirname "$LOG_FILE")"
    
    log "Starting database restore script..."
    
    parse_database_url
    
    if [[ "$LIST_ONLY" == true ]]; then
        list_backups > /dev/null
        exit 0
    fi
    
    # Get backup file
    if [[ -n "$BACKUP_FILE" ]]; then
        if [[ ! -f "$BACKUP_FILE" ]]; then
            # Try to find file in backup directory
            local full_path="$BACKUP_DIR/$BACKUP_FILE"
            if [[ -f "$full_path" ]]; then
                BACKUP_FILE="$full_path"
            else
                error "Backup file not found: $BACKUP_FILE"
                exit 1
            fi
        fi
        log "Using specified backup file: $(basename "$BACKUP_FILE")"
    else
        # Interactive selection
        local available_backups=$(list_backups)
        BACKUP_FILE=$(select_backup "$available_backups")
    fi
    
    # Verify backup file
    verify_backup "$BACKUP_FILE"
    
    # Confirmation
    warn "This operation will REPLACE ALL DATA in database: $DB_NAME"
    warn "Backup file: $(basename "$BACKUP_FILE")"
    echo
    read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm
    if [[ "$confirm" != "yes" ]]; then
        log "Restore cancelled by user"
        exit 0
    fi
    
    # Create safety backup
    if [[ "$CREATE_SAFETY_BACKUP" == true ]]; then
        create_safety_backup
    fi
    
    # Perform restore based on database type
    case "$DB_TYPE" in
        postgresql)
            restore_postgresql "$BACKUP_FILE"
            ;;
        mysql)
            restore_mysql "$BACKUP_FILE"
            ;;
        *)
            error "Unsupported database type: $DB_TYPE"
            exit 1
            ;;
    esac
    
    # Verify restore
    if verify_restore; then
        log "Database restore completed successfully"
        log "You may need to run database migrations if the backup is from an older version"
    else
        error "Database restore verification failed"
        exit 1
    fi
}

# Handle script interruption
trap 'error "Restore process interrupted"; exit 1' INT TERM

# Parse arguments and run main function
parse_arguments "$@"
main