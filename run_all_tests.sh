#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

echo "Starting all tests using Docker environment..."

# Ensure we are in the project root where docker-compose.yml is located
# This script assumes it's being run from the project root: /home/ben/all_projects/spanish/
PROJECT_ROOT=$(pwd) # Or set this to your project root if running from elsewhere

# Cleanup previous runs, if any (optional, but good practice)
echo "Bringing down any existing Docker services..."
docker-compose down -v --remove-orphans

echo ""
echo "Building and starting Docker services in detached mode..."
docker-compose up -d --build
echo "Services started by docker-compose up -d."

echo ""
echo "Showing logs for the backend service shortly after startup:"
docker-compose logs --tail="50" backend # Show last 50 log lines for backend
echo ""
echo "Showing logs for the frontend service shortly after startup:"
docker-compose logs --tail="50" frontend # Show last 50 log lines for frontend

echo ""
echo "Waiting for services to initialize (e.g., database migrations, servers to start)..."
# You might need to adjust this sleep duration or implement a more robust health check
sleep 15 # Give services ~15 seconds to start up

# Trap to ensure docker-compose down is called on script exit (success, error, or interrupt)
cleanup() {
    echo ""
    echo "Bringing down Docker services..."
    docker-compose down -v --remove-orphans
    echo "Docker services stopped."
}
trap cleanup EXIT

echo ""
echo "------------------------------------"
echo " Phase 1: Backend Django tests      "
echo "------------------------------------"
echo "Running backend Django tests with coverage inside the 'backend' container..."
# Ensure manage.py is executable and at the correct path within the container context (/app/)
docker-compose exec -T backend sh -c "coverage run manage.py test && coverage xml -o /app/coverage.xml"
BACKEND_TEST_STATUS=$?
if [ $BACKEND_TEST_STATUS -eq 0 ]; then
    echo "Backend Django tests completed and coverage report generated (coverage.xml in anki_web_app/)."
else
    echo "Backend Django tests FAILED."
fi
# Copy coverage file out if needed, though volume mount should make it available in ./anki_web_app/coverage.xml

echo ""
echo "----------------------------------------"
echo " Phase 2: Frontend Unit tests (Jest)  "
echo "----------------------------------------"
echo "Running frontend unit tests (Jest) inside the 'frontend' container..."
docker-compose exec -T frontend npm run test:unit
FRONTEND_UNIT_TEST_STATUS=$?
if [ $FRONTEND_UNIT_TEST_STATUS -eq 0 ]; then
    echo "Frontend unit tests completed."
else
    echo "Frontend unit tests FAILED."
fi

echo ""
echo "-----------------------------------------"
echo " Phase 3: Frontend E2E tests (Cypress) "
echo "-----------------------------------------"
echo "Running frontend E2E tests (Cypress) from host against Dockerized frontend..."
# This assumes Cypress is installed on the host and configured to run against http://localhost:8080
# The frontend container (running `npm run serve`) will proxy API calls to the backend container.
(cd anki_web_app/spanish_anki_frontend && npx cypress run)
FRONTEND_E2E_TEST_STATUS=$?
if [ $FRONTEND_E2E_TEST_STATUS -eq 0 ]; then
    echo "Frontend E2E tests completed."
else
    echo "Frontend E2E tests FAILED."
fi

echo ""
echo "------------------------------------"
echo " All test suites executed.          "
echo "------------------------------------"

# Final status check
if [ $BACKEND_TEST_STATUS -ne 0 ] || [ $FRONTEND_UNIT_TEST_STATUS -ne 0 ] || [ $FRONTEND_E2E_TEST_STATUS -ne 0 ]; then
    echo "One or more test suites FAILED!"
    exit 1
else
    echo "All tests PASSED successfully in Docker environment!"
    exit 0
fi 