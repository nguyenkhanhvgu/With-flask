#!/bin/bash
# Database migration script for production deployment
# This script handles database migrations with safety checks and rollback capabilities

set -euo pipefail

# Configuration
FLASK_APP="${FLASK_APP:-wsgi.py}"
DATABASE_URL="${DATABASE_URL:-}"
BACKUP_BEFORE_MIGRATE="${BACKUP_BEFORE_MIGRATE:-true}"
MIGRATION_TIMEOUT="${MIGRATION_TIMEOUT:-300}"
LOG_FILE="${LOG_FILE:-/var/log/flask-blog/migration.log}"

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

# Check if Flask app is available
check_flask_app() {
    if [[ ! -f "$FLASK_APP" ]]; then
        error "Flask application file not found: $FLASK_APP"
        exit 1
    fi
    
    # Test if Flask app can be imported
    if ! python -c "from $FLASK_APP import app" 2>/dev/null; then
        error "Cannot import Flask application from $FLASK_APP"
        exit 1
    fi
    
    log "Flask application verified: $FLASK_APP"
}

# Check database connectivity
check_database_connection() {
    log "Checking database connection..."
    
    if ! python -c "
from $FLASK_APP import app
from app.extensions import db
with app.app_context():
    db.engine.execute('SELECT 1')
print('Database connection successful')
" 2>>"$LOG_FILE"; then
        error "Cannot connect to database"
        exit 1
    fi
    
    log "Database connection verified"
}

# Get current migration revision
get_current_revision() {
    python -c "
from $FLASK_APP import app
from flask_migrate import current
with app.app_context():
    rev = current()
    print(rev if rev else 'None')
" 2>/dev/null || echo "None"
}

# Get pending migrations
get_pending_migrations() {
    python -c "
from $FLASK_APP import app
from flask_migrate import current, heads
with app.app_context():
    current_rev = current()
    head_revs = heads()
    if current_rev in head_revs:
        print('No pending migrations')
    else:
        print('Pending migrations found')
" 2>/dev/null || echo "Unknown"
}

# Show migration history
show_migration_history() {
    log "Current migration status:"
    
    python -c "
from $FLASK_APP import app
from flask_migrate import current, history, heads
with app.app_context():
    current_rev = current()
    head_revs = heads()
    
    print(f'Current revision: {current_rev or \"None\"}')
    print(f'Head revisions: {head_revs}')
    
    print('\nMigration history (last 5):')
    for rev in history(rev_range='-5:'):
        marker = ' (current)' if rev.revision == current_rev else ''
        print(f'  {rev.revision}: {rev.doc}{marker}')
" 2>>"$LOG_FILE" || warn "Could not retrieve migration history"
}

# Create database backup before migration
create_backup() {
    if [[ "$BACKUP_BEFORE_MIGRATE" != "true" ]]; then
        log "Skipping backup (BACKUP_BEFORE_MIGRATE=false)"
        return 0
    fi
    
    log "Creating database backup before migration..."
    
    local backup_script="$(dirname "$0")/backup_database.sh"
    if [[ -f "$backup_script" ]]; then
        if "$backup_script"; then
            log "Pre-migration backup completed successfully"
        else
            error "Pre-migration backup failed"
            exit 1
        fi
    else
        warn "Backup script not found: $backup_script"
        warn "Proceeding without backup (not recommended for production)"
    fi
}

# Run database migrations
run_migrations() {
    log "Starting database migration..."
    
    # Set timeout for migration
    timeout "$MIGRATION_TIMEOUT" python -c "
from $FLASK_APP import app
from flask_migrate import upgrade
import sys

try:
    with app.app_context():
        upgrade()
    print('Migration completed successfully')
except Exception as e:
    print(f'Migration failed: {e}', file=sys.stderr)
    sys.exit(1)
" 2>>"$LOG_FILE"
    
    local exit_code=$?
    if [[ $exit_code -eq 0 ]]; then
        log "Database migration completed successfully"
    elif [[ $exit_code -eq 124 ]]; then
        error "Migration timed out after $MIGRATION_TIMEOUT seconds"
        exit 1
    else
        error "Migration failed with exit code $exit_code"
        exit 1
    fi
}

# Verify migration success
verify_migration() {
    log "Verifying migration success..."
    
    # Check if database is accessible
    if ! check_database_connection; then
        error "Database not accessible after migration"
        return 1
    fi
    
    # Check if current revision matches head
    local current_rev=$(get_current_revision)
    local pending_status=$(get_pending_migrations)
    
    if [[ "$pending_status" == "No pending migrations" ]]; then
        log "Migration verification successful - database is up to date"
        log "Current revision: $current_rev"
        return 0
    else
        error "Migration verification failed - pending migrations still exist"
        return 1
    fi
}

# Rollback to previous revision
rollback_migration() {
    local target_revision="$1"
    
    warn "Rolling back migration to revision: $target_revision"
    
    python -c "
from $FLASK_APP import app
from flask_migrate import downgrade
import sys

try:
    with app.app_context():
        downgrade('$target_revision')
    print('Rollback completed successfully')
except Exception as e:
    print(f'Rollback failed: {e}', file=sys.stderr)
    sys.exit(1)
" 2>>"$LOG_FILE"
    
    if [[ $? -eq 0 ]]; then
        log "Rollback completed successfully"
    else
        error "Rollback failed"
        exit 1
    fi
}

# Show help
show_help() {
    cat << EOF
Database Migration Script for Flask Blog Enhanced

Usage: $0 [OPTIONS] [COMMAND]

Commands:
    migrate     Run pending migrations (default)
    status      Show current migration status
    history     Show migration history
    rollback    Rollback to previous revision
    help        Show this help message

Options:
    --no-backup         Skip database backup before migration
    --timeout SECONDS   Set migration timeout (default: 300)
    --log-file FILE     Set log file path

Environment Variables:
    FLASK_APP                   Flask application module (default: wsgi.py)
    DATABASE_URL               Database connection URL
    BACKUP_BEFORE_MIGRATE      Create backup before migration (default: true)
    MIGRATION_TIMEOUT          Migration timeout in seconds (default: 300)
    LOG_FILE                   Log file path

Examples:
    $0                          # Run migrations with backup
    $0 --no-backup migrate      # Run migrations without backup
    $0 status                   # Show migration status
    $0 rollback                 # Rollback to previous revision
    $0 --timeout 600 migrate    # Run with 10-minute timeout

EOF
}

# Parse command line arguments
parse_arguments() {
    COMMAND="migrate"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-backup)
                BACKUP_BEFORE_MIGRATE="false"
                shift
                ;;
            --timeout)
                MIGRATION_TIMEOUT="$2"
                shift 2
                ;;
            --log-file)
                LOG_FILE="$2"
                shift 2
                ;;
            migrate|status|history|rollback|help)
                COMMAND="$1"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Main execution
main() {
    # Create log directory if it doesn't exist
    mkdir -p "$(dirname "$LOG_FILE")"
    
    log "Starting database migration script..."
    log "Command: $COMMAND"
    log "Flask app: $FLASK_APP"
    log "Backup enabled: $BACKUP_BEFORE_MIGRATE"
    log "Timeout: $MIGRATION_TIMEOUT seconds"
    
    case "$COMMAND" in
        migrate)
            check_flask_app
            check_database_connection
            show_migration_history
            
            local current_rev=$(get_current_revision)
            local pending_status=$(get_pending_migrations)
            
            if [[ "$pending_status" == "No pending migrations" ]]; then
                log "No pending migrations found - database is up to date"
                exit 0
            fi
            
            create_backup
            run_migrations
            
            if verify_migration; then
                log "Migration process completed successfully"
            else
                error "Migration verification failed"
                if [[ "$current_rev" != "None" ]]; then
                    warn "Consider rolling back to previous revision: $current_rev"
                fi
                exit 1
            fi
            ;;
        status)
            check_flask_app
            check_database_connection
            show_migration_history
            ;;
        history)
            check_flask_app
            show_migration_history
            ;;
        rollback)
            check_flask_app
            check_database_connection
            local current_rev=$(get_current_revision)
            if [[ "$current_rev" == "None" ]]; then
                error "No current revision found - cannot rollback"
                exit 1
            fi
            
            # Get previous revision
            local prev_rev=$(python -c "
from $FLASK_APP import app
from flask_migrate import history
with app.app_context():
    revs = list(history())
    if len(revs) > 1:
        print(revs[1].revision)
    else:
        print('None')
" 2>/dev/null)
            
            if [[ "$prev_rev" == "None" ]]; then
                error "No previous revision found - cannot rollback"
                exit 1
            fi
            
            create_backup
            rollback_migration "$prev_rev"
            ;;
        help)
            show_help
            ;;
        *)
            error "Unknown command: $COMMAND"
            show_help
            exit 1
            ;;
    esac
}

# Handle script interruption
trap 'error "Migration process interrupted"; exit 1' INT TERM

# Parse arguments and run main function
parse_arguments "$@"
main