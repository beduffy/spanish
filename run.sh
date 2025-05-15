#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

echo "Starting backend and frontend services using Docker environment..."

# Ensure we are in the project root where docker-compose.yml is located
# This script assumes it's being run from the project root.
# If your docker-compose.yml is elsewhere, adjust PROJECT_ROOT or cd accordingly.
PROJECT_ROOT=$(pwd)

# Use docker-compose (v1, hyphenated) command
# If you use Docker Compose V2 (docker compose), change this to "docker compose"
DC_COMMAND="docker-compose"

# Cleanup previous runs, if any (optional, but good practice)
echo ""
echo "Bringing down any existing Docker services to ensure a clean start..."
$DC_COMMAND down -v # Using -v for volume removal.

echo ""
echo "Building and starting Docker services in detached mode..."
# --build flag ensures images are rebuilt if Dockerfiles or context changes.
# -d flag runs containers in the background.
$DC_COMMAND up -d --build
echo "Services have been started by '$DC_COMMAND up -d --build'."

echo ""
echo "Backend and frontend services should now be running in the background."
echo "You can view combined logs using: $DC_COMMAND logs -f"
echo "Or view logs for a specific service, e.g., for backend: $DC_COMMAND logs -f backend"
echo "Or for frontend: $DC_COMMAND logs -f frontend"
echo ""
echo "To stop the services, run: $DC_COMMAND down -v"
echo ""
echo "Script finished. Services remain running in detached mode." 