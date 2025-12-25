# Spanish Anki Web App

[![Django CI](https://github.com/beduffy/spanish/actions/workflows/ci.yml/badge.svg)](https://github.com/beduffy/spanish/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/beduffy/spanish/graph/badge.svg)](https://codecov.io/gh/beduffy/spanish)

## Overview

This project is a web application designed to help you learn Spanish vocabulary and sentences using an Anki-inspired digital flashcard system. The core idea is to leverage Spaced Repetition System (SRS) principles to optimize learning and memory retention. You can review Spanish sentences, translate them, self-assess your understanding with a score, and add personal comments to track your learning journey.

The application provides a clean interface for reviewing flashcards, tracks your progress through various statistics on a dashboard, and allows you to browse and manage all imported sentences.

For a detailed breakdown of all features, user stories, and the data model, please refer to the [Product Requirements Document](anki_web_app/product_requirements_doc.md).

## Technology Stack

*   **Backend:** Python, Django, Django REST Framework
*   **Frontend:** Vue.js (v3), Vue Router, Axios
*   **Database:** SQLite
*   **Containerization:** Docker, Docker Compose
*   **Testing:**
    *   Backend: Django's built-in test framework, `coverage.py`
    *   Frontend Unit: Jest
    *   Frontend E2E: Cypress
*   **CI/CD:** GitHub Actions
*   **Code Coverage:** Codecov
*   **Web Server (for deployment):** Nginx (configured for frontend static files and as a reverse proxy to the Django backend)

## Application Architecture Summary

The application follows a client-server model:

1.  **Backend (Django):**
    *   Manages the SQLite database (sentences, user reviews, SRS data).
    *   Implements the Spaced Repetition System (SRS) logic.
    *   Exposes a RESTful API for the frontend to interact with.
2.  **Frontend (Vue.js):**
    *   A Single Page Application (SPA) that runs in your browser.
    *   Communicates with the Django backend API to fetch and submit data.
    *   Handles all user interface elements, interactions, and navigation.
3.  **Docker:** Both backend and frontend services are containerized using Docker and orchestrated with `docker-compose` for consistent development, testing, and deployment environments.

For a more detailed architectural overview, see the [Application Architecture section in the PRD](anki_web_app/product_requirements_doc.md#9-application-architecture--data-flow).

## Core Features Summary

*   **Flashcard Review:** Spanish-to-English sentence translation practice.
*   **Spaced Repetition System (SRS):** Optimizes review scheduling based on performance.
*   **Self-Scoring & Comments:** Subjective scoring (0.0-1.0) and timestamped comments for each review.
*   **Dashboard:** Displays learning statistics (reviews today/week, overall score, sentences learned/mastered).
*   **Sentence Management:** View all sentences, individual statistics, and review history.
*   **Data Import:** Initial sentence data loaded from a CSV file.

Refer to the [Core Features section in the PRD](anki_web_app/product_requirements_doc.md#4-core-features) for full details.

## Project Structure

The project is organized into a Django backend and a Vue.js frontend, primarily within the `anki_web_app` directory.

### Backend (Django - `anki_web_app/`)

*   **`manage.py`**: Django's command-line utility.
*   **`spanish_anki_project/`**: Project-level configuration (settings, main URLs).
    *   `settings.py`: Key settings like `INSTALLED_APPS` (including `flashcards`, `rest_framework`, `corsheaders`), `DATABASES` (SQLite), middleware, etc.
    *   `urls.py`: Main project URL routing, including routing to the `flashcards` app URLs.
*   **`flashcards/`**: The core Django app for flashcard functionality.
    *   `models.py`: Defines `Sentence` and `Review` database models, including SRS logic in `Sentence.process_review()`.
    *   `views.py`: Contains API viewsets (e.g., `SentenceViewSet`, `ReviewViewSet`, `NextCardView`, `StatisticsView`) that handle requests from the frontend.
    *   `serializers.py`: Defines how Django models are converted to and from JSON for the API.
    *   `urls.py`: URL routing specific to the `flashcards` API endpoints.
    *   `tests.py`: Contains backend unit and API/integration tests.
    *   `management/commands/import_csv.py`: Custom command to import data from CSV.
    *   `migrations/`: Database schema changes.
*   **`data/`**: Directory for input CSV files and potentially other data assets.
*   **`db.sqlite3`**: The SQLite database file (created when migrations are run).
*   **`Dockerfile`**: Instructions to build the Docker image for the backend.
*   **`entrypoint.sh`**: Script executed when the backend Docker container starts (runs migrations, starts the server).
*   **`requirements.txt`**: Python dependencies for the backend.

### Frontend (Vue.js - `anki_web_app/spanish_anki_frontend/`)

*   **`public/`**: Static assets, including `index.html`.
*   **`src/`**: Main frontend application code.
    *   `main.js`: Entry point for the Vue application (initializes Vue, router, etc.).
    *   `App.vue`: Root Vue component.
    *   `router/index.js`: Defines frontend routes (e.g., `/`, `/dashboard`, `/sentences`, `/sentences/:id`) and maps them to Vue components.
    *   `views/`: Vue components that act as pages for routes (e.g., `FlashcardView.vue`, `DashboardView.vue`, `SentenceListView.vue`, `SentenceDetailView.vue`).
    *   `components/`: Reusable Vue components (if any, though views might be the primary components for this app size).
    *   `services/ApiService.js`: (Or similar) A module responsible for making API calls to the Django backend (likely using Axios).
    *   `assets/`: Static assets like images or global styles.
*   **`tests/`**:
    *   `unit/`: Contains Jest unit tests for Vue components.
    *   `e2e/`: Contains Cypress end-to-end tests. (Note: Cypress setup often places specs in a top-level `cypress/e2e` directory instead of `tests/e2e`).
*   **`babel.config.js`, `vue.config.js`, `package.json`, `package-lock.json`**: Configuration files for Vue CLI, Babel, Node.js dependencies, etc.
    *   `vue.config.js` is important as it contains `devServer.proxy` to route API calls during development from `localhost:8080` to the backend at `localhost:8000`.
*   **`Dockerfile`**: Instructions to build the Docker image for the frontend (typically builds static files and sets up Nginx to serve them).
*   **`nginx.conf`**: Nginx configuration used by the frontend Docker container to serve static files and proxy API requests to the backend service in a Docker environment.

## Dockerization

This project uses Docker and Docker Compose to simplify development, testing, and deployment.

*   **`Dockerfile` (in `anki_web_app/`):** Defines how to build the Django backend Docker image.
*   **`Dockerfile` (in `anki_web_app/spanish_anki_frontend/`):** Defines how to build the Vue.js frontend Docker image (compiling static assets and setting up Nginx).
*   **`docker-compose.yml` (in project root):**
    *   Defines two main services: `backend` and `frontend`.
    *   Specifies how to build each service (using their respective Dockerfiles).
    *   Manages networking between services (e.g., allowing the frontend Nginx to proxy to the backend).
    *   Sets up volume mounts for live code reloading during development.
    *   Defines ports for accessing the application.
*   **Benefits:**
    *   **Consistent Environments:** Ensures the application runs the same way everywhere.
    *   **Simplified Setup:** New developers can get started quickly.
    *   **Isolated Dependencies:** Prevents conflicts with other projects.
    *   **Streamlined Testing:** Allows tests to run in a clean, controlled environment.

## Testing Strategy Overview

The project employs a comprehensive testing strategy to ensure code quality and application stability:

1.  **Backend Django Tests:**
    *   **Location:** `anki_web_app/flashcards/tests.py`
    *   **Purpose:** Verify the correctness of backend logic, including database interactions, SRS calculations, and API endpoint responses. Includes both unit and integration tests.
2.  **Frontend Unit Tests (Jest):**
    *   **Location:** `anki_web_app/spanish_anki_frontend/tests/unit/`
    *   **Purpose:** Test individual Vue.js components in isolation to ensure they render correctly and their internal logic works as expected. API calls are typically mocked.
3.  **Frontend End-to-End (E2E) Tests (Cypress):**
    *   **Location:** `anki_web_app/spanish_anki_frontend/cypress/e2e/`
    *   **Purpose:** Simulate real user scenarios in a browser, testing the integrated application (frontend and backend) from the user's perspective.
4.  **Execution:**
    *   The `run_all_tests.sh` script in the project root is the primary way to execute all tests locally using Docker Compose.
    *   `act` can be used to simulate GitHub Actions CI runs locally.

For a detailed breakdown of the testing plan for each component and phase, see the [Testing Plan in the PRD](anki_web_app/product_requirements_doc.md#testing-plan).

## Development Setup

### Prerequisites
*   Docker
*   Docker Compose (v2 or later):
    *   **Standalone binary:** `docker-compose ...` (most common, works with `docker-compose up`)
    *   **Plugin form:** `docker compose ...` (Ubuntu/Debian: `sudo apt-get install -y docker-compose-plugin`)
    *   If you see `kwargs_from_env() got an unexpected keyword argument 'ssl_version'`, you are almost certainly running the old Python `docker-compose` v1 binary. Install a modern Docker Compose v2+ instead.
*   (Optional) Buildx plugin (fixes `Docker Compose requires buildx plugin to be installed` warning):
    *   Ubuntu/Debian: `sudo apt-get install -y docker-buildx-plugin`
    *   Note: The warning is harmless if you're using standalone `docker-compose` binary

### Using Docker Compose (Recommended for Dev & Testing)

1.  **Build and Start Services:**
    From the project root directory:
    ```bash
    docker-compose up --build -d
    ```
    Or if you have the plugin form:
    ```bash
    docker compose up --build -d
    ```
2.  **Accessing the App:**
    *   Frontend: `http://localhost:8080`
    *   Backend API: `http://localhost:8000` (e.g., `http://localhost:8000/api/flashcards/statistics/`)
3.  **Initial Data Import (run once after starting services):**
    ```bash
    docker-compose exec backend python manage.py import_csv data/your_csv_file_name.csv
    ```
    (Replace `your_csv_file_name.csv` with your actual CSV file located in `anki_web_app/data/`)
4.  **Viewing Logs:**
    ```bash
    # All services
    docker-compose logs -f
    
    # Specific service
    docker-compose logs -f backend
    docker-compose logs -f frontend
    ```
5.  **Stopping Services:**
    ```bash
    docker-compose down
    ```

### Manual Setup (Alternative - If not using Docker for local dev)

#### Backend (Django)

1.  **Navigate to the backend directory:**
    ```bash
    cd anki_web_app
    ```
2.  **Activate your Python virtual environment** (e.g., Conda `py38` or your `venv`).
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Apply database migrations:**
    ```bash
    python manage.py migrate
    ```
5.  **(Optional) Import initial data from CSV:**
    Make sure your CSV file is in `anki_web_app/data/`.
    ```bash
    python manage.py import_csv data/your_csv_file_name.csv
    ```
6.  **Run the Django development server:**
    ```bash
    python manage.py runserver
    ```
    The backend API will typically be available at `http://127.0.0.1:8000/`.

#### Frontend (Vue.js)

1.  **Navigate to the frontend directory:**
    ```bash
    cd anki_web_app/spanish_anki_frontend 
    ```
2.  **Install dependencies:**
    ```bash
    npm install
    ```
3.  **Run the Vue development server:**
    ```bash
    npm run serve
    ```
    The frontend application will typically be available at `http://localhost:8080/`. Ensure your `vue.config.js` has the proxy correctly set up to communicate with the backend.

## Running Tests

This project includes backend tests (Django), frontend unit tests (Jest), and frontend end-to-end tests (Cypress).

### Run All Tests with Docker (Recommended)

A script is provided in the project root to run all test suites sequentially within a Docker environment:

1.  **Navigate to the project root directory.**
2.  **Make the script executable (if you haven't already):**
    ```bash
    chmod +x run_all_tests.sh
    ```
3.  **Execute the script:**
    ```bash
    ./run_all_tests.sh
    ```
    This will:
    *   Bring down any existing Docker services.
    *   Build/rebuild Docker images if necessary.
    *   Start services in detached mode.
    *   Execute Django backend tests (with coverage) inside the `backend` container.
    *   Seed the database for E2E tests.
    *   Execute Jest frontend unit tests inside the `frontend` container (or a temporary Node container).
    *   Execute Cypress E2E tests from the host machine against the Dockerized frontend.
    *   Bring down Docker services.

### Individual Test Suites (Manual Docker Execution or Local Dev)

*   **Backend Django Tests (inside Docker):**
    After `docker-compose up -d --build`:
    ```bash
    docker-compose exec -T backend coverage run manage.py test flashcards
    docker-compose exec -T backend coverage xml -o coverage.xml 
    ```

*   **Frontend Unit Tests (Jest - inside Docker):**
    After `docker-compose up -d --build`:
    ```bash
    docker-compose exec -T frontend npm run test:unit
    ```
    Or locally (if Node.js is set up): Navigate to `anki_web_app/spanish_anki_frontend` and run `npm run test:unit`.

*   **Frontend E2E Tests (Cypress - from host):**
    Ensure backend and frontend services are running (e.g., via `docker-compose up -d`).
    Navigate to `anki_web_app/spanish_anki_frontend` and run:
    To run in headless mode:
    ```bash
    npx cypress run
    ```
    To open the Cypress Test Runner UI:
    ```bash
    npx cypress open
    ```

## CI/CD (Continuous Integration/Continuous Deployment)

*   **GitHub Actions:** The workflow is defined in `.github/workflows/ci.yml`.
    *   **Trigger:** Runs on pushes to `master` and on pull requests targeting `master`.
    *   **Key Steps:**
        1.  Checks out the code.
        2.  Sets up Python and Node.js.
        3.  Installs Docker Compose v2 plugin.
        4.  Installs frontend dependencies (for Cypress host execution) and Cypress system dependencies.
        5.  Runs all tests using `./run_all_tests.sh` (which uses Docker Compose).
        6.  Uploads backend test coverage results to Codecov.io.
        7.  Uploads Cypress screenshots/videos as artifacts if E2E tests fail.
*   **Codecov:** Integrated to track test coverage for the Django backend. The badge at the top of this README reflects the current coverage status.

This setup ensures that every change is automatically tested, maintaining code quality and providing quick feedback on the impact of new commits.