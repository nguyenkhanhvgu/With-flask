# Flask Blog Enhancement - Deployment Guide

This guide provides comprehensive instructions for deploying the Flask Blog Enhancement application to various environments, from development to production.

## 📋 Table of Contents

1. [Development Setup](#development-setup)
2. [Testing Environment](#testing-environment)
3. [Production Deployment](#production-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)
7. [Troubleshooting](#troubleshooting)

## 🛠️ Development Setup

### Prerequisites

- Python 3.8+
- Redis server
- Git
- Virtual environment tool (venv, virtualenv, or conda)

### Step-by-Step Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd flask-blog-enhanced
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file:
   ```env
   FLASK_ENV=development
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:///blog.db
   REDIS_URL=redis://localhost:6379/0
   MAIL_SERVER=localhost
   MAIL_PORT=587
   ```

5. **Initialize database:**
   ```bash
   flask db upgrade
   python -c "from app.models.role import Role; Role.create_default_roles()"
   ```

6. **Run the application:**
   ```bash
   python run.py
   ```

### Development Tools

- **Flask Debug Toolbar**: Enabled in development for debugging
- **Hot Reloading**: Automatic restart on code changes
- **Debug Mode**: Detailed error pages and interactive debugger

## 🧪 Testing Environment

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/functional/

# Run performance tests
pytest tests/performance/
```

### Test Database Setup

Tests use an in-memory SQLite database by default. For more realistic testing:

```bash
# Set up test database
export TEST_DATABASE_URL=postgresql://user:pass@localhost/blog_test
pytest
```

### Continuous Integration

Example GitHub Actions workflow (`.github/workflows/test.yml`):

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:6
        ports:
          - 6379:6379
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest --cov=app
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/postgres
        REDIS_URL: redis://localhost:6379/0
```

## 🚀 Production Deployment

### Production Checklist

- [ ] Set `FLASK_ENV=production`
- [ ] Use strong `SECRET_KEY`
- [ ] Configure production database (PostgreSQL recommended)
- [ ] Set up Redis for caching and sessions
- [ ] Configure email server
- [ ] Set up HTTPS/SSL certificates
- [ ] Configure reverse proxy (nginx)
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy
- [ ] Set up error tracking (Sentry)

### Environment Variables

Create a production `.env` file:

```env
FLASK_ENV=production
SECRET_KEY=your-very-secure-secret-key
DATABASE_URL=postgresql://user:password@localhost/blog_prod
REDIS_URL=redis://localhost:6379/0
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### Database Setup

1. **Create production database:**
   ```bash
   createdb blog_prod
   ```

2. **Run migrations:**
   ```bash
   flask db upgrade
   ```

3. **Create default roles:**
   ```bash
   python -c "from app.models.role import Role; Role.create_default_roles()"
   ```

### Web Server Configuration

#### Gunicorn Configuration (`gunicorn.conf.py`)

```python
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
```

#### Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Systemd Service

Create `/etc/systemd/system/flask-blog.service`:

```ini
[Unit]
Description=Flask Blog Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/flask-blog-enhanced
Environment=PATH=/path/to/flask-blog-enhanced/venv/bin
EnvironmentFile=/path/to/flask-blog-enhanced/.env
ExecStart=/path/to/flask-blog-enhanced/venv/bin/gunicorn --config gunicorn.conf.py wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable flask-blog
sudo systemctl start flask-blog
```

## 🐳 Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run application
CMD ["gunicorn", "--config", "gunicorn.conf.py", "wsgi:app"]
```

### Docker Compose for Production

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://postgres:password@db:5432/blog
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=blog
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Deployment Commands

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# Run database migrations
docker-compose -f docker-compose.prod.yml exec web flask db upgrade

# Create default roles
docker-compose -f docker-compose.prod.yml exec web python -c "from app.models.role import Role; Role.create_default_roles()"

# View logs
docker-compose -f docker-compose.prod.yml logs -f web
```

## ☁️ Cloud Deployment

### AWS Deployment

#### Using AWS Elastic Beanstalk

1. **Install EB CLI:**
   ```bash
   pip install awsebcli
   ```

2. **Initialize EB application:**
   ```bash
   eb init flask-blog
   ```

3. **Create environment:**
   ```bash
   eb create production
   ```

4. **Deploy:**
   ```bash
   eb deploy
   ```

#### Using AWS ECS

Create `docker-compose.aws.yml`:

```yaml
version: '3.8'
services:
  web:
    image: your-account.dkr.ecr.region.amazonaws.com/flask-blog:latest
    ports:
      - "80:8000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    logging:
      driver: awslogs
      options:
        awslogs-group: flask-blog
        awslogs-region: us-east-1
```

### Heroku Deployment

1. **Create Heroku app:**
   ```bash
   heroku create your-app-name
   ```

2. **Add buildpacks:**
   ```bash
   heroku buildpacks:add heroku/python
   ```

3. **Set environment variables:**
   ```bash
   heroku config:set FLASK_ENV=production
   heroku config:set SECRET_KEY=your-secret-key
   ```

4. **Add database:**
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   heroku addons:create heroku-redis:hobby-dev
   ```

5. **Deploy:**
   ```bash
   git push heroku main
   ```

6. **Run migrations:**
   ```bash
   heroku run flask db upgrade
   ```

### Google Cloud Platform

#### Using Cloud Run

1. **Build and push image:**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT-ID/flask-blog
   ```

2. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy --image gcr.io/PROJECT-ID/flask-blog --platform managed
   ```

## 📊 Monitoring and Maintenance

### Logging Configuration

Production logging setup in `app/config.py`:

```python
class ProductionConfig(Config):
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to syslog
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)
        
        # Log to file with rotation
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            'logs/flask-blog.log',
            maxBytes=10240000,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
```

### Health Checks

The application includes health check endpoints:

- `/api/v1/health` - Basic health check
- `/api/v1/health/detailed` - Detailed system status

### Backup Strategy

1. **Database backups:**
   ```bash
   # Daily backup script
   #!/bin/bash
   DATE=$(date +%Y%m%d_%H%M%S)
   pg_dump blog_prod > backups/blog_backup_$DATE.sql
   
   # Keep only last 30 days
   find backups/ -name "blog_backup_*.sql" -mtime +30 -delete
   ```

2. **File backups:**
   ```bash
   # Backup uploaded files
   rsync -av static/uploads/ backups/uploads/
   ```

### Performance Monitoring

1. **Application Performance Monitoring (APM):**
   - New Relic
   - DataDog
   - Sentry Performance

2. **Infrastructure Monitoring:**
   - Prometheus + Grafana
   - CloudWatch (AWS)
   - Stackdriver (GCP)

### Security Updates

1. **Regular dependency updates:**
   ```bash
   pip list --outdated
   pip install -U package-name
   ```

2. **Security scanning:**
   ```bash
   safety check
   bandit -r app/
   ```

## 🔧 Troubleshooting

### Common Issues

#### Database Connection Issues

```bash
# Check database connectivity
psql $DATABASE_URL -c "SELECT 1;"

# Check migrations
flask db current
flask db history
```

#### Redis Connection Issues

```bash
# Test Redis connection
redis-cli -u $REDIS_URL ping
```

#### Permission Issues

```bash
# Fix file permissions
chown -R app:app /path/to/app
chmod -R 755 /path/to/app
```

#### Memory Issues

```bash
# Monitor memory usage
htop
free -h

# Check application memory usage
ps aux | grep gunicorn
```

### Log Analysis

```bash
# View application logs
tail -f logs/flask-blog.log

# Search for errors
grep -i error logs/flask-blog.log

# Monitor access patterns
tail -f /var/log/nginx/access.log | grep -v "GET /static"
```

### Performance Debugging

```bash
# Profile application
python -m cProfile -o profile.stats run.py

# Analyze database queries
export SQLALCHEMY_ECHO=True
python run.py
```

### Rollback Procedures

1. **Application rollback:**
   ```bash
   # Docker
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml up -d --scale web=0
   docker tag flask-blog:previous flask-blog:latest
   docker-compose -f docker-compose.prod.yml up -d
   
   # Systemd
   sudo systemctl stop flask-blog
   git checkout previous-version
   sudo systemctl start flask-blog
   ```

2. **Database rollback:**
   ```bash
   # Restore from backup
   psql blog_prod < backups/blog_backup_YYYYMMDD_HHMMSS.sql
   
   # Or rollback migrations
   flask db downgrade revision-id
   ```

---

This deployment guide provides comprehensive instructions for deploying the Flask Blog Enhancement application across different environments and platforms. Follow the appropriate section based on your deployment target and requirements.