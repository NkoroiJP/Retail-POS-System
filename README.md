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
- **Responsive Design**: Works on different device sizes

## System Requirements

- Docker
- Docker Compose

## Installation

1. Clone this repository
2. Navigate to the project directory: `cd pos_system`
3. Build the Docker images: `docker-compose build`
4. Start the services: `docker-compose up`
5. Run the database migrations: `docker-compose exec web python manage.py migrate`
6. Create a superuser account: `docker-compose exec web python manage.py createsuperuser`
7. (Optional) Load initial data: `docker-compose exec web python manage.py setup_initial_data`

The application will be available at `http://localhost:8000`

## Default Users

After running the `setup_initial_data` command, the following default users will be created:

- **Director**: Username: `director`, Password: `director123`
- **Admin**: Username: `admin`, Password: `admin123`
- **Manager**: Username: `manager1`, Password: `manager123`, assigned to "Main Store"
- **Staff**: Username: `staff1`, Password: `staff123`, assigned to "Main Store"

## Usage

### For Directors/Admins
- Access the entire system
- View sales analytics for all stores
- Approve inventory transfers between stores

### For Store Managers
- Manage inventory for their store
- Manage POS operations
- View sales analytics for their store
- Initiate inventory transfers (requires director approval)

### For Shop Attendants
- Process sales through the POS terminal
- View their commission earnings

## Architecture

- **Backend**: Django 4.2.7
- **Database**: PostgreSQL
- **Frontend**: HTML, CSS, Bootstrap 5, JavaScript
- **Containerization**: Docker and Docker Compose
- **Web Server**: Gunicorn

## Development

To make changes to the application:

1. Stop the Docker containers with `Ctrl+C`
2. Make your changes to the code
3. Restart the containers with `docker-compose up`

## Testing

To run the tests:

```bash
docker-compose exec web python manage.py test
```

## License

This project is created for educational purposes.