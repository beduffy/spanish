# Deployment Guide: Anki-Style Spanish Learning App

## 1. Introduction

This guide provides step-by-step instructions for deploying the Anki-Style Spanish Learning App to a production environment. The application utilizes Docker and Docker Compose for containerization, with Nginx serving the frontend and acting as a reverse proxy for the Django backend API.

**Technology Stack:**
-   **Docker:** For containerizing the application components.
-   **Docker Compose:** For defining and managing multi-container Docker applications.
-   **Nginx:** As a web server for the Vue.js frontend and a reverse proxy for the Django API.
-   **Django:** Python web framework for the backend API.
-   **Vue.js:** JavaScript framework for the frontend user interface.
-   **SQLite:** Default database (can be configured for PostgreSQL or other databases).

## 2. Prerequisites

### Server Setup
-   **Recommended OS:** Ubuntu 20.04 LTS or 22.04 LTS. Other Linux distributions should work but commands might vary.
-   **User:** A non-root user with `sudo` privileges.

### Software Installation
-   **`git`:** For cloning the repository.
    ```bash
    sudo apt update
    sudo apt install git
    ```
-   **Docker:** Install Docker Engine. Follow the official Docker installation guide for your OS: [Install Docker Engine](https://docs.docker.com/engine/install/).
    After installation, add your user to the `docker` group to run Docker commands without `sudo`:
    ```bash
    sudo usermod -aG docker ${USER}
    # Log out and log back in for this change to take effect.
    ```
-   **Docker Compose:** Install Docker Compose. Follow the official guide: [Install Docker Compose](https://docs.docker.com/compose/install/).
    Example for Linux:
    ```bash
    # Check the latest release version on the Docker Compose GitHub page
    LATEST_COMPOSE_VERSION="v2.24.6" # Example, replace with actual latest version
    sudo curl -L "https://github.com/docker/compose/releases/download/${LATEST_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    # Verify installation
    docker-compose --version
    ```
-   **Nginx:** For serving the frontend and reverse proxying.
    ```bash
    sudo apt update
    sudo apt install nginx
    ```
    Ensure your firewall allows HTTP (port 80) and HTTPS (port 443) traffic:
    ```bash
    sudo ufw allow 'Nginx Full'
    sudo ufw enable # If ufw is not already enabled
    ```

### Domain Name (Optional but Recommended)
-   A registered domain name (e.g., `your_domain.com`) pointing to your server's public IP address via DNS A records. This is essential for HTTPS setup with Let's Encrypt.

## 3. Repository Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url> # Replace <repository_url> with the actual URL
    ```
2.  **Navigate into the project directory:**
    ```bash
    cd <repository_name> # Replace <repository_name> with the cloned directory name
    ```

## 4. Configuration

### Backend (Django)

1.  **Create a `.env` file:**
    This file stores sensitive configuration for the Django backend. It should be placed in a location accessible at runtime by the Django application, typically alongside `docker-compose.yml` or within the `anki_web_app/` directory if your `docker-compose.yml` is in the root. The `docker-compose.yml` should specify `env_file` for the backend service.

    Example location: `./.env` (in the project root) or `anki_web_app/.env`.

2.  **Populate `.env` with essential environment variables:**

    ```ini
    # .env

    # Generate a strong secret key.
    # You can use Python: from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())
    # Or an online generator.
    SECRET_KEY='your_strong_random_secret_key_here'

    # Set DEBUG to False for production.
    DEBUG=False

    # List of allowed hosts (your domain(s) and IP address if needed temporarily).
    # Example: your_domain.com,www.your_domain.com
    ALLOWED_HOSTS='your_domain.com,www.your_domain.com,your_server_ip'

    # Database Configuration
    # For the default SQLite, the path is usually relative to BASE_DIR in settings.py.
    # If using SQLite, ensure the volume mount for the database file (e.g., /app/db/app.db)
    # in docker-compose.yml has correct permissions for the user inside the Docker container (often www-data or a specific UID/GID).
    # DATABASE_URL=sqlite:///db/app.db # Example for SQLite if settings.py uses dj-database-url

    # If using PostgreSQL or another external database:
    # DATABASE_URL='postgres://user:password@host:port/dbname'
    # Ensure the backend container can reach this database.

    # Other variables your app might need:
    # DJANGO_LOG_LEVEL=INFO
    ```
    **Important:** Ensure the `.env` file is included in your `.gitignore` to prevent committing sensitive information.

3.  **Code Mounting vs. Image Builds:**
    The `docker-compose.yml` might mount the Django app code directly for development. For production, it's better to build a specific tagged Docker image containing your application code. This ensures consistency and aligns with best practices for releases. (This will be detailed further in a "Release Tagging and Strategy" document.)

### Nginx

1.  **Copy the Nginx configuration file:**
    The project includes a production-ready Nginx configuration at `anki_web_app/nginx.prod.conf`. Copy this to Nginx's `sites-available` directory.
    ```bash
    sudo cp anki_web_app/nginx.prod.conf /etc/nginx/sites-available/anki_app
    ```

2.  **Create a symbolic link to `sites-enabled`:**
    This enables the site configuration.
    ```bash
    sudo ln -s /etc/nginx/sites-available/anki_app /etc/nginx/sites-enabled/
    ```
    Ensure there isn't a default Nginx configuration symlink in `sites-enabled` that might conflict (e.g., `/etc/nginx/sites-enabled/default`). If it exists, you might want to remove it:
    ```bash
    # sudo rm /etc/nginx/sites-enabled/default # Optional, if it conflicts
    ```

3.  **Update `server_name`:**
    Edit the Nginx configuration file to include your actual domain name(s).
    ```bash
    sudo nano /etc/nginx/sites-available/anki_app
    ```
    Change the line:
    `server_name example.com www.example.com;`
    to:
    `server_name your_domain.com www.your_domain.com;`

4.  **Test Nginx configuration:**
    Verify that the configuration syntax is correct.
    ```bash
    sudo nginx -t
    ```
    If successful, you should see a message like:
    `nginx: the configuration file /etc/nginx/nginx.conf syntax is ok`
    `nginx: configuration file /etc/nginx/nginx.conf test is successful`

5.  **Reload Nginx:**
    Apply the changes by reloading Nginx.
    ```bash
    sudo systemctl reload nginx
    ```

### Frontend Build

The `anki_web_app/nginx.prod.conf` assumes that the built Vue.js static files are available in a directory like `/var/www/frontend_dist` *inside the Nginx container*. How these files get there depends on your `docker-compose.yml` and `Dockerfile` for the Nginx service.

**Ideal Approach (Multi-stage Docker build):**
The best practice is to use a multi-stage Dockerfile for your Nginx service.
-   **Stage 1:** Uses a Node.js image to install dependencies (`npm install`) and build the Vue.js application (`npm run build`).
-   **Stage 2:** Uses an Nginx image and copies the built static files from Stage 1 (e.g., from `/app/dist` in Stage 1 to `/var/www/frontend_dist` in Stage 2).
This creates a self-contained Nginx image with the frontend assets. The `docker-compose.yml` would then simply use this image for the Nginx service.

**Alternative (Manual Build on Server - Less Ideal for Production):**
If your Docker setup for Nginx expects the built files to be volume-mounted from the host, you would need to build them on the server first:
```bash
# Navigate to your Vue.js frontend directory
cd anki_web_app/spanish_anki_frontend

# Install dependencies
npm install

# Build for production
npm run build

# Navigate back to the project root
cd ../..
```
Then, your `docker-compose.yml` would need a volume mount for the Nginx service, like:
```yaml
# Example snippet in docker-compose.yml for Nginx service
services:
  nginx: # Or whatever you name your Nginx service
    # ... other Nginx service config ...
    volumes:
      - ./anki_web_app/spanish_anki_frontend/dist:/var/www/frontend_dist:ro # Mount built files
      # ... other volumes ...
```
Ensure the `root` directive in `anki_web_app/nginx.prod.conf` matches the target path in the Nginx container (e.g., `/var/www/frontend_dist`).

## 5. Building and Running with Docker Compose

1.  **Build Docker images (if not pulling pre-built images from a registry):**
    If your `docker-compose.yml` defines services that need to be built from Dockerfiles in your project:
    ```bash
    docker-compose build
    ```

2.  **Start the application:**
    Run the services in detached mode (`-d`).
    ```bash
    docker-compose up -d
    ```
    This will start all services defined in your `docker-compose.yml` (typically the Django backend and the Nginx frontend/proxy).

3.  **Viewing logs:**
    To check the logs of the running containers (useful for troubleshooting):
    ```bash
    docker-compose logs -f
    ```
    You can also view logs for specific services:
    ```bash
    docker-compose logs -f backend
    docker-compose logs -f nginx # Or your Nginx service name
    ```

4.  **Stopping the application:**
    To stop all services:
    ```bash
    docker-compose down
    ```
    To stop and remove volumes (use with caution, as this will delete data like the SQLite database if it's in a named volume not persisted elsewhere):
    ```bash
    # docker-compose down -v
    ```

## 6. Initial Data Import

The application requires an initial data import from a CSV file using a Django management command.

1.  **Place your CSV file:**
    Make sure your CSV data file (e.g., `your_data.csv`) is accessible to the backend container. The easiest way is to place it on the host machine and mount it as a volume or copy it into the container.
    If you use a volume mount, you might add this to your `backend` service in `docker-compose.yml`:
    ```yaml
    # Example snippet in docker-compose.yml for backend service
    services:
      backend:
        # ... other backend service config ...
        volumes:
          - ./path_on_host/your_data.csv:/app/your_data.csv:ro # Mount the CSV
          # ... other volumes ...
    ```
    Replace `./path_on_host/your_data.csv` with the actual path to your CSV file on the host. The path `/app/your_data.csv` is where it will appear inside the container.

2.  **Run the `import_csv` management command:**
    Use `docker-compose exec` to run the command inside the running `backend` container.
    ```bash
    docker-compose exec backend python manage.py import_csv /app/your_data.csv
    ```
    (Adjust `/app/your_data.csv` if you used a different target path in your volume mount or if the default location within the container is different.)

    The command should output progress or success/error messages.

## 7. Setting up HTTPS (SSL/TLS with Let's Encrypt)

Using HTTPS is crucial for production to secure data in transit. Certbot with Let's Encrypt provides free SSL/TLS certificates.

1.  **Install Certbot and the Nginx plugin:**
    ```bash
    sudo apt install certbot python3-certbot-nginx
    ```

2.  **Obtain an SSL certificate:**
    Run Certbot, specifying your domain(s). Certbot will automatically detect your Nginx configuration for the specified domains and offer to modify it for HTTPS.
    ```bash
    sudo certbot --nginx -d your_domain.com -d www.your_domain.com
    ```
    Follow the on-screen prompts. Choose the option to redirect HTTP traffic to HTTPS.

3.  **Verify Auto-Renewal:**
    Certbot typically sets up a cron job or systemd timer for automatic certificate renewal. You can test the renewal process:
    ```bash
    sudo certbot renew --dry-run
    ```
    If this works, your certificates will auto-renew. Nginx will also be reloaded automatically by Certbot after a successful renewal.

## 8. Updating the Application

(This section provides a brief overview. A more detailed update strategy, including release tagging and blue/green deployments, should be covered in a separate "Release Strategy" document.)

1.  **Pull the latest code changes:**
    ```bash
    git pull origin main # Or your production branch
    ```

2.  **Rebuild Docker images (if code changes affect the build):**
    ```bash
    docker-compose build
    ```
    This is necessary if you've updated application code, dependencies, or Dockerfiles.

3.  **Restart services:**
    `docker-compose up -d` will recreate containers whose images have changed or whose configuration has been updated.
    ```bash
    docker-compose up -d
    ```
    For changes that only involve restarting (e.g., environment variable changes that don't require a rebuild), you can sometimes just restart specific services:
    ```bash
    # docker-compose restart backend
    ```
    However, `docker-compose up -d` is generally safer for applying all changes.

## 9. Troubleshooting

-   **Port Conflicts:**
    *   Ensure Nginx (port 80/443 on the host) or other services are not conflicting with existing applications using these ports.
    *   Use `sudo ss -tulnp | grep ':80\|:443'` to check port usage.
-   **File Permissions:**
    *   **Docker Volumes:** If using volume mounts (especially for the SQLite database or static files), ensure the user inside the Docker container has the necessary read/write permissions to the mounted directories/files on the host. This can sometimes be tricky due_to_uid/gid differences. Check `docker-compose logs` for permission errors.
    *   **Nginx Log Dirs:** Ensure Nginx has permission to write to `/var/log/nginx/`.
-   **Nginx Configuration Errors:**
    *   Always run `sudo nginx -t` after modifying Nginx configurations before reloading.
    *   Check Nginx error logs: `/var/log/nginx/error.log` (host Nginx) and `docker-compose logs nginx` (if Nginx is containerized).
-   **Backend Application Errors:**
    *   Check backend logs: `docker-compose logs backend`.
    *   Ensure all environment variables (especially `SECRET_KEY`, `ALLOWED_HOSTS`, `DEBUG=False`) are correctly set in the `.env` file and that the file is being loaded by Docker Compose.
-   **Static File Issues (404s for CSS/JS):**
    *   Verify the `root` path in your Nginx configuration (`/etc/nginx/sites-available/anki_app`) correctly points to where the frontend static files are located *within the Nginx container*.
    *   Ensure your frontend build process is outputting files to the directory that Nginx is expecting (e.g., if Nginx expects `/var/www/frontend_dist/index.html`, make sure your Vue build outputs to `dist` and this `dist` is correctly copied/mounted to `/var/www/frontend_dist` in the Nginx container).
-   **API Not Reachable (502 Bad Gateway from Nginx):**
    *   Check if the backend service is running: `docker-compose ps`.
    *   Verify backend logs (`docker-compose logs backend`) for any startup errors.
    *   Ensure the `proxy_pass` URL in the Nginx configuration (`http://backend:8000/api/` or similar) correctly matches the backend service name and port defined in `docker-compose.yml` and the API path structure.
    *   Check network connectivity between the Nginx container and the backend container if they are on a custom Docker network.

## 10. Release Management & Tagging Strategy

A consistent tagging strategy is crucial for managing releases and enabling rollbacks if necessary. We recommend using Semantic Versioning (SemVer).

### 10.1. Git Tagging

-   **Semantic Versioning:** Use tags like `vX.Y.Z` (e.g., `v1.0.0`, `v1.0.1`, `v1.1.0`).
    -   `MAJOR` version (X) when you make incompatible API changes.
    -   `MINOR` version (Y) when you add functionality in a backward-compatible manner.
    -   `PATCH` version (Z) when you make backward-compatible bug fixes.
-   **Creating a Tag:**
    After committing your changes for a release, create an annotated tag:
    ```bash
    git tag -a v1.0.0 -m "Release version 1.0.0"
    ```
-   **Pushing Tags to Remote:**
    Push the specific tag:
    ```bash
    git push origin v1.0.0
    ```
    Or push all your local tags (use with caution if you have tags you don't want to push yet):
    ```bash
    # git push --tags
    ```

### 10.2. Deploying a Specific Tag on the Server

1.  **Fetch all tags from the remote repository:**
    ```bash
    git fetch --tags
    ```
2.  **Checkout the specific tag:**
    This creates a detached HEAD state for the specific release version.
    ```bash
    git checkout tags/v1.0.0 # Or simply: git checkout v1.0.0
    ```
3.  **Build and Deploy:**
    Use the provided scripts (`build.sh` and `deploy.sh`) to build and deploy this version. These scripts are designed to work with version tags.

## 11. Using Build and Deploy Scripts

The project includes `build.sh` and `deploy.sh` scripts to streamline the build and deployment process. These scripts expect to be run from the project root directory.

### 11.1. `build.sh`

This script builds the Docker images for the backend and frontend services.

-   **Purpose:** To build and tag Docker images based on the current state of the repository or a specified Git tag.
-   **Usage:**
    ```bash
    ./build.sh [VERSION_TAG]
    ```
    -   `[VERSION_TAG]` (optional): The Git tag you want to build (e.g., `v1.0.0`).
        If not provided, the script will default to using `latest` as the Docker image tag and build from the current `HEAD`.
-   **Process:**
    1.  Sets the version tag (either from argument or defaults to `latest`).
    2.  Builds the backend Docker image and tags it (e.g., `your_docker_repo/anki_backend:v1.0.0`).
    3.  Builds the frontend (Nginx + Vue app) Docker image and tags it (e.g., `your_docker_repo/anki_frontend:v1.0.0`).
    4.  (Optional) If `DOCKER_REGISTRY` environment variable is set, it will attempt to push the images.

### 11.2. `deploy.sh`

This script deploys the application using Docker Compose, referencing specific image tags.

-   **Purpose:** To pull specified Docker image versions (if using a registry) and (re)start the application services.
-   **Usage:**
    ```bash
    ./deploy.sh [VERSION_TAG]
    ```
    -   `[VERSION_TAG]` (optional): The version tag of the images to deploy (e.g., `v1.0.0`).
        If not provided, it defaults to deploying images tagged as `latest`.
-   **Environment Variables for `docker-compose.prod.yml`:**
    The `deploy.sh` script sets the following environment variables which are used by `docker-compose.prod.yml` to determine which image versions to run:
    -   `BACKEND_TAG`
    -   `FRONTEND_TAG`
    -   `DOCKER_REGISTRY` (optional, for specifying your Docker image registry prefix)
-   **Process:**
    1.  Sets the version tag for backend and frontend images.
    2.  Shuts down any currently running services defined in `docker-compose.prod.yml` (`docker-compose -f docker-compose.prod.yml down`).
    3.  (Optional) If `DOCKER_REGISTRY` is set, it attempts to pull the specified image versions from the registry.
    4.  Starts the services using `docker-compose -f docker-compose.prod.yml up -d`.

### 11.3. Example Deployment Flow for a New Release

1.  **Finalize and commit changes for the release.**
2.  **Tag the release:**
    ```bash
    git tag -a v1.0.1 -m "Release version 1.0.1"
    git push origin v1.0.1
    ```
3.  **On the production server:**
    a.  Fetch the new tag and checkout the code:
        ```bash
        git fetch --tags
        git checkout v1.0.1
        ```
    b.  Build the Docker images for the new version (replace `your_docker_repo/` if you use one):
        ```bash
        # Example: DOCKER_REGISTRY=myregistry ./build.sh v1.0.1
        ./build.sh v1.0.1
        ```
        If you are using a Docker registry and have configured it in `build.sh` (or via `DOCKER_REGISTRY` env var), this step will also push the images.
    c.  Deploy the new version:
        ```bash
        # Example: DOCKER_REGISTRY=myregistry ./deploy.sh v1.0.1
        ./deploy.sh v1.0.1
        ```

This deployment guide should provide a solid foundation for getting the application live. Remember to adapt paths and names according to your specific setup.
