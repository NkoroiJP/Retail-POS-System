# POS System

A comprehensive Django-based Point of Sale system with multi-store support, role-based access control, inventory management, repair tracking, and professional receipt generation.

## Features

### Core Features
- **Multi-Store Support**: Each store operates independently with its own inventory and staff
- **Role-Based Access Control**:
  - **Director/Admin**: Full system access, all stores analytics, user management
  - **Store Manager**: Manage inventory, staff, and POS for their store; view store analytics
  - **Shop Attendant**: Use POS terminal, view sales commissions
  - **Technician**: Manage device repairs, track repair status
- **Inventory Management**: 
  - Track inventory by store with reorder levels
  - Transfer between stores (with director approval)
  - SKU and barcode support
  - Stock take functionality
- **Sales & Analytics**: 
  - Real-time sales tracking
  - Commission tracking (5% default)
  - Reports by user, store, and date range
  - CSV export functionality
- **Repair Module**:
  - Device repair tracking
  - Customer information management
  - Repair status workflow (Pending → In Progress → Completed)
  - Repair receipts with QR codes
- **Professional Receipts**:
  - Business identification (name, address, tax ID/VAT)
  - Itemized purchases with SKU
  - VAT calculation (16%)
  - Payment method tracking
  - Return/exchange policy
  - PDF download and print functionality
- **Security**: Rate limiting, secure sessions, HTTPS support, audit logging
- **Performance**: Database connection pooling, caching, query optimization

## Quick Start

### Prerequisites
- Docker and Docker Compose
- 2GB RAM minimum
- 10GB disk space

### Installation

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd pos_system
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start the application**
   ```bash
   docker compose up -d
   ```

3. **Run migrations**
   ```bash
   docker compose exec web python manage.py migrate
   ```

4. **Create superuser**
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

5. **Setup initial data**
   ```bash
   docker compose exec web python manage.py shell
   ```
   
   Then run:
   ```python
   from pos_app.models import Store, Category
   
   # Create your store
   store = Store.objects.create(
       name="Main Store",
       address="123 Main Street, City",
       phone="+254700000000",
       email="store@example.com",
       tax_id="VAT123456789",
       website="https://yourstore.com",
       return_policy_days=7
   )
   
   # Create categories
   Category.objects.create(name="Electronics")
   Category.objects.create(name="Accessories")
   
   print("✅ Initial setup complete")
   exit()
   ```

6. **Access the application**
   - Application: http://localhost:8000
   - Admin panel: http://localhost:8000/admin/
   - Login with your superuser credentials

## Docker Commands Reference

### Essential Commands
```bash
# Run Django management commands
docker compose exec web python manage.py <command>

# Examples:
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py shell
docker compose exec web python manage.py collectstatic

# Container management
docker compose ps              # View running containers
docker compose up -d           # Start containers
docker compose down            # Stop containers
docker compose restart         # Restart all containers
docker compose restart web     # Restart specific container
docker compose logs -f web     # View logs in real-time

# Database shell
docker compose exec db psql -U pos_user -d pos_db
```

## User Roles & Permissions

### Director/Admin
- Full system access
- Manage all stores and users
- View analytics across all stores
- Approve inventory transfers
- Export reports to CSV

### Manager
- Manage their store's inventory
- Create and manage store users
- Process sales and view store analytics
- Approve stock takes
- View store-specific reports

### Staff (Shop Attendant)
- Process sales at POS terminal
- View their commission earnings
- View their transaction history
- Generate receipts

### Technician
- Create and manage device repairs
- Update repair status
- Generate repair receipts
- View repair analytics

## Receipt System

### Features
- **Shortened receipt numbers** (8 characters, e.g., "ABC12345")
- **Complete business information** (name, address, tax ID, website)
- **Itemized products** with SKU and barcode support
- **Financial breakdown** (subtotal, VAT 16%, total)
- **Payment tracking** (Cash, Card, Mobile, Bank Transfer)
- **Return policy** (configurable days per store)
- **Professional layout** with color-coded sections
- **PDF download** and print functionality
- **Backward compatible** with old receipts

### Receipt Information Included
✅ Business identification (name, address, phone, email, website)
✅ Tax ID/VAT number
✅ Unique receipt number
✅ Date and time of purchase
✅ Cashier name and ID
✅ Store location
✅ Itemized products (name, SKU, quantity, price)
✅ Financial summary (subtotal, VAT, total)
✅ Payment method and card details (last 4 digits)
✅ Return/exchange policy
✅ Proof of purchase notice

## Reports & Analytics

### Available Reports
- **Sales by User**: Track individual performance with commission data
- **Sales by Store**: Compare store performance
- **Daily Sales**: Trend analysis with charts
- **Top Products**: Best-selling items
- **Commission Tracking**: Staff earnings

### Filters
- Date range (start and end date)
- Store (Admin/Director only)
- User (filtered by permissions)

### Export Options
- CSV download with all filtered data
- Includes: sales summary, user breakdown, store breakdown, daily sales

## Navigation Structure

### Admin/Director Menu
```
Dashboard | Inventory ▼ | Users ▼ | Reports | Receipts | Repairs
            └─ View          └─ All Users
            └─ Add           └─ Create User
            └─ Add Product
            └─ Transfers
```

### Manager Menu
```
Dashboard | POS | Inventory ▼ | Users ▼ | Reports | Receipts | Repairs
                  └─ View          └─ Store Users
                  └─ Add           └─ Create User
                  └─ Add Product
                  └─ Transfers
                  └─ Stock Take
```

## Architecture

### Technology Stack
- **Backend**: Django 4.2.7
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Frontend**: HTML, CSS, Bootstrap 5, JavaScript
- **Web Server**: Gunicorn
- **Containerization**: Docker & Docker Compose

### Project Structure
```
pos_system/
├── pos_app/              # Main application
│   ├── models.py         # Database models
│   ├── views.py          # View functions
│   ├── services_*.py     # Business logic
│   ├── validators.py     # Input validation
│   ├── helpers.py        # Utility functions
│   └── tests*.py         # Test suite
├── mpesa/                # M-Pesa integration
├── pos_system/           # Django settings
├── templates/            # HTML templates
├── static/               # Static files
├── scripts/              # Utility scripts
├── docker-compose.yml    # Docker configuration
└── requirements.txt      # Python dependencies
```

## Environment Configuration

Key variables in `.env`:

```bash
# Django
SECRET_KEY=<your-secret-key>
DEBUG=False
DJANGO_ENV=production
ALLOWED_HOSTS=yourdomain.com

# Database
DB_NAME=pos_db
DB_USER=pos_user
DB_PASSWORD=<strong-password>
DB_HOST=db

# Email (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-password

# Security (Production)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

## Backup & Restore

### Backup Database
```bash
docker compose exec web bash /app/scripts/backup.sh
```

### Restore Database
```bash
docker compose exec web bash /app/scripts/restore.sh /app/backups/backup_file.sql.gz
```

## Monitoring

### Health Checks
- Health: http://localhost:8000/health/
- Readiness: http://localhost:8000/ready/

### View Logs
```bash
# Application logs
docker compose logs -f web

# Database logs
docker compose logs -f db
```

## Common Tasks

### Update Store Information
```bash
docker compose exec web python manage.py shell
```
```python
from pos_app.models import Store

store = Store.objects.first()
store.tax_id = "VAT123456789"
store.website = "https://yourstore.com"
store.return_policy_days = 7
store.save()
```

### Add Products with SKU
```bash
# Via admin panel: http://localhost:8000/admin/
# Or via shell:
docker compose exec web python manage.py shell
```
```python
from pos_app.models import Product, Category

category = Category.objects.get(name="Electronics")
Product.objects.create(
    name="Product Name",
    sku="PROD-001",
    barcode="1234567890",
    category=category,
    price=100.00
)
```

### Create Users
```bash
# Via admin panel or shell:
docker compose exec web python manage.py shell
```
```python
from pos_app.models import User, Store

store = Store.objects.first()
User.objects.create_user(
    username="staff1",
    password="secure_password",
    role="staff",
    store=store,
    commission_rate=5.0
)
```

## Troubleshooting

### Receipt Errors
If you see "column payment_method does not exist":
```bash
docker compose exec web python manage.py migrate
docker compose restart web
```

### Database Connection Issues
```bash
docker compose ps              # Check containers are running
docker compose restart         # Restart all containers
docker compose logs db         # Check database logs
```

### Migration Issues
```bash
# Check migration status
docker compose exec web python manage.py showmigrations

# Force migration
docker compose exec web python manage.py migrate --run-syncdb
```

### Clear Cache
```bash
docker compose exec redis redis-cli FLUSHALL
docker compose restart web
```

## Security Features

✅ Environment-based configuration
✅ Secure secret key management  
✅ HTTPS/SSL support
✅ CSRF & XSS protection
✅ SQL injection prevention (ORM)
✅ Rate limiting on login
✅ Session security
✅ Audit logging
✅ Password validation & hashing

## Performance Features

✅ Database connection pooling
✅ Query optimization with indexes
✅ Redis caching
✅ Static file compression
✅ Gunicorn with multiple workers
✅ Health check endpoints

## Testing

```bash
# Run all tests
docker compose exec web python manage.py test

# Run specific tests
docker compose exec web python manage.py test pos_app.tests

# With coverage
docker compose exec web coverage run --source='.' manage.py test
docker compose exec web coverage report
```

## Recent Updates (v3.0.0)

### Navigation Enhancements
- Dropdown menus for Inventory and Users
- Store-filtered access for managers
- Clean, organized structure

### Reports Enhancements
- Sales analytics by user and store
- CSV export with comprehensive data
- Commission tracking per user
- Advanced filtering (date, store, user)

### Receipt Enhancements
- Professional layout with all mandatory information
- Shortened receipt numbers (8 characters)
- Payment method tracking
- SKU and barcode support
- Return policy and proof of purchase sections
- Backward compatible with old receipts

### Repair Module
- Complete repair tracking system
- Customer management
- Status workflow
- Repair receipts with QR codes

## License

Created for educational and commercial purposes.

## Support

For issues or questions:
- Create an issue in the repository
- Contact: admin@yourdomain.com

---

**Quick Command Cheat Sheet**

```bash
# Start system
docker compose up -d

# Run migrations
docker compose exec web python manage.py migrate

# Create admin user
docker compose exec web python manage.py createsuperuser

# Access shell
docker compose exec web python manage.py shell

# View logs
docker compose logs -f web

# Restart
docker compose restart web

# Stop system
docker compose down
```