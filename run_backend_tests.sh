#!/bin/bash
# Quick script to run only backend Django tests

set -e

echo "Running backend Django tests..."
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
    sleep 10
fi

# Run tests
if [ -z "$1" ]; then
    echo "Running all backend tests..."
    $DOCKER_COMPOSE exec -T backend coverage run manage.py test flashcards.tests flashcards.tests_card_functionality flashcards.tests_reader flashcards.tests_study_sessions --noinput
    $DOCKER_COMPOSE exec -T backend coverage xml -o /app/coverage.xml
    echo ""
    echo "Coverage report:"
    $DOCKER_COMPOSE exec -T backend coverage report
else
    echo "Running specific test: $1"
    $DOCKER_COMPOSE exec -T backend python manage.py test "$1" --noinput
fi

echo ""
echo "Backend tests completed!"
