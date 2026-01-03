#!/bin/bash
# Check and fix TokenStatus migration issue

set -e

echo "=== Checking TokenStatus Migration Status ==="
echo ""

cd anki_web_app

# Check if we're in a Docker environment
if [ -f "/.dockerenv" ] || [ -n "$DOCKER_CONTAINER" ]; then
    echo "Running in Docker container"
    PYTHON_CMD="python"
else
    echo "Running on host (need Django environment)"
    PYTHON_CMD="python3"
fi

echo ""
echo "1. Checking if migration file exists..."
if [ -f "flashcards/migrations/0011_add_token_status.py" ]; then
    echo "   ✓ Migration file exists"
else
    echo "   ✗ Migration file missing!"
    exit 1
fi

echo ""
echo "2. Checking migration status..."
if command -v $PYTHON_CMD &> /dev/null; then
    if $PYTHON_CMD -c "import django" &> /dev/null; then
        echo "   Django is available"
        echo ""
        echo "   To apply migration, run:"
        echo "   $PYTHON_CMD manage.py migrate flashcards"
        echo ""
        echo "   Or if using Docker:"
        echo "   docker-compose exec backend python manage.py migrate flashcards"
    else
        echo "   Django not available in current environment"
        echo ""
        echo "   To apply migration:"
        echo "   1. Activate your Django environment (conda/venv)"
        echo "   2. Run: python manage.py migrate flashcards"
        echo ""
        echo "   Or if using Docker:"
        echo "   docker-compose exec backend python manage.py migrate flashcards"
    fi
else
    echo "   Python not found"
fi

echo ""
echo "3. Code changes made to handle missing table gracefully:"
echo "   ✓ TokenSerializer.get_status() now catches OperationalError/ProgrammingError"
echo "   ✓ Returns None if TokenStatus table doesn't exist"
echo "   ✓ Prevents 500 errors when migration not applied"
echo ""
echo "=== Summary ==="
echo "The code will now work even if migration isn't applied (status will be None)."
echo "To enable TokenStatus feature, run the migration as shown above."
