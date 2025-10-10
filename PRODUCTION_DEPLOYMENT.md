# Production Deployment Guide

This guide covers the production deployment configuration for the Flask Blog Enhanced application, including Gunicorn WSGI server, Nginx reverse proxy, database backup and migration scripts, and comprehensive monitoring.

## Overview

The production deployment includes:

- **Gunicorn WSGI Server**: High-performance Python WSGI HTTP Server
- **Nginx Reverse Proxy**: Load balancing, SSL termination, and static file serving
- **Database Management**: Automated backup, migration, and restore scripts
- **Docker Containerization**: Multi-container production setup with health checks
- **Monitoring & Logging**: Comprehensive logging and health monitoring

## Prerequisites

- Docker and Docker Compose installed
- SSL certificates (for HTTPS)
- Production environment variables configured
- Database credentials and connection details

## Quick Start

1. **Copy Environment Template**:
   ```bash
   cp .env.prod.template .env.prod
   ```

2. **Configure Environment Variables**:
   Edit `.env.prod` with your production values:
   ```bash
   SECRET_KEY=your-super-secret-key-here
   DB_PASSWORD=your-secure-database-password
   MAIL_SERVER=smtp.gmail.com
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   DOMAIN_NAME=your-domain.com
   ```

3. **Deploy to Production**:
   ```bash
   ./scripts/deploy.sh prod deploy
   ```

## Configuration Files

### Gunicorn Configuration (`gunicorn.conf.py`)

The Gunicorn configuration optimizes the WSGI server for production:

```python
# Key configurations
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
timeout = 30
```

**Features**:
- Automatic worker scaling based on CPU cores
- Gevent async worker class for better concurrency
- Request recycling to prevent memory leaks
- Comprehensive logging configuration
- SSL support when certificates are provided

### Nginx Configuration (`docker/nginx.prod.conf`)

The Nginx reverse proxy provides:

**Load Balancing**:
- Upstream configuration with health checks
- Least connections load balancing
- Automatic failover to backup servers

**Security Features**:
- SSL/TLS termination with modern cipher suites
- Security headers (HSTS, CSP, X-Frame-Options)
- Rate limiting for different endpoint types
- HTTP to HTTPS redirection

**Performance Optimization**:
- Gzip compression for text content
- Static file serving with long-term caching
- Proxy caching for API responses
- Connection keep-alive and buffering

**Rate Limiting Zones**:
- Login endpoints: 5 requests per minute
- API endpoints: 100 requests per minute
- General endpoints: 200 requests per minute

### Docker Compose Production (`docker-compose.prod.yml`)

The production Docker setup includes:

**Services**:
- `nginx`: Reverse proxy and load balancer
- `app1`, `app2`: Primary and backup application servers
- `db`: PostgreSQL database with optimized configuration
- `redis`: Cache and session store
- `backup`: Database backup service
- `logrotate`: Log rotation and management

**Features**:
- Health checks for all services
- Automatic restart policies
- Resource limits and reservations
- Separate frontend and backend networks
- Persistent volumes for data storage

## Database Management

### Backup Script (`scripts/backup_database.sh`)

Automated database backup with:
- Support for PostgreSQL and MySQL
- Compressed backups with gzip
- Automatic retention policy (30 days default)
- Backup verification and integrity checks
- Notification integration support

**Usage**:
```bash
# Manual backup
./scripts/backup_database.sh

# Configure automatic backups via cron
0 2 * * * /path/to/scripts/backup_database.sh
```

### Migration Script (`scripts/migrate_database.sh`)

Safe database migration with:
- Pre-migration backup creation
- Migration timeout protection
- Rollback capability
- Migration verification
- Comprehensive logging

**Usage**:
```bash
# Run migrations
./scripts/migrate_database.sh migrate

# Check migration status
./scripts/migrate_database.sh status

# Rollback to previous version
./scripts/migrate_database.sh rollback
```

### Restore Script (`scripts/restore_database.sh`)

Database restoration with:
- Interactive backup file selection
- Safety backup before restore
- Backup file verification
- Database structure validation

**Usage**:
```bash
# Interactive restore
./scripts/restore_database.sh

# Restore specific backup
./scripts/restore_database.sh backup_20240101_120000.sql.gz
```

## Deployment Script (`scripts/deploy.sh`)

Enhanced deployment script with:

**Safety Features**:
- Pre-deployment database backup
- Environment validation
- Health checks after deployment
- Rollback capability

**Commands**:
```bash
# Deploy to production
./scripts/deploy.sh prod deploy

# Deploy without backup (faster)
./scripts/deploy.sh prod --skip-backup deploy

# Force deployment without confirmation
./scripts/deploy.sh prod --force deploy

# Check deployment status
./scripts/deploy.sh prod status

# View application logs
./scripts/deploy.sh prod logs

# Rollback deployment
./scripts/deploy.sh prod rollback

# Check application health
./scripts/deploy.sh prod health
```

## Environment Configuration

### Required Environment Variables

**Flask Configuration**:
- `SECRET_KEY`: Strong secret key (minimum 32 characters)
- `FLASK_ENV`: Set to "production"
- `DEBUG`: Set to False

**Database Configuration**:
- `DATABASE_URL`: PostgreSQL connection string
- `DB_PASSWORD`: Secure database password

**Redis Configuration**:
- `REDIS_URL`: Redis connection string

**Email Configuration**:
- `MAIL_SERVER`: SMTP server hostname
- `MAIL_PORT`: SMTP server port (587 for TLS)
- `MAIL_USERNAME`: SMTP username
- `MAIL_PASSWORD`: SMTP password or app password

**Security Configuration**:
- `SESSION_COOKIE_SECURE`: True for HTTPS
- `SESSION_COOKIE_HTTPONLY`: True for security
- `WTF_CSRF_ENABLED`: True for CSRF protection

### Optional Configuration

**SSL Configuration**:
- `SSL_DISABLE`: False to enable SSL
- `SSL_REDIRECT`: True to redirect HTTP to HTTPS
- `PREFERRED_URL_SCHEME`: "https" for secure URLs

**Monitoring**:
- `HEALTH_CHECK_ENABLED`: True to enable health checks
- `METRICS_ENABLED`: True to enable metrics collection

**Performance**:
- `GUNICORN_WORKERS`: Number of Gunicorn workers
- `GUNICORN_WORKER_CLASS`: Worker class (gevent recommended)
- `CACHE_DEFAULT_TIMEOUT`: Default cache timeout in seconds

## SSL/TLS Configuration

### Certificate Setup

1. **Obtain SSL Certificates**:
   - Use Let's Encrypt for free certificates
   - Or purchase certificates from a CA

2. **Place Certificates**:
   ```
   ssl/
   ├── your-domain.crt
   └── your-domain.key
   ```

3. **Update Nginx Configuration**:
   Edit `docker/nginx.prod.conf` with your domain and certificate paths.

### Let's Encrypt Integration

For automatic certificate management:

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Set up automatic renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Monitoring and Logging

### Health Checks

The application provides comprehensive health checks:

**Endpoint**: `/health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "services": {
    "database": "healthy",
    "cache": "healthy"
  },
  "version": "1.0.0"
}
```

### Logging Configuration

**Log Locations**:
- Application logs: `/var/log/flask-blog/`
- Gunicorn logs: `/var/log/gunicorn/`
- Nginx logs: `/var/log/nginx/`

**Log Rotation**:
- Automatic daily rotation
- 30-day retention
- Compression for old logs

### Monitoring Integration

**Prometheus Metrics** (if enabled):
- Request count and duration
- Error rates
- Database connection pool status
- Cache hit rates

**External Monitoring**:
- Configure health check URL in your monitoring system
- Set up alerts for service failures
- Monitor resource usage and performance

## Performance Optimization

### Database Optimization

**PostgreSQL Configuration**:
```sql
-- Optimized settings in docker-compose.prod.yml
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
```

**Connection Pooling**:
- Pool size: 20 connections
- Max overflow: 30 connections
- Pool timeout: 30 seconds
- Pool recycle: 1 hour

### Redis Configuration

**Memory Management**:
- Max memory: 512MB
- Eviction policy: allkeys-lru
- Persistence: AOF + RDB snapshots

**Performance Settings**:
- TCP keep-alive: 300 seconds
- Timeout: 300 seconds
- Max clients: 10,000

### Application Performance

**Gunicorn Workers**:
- Worker count: CPU cores × 2 + 1
- Worker class: gevent (async)
- Worker connections: 1000
- Max requests: 1000 (prevents memory leaks)

**Caching Strategy**:
- Page caching: 5 minutes
- API responses: 5 minutes
- Database queries: 10 minutes
- Static files: 1 year

## Security Considerations

### Network Security

**Firewall Rules**:
- Allow ports 80, 443 (HTTP/HTTPS)
- Block direct access to application ports
- Restrict database access to application servers

**Docker Security**:
- Non-root user in containers
- Read-only file systems where possible
- Resource limits to prevent DoS
- Separate networks for frontend/backend

### Application Security

**Headers**:
- HSTS for HTTPS enforcement
- CSP for XSS protection
- X-Frame-Options for clickjacking protection
- X-Content-Type-Options for MIME sniffing protection

**Authentication**:
- Strong password requirements
- Session security (secure, httponly cookies)
- CSRF protection enabled
- Rate limiting on authentication endpoints

### Data Security

**Database**:
- Encrypted connections (SSL/TLS)
- Strong authentication (SCRAM-SHA-256)
- Regular security updates
- Backup encryption (recommended)

**Secrets Management**:
- Environment variables for secrets
- No secrets in code or images
- Secure secret generation
- Regular secret rotation

## Troubleshooting

### Common Issues

**Service Won't Start**:
1. Check environment variables
2. Verify database connectivity
3. Check log files for errors
4. Ensure ports are available

**Health Check Failures**:
1. Check database connection
2. Verify Redis connectivity
3. Check application logs
4. Test endpoints manually

**Performance Issues**:
1. Monitor resource usage
2. Check database query performance
3. Verify cache hit rates
4. Review Gunicorn worker configuration

### Log Analysis

**Application Errors**:
```bash
# View recent application logs
docker-compose -f docker-compose.prod.yml logs app1 --tail=100

# Follow logs in real-time
docker-compose -f docker-compose.prod.yml logs -f
```

**Database Issues**:
```bash
# Check database logs
docker-compose -f docker-compose.prod.yml logs db

# Connect to database for debugging
docker-compose -f docker-compose.prod.yml exec db psql -U flask_user flask_blog_prod
```

**Nginx Issues**:
```bash
# Check Nginx configuration
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# View access logs
docker-compose -f docker-compose.prod.yml logs nginx
```

## Maintenance

### Regular Tasks

**Daily**:
- Monitor application health
- Check error logs
- Verify backup completion

**Weekly**:
- Review performance metrics
- Update security patches
- Clean up old log files

**Monthly**:
- Review and rotate secrets
- Update dependencies
- Performance optimization review

### Updates and Patches

**Application Updates**:
1. Test in staging environment
2. Create database backup
3. Deploy with rollback capability
4. Verify health checks pass
5. Monitor for issues

**Security Updates**:
1. Review security advisories
2. Test updates in staging
3. Schedule maintenance window
4. Apply updates with monitoring
5. Verify security improvements

## Backup and Recovery

### Backup Strategy

**Automated Backups**:
- Daily database backups
- 30-day retention policy
- Compressed and verified backups
- Off-site backup storage (recommended)

**Manual Backups**:
```bash
# Create immediate backup
./scripts/backup_database.sh

# Backup with custom retention
RETENTION_DAYS=90 ./scripts/backup_database.sh
```

### Disaster Recovery

**Recovery Procedures**:
1. Assess the scope of the issue
2. Stop affected services
3. Restore from latest backup
4. Verify data integrity
5. Restart services
6. Monitor for issues

**Recovery Testing**:
- Regular backup restoration tests
- Documented recovery procedures
- Recovery time objectives (RTO)
- Recovery point objectives (RPO)

## Scaling Considerations

### Horizontal Scaling

**Application Servers**:
- Add more app containers
- Update Nginx upstream configuration
- Ensure session storage in Redis

**Database Scaling**:
- Read replicas for read-heavy workloads
- Connection pooling optimization
- Query optimization and indexing

### Vertical Scaling

**Resource Allocation**:
- Monitor CPU and memory usage
- Adjust container resource limits
- Optimize worker configurations

**Performance Tuning**:
- Database parameter tuning
- Cache size optimization
- Worker process optimization

This production deployment configuration provides a robust, secure, and scalable foundation for the Flask Blog Enhanced application. Regular monitoring, maintenance, and updates ensure optimal performance and security in production environments.