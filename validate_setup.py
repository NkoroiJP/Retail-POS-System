#!/usr/bin/env python
"""
Simple validation script to check if the Django POS system is properly configured
"""

import sys
import os

def check_file_exists(filepath):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✓ {filepath} exists")
        return True
    else:
        print(f"✗ {filepath} does not exist")
        return False

def check_directory_exists(dirpath):
    """Check if a directory exists"""
    if os.path.exists(dirpath) and os.path.isdir(dirpath):
        print(f"✓ {dirpath}/ exists")
        return True
    else:
        print(f"✗ {dirpath}/ does not exist")
        return False

def main():
    print("Validating Django POS System setup...")
    print("=" * 50)
    
    # Define the expected files and directories
    expected_files = [
        "Dockerfile",
        "docker-compose.yml",
        "requirements.txt",
        "manage.py",
        "pos_system/__init__.py",
        "pos_system/settings.py",
        "pos_system/urls.py",
        "pos_system/wsgi.py",
        "pos_app/__init__.py",
        "pos_app/models.py",
        "pos_app/views.py",
        "pos_app/urls.py",
        "pos_app/admin.py",
        "pos_app/apps.py",
        "pos_app/middleware.py",
        "pos_app/utils.py",
        "pos_app/tests.py",
        "pos_app/management/commands/setup_initial_data.py",
        "templates/base.html",
        "templates/pos_app/login.html",
        "templates/pos_app/dashboard.html",
        "templates/pos_app/admin_dashboard.html",
        "templates/pos_app/manager_dashboard.html",
        "templates/pos_app/pos.html",
        "templates/pos_app/inventory.html",
        "templates/pos_app/inventory_transfer.html",
        "templates/pos_app/sales_report.html",
        "templates/pos_app/commissions.html",
        "static/css/style.css",
    ]
    
    expected_dirs = [
        "pos_system",
        "pos_app",
        "pos_app/migrations",
        "pos_app/management",
        "pos_app/management/commands",
        "templates",
        "templates/pos_app",
        "static",
        "static/css"
    ]
    
    all_good = True
    
    print("\nChecking expected directories:")
    print("-" * 30)
    for dir_path in expected_dirs:
        if not check_directory_exists(dir_path):
            all_good = False
    
    print("\nChecking expected files:")
    print("-" * 30)
    for file_path in expected_files:
        if not check_file_exists(file_path):
            all_good = False
    
    print("\n" + "=" * 50)
    if all_good:
        print("✓ All required files and directories are present!")
        print("\nTo run the application:")
        print("1. Build the Docker containers: docker-compose build")
        print("2. Start the services: docker-compose up")
        print("3. Run migrations: docker-compose exec web python manage.py migrate")
        print("4. Create superuser: docker-compose exec web python manage.py createsuperuser")
        print("5. Load initial data: docker-compose exec web python manage.py setup_initial_data")
        print("\nThe application will be available at http://localhost:8000")
    else:
        print("✗ Some required files or directories are missing!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())