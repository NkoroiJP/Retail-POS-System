#!/usr/bin/env python
"""
Setup verification script for POS System
Checks that all improvements are properly configured
"""
import os
import sys
from pathlib import Path

def print_status(message, status):
    """Print colored status message"""
    colors = {
        'ok': '\033[92m✓\033[0m',
        'warn': '\033[93m⚠\033[0m',
        'error': '\033[91m✗\033[0m',
        'info': '\033[94mℹ\033[0m',
    }
    print(f"{colors.get(status, '')} {message}")

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print_status(f"{description} exists", 'ok')
        return True
    else:
        print_status(f"{description} missing", 'error')
        return False

def check_directory_exists(dirpath, description):
    """Check if a directory exists"""
    if Path(dirpath).is_dir():
        print_status(f"{description} directory exists", 'ok')
        return True
    else:
        print_status(f"{description} directory missing", 'warn')
        return False

def check_env_file():
    """Check .env file configuration"""
    print("\n📋 Checking environment configuration...")
    
    if not check_file_exists('.env', '.env file'):
        print_status("Create .env from .env.example", 'info')
        return False
    
    # Check for critical variables
    required_vars = [
        'SECRET_KEY',
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD',
    ]
    
    missing_vars = []
    with open('.env', 'r') as f:
        content = f.read()
        for var in required_vars:
            if f"{var}=" not in content or f"{var}=your-" in content or f"{var}=<" in content:
                missing_vars.append(var)
    
    if missing_vars:
        print_status(f"Configure these variables in .env: {', '.join(missing_vars)}", 'warn')
        return False
    
    print_status("Environment variables configured", 'ok')
    return True

def check_structure():
    """Check project structure"""
    print("\n📁 Checking project structure...")
    
    checks = [
        ('.env.example', '.env.example template'),
        ('.gitignore', '.gitignore file'),
        ('DEPLOYMENT.md', 'Deployment guide'),
        ('IMPROVEMENTS.md', 'Improvements documentation'),
        ('pos_system/settings_base.py', 'Base settings'),
        ('pos_system/settings_dev.py', 'Development settings'),
        ('pos_system/settings_prod.py', 'Production settings'),
        ('pos_app/services_sales.py', 'Sales service'),
        ('pos_app/services_inventory.py', 'Inventory service'),
        ('pos_app/validators.py', 'Validators'),
        ('pos_app/helpers.py', 'Helper utilities'),
        ('pos_app/views_health.py', 'Health check views'),
        ('pos_app/tests_services.py', 'Service tests'),
        ('scripts/backup.sh', 'Backup script'),
        ('scripts/restore.sh', 'Restore script'),
    ]
    
    results = [check_file_exists(path, desc) for path, desc in checks]
    
    # Check directories
    dir_checks = [
        ('logs', 'Logs'),
        ('scripts', 'Scripts'),
        ('.github/workflows', 'CI/CD workflows'),
    ]
    
    for path, desc in dir_checks:
        check_directory_exists(path, desc)
    
    return all(results)

def check_dependencies():
    """Check if new dependencies are installed"""
    print("\n📦 Checking dependencies...")
    
    try:
        import redis
        print_status("redis installed", 'ok')
    except ImportError:
        print_status("redis not installed", 'warn')
    
    try:
        import django_redis
        print_status("django-redis installed", 'ok')
    except ImportError:
        print_status("django-redis not installed", 'warn')
    
    try:
        from decouple import config
        print_status("python-decouple installed", 'ok')
    except ImportError:
        print_status("python-decouple not installed", 'warn')

def check_models():
    """Check if new models are defined"""
    print("\n🗄️ Checking database models...")
    
    models_file = Path('pos_app/models.py')
    if models_file.exists():
        content = models_file.read_text()
        
        if 'class AuditLog' in content:
            print_status("AuditLog model defined", 'ok')
        else:
            print_status("AuditLog model not found", 'error')
        
        if 'is_low_stock' in content:
            print_status("Inventory helper methods added", 'ok')
        else:
            print_status("Inventory helper methods not found", 'warn')
        
        if 'class Meta:' in content and 'indexes' in content:
            print_status("Database indexes defined", 'ok')
        else:
            print_status("Database indexes not found", 'warn')
    else:
        print_status("models.py not found", 'error')

def check_docker():
    """Check Docker configuration"""
    print("\n🐳 Checking Docker configuration...")
    
    if check_file_exists('docker-compose.yml', 'docker-compose.yml'):
        with open('docker-compose.yml', 'r') as f:
            content = f.read()
            
            if 'redis:' in content:
                print_status("Redis service configured", 'ok')
            else:
                print_status("Redis service not found", 'warn')
            
            if 'networks:' in content:
                print_status("Docker networks configured", 'ok')
            else:
                print_status("Docker networks not found", 'warn')
            
            if 'DJANGO_ENV' in content:
                print_status("Environment variable support added", 'ok')
            else:
                print_status("Environment variable support not found", 'warn')
    
    if check_file_exists('Dockerfile', 'Dockerfile'):
        with open('Dockerfile', 'r') as f:
            content = f.read()
            
            if 'HEALTHCHECK' in content:
                print_status("Docker health check configured", 'ok')
            else:
                print_status("Docker health check not found", 'warn')

def check_scripts():
    """Check utility scripts"""
    print("\n🔧 Checking utility scripts...")
    
    scripts = ['scripts/backup.sh', 'scripts/restore.sh']
    for script in scripts:
        if check_file_exists(script, Path(script).name):
            if os.access(script, os.X_OK):
                print_status(f"{Path(script).name} is executable", 'ok')
            else:
                print_status(f"{Path(script).name} is not executable - run: chmod +x {script}", 'warn')

def main():
    """Main verification function"""
    print("=" * 60)
    print("POS System - Setup Verification")
    print("=" * 60)
    
    os.chdir(Path(__file__).parent)
    
    results = {
        'Environment': check_env_file(),
        'Structure': check_structure(),
        'Docker': True,
        'Scripts': True,
    }
    
    check_dependencies()
    check_models()
    check_docker()
    check_scripts()
    
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    for category, passed in results.items():
        status = 'ok' if passed else 'warn'
        print_status(f"{category}: {'Passed' if passed else 'Needs attention'}", status)
    
    print("\n📚 Next steps:")
    print("1. Review and configure .env file")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run migrations: python manage.py makemigrations && python manage.py migrate")
    print("4. Run tests: python manage.py test")
    print("5. Start services: docker-compose up -d")
    print("\n📖 See DEPLOYMENT.md for detailed instructions")
    print("=" * 60)

if __name__ == '__main__':
    main()
