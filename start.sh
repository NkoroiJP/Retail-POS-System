#!/bin/bash

echo "Building and starting POS System..."

# Build the Docker images
echo "Building Docker images..."
docker-compose build

if [ $? -ne 0 ]; then
    echo "Error: Docker build failed"
    exit 1
fi

# Start the services in detached mode
echo "Starting services..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "Error: Failed to start services"
    exit 1
fi

echo "Waiting for services to be ready..."
sleep 10

# Run migrations
echo "Running database migrations..."
docker-compose exec web python manage.py migrate

if [ $? -ne 0 ]; then
    echo "Error: Database migrations failed"
    exit 1
fi

# Ask if user wants to load initial data
echo "Do you want to load initial data? (y/n)"
read -r response
if [[ $response =~ ^[Yy]$ ]]; then
    echo "Loading initial data..."
    docker-compose exec web python manage.py setup_initial_data
fi

echo ""
echo "POS System is now running!"
echo "Access the application at http://localhost:8000"
echo ""
echo "Default login credentials after loading initial data:"
echo "  Director: username: director, password: director123"
echo "  Admin:    username: admin,    password: admin123"
echo "  Manager:  username: manager1, password: manager123"
echo "  Staff:    username: staff1,   password: staff123"