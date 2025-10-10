#!/bin/bash
# Enhanced production deployment script with safety checks and rollback capability

set -euo pipefail

# Configuration
ENVIRONMENT=${1:-dev}
COMPOSE_FILE=""
ENV_FILE=""
BACKUP_DIR="/var/backups/flask-blog"
DEPLOYMENT_LOG="/var/log/flask-blog/deployment.log"
ROLLBACK_TAG=""
SKIP_BACKUP=false
SKIP_MIGRATION=false
FORCE_DEPLOY=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

# Show help
show_help() {
    cat << EOF
Enhanced Deployment Script for Flask Blog Enhanced

Usage: $0 [ENVIRONMENT] [OPTIONS] [COMMAND]

Environments:
    dev         Development environment (default)
    staging     Staging environment
    prod        Production environment

Commands:
    deploy      Deploy the application (default)
    rollback    Rollback to previous version
    status      Show deployment status
    logs        Show application logs
    health      Check application health
    backup      Create database backup
    stop        Stop services
    clean       Stop services and remove volumes
    help        Show this help message

Options:
    --skip-backup       Skip database backup before deployment
    --skip-migration    Skip database migration
    --force             Force deployment without confirmation
    --rollback-tag TAG  Specify rollback tag/version

Examples:
    $0 dev deploy                       # Deploy to development
    $0 prod --force deploy              # Force production deployment
    $0 prod --skip-backup deploy        # Deploy without database backup
    $0 prod rollback                    # Rollback production deployment
    $0 prod status                      # Show production status

EOF
}

# Check prerequisites
check_prerequisites() {
    log "Checking deployment prerequisites for $ENVIRONMENT environment..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    log "Prerequisites check completed successfully"
}

# Load environment configuration
load_environment() {
    log "Loading $ENVIRONMENT environment configuration..."
    
    case "$ENVIRONMENT" in
        dev)
            ENV_FILE=".env"
            COMPOSE_FILE="docker-compose.yml"
            ;;
        staging)
            ENV_FILE=".env.staging"
            COMPOSE_FILE="docker-compose.staging.yml"
            ;;
        prod)
            ENV_FILE=".env.prod"
            COMPOSE_FILE="docker-compose.prod.yml"
            ;;
        *)
            error "Unknown environment: $ENVIRONMENT"
            exit 1
            ;;
    esac
    
    # Check if environment file exists
    if [[ ! -f "$ENV_FILE" ]]; then
        if [[ "$ENVIRONMENT" == "dev" && -f ".env.example" ]]; then
            warn "Environment file not found, creating from .env.example"
            cp .env.example .env
        else
            error "Environment file not found: $ENV_FILE"
            if [[ -f ".env.prod.template" ]]; then
                error "Please copy .env.prod.template to $ENV_FILE and configure it"
            fi
            exit 1
        fi
    fi
    
    # Check if compose file exists
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        error "Docker Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    log "Environment configuration loaded: $ENV_FILE, $COMPOSE_FILE"
}

# Create necessary directories
setup_directories() {
    log "Setting up deployment directories..."
    
    mkdir -p "$(dirname "$DEPLOYMENT_LOG")"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "./static/uploads"
    
    # Set appropriate permissions
    chmod 755 "./static/uploads"
    if [[ "$ENVIRONMENT" == "prod" ]]; then
        chmod 750 "$BACKUP_DIR"
    fi
    
    log "Directory setup completed"
}

# Create database backup
create_backup() {
    if [[ "$SKIP_BACKUP" == true ]]; then
        log "Skipping database backup (--skip-backup specified)"
        return 0
    fi
    
    log "Creating database backup before deployment..."
    
    local backup_script="$(dirname "$0")/backup_database.sh"
    if [[ -f "$backup_script" && "$ENVIRONMENT" == "prod" ]]; then
        if "$backup_script"; then
            log "Database backup completed successfully"
        else
            error "Database backup failed"
            if [[ "$FORCE_DEPLOY" != true ]]; then
                exit 1
            else
                warn "Continuing deployment despite backup failure (--force specified)"
            fi
        fi
    else
        # Simple backup for dev/staging
        log "Creating simple database backup..."
        local backup_file="${BACKUP_DIR}/backup_${ENVIRONMENT}_$(date +%Y%m%d_%H%M%S).sql"
        if docker-compose -f "$COMPOSE_FILE" exec -T db pg_dump -U "${POSTGRES_USER:-user}" "${POSTGRES_DB:-flask_blog}" > "$backup_file" 2>/dev/null; then
            log "Backup created: $backup_file"
        else
            warn "Could not create database backup"
        fi
    fi
}

# Build application images
build_images() {
    log "Building application images..."
    
    # Tag current images for rollback (production only)
    if [[ "$ENVIRONMENT" == "prod" ]]; then
        local current_images=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "flask-blog-enhanced" || true)
        if [[ -n "$current_images" ]]; then
            local timestamp=$(date +"%Y%m%d_%H%M%S")
            while IFS= read -r image; do
                local rollback_image="${image%:*}:rollback_${timestamp}"
                docker tag "$image" "$rollback_image"
                log "Tagged $image as $rollback_image for rollback"
            done <<< "$current_images"
            ROLLBACK_TAG="rollback_${timestamp}"
        fi
    fi
    
    # Build new images
    if docker-compose -f "$COMPOSE_FILE" build --no-cache; then
        log "Image build completed successfully"
    else
        error "Image build failed"
        exit 1
    fi
}

# Run database migrations
run_migrations() {
    if [[ "$SKIP_MIGRATION" == true ]]; then
        log "Skipping database migration (--skip-migration specified)"
        return 0
    fi
    
    log "Running database migrations..."
    
    if [[ "$ENVIRONMENT" == "prod" ]]; then
        local migration_script="$(dirname "$0")/migrate_database.sh"
        if [[ -f "$migration_script" ]]; then
            if "$migration_script" migrate; then
                log "Database migration completed successfully"
            else
                error "Database migration failed"
                exit 1
            fi
        else
            warn "Migration script not found, running basic migration"
            docker-compose -f "$COMPOSE_FILE" exec -T app1 flask db upgrade || true
        fi
    else
        # Simple migration for dev/staging
        docker-compose -f "$COMPOSE_FILE" exec -T web flask db upgrade || true
    fi
}

# Deploy application
deploy_application() {
    log "Deploying application to $ENVIRONMENT environment..."
    
    # Stop existing services gracefully
    if docker-compose -f "$COMPOSE_FILE" ps -q | grep -q .; then
        log "Stopping existing services..."
        docker-compose -f "$COMPOSE_FILE" down --timeout 30
    fi
    
    # Start new services
    log "Starting new services..."
    if docker-compose -f "$COMPOSE_FILE" up -d; then
        log "Services started successfully"
    else
        error "Failed to start services"
        exit 1
    fi
    
    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    if check_health; then
        log "Application deployment completed successfully"
        show_deployment_info
    else
        error "Health check failed after deployment"
        if [[ "$FORCE_DEPLOY" != true ]]; then
            warn "Consider rolling back the deployment"
            exit 1
        fi
    fi
}

# Check application health
check_health() {
    log "Checking application health..."
    
    local max_attempts=10
    local attempt=1
    local health_url="http://localhost:8000/health"
    
    if [[ "$ENVIRONMENT" == "dev" ]]; then
        health_url="http://localhost:5000/health"
    fi
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f "$health_url" &>/dev/null; then
            log "Health check passed (attempt $attempt/$max_attempts)"
            return 0
        fi
        
        warn "Health check failed (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    error "Health check failed after $max_attempts attempts"
    return 1
}

# Show deployment information
show_deployment_info() {
    log "Deployment completed successfully!"
    
    case "$ENVIRONMENT" in
        dev)
            info "Development services:"
            info "  - Web: http://localhost:5000"
            info "  - Database: localhost:5432"
            info "  - Redis: localhost:6379"
            ;;
        staging)
            info "Staging environment deployed"
            info "  - Application: http://staging.your-domain.com"
            ;;
        prod)
            info "Production environment deployed"
            info "  - Application: https://your-domain.com"
            info "  - Load balanced with Nginx"
            info "  - SSL termination enabled"
            ;;
    esac
}

# Rollback deployment
rollback_deployment() {
    log "Starting deployment rollback for $ENVIRONMENT environment..."
    
    if [[ "$ENVIRONMENT" != "prod" ]]; then
        error "Rollback is only supported for production environment"
        exit 1
    fi
    
    if [[ -z "$ROLLBACK_TAG" ]]; then
        # Find latest rollback tag
        ROLLBACK_TAG=$(docker images --format "{{.Tag}}" | grep "^rollback_" | sort -r | head -n1)
        if [[ -z "$ROLLBACK_TAG" ]]; then
            error "No rollback tag found"
            exit 1
        fi
    fi
    
    log "Rolling back to tag: $ROLLBACK_TAG"
    
    # Stop current services
    docker-compose -f "$COMPOSE_FILE" down --timeout 30
    
    # Restore rollback images
    local rollback_images=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep ":$ROLLBACK_TAG")
    while IFS= read -r rollback_image; do
        local current_image="${rollback_image%:*}:latest"
        docker tag "$rollback_image" "$current_image"
        log "Restored $rollback_image to $current_image"
    done <<< "$rollback_images"
    
    # Start services with rollback images
    docker-compose -f "$COMPOSE_FILE" up -d
    
    # Check health
    if check_health; then
        log "Rollback completed successfully"
    else
        error "Rollback health check failed"
        exit 1
    fi
}

# Show deployment status
show_status() {
    log "Deployment Status for $ENVIRONMENT:"
    echo
    
    # Show running services
    info "Running Services:"
    docker-compose -f "$COMPOSE_FILE" ps
    echo
    
    # Show resource usage
    info "Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" || true
}

# Show application logs
show_logs() {
    docker-compose -f "$COMPOSE_FILE" logs -f
}

# Stop services
stop_services() {
    log "Stopping $ENVIRONMENT services..."
    docker-compose -f "$COMPOSE_FILE" down
    log "Services stopped"
}

# Clean deployment (stop and remove volumes)
clean_deployment() {
    warn "This will stop services and remove all data volumes for $ENVIRONMENT"
    if [[ "$FORCE_DEPLOY" != true ]]; then
        read -p "Are you sure? (y/N): " confirm
        if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
            log "Clean cancelled by user"
            exit 0
        fi
    fi
    
    log "Cleaning $ENVIRONMENT deployment..."
    docker-compose -f "$COMPOSE_FILE" down -v
    log "Deployment cleaned"
}

# Parse command line arguments
parse_arguments() {
    COMMAND="deploy"
    
    # Skip environment argument
    shift
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            --skip-migration)
                SKIP_MIGRATION=true
                shift
                ;;
            --force)
                FORCE_DEPLOY=true
                shift
                ;;
            --rollback-tag)
                ROLLBACK_TAG="$2"
                shift 2
                ;;
            deploy|rollback|status|logs|health|backup|stop|clean|help)
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
    mkdir -p "$(dirname "$DEPLOYMENT_LOG")"
    
    log "Starting deployment script for $ENVIRONMENT environment..."
    log "Command: $COMMAND"
    
    case "$COMMAND" in
        deploy)
            check_prerequisites
            load_environment
            setup_directories
            
            if [[ "$ENVIRONMENT" == "prod" && "$FORCE_DEPLOY" != true ]]; then
                warn "This will deploy the application to PRODUCTION"
                read -p "Are you sure you want to continue? (y/N): " confirm
                if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
                    log "Deployment cancelled by user"
                    exit 0
                fi
            fi
            
            create_backup
            build_images
            run_migrations
            deploy_application
            ;;
        rollback)
            check_prerequisites
            load_environment
            rollback_deployment
            ;;
        status)
            load_environment
            show_status
            ;;
        logs)
            load_environment
            show_logs
            ;;
        health)
            load_environment
            if check_health; then
                log "Application is healthy"
                exit 0
            else
                error "Application health check failed"
                exit 1
            fi
            ;;
        backup)
            load_environment
            create_backup
            ;;
        stop)
            load_environment
            stop_services
            ;;
        clean)
            load_environment
            clean_deployment
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
trap 'error "Deployment process interrupted"; exit 1' INT TERM

# Parse arguments and run main function
if [[ $# -eq 0 ]]; then
    show_help
    exit 0
fi

parse_arguments "$@"
main