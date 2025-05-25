#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

# --- Configuration ---
# These can be overridden by environment variables or modified directly here.
DOCKER_REGISTRY="${DOCKER_REGISTRY:-}" # Your Docker registry prefix (e.g., "yourusername" or "yourorg/project")
BACKEND_IMAGE_NAME="${BACKEND_IMAGE_NAME:-anki_backend}"
FRONTEND_IMAGE_NAME="${FRONTEND_IMAGE_NAME:-anki_frontend}"

# Dockerfile locations (relative to project root)
BACKEND_DOCKERFILE_PATH="anki_web_app/Dockerfile" # Assuming Dockerfile is in anki_web_app
FRONTEND_DOCKERFILE_PATH="anki_web_app/spanish_anki_frontend/Dockerfile" # Assuming Dockerfile is in spanish_anki_frontend for a multi-stage build

# Build contexts (relative to project root)
# The build context is usually the directory containing the Dockerfile and the application code.
BACKEND_BUILD_CONTEXT="anki_web_app"
FRONTEND_BUILD_CONTEXT="anki_web_app/spanish_anki_frontend"


# --- Script Logic ---
VERSION_TAG="${1:-latest}" # Use the first argument as the version tag, or default to "latest"

echo "Building Docker images with version tag: $VERSION_TAG"

# Construct full image names
if [ -n "$DOCKER_REGISTRY" ]; then
    FULL_BACKEND_IMAGE_NAME="${DOCKER_REGISTRY}/${BACKEND_IMAGE_NAME}"
    FULL_FRONTEND_IMAGE_NAME="${DOCKER_REGISTRY}/${FRONTEND_IMAGE_NAME}"
else
    FULL_BACKEND_IMAGE_NAME="${BACKEND_IMAGE_NAME}"
    FULL_FRONTEND_IMAGE_NAME="${FRONTEND_IMAGE_NAME}"
fi

# --- Build Backend Image ---
echo ""
echo "Building Backend image: ${FULL_BACKEND_IMAGE_NAME}:${VERSION_TAG}"
echo "Dockerfile: ${BACKEND_DOCKERFILE_PATH}"
echo "Build context: ${BACKEND_BUILD_CONTEXT}"
echo ""

if [ ! -f "${BACKEND_BUILD_CONTEXT}/${BACKEND_DOCKERFILE_PATH}" ] && [ ! -f "${BACKEND_DOCKERFILE_PATH}" ]; then
    if [ -f "${BACKEND_BUILD_CONTEXT}/Dockerfile" ]; then
        echo "Using Dockerfile at ${BACKEND_BUILD_CONTEXT}/Dockerfile for backend."
        ACTUAL_BACKEND_DOCKERFILE_PATH="${BACKEND_BUILD_CONTEXT}/Dockerfile"
    elif [ -f "Dockerfile.backend" ]; then # Common naming convention
        echo "Using Dockerfile.backend for backend."
        ACTUAL_BACKEND_DOCKERFILE_PATH="Dockerfile.backend"
    else
        echo "Error: Backend Dockerfile not found at expected paths: ${BACKEND_DOCKERFILE_PATH} or ${BACKEND_BUILD_CONTEXT}/Dockerfile or Dockerfile.backend"
        exit 1
    fi
else
    # Prefer explicit path if it exists, otherwise assume it's relative to context
    if [ -f "${BACKEND_DOCKERFILE_PATH}" ]; then
      ACTUAL_BACKEND_DOCKERFILE_PATH="${BACKEND_DOCKERFILE_PATH}"
    else
      ACTUAL_BACKEND_DOCKERFILE_PATH="${BACKEND_BUILD_CONTEXT}/${BACKEND_DOCKERFILE_PATH}"
    fi
fi


docker build -t "${FULL_BACKEND_IMAGE_NAME}:${VERSION_TAG}" -f "${ACTUAL_BACKEND_DOCKERFILE_PATH}" "${BACKEND_BUILD_CONTEXT}"

if [ "$VERSION_TAG" == "latest" ]; then
    docker tag "${FULL_BACKEND_IMAGE_NAME}:latest" "${FULL_BACKEND_IMAGE_NAME}:latest"
fi

# --- Build Frontend Image ---
# This assumes a multi-stage Dockerfile for the frontend that builds the Vue app
# and then sets up Nginx to serve it.
echo ""
echo "Building Frontend (Nginx + Vue app) image: ${FULL_FRONTEND_IMAGE_NAME}:${VERSION_TAG}"
echo "Dockerfile: ${FRONTEND_DOCKERFILE_PATH}"
echo "Build context: ${FRONTEND_BUILD_CONTEXT}"
echo ""

if [ ! -f "${FRONTEND_BUILD_CONTEXT}/${FRONTEND_DOCKERFILE_PATH}" ] && [ ! -f "${FRONTEND_DOCKERFILE_PATH}" ]; then
    if [ -f "${FRONTEND_BUILD_CONTEXT}/Dockerfile" ]; then
        echo "Using Dockerfile at ${FRONTEND_BUILD_CONTEXT}/Dockerfile for frontend."
        ACTUAL_FRONTEND_DOCKERFILE_PATH="${FRONTEND_BUILD_CONTEXT}/Dockerfile"
    elif [ -f "Dockerfile.frontend" ]; then # Common naming convention
        echo "Using Dockerfile.frontend for frontend."
        ACTUAL_FRONTEND_DOCKERFILE_PATH="Dockerfile.frontend"
    else
        echo "Error: Frontend Dockerfile not found at expected paths: ${FRONTEND_DOCKERFILE_PATH} or ${FRONTEND_BUILD_CONTEXT}/Dockerfile or Dockerfile.frontend"
        exit 1
    fi
else
    if [ -f "${FRONTEND_DOCKERFILE_PATH}" ]; then
      ACTUAL_FRONTEND_DOCKERFILE_PATH="${FRONTEND_DOCKERFILE_PATH}"
    else
      ACTUAL_FRONTEND_DOCKERFILE_PATH="${FRONTEND_BUILD_CONTEXT}/${FRONTEND_DOCKERFILE_PATH}"
    fi
fi

docker build -t "${FULL_FRONTEND_IMAGE_NAME}:${VERSION_TAG}" -f "${ACTUAL_FRONTEND_DOCKERFILE_PATH}" "${FRONTEND_BUILD_CONTEXT}"

if [ "$VERSION_TAG" == "latest" ]; then
    docker tag "${FULL_FRONTEND_IMAGE_NAME}:latest" "${FULL_FRONTEND_IMAGE_NAME}:latest"
fi

echo ""
echo "Build complete."
echo "Backend image: ${FULL_BACKEND_IMAGE_NAME}:${VERSION_TAG}"
echo "Frontend image: ${FULL_FRONTEND_IMAGE_NAME}:${VERSION_TAG}"

# --- Optional: Push images to Docker Registry ---
if [ -n "$DOCKER_REGISTRY" ]; then
    echo ""
    echo "Pushing images to Docker Hub registry: $DOCKER_REGISTRY"
    
    echo "Pushing ${FULL_BACKEND_IMAGE_NAME}:${VERSION_TAG}"
    docker push "${FULL_BACKEND_IMAGE_NAME}:${VERSION_TAG}"
    
    echo "Pushing ${FULL_FRONTEND_IMAGE_NAME}:${VERSION_TAG}"
    docker push "${FULL_FRONTEND_IMAGE_NAME}:${VERSION_TAG}"
    
    if [ "$VERSION_TAG" != "latest" ]; then
        echo "Pushing ${FULL_BACKEND_IMAGE_NAME}:latest (as alias for $VERSION_TAG)"
        docker tag "${FULL_BACKEND_IMAGE_NAME}:${VERSION_TAG}" "${FULL_BACKEND_IMAGE_NAME}:latest"
        docker push "${FULL_BACKEND_IMAGE_NAME}:latest"

        echo "Pushing ${FULL_FRONTEND_IMAGE_NAME}:latest (as alias for $VERSION_TAG)"
        docker tag "${FULL_FRONTEND_IMAGE_NAME}:${VERSION_TAG}" "${FULL_FRONTEND_IMAGE_NAME}:latest"
        docker push "${FULL_FRONTEND_IMAGE_NAME}:latest"
    fi
    echo "Push complete."
else
    echo ""
    echo "DOCKER_REGISTRY not set. Skipping push to registry."
    echo "To push images, set the DOCKER_REGISTRY environment variable (e.g., your Docker Hub username)."
fi

echo ""
echo "Script finished."
