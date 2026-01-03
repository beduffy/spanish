#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

# Define a function for printing styled messages
print_message() {
    echo "------------------------------------"
    echo " $1 "
    echo "------------------------------------"
}

echo "Starting all tests using Docker environment..."

# Ensure DOCKER_HOST is set if not already (useful for some CI environments or local setups)
export DOCKER_HOST=${DOCKER_HOST:-unix:///var/run/docker.sock}

# Prefer Docker Compose V2 plugin (`docker compose`) if available.
# Otherwise, use `docker-compose` if it runs successfully.
if docker compose version >/dev/null 2>&1; then
    DC_COMMAND="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    if docker-compose version >/dev/null 2>&1; then
        DC_COMMAND="docker-compose"
    else
        echo "ERROR: `docker-compose` exists but failed to run."
        echo ""
        echo "Fix options:"
        echo "  - Install Docker Compose v2 plugin (recommended): sudo apt-get install -y docker-compose-plugin"
        echo "  - Or remove the broken Python docker-compose v1 from your PATH and install a newer Compose"
        exit 1
    fi
else
    echo "ERROR: Docker Compose not found."
    echo "Install Docker Compose v2 (recommended):"
    echo "  - Ubuntu/Debian plugin: sudo apt-get install -y docker-compose-plugin"
    exit 1
fi

print_message "Bringing down any existing Docker services..."
$DC_COMMAND down --remove-orphans || echo "No existing services to bring down or an error occurred during down. Continuing..."

print_message "Building and starting Docker services in detached mode..."
# Build and start services in detached mode
# Force rebuild of images to pick up any changes
# Note: SUPABASE_URL and SUPABASE_ANON_KEY warnings are expected in CI (they're optional for backend)
$DC_COMMAND up --build -d

# Wait a moment for containers to start
sleep 3

# Give services a moment to initialize (e.g., database migrations, servers to start)
print_message "Waiting for services to initialize (e.g., database migrations, servers to start)..."
# Wait for backend to be healthy or for a timeout
MAX_WAIT=60 # seconds
INTERVAL=5  # seconds
ELAPSED_TIME=0

# Output some initial logs to help diagnose startup issues
echo "Showing logs for the backend service shortly after startup:"
$DC_COMMAND logs --tail="20" backend || echo "Could not get backend logs yet."
echo "Showing logs for the frontend service shortly after startup:"
$DC_COMMAND logs --tail="20" frontend || echo "Could not get frontend logs yet."


# Wait for services to be ready with health checks
SLEEP_SECONDS=15 
echo "Sleeping for $SLEEP_SECONDS seconds to allow services to fully initialize..."

# Check if backend is running
echo "Checking if backend service is running..."
for i in {1..12}; do
  if $DC_COMMAND ps backend | grep -q "Up"; then
    echo "Backend service is running."
    break
  else
    echo "Waiting for backend service to start... ($i/12)"
    sleep 2
  fi
done

# Verify backend is actually running before proceeding
if ! $DC_COMMAND ps backend | grep -q "Up"; then
  echo "ERROR: Backend service failed to start!"
  echo "Checking backend container status..."
  $DC_COMMAND ps -a | grep backend || true
  echo ""
  echo "Backend logs (last 50 lines):"
  $DC_COMMAND logs --tail="50" backend || true
  echo ""
  echo "Frontend logs (last 20 lines):"
  $DC_COMMAND logs --tail="20" frontend || true
  echo ""
  echo "All services status:"
  $DC_COMMAND ps -a || true
  echo ""
  echo "Trying to start backend manually to see error..."
  $DC_COMMAND up backend 2>&1 | head -30 || true
  exit 1
fi

sleep $SLEEP_SECONDS 


# --- Phase 1: Backend Django tests ---
print_message "Phase 1: Backend Django tests"

# Verify backend is running before attempting tests
if ! $DC_COMMAND ps backend | grep -q "Up"; then
  echo "ERROR: Backend service is not running!"
  echo "Backend logs:"
  $DC_COMMAND logs backend || true
  echo "All services status:"
  $DC_COMMAND ps -a || true
  exit 1
fi

echo "Running backend Django tests with coverage inside the 'backend' container..."
# The command to run tests and generate coverage.xml. Output will be in /app/coverage.xml inside the container.
# Run all test modules: tests.py, tests_card_functionality.py, tests_reader.py, and tests_study_sessions.py
$DC_COMMAND exec -T backend coverage run manage.py test flashcards.tests flashcards.tests_card_functionality flashcards.tests_reader flashcards.tests_study_sessions --noinput
# Generate XML report from coverage data
$DC_COMMAND exec -T backend coverage xml -o /app/coverage.xml
echo "Backend Django tests completed and coverage report generated (coverage.xml in anki_web_app/)."


# --- Phase 1.5: Seed data for E2E tests ---
print_message "Phase 1.5: Seeding database for E2E tests"
echo "Running seed_e2e_data management command inside the 'backend' container..."
$DC_COMMAND exec -T backend python manage.py seed_e2e_data
echo "E2E data seeding completed."


# --- Phase 2: Frontend Unit tests (Jest) ---
print_message "Phase 2: Frontend Unit tests (Jest)"
echo "Running frontend unit tests (Jest) inside the 'frontend' container..."
# The frontend service in docker-compose.yml should be using the 'build-stage' which has Node installed.
$DC_COMMAND exec -T frontend npm run test:unit
echo "Frontend unit tests completed."


# --- Phase 3: Frontend E2E tests (Cypress) ---
print_message "Phase 3: Frontend E2E tests (Cypress)"
echo "Running frontend E2E tests (Cypress) from host against Dockerized frontend..."
# The baseUrl for Cypress tests is configured in cypress.config.js to point to the frontend service (e.g., http://localhost:8080)
# Ensure the frontend service is accessible from the host machine at the configured baseUrl.
# Cypress runs in headless mode for CI environments.

EXPECTED_CYPRESS_PROJECT_PATH="./anki_web_app/spanish_anki_frontend"
if [ -d "$EXPECTED_CYPRESS_PROJECT_PATH" ]; then
    echo "Changing to $EXPECTED_CYPRESS_PROJECT_PATH to run Cypress tests..."
    pushd "$EXPECTED_CYPRESS_PROJECT_PATH" > /dev/null
    
    # Check if Cypress is installed, if not install it
    if ! command -v npx &> /dev/null || ! npx cypress version &> /dev/null; then
        echo "Cypress not found, installing dependencies..."
        npm install
    fi
    
    # Run Cypress tests in headless mode
    npx cypress run --headless || {
        echo "Cypress tests failed or Cypress not available"
        echo "If Cypress is not installed, you can skip E2E tests or install it:"
        echo "  cd $EXPECTED_CYPRESS_PROJECT_PATH && npm install"
        popd > /dev/null
        exit 1
    }
    
    popd > /dev/null
    echo "Cypress E2E tests completed."
else
    echo "WARNING: Cypress project path not found: $EXPECTED_CYPRESS_PROJECT_PATH"
    echo "Skipping E2E tests."
fi


print_message "Bringing down Docker services..."
# Stop and remove containers, networks, volumes, and images created by `up`.
$DC_COMMAND down --remove-orphans

echo "Docker services stopped."
print_message "All tests completed successfully!"

exit 0 