# POS System - Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Docker Deployment](#docker-deployment)
4. [Production Deployment](#production-deployment)
5. [Database Management](#database-management)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- PostgreSQL 15+ (if not using Docker)
- Redis 7+ (optional, for caching)
- Python 3.11+ (for local development)
- Minimum 2GB RAM, 10GB disk space

## Environment Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd pos_system
```

### 2. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and configure:

```bash
# Django Settings
SECRET_KEY=<generate-a-strong-secret-key>
DEBUG=False
DJANGO_ENV=production
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_NAME=pos_system
DB_USER=pos_user
DB_PASSWORD=<strong-password>
DB_HOST=db
DB_PORT=5432

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
ADMIN_EMAIL=admin@yourdomain.com

# Security (Production only)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# M-Pesa (if applicable)
MPESA_ENVIRONMENT=production
MPESA_CONSUMER_KEY=your-consumer-key
MPESA_CONSUMER_SECRET=your-consumer-secret
MPESA_SHORTCODE=your-shortcode
MPESA_PASSKEY=your-passkey
```

### 3. Generate Secret Key

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Docker Deployment

### Development Environment

```bash
# Build and start services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Load initial data (optional)
docker-compose exec web python manage.py setup_initial_data

# View logs
docker-compose logs -f web
```

### Production Environment

```bash
# Set environment to production
export DJANGO_ENV=production

# Build with production settings
docker-compose -f docker-compose.yml build

# Start services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Create admin user
docker-compose exec web python manage.py createsuperuser
```

## Production Deployment

### Using Nginx as Reverse Proxy

Create `/etc/nginx/sites-available/pos-system`:

```nginx
upstream pos_app {
    server localhost:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    location / {
        proxy_pass http://pos_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /app/media/;
        expires 7d;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/pos-system /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL/TLS Certificate with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## Database Management

### Backup

```bash
# Manual backup
docker-compose exec web bash /app/scripts/backup.sh

# Setup automated daily backups (cron)
0 2 * * * cd /path/to/pos_system && docker-compose exec -T web bash /app/scripts/backup.sh >> /var/log/pos_backup.log 2>&1
```

### Restore

```bash
# List available backups
docker-compose exec web ls -lh /app/backups/

# Restore from backup
docker-compose exec web bash /app/scripts/restore.sh /app/backups/pos_backup_20240101_020000.sql.gz
```

### Migrations

```bash
# Create migrations
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate

# View migration status
docker-compose exec web python manage.py showmigrations
```

## Monitoring

### Health Checks

```bash
# Application health
curl http://localhost:8000/health/

# Readiness check
curl http://localhost:8000/ready/
```

### Logs

```bash
# Application logs
docker-compose logs -f web

# Database logs
docker-compose logs -f db

# Access application log files
docker-compose exec web tail -f /app/logs/pos_system.log
docker-compose exec web tail -f /app/logs/errors.log
```

### Performance Monitoring

Monitor these metrics:
- CPU and memory usage
- Database connection pool
- Response times
- Error rates
- Disk usage

## Troubleshooting

### Application won't start

```bash
# Check logs
docker-compose logs web

# Verify environment variables
docker-compose exec web env | grep DB_

# Test database connection
docker-compose exec web python manage.py check --database default
```

### Database connection issues

```bash
# Check if database is running
docker-compose ps db

# Test connection manually
docker-compose exec db psql -U pos_user -d pos_system -c "SELECT 1"

# Reset database (⚠️ destroys data)
docker-compose down -v
docker-compose up -d
```

### Static files not loading

```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Check permissions
docker-compose exec web ls -la /app/staticfiles/
```

### Permission errors

```bash
# Fix ownership
docker-compose exec web chown -R appuser:appuser /app/media /app/logs
```

### Reset admin password

```bash
docker-compose exec web python manage.py changepassword <username>
```

## Scaling

### Horizontal Scaling

Update `docker-compose.yml`:

```yaml
web:
  deploy:
    replicas: 3
```

Use a load balancer (nginx, HAProxy) to distribute traffic.

### Database Optimization

- Enable connection pooling
- Add database read replicas
- Implement caching with Redis
- Optimize queries with indexes

## Security Checklist

- [x] SECRET_KEY is unique and secret
- [x] DEBUG=False in production
- [x] HTTPS enabled
- [x] Security headers configured
- [x] Database credentials are strong
- [x] Regular backups configured
- [x] Firewall rules configured
- [x] Log monitoring enabled
- [x] Rate limiting configured
- [x] CSRF protection enabled

## Support

For issues and questions:
- Check logs in `/app/logs/`
- Review this documentation
- Contact: admin@yourdomain.com
