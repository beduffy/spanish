#!/bin/bash
set -e

echo "WARNING: This script will attempt to stop and remove ALL Docker containers on your system."
read -p "Are you sure you want to continue? (y/N): " confirmation

if [[ "$confirmation" != "y" && "$confirmation" != "Y" ]]; then
    echo "Operation cancelled by user."
    exit 0
fi

echo ""
echo "Stopping all running Docker containers..."
# Get IDs of all running containers and stop them.
# The `docker ps -q` command lists only the IDs of running containers.
# If no containers are running, `docker ps -q` will be empty, and `docker stop` will do nothing.
docker ps -q | xargs -r docker stop

echo ""
echo "Removing all Docker containers (running and stopped)..."
# Get IDs of all containers (running or stopped) and remove them.
# The `docker ps -a -q` command lists IDs of all containers.
# If no containers exist, `docker ps -a -q` will be empty, and `docker rm` will do nothing.
docker ps -a -q | xargs -r docker rm

echo ""
echo "All specified Docker containers have been stopped and removed."
echo "You can also consider running 'docker system prune -a' to remove unused images, networks, and volumes, but use with caution." 