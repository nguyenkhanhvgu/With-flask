# Multi-stage Dockerfile for Flask Blog Enhanced
# Stage 1: Build stage for dependencies
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install gunicorn gevent

# Stage 2: Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=wsgi.py \
    FLASK_ENV=production \
    PYTHONPATH=/app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    gzip \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r flaskuser && useradd -r -g flaskuser flaskuser

# Create application directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY . .

# Copy production configuration files (if they don't exist)
COPY gunicorn.conf.py wsgi.py ./

# Make deployment scripts executable
RUN chmod +x ./scripts/*.sh

# Create necessary directories and set permissions
RUN mkdir -p logs static/uploads /var/log/gunicorn /var/log/flask-blog /var/backups/flask-blog && \
    chown -R flaskuser:flaskuser /app /var/log/gunicorn /var/log/flask-blog /var/backups/flask-blog

# Switch to non-root user
USER flaskuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (production with Gunicorn)
CMD ["gunicorn", "--config", "gunicorn.conf.py", "wsgi:app"]