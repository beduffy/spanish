#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

# --- Configuration ---
# These can be overridden by environment variables or modified directly here.
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-}" # Your Docker registry prefix (e.g., "yourusername" or "yourorg/project")
BACKEND_IMAGE_NAME="${BACKEND_IMAGE_NAME:-anki_backend}"
FRONTEND_IMAGE_NAME="${FRONTEND_IMAGE_NAME:-anki_frontend}"

# --- Script Logic ---
VERSION_TAG="${1:-latest}" # Use the first argument as the version tag, or default to "latest"

echo "Deploying application with version tag: $VERSION_TAG"

# Export variables for docker-compose.prod.yml to use
export BACKEND_TAG="$VERSION_TAG"
export FRONTEND_TAG="$VERSION_TAG"
export DOCKER_REGISTRY # Pass DOCKER_REGISTRY through
export BACKEND_IMAGE_NAME # Pass backend image name through
export FRONTEND_IMAGE_NAME # Pass frontend image name through


# Check if the Docker Compose file exists
if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    echo "Error: Docker Compose file '$DOCKER_COMPOSE_FILE' not found."
    exit 1
fi

# Stop any currently running services defined in the compose file
echo ""
echo "Stopping current services (if any)..."
docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans # --remove-orphans is good practice

# Optional: Pull new images from the registry
if [ -n "$DOCKER_REGISTRY" ]; then
    echo ""
    echo "Pulling images from Docker Hub registry: $DOCKER_REGISTRY with tag $VERSION_TAG..."
    
    FULL_BACKEND_IMAGE="${DOCKER_REGISTRY}/${BACKEND_IMAGE_NAME}:${VERSION_TAG}"
    FULL_FRONTEND_IMAGE="${DOCKER_REGISTRY}/${FRONTEND_IMAGE_NAME}:${VERSION_TAG}"

    echo "Pulling $FULL_BACKEND_IMAGE"
    docker pull "$FULL_BACKEND_IMAGE"
    
    echo "Pulling $FULL_FRONTEND_IMAGE"
    docker pull "$FULL_FRONTEND_IMAGE"
    
    # If deploying a specific version (not 'latest'), and you also pushed 'latest' aliases during build:
    if [ "$VERSION_TAG" != "latest" ]; then
        echo "Pulling latest alias for $FULL_BACKEND_IMAGE (if exists)"
        docker pull "${DOCKER_REGISTRY}/${BACKEND_IMAGE_NAME}:latest" || echo "Info: latest tag for backend not found or up-to-date."
        echo "Pulling latest alias for $FULL_FRONTEND_IMAGE (if exists)"
        docker pull "${DOCKER_REGISTRY}/${FRONTEND_IMAGE_NAME}:latest" || echo "Info: latest tag for frontend not found or up-to-date."
    fi
    echo "Image pull complete (or attempted)."
else
    echo ""
    echo "DOCKER_REGISTRY not set. Assuming images are available locally."
fi

# Start the application services
echo ""
echo "Starting application services using $DOCKER_COMPOSE_FILE with tag $VERSION_TAG..."
docker-compose -f "$DOCKER_COMPOSE_FILE" up -d --remove-orphans

echo ""
echo "Deployment complete for version: $VERSION_TAG"
echo "Services started. Use 'docker-compose -f $DOCKER_COMPOSE_FILE logs -f' to view logs."

# Unset exported variables (optional, for cleanliness if script is sourced)
unset BACKEND_TAG
unset FRONTEND_TAG
# DOCKER_REGISTRY, BACKEND_IMAGE_NAME, FRONTEND_IMAGE_NAME are passed by environment, so might not need unsetting if script not sourced.

echo ""
echo "Script finished."
