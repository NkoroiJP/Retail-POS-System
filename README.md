# POS System

A Django-based Point of Sale system that supports multiple store outlets with role-based access control.

## Features

- **Multi-Store Support**: Each store outlet operates independently with its own inventory, staff, and manager
- **Role-Based Access Control**:
  - Director: Full system access, can see analytics for all stores
  - System Admin: Full system access, can see analytics for all stores
  - Store Manager: Can manage inventory, staff, and POS for their store; view analytics for their store
  - Shop Attendant: Can use POS terminal, view their sales commissions
- **Inventory Management**: Track inventory by store, set reorder levels, transfer between stores (with director approval)
- **Sales Analytics**: Reports and dashboards for different user roles
- **Commission Tracking**: Shop attendants earn 5% commission on sales they process
- **Audit Logging**: Track all critical system actions
- **Responsive Design**: Works on different device sizes
- **Security**: Rate limiting, secure session handling, HTTPS support
- **Performance**: Database connection pooling, caching support, query optimization

## Quick Start

### Prerequisites

- Docker and Docker Compose
- 2GB RAM minimum
- 10GB disk space

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pos_system
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Run migrations**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

6. **Access the application**
   - Open http://localhost:8000
   - Login with your superuser credentials

## Documentation

- [Deployment Guide](DEPLOYMENT.md) - Complete deployment instructions
- [API Documentation](API.md) - API endpoints and usage (coming soon)
- [Development Guide](DEVELOPMENT.md) - Setup for developers (coming soon)

## Architecture

- **Backend**: Django 4.2.7
- **Database**: PostgreSQL 15
- **Cache**: Redis 7 (optional)
- **Frontend**: HTML, CSS, Bootstrap 5, JavaScript
- **Containerization**: Docker and Docker Compose
- **Web Server**: Gunicorn
- **Reverse Proxy**: Nginx (production)

## Project Structure

```
pos_system/
├── pos_app/              # Main application
│   ├── models.py         # Database models
│   ├── views.py          # View functions
│   ├── services_*.py     # Business logic layer
│   ├── validators.py     # Input validation
│   ├── helpers.py        # Utility functions
│   ├── middleware.py     # Custom middleware
│   └── tests*.py         # Comprehensive tests
├── mpesa/                # M-Pesa payment integration
├── pos_system/           # Django project settings
│   ├── settings.py       # Settings loader
│   ├── settings_base.py  # Base settings
│   ├── settings_dev.py   # Development settings
│   └── settings_prod.py  # Production settings
├── templates/            # HTML templates
├── static/               # Static files (CSS, JS, images)
├── scripts/              # Utility scripts (backup, restore)
├── logs/                 # Application logs
├── docker-compose.yml    # Docker compose configuration
├── Dockerfile            # Docker image definition
└── requirements.txt      # Python dependencies
```

## Environment Configuration

Key environment variables:

```bash
# Django
SECRET_KEY=<your-secret-key>
DEBUG=False
DJANGO_ENV=production
ALLOWED_HOSTS=yourdomain.com

# Database
DB_NAME=pos_system
DB_USER=pos_user
DB_PASSWORD=<strong-password>
DB_HOST=db

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-password
ADMIN_EMAIL=admin@yourdomain.com

# Security (Production)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

See `.env.example` for complete configuration options.

## Development

### Setup Local Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Run Tests

```bash
# Run all tests
python manage.py test

# Run specific test file
python manage.py test pos_app.tests

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Code Quality

```bash
# Format code
black .

# Check security
bandit -r pos_app/ pos_system/

# Check dependencies
safety check
```

## Backup and Restore

### Backup Database

```bash
docker-compose exec web bash /app/scripts/backup.sh
```

### Restore Database

```bash
docker-compose exec web bash /app/scripts/restore.sh /app/backups/pos_backup_YYYYMMDD_HHMMSS.sql.gz
```

## Monitoring

### Health Checks

- Health: http://localhost:8000/health/
- Readiness: http://localhost:8000/ready/

### Logs

```bash
# Application logs
docker-compose logs -f web

# Error logs
docker-compose exec web tail -f /app/logs/errors.log

# Application logs
docker-compose exec web tail -f /app/logs/pos_system.log
```

## Security Features

- ✅ Environment-based configuration
- ✅ Secure secret key management
- ✅ HTTPS/SSL support
- ✅ CSRF protection
- ✅ XSS protection
- ✅ Clickjacking protection
- ✅ SQL injection prevention (ORM)
- ✅ Rate limiting on login
- ✅ Session security
- ✅ Audit logging
- ✅ Password validation
- ✅ Secure password storage (hashing)

## Performance Features

- ✅ Database connection pooling
- ✅ Query optimization with indexes
- ✅ Select/prefetch related queries
- ✅ Redis caching support
- ✅ Static file compression
- ✅ CDN-ready static files
- ✅ Gunicorn with multiple workers
- ✅ Health check endpoints

## Testing

The project includes comprehensive tests:

- Unit tests for models
- Service layer tests
- Validator tests
- Integration tests
- View tests
- Helper function tests

Run tests with:
```bash
python manage.py test
```

## Troubleshooting

See [DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting) for common issues and solutions.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Run tests and ensure they pass
6. Submit a pull request

## License

This project is created for educational purposes.

## Support

For issues, questions, or suggestions:
- Create an issue in the repository
- Contact: admin@yourdomain.com

## Changelog

### Version 2.0.0 (Latest)
- ✅ Improved security with environment-based configuration
- ✅ Service layer for business logic
- ✅ Comprehensive input validation
- ✅ Audit logging for critical actions
- ✅ Rate limiting on login attempts
- ✅ Database query optimization
- ✅ Comprehensive test suite
- ✅ Health check endpoints
- ✅ Backup and restore scripts
- ✅ CI/CD pipeline configuration
- ✅ Production-ready Docker setup
- ✅ Improved documentation

### Version 1.0.0
- Initial release with basic POS functionality