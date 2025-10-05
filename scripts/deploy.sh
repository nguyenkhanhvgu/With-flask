#!/bin/bash

# Flask Blog Application Deployment Script
# Usage: ./scripts/deploy.sh [environment]
# Environment: dev, staging, prod (default: dev)

set -e

ENVIRONMENT=${1:-dev}
PROJECT_NAME="flask-blog"

echo "🚀 Deploying Flask Blog Application - Environment: $ENVIRONMENT"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed and running
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Load environment variables
load_env() {
    if [ "$ENVIRONMENT" = "prod" ]; then
        if [ ! -f ".env.prod" ]; then
            print_error "Production environment file .env.prod not found!"
            print_warning "Please create .env.prod from .env.prod.example"
            exit 1
        fi
        export $(cat .env.prod | grep -v '^#' | xargs)
        COMPOSE_FILE="docker-compose.prod.yml"
    else
        if [ ! -f ".env" ]; then
            print_warning "Environment file .env not found. Creating from .env.example"
            cp .env.example .env
        fi
        export $(cat .env | grep -v '^#' | xargs)
        COMPOSE_FILE="docker-compose.yml"
    fi
}

# Build and deploy
deploy() {
    print_status "Building Docker images..."
    docker-compose -f $COMPOSE_FILE build --no-cache

    print_status "Starting services..."
    docker-compose -f $COMPOSE_FILE up -d

    print_status "Waiting for services to be ready..."
    sleep 10

    # Run database migrations
    print_status "Running database migrations..."
    docker-compose -f $COMPOSE_FILE exec web flask db upgrade

    # Check service health
    print_status "Checking service health..."
    if docker-compose -f $COMPOSE_FILE ps | grep -q "Up"; then
        print_status "✅ Deployment successful!"
        print_status "Application is running at: http://localhost"
        
        if [ "$ENVIRONMENT" = "dev" ]; then
            print_status "Development services:"
            print_status "  - Web: http://localhost:5000"
            print_status "  - Database: localhost:5432"
            print_status "  - Redis: localhost:6379"
        fi
    else
        print_error "❌ Deployment failed. Check logs with: docker-compose -f $COMPOSE_FILE logs"
        exit 1
    fi
}

# Cleanup function
cleanup() {
    print_status "Stopping services..."
    docker-compose -f $COMPOSE_FILE down
    
    if [ "$1" = "--volumes" ]; then
        print_warning "Removing volumes (this will delete all data)..."
        docker-compose -f $COMPOSE_FILE down -v
    fi
}

# Backup function
backup() {
    print_status "Creating database backup..."
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    docker-compose -f $COMPOSE_FILE exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > $BACKUP_FILE
    print_status "Backup created: $BACKUP_FILE"
}

# Main execution
case "${2:-deploy}" in
    "deploy")
        check_docker
        load_env
        deploy
        ;;
    "stop")
        load_env
        cleanup
        ;;
    "clean")
        load_env
        cleanup --volumes
        ;;
    "backup")
        load_env
        backup
        ;;
    "logs")
        load_env
        docker-compose -f $COMPOSE_FILE logs -f
        ;;
    *)
        echo "Usage: $0 [environment] [action]"
        echo "Environment: dev, staging, prod (default: dev)"
        echo "Actions: deploy, stop, clean, backup, logs (default: deploy)"
        exit 1
        ;;
esac