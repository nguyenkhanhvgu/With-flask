# Docker Deployment Guide

This guide covers how to deploy the Flask Blog Application using Docker and Docker Compose for both development and production environments.

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)
- Git (for cloning the repository)

## Quick Start

### Development Environment

1. **Clone the repository and navigate to the project directory**
   ```bash
   git clone <repository-url>
   cd flask-blog-enhanced
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

3. **Start the development environment**
   ```bash
   # Linux/macOS
   ./scripts/deploy.sh dev

   # Windows
   scripts\deploy.bat dev
   ```

4. **Access the application**
   - Web Application: http://localhost:5000
   - Nginx Proxy: http://localhost
   - Database: localhost:5432
   - Redis: localhost:6379

### Production Environment

1. **Create production environment file**
   ```bash
   cp .env.prod.example .env.prod
   # Edit .env.prod with secure production values
   ```

2. **Deploy to production**
   ```bash
   # Linux/macOS
   ./scripts/deploy.sh prod

   # Windows
   scripts\deploy.bat prod
   ```

## Architecture Overview

The Docker setup includes the following services:

- **web**: Flask application running with Gunicorn (production) or Flask dev server (development)
- **db**: PostgreSQL database for data persistence
- **redis**: Redis cache for session storage and caching
- **nginx**: Reverse proxy for load balancing and static file serving

## Environment Configuration

### Development (.env)

```env
FLASK_ENV=development
FLASK_DEBUG=1
DATABASE_URL=postgresql://bloguser:blogpass@db:5432/blogdb
REDIS_URL=redis://redis:6379/0
SECRET_KEY=dev-secret-key
```

### Production (.env.prod)

```env
FLASK_ENV=production
FLASK_DEBUG=0
DATABASE_URL=postgresql://bloguser:secure_password@db:5432/blogdb
REDIS_URL=redis://redis:6379/0
SECRET_KEY=very-secure-production-key
```

## Development Workflow

### Common Development Tasks

Use the development helper scripts for common tasks:

```bash
# Linux/macOS
./scripts/dev.sh <command>

# Windows
scripts\dev.bat <command>
```

Available commands:

- `shell` - Open Flask application shell
- `db-shell` - Open database shell (psql)
- `redis-shell` - Open Redis shell
- `logs [service]` - Show logs for a service
- `migrate [message]` - Create database migration
- `upgrade` - Apply database migrations
- `test [path]` - Run tests
- `seed` - Seed database with sample data
- `status` - Show service status

### Examples

```bash
# Open Flask shell for debugging
./scripts/dev.sh shell

# Create a new database migration
./scripts/dev.sh migrate "Add user roles"

# Run tests
./scripts/dev.sh test

# View application logs
./scripts/dev.sh logs web

# Seed database with sample data
./scripts/dev.sh seed
```

## Production Deployment

### SSL Configuration

For production with HTTPS:

1. Place SSL certificates in `docker/ssl/`:
   - `cert.pem` - SSL certificate
   - `key.pem` - Private key

2. Update `docker/nginx.prod.conf` with your domain name

### Environment Variables

Key production environment variables:

```env
# Security
SECRET_KEY=your-very-secure-secret-key
WTF_CSRF_ENABLED=1

# Database
DATABASE_URL=postgresql://user:password@db:5432/dbname
POSTGRES_DB=blogdb
POSTGRES_USER=bloguser
POSTGRES_PASSWORD=secure_password

# Email (for notifications)
MAIL_SERVER=smtp.your-domain.com
MAIL_USERNAME=noreply@your-domain.com
MAIL_PASSWORD=secure_email_password

# Performance
GUNICORN_WORKERS=4
GUNICORN_TIMEOUT=120
```

### Deployment Commands

```bash
# Deploy to production
./scripts/deploy.sh prod deploy

# Stop production services
./scripts/deploy.sh prod stop

# View production logs
./scripts/deploy.sh prod logs

# Create database backup
./scripts/deploy.sh prod backup
```

## Monitoring and Health Checks

### Health Check Endpoint

The application includes a health check endpoint at `/health`:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "services": {
    "database": "healthy",
    "cache": "healthy"
  },
  "version": "1.0.0"
}
```

### Service Monitoring

Monitor service health:

```bash
# Check service status
docker-compose ps

# View resource usage
docker stats

# Check logs
docker-compose logs -f web
```

## Troubleshooting

### Common Issues

1. **Port conflicts**
   ```bash
   # Check what's using the ports
   netstat -tulpn | grep :5000
   netstat -tulpn | grep :5432
   ```

2. **Database connection issues**
   ```bash
   # Check database logs
   docker-compose logs db
   
   # Connect to database manually
   ./scripts/dev.sh db-shell
   ```

3. **Redis connection issues**
   ```bash
   # Check Redis logs
   docker-compose logs redis
   
   # Connect to Redis manually
   ./scripts/dev.sh redis-shell
   ```

4. **Permission issues (Linux/macOS)**
   ```bash
   # Make scripts executable
   chmod +x scripts/*.sh
   ```

### Debugging

1. **Access container shell**
   ```bash
   docker-compose exec web bash
   ```

2. **View application logs**
   ```bash
   docker-compose logs -f web
   ```

3. **Check container resource usage**
   ```bash
   docker stats
   ```

## Performance Optimization

### Production Optimizations

1. **Multi-stage Docker build** - Reduces image size
2. **Nginx caching** - Static file caching and compression
3. **Redis caching** - Application-level caching
4. **Database connection pooling** - Efficient database connections
5. **Gunicorn workers** - Multiple worker processes

### Scaling

To scale the application:

```bash
# Scale web service to 3 instances
docker-compose up -d --scale web=3

# Use Docker Swarm for multi-node deployment
docker swarm init
docker stack deploy -c docker-compose.prod.yml flask-blog
```

## Security Considerations

1. **Environment Variables** - Never commit `.env` files
2. **SSL/TLS** - Use HTTPS in production
3. **Database Security** - Use strong passwords and limit access
4. **Container Security** - Run as non-root user
5. **Network Security** - Use Docker networks for service isolation

## Backup and Recovery

### Database Backup

```bash
# Create backup
./scripts/deploy.sh prod backup

# Restore from backup
docker-compose exec db psql -U bloguser -d blogdb < backup_file.sql
```

### Volume Backup

```bash
# Backup volumes
docker run --rm -v flask-blog_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

## Learning Objectives

This Docker setup demonstrates:

1. **Multi-stage Docker builds** for optimization
2. **Docker Compose** for multi-service applications
3. **Environment-based configuration** management
4. **Service orchestration** and dependencies
5. **Production deployment** best practices
6. **Health checks** and monitoring
7. **Security** considerations for containerized applications

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Flask Deployment Options](https://flask.palletsprojects.com/en/2.0.x/deploying/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [PostgreSQL Docker](https://hub.docker.com/_/postgres)
- [Redis Docker](https://hub.docker.com/_/redis)