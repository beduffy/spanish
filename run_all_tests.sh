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
$DC_COMMAND up --build -d

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


# A more robust wait: check for a specific log message or port availability if possible.
# For now, a simple sleep is used, but this could be improved.
# Example: Wait for Django migrations to complete in backend
# This is a placeholder; a more robust check would be `docker-compose exec -T backend python manage.py showmigrations --plan | grep -q "\[ \]"`
# or checking if the port is open and responsive.

# Simple sleep for now, can be improved with health checks
SLEEP_SECONDS=15 
echo "Sleeping for $SLEEP_SECONDS seconds to allow services to fully initialize..."
sleep $SLEEP_SECONDS 


# --- Phase 1: Backend Django tests ---
print_message "Phase 1: Backend Django tests"
echo "Running backend Django tests with coverage inside the 'backend' container..."
# The command to run tests and generate coverage.xml. Output will be in /app/coverage.xml inside the container.
$DC_COMMAND exec -T backend coverage run manage.py test flashcards --noinput
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
# Assuming Cypress is installed globally on the host or as a dev dependency in the project root's package.json
# The baseUrl for Cypress tests is configured in cypress.config.js to point to the frontend service (e.g., http://localhost:8080)
# Ensure the frontend service is accessible from the host machine at the configured baseUrl.
# Note: If running in a CI environment without a display, Cypress might need to run in headless mode.
# This is usually handled by Cypress itself or by adding flags like `--headless --browser chrome` or electron (default)

# Change to the frontend directory to run Cypress commands if Cypress is installed there
# Make sure to adjust paths if your Cypress setup is different.
EXPECTED_CYPRESS_PROJECT_PATH="./anki_web_app/spanish_anki_frontend"

if [ -d "$EXPECTED_CYPRESS_PROJECT_PATH" ]; then
    # Temporarily change to the Cypress project directory to run tests
    # This is often necessary if Cypress is installed as a local dev dependency
    # and scripts in package.json refer to `cypress open` or `cypress run`
    echo "Changing to $EXPECTED_CYPRESS_PROJECT_PATH to run Cypress tests..."
    pushd "$EXPECTED_CYPRESS_PROJECT_PATH" > /dev/null
    
    # Run Cypress tests. 
    # `npx cypress run` is generally preferred as it uses the project's version of Cypress.
    # Add `--headless` if not default or if issues occur in CI.
    # Add `--browser chrome` or other browsers if needed.
    # The CYPRESS_BASE_URL is often set in cypress.config.js or via env var.
    # Here, we rely on baseUrl in cypress.config.js pointing to http://localhost:8080 (frontend service)
    npx cypress run # Using npx ensures we use the locally installed Cypress version
    
    # Return to the original directory
    popd > /dev/null
    echo "Cypress E2E tests completed."
else
    echo "Error: Cypress project directory not found at $EXPECTED_CYPRESS_PROJECT_PATH" >&2
    echo "Skipping Cypress E2E tests." >&2
    # Optionally, exit with an error if E2E tests are critical
    # exit 1 
fi


print_message "Bringing down Docker services..."
# Stop and remove containers, networks, volumes, and images created by `up`.
$DC_COMMAND down --remove-orphans

echo "Docker services stopped."
print_message "All tests completed successfully!"

exit 0 