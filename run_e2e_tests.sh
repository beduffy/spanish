#!/bin/bash
# Quick script to run only E2E Cypress tests

set -e

echo "Running E2E Cypress tests..."
echo "------------------------------------"

# Detect docker-compose command
if command -v docker &> /dev/null && docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo "Error: docker-compose or docker compose not found"
    exit 1
fi

# Check if services are running
if ! $DOCKER_COMPOSE ps | grep -q "backend.*Up"; then
    echo "Starting Docker services..."
    $DOCKER_COMPOSE up -d
    echo "Waiting for services to initialize..."
    sleep 15
fi

# Seed E2E data
echo "Seeding E2E test data..."
$DOCKER_COMPOSE exec -T backend python manage.py seed_e2e_data || echo "Warning: seed_e2e_data command may not exist, continuing..."

# Navigate to frontend directory
cd anki_web_app/spanish_anki_frontend

# Run Cypress tests
if [ -z "$1" ]; then
    echo "Running all E2E tests..."
    npx cypress run
else
    echo "Running specific E2E test: $1"
    npx cypress run --spec "$1"
fi

echo ""
echo "E2E tests completed!"
