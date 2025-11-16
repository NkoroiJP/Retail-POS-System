#!/bin/bash
# Quick Migration Fix Script
# Run this to apply the database changes for receipt enhancements

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         POS System - Database Migration Script            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found. Please run this script from the project root."
    exit 1
fi

echo "📋 Checking environment..."
echo ""

# Check if Docker is being used
if docker compose ps > /dev/null 2>&1; then
    echo "🐳 Docker detected - Using Docker environment"
    echo ""
    echo "🔄 Applying migrations in Docker container..."
    docker compose exec web python manage.py migrate
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Migrations applied successfully in Docker!"
        echo ""
        echo "📝 IMPORTANT: Update your stores with:"
        echo "   1. Tax ID / VAT Number"
        echo "   2. Website URL"
        echo "   3. Return Policy Days (default: 7)"
        echo ""
        echo "You can do this via:"
        echo "   • Django Admin: http://0.0.0.0:8000/admin/"
        echo "   • Or run: docker compose exec web python manage.py shell"
        echo ""
        echo "✅ Receipt enhancements are now active!"
        echo "   • Receipt numbers are shortened (8 characters)"
        echo "   • Payment method field added"
        echo "   • All mandatory information included"
        echo ""
        echo "📚 See DOCKER_COMMANDS.md for more Docker commands"
    else
        echo ""
        echo "❌ Migration failed in Docker. Please check the error above."
        exit 1
    fi
elif [ -d "venv" ]; then
    echo "🐍 Virtual environment detected - Using venv"
    echo ""
    echo "🔄 Applying migrations..."
    source venv/bin/activate
    python manage.py migrate
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Migrations applied successfully!"
        echo ""
        echo "📝 IMPORTANT: Update your stores with:"
        echo "   1. Tax ID / VAT Number"
        echo "   2. Website URL"
        echo "   3. Return Policy Days (default: 7)"
        echo ""
        echo "You can do this via:"
        echo "   • Django Admin: http://your-domain/admin/"
        echo "   • Or run: python manage.py shell"
        echo ""
        echo "✅ Receipt enhancements are now active!"
        echo "   • Receipt numbers are shortened (8 characters)"
        echo "   • Payment method field added"
        echo "   • All mandatory information included"
    else
        echo ""
        echo "❌ Migration failed. Please check the error above."
        exit 1
    fi
else
    echo "⚠️  No Docker or venv detected. Trying direct Python..."
    echo ""
    echo "🔄 Applying migrations..."
    python3 manage.py migrate
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Migrations applied successfully!"
        echo ""
        echo "📝 IMPORTANT: Update your stores with:"
        echo "   1. Tax ID / VAT Number"
        echo "   2. Website URL"
        echo "   3. Return Policy Days (default: 7)"
    else
        echo ""
        echo "❌ Migration failed."
        echo ""
        echo "Common fixes:"
        echo "   1. If using Docker: Run 'docker compose exec web python manage.py migrate'"
        echo "   2. If using venv: Run 'source venv/bin/activate && python manage.py migrate'"
        echo "   3. Check database connection and credentials"
        exit 1
    fi
fi
