#!/bin/bash

# Flask Blog Development Helper Script
# Provides common development tasks for Docker environment

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Check if services are running
check_services() {
    if ! docker-compose ps | grep -q "Up"; then
        print_error "Services are not running. Start them with: ./scripts/deploy.sh dev"
        exit 1
    fi
}

# Development commands
case "${1}" in
    "shell")
        print_header "Opening Flask Application Shell"
        check_services
        docker-compose exec web flask shell
        ;;
    "db-shell")
        print_header "Opening Database Shell"
        check_services
        docker-compose exec db psql -U bloguser -d blogdb
        ;;
    "redis-shell")
        print_header "Opening Redis Shell"
        check_services
        docker-compose exec redis redis-cli
        ;;
    "logs")
        SERVICE=${2:-web}
        print_header "Showing logs for service: $SERVICE"
        docker-compose logs -f $SERVICE
        ;;
    "migrate")
        print_header "Running Database Migration"
        check_services
        docker-compose exec web flask db migrate -m "${2:-Auto migration}"
        ;;
    "upgrade")
        print_header "Upgrading Database"
        check_services
        docker-compose exec web flask db upgrade
        ;;
    "downgrade")
        print_header "Downgrading Database"
        check_services
        docker-compose exec web flask db downgrade
        ;;
    "test")
        print_header "Running Tests"
        check_services
        docker-compose exec web python -m pytest ${2:-tests/} -v
        ;;
    "lint")
        print_header "Running Code Linting"
        check_services
        docker-compose exec web flake8 app/ --max-line-length=120
        ;;
    "format")
        print_header "Formatting Code"
        check_services
        docker-compose exec web black app/ --line-length=120
        ;;
    "seed")
        print_header "Seeding Database with Sample Data"
        check_services
        docker-compose exec web python -c "
from app import create_app, db
from app.models import User, Post, Category
import os

app = create_app()
with app.app_context():
    # Create sample data
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@example.com')
        admin.set_password('admin123')
        admin.is_admin = True
        db.session.add(admin)
    
    if not Category.query.filter_by(name='Technology').first():
        tech_cat = Category(name='Technology', description='Tech posts')
        db.session.add(tech_cat)
    
    db.session.commit()
    print('Sample data created successfully!')
"
        ;;
    "clean")
        print_header "Cleaning Development Environment"
        docker-compose down
        docker system prune -f
        docker volume prune -f
        ;;
    "rebuild")
        print_header "Rebuilding Services"
        docker-compose down
        docker-compose build --no-cache
        docker-compose up -d
        ;;
    "status")
        print_header "Service Status"
        docker-compose ps
        echo ""
        print_status "Service URLs:"
        print_status "  Web Application: http://localhost:5000"
        print_status "  Database: localhost:5432"
        print_status "  Redis: localhost:6379"
        print_status "  Nginx: http://localhost"
        ;;
    *)
        echo "Flask Blog Development Helper"
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  shell              Open Flask application shell"
        echo "  db-shell           Open database shell (psql)"
        echo "  redis-shell        Open Redis shell"
        echo "  logs [service]     Show logs (default: web)"
        echo "  migrate [message]  Create new database migration"
        echo "  upgrade            Apply database migrations"
        echo "  downgrade          Rollback database migration"
        echo "  test [path]        Run tests (default: all tests)"
        echo "  lint               Run code linting"
        echo "  format             Format code with black"
        echo "  seed               Seed database with sample data"
        echo "  clean              Clean development environment"
        echo "  rebuild            Rebuild and restart services"
        echo "  status             Show service status and URLs"
        echo ""
        echo "Examples:"
        echo "  $0 shell"
        echo "  $0 logs web"
        echo "  $0 migrate 'Add user roles'"
        echo "  $0 test tests/unit/"
        exit 1
        ;;
esac