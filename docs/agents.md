# Agents Guide (`agents.md`)

This file is **for coding agents** (human or AI) working in this repo. It explains **what this project is**, **where the code lives**, and **the safest/fastest ways to run and test changes**.


## Project summary

- **What it is**: An Anki-inspired Spanish flashcard web app with a Django REST backend and a Vue (Vue CLI) frontend.
- **Backend**: Django + DRF in `anki_web_app/` (core app: `anki_web_app/flashcards/`)
- **Frontend**: Vue app in `anki_web_app/spanish_anki_frontend/`
- **Default dev ports (Docker)**:
  - Frontend: `http://localhost:8080`
  - Backend API: `http://localhost:8000`
  - API prefix: `/api/flashcards/` (Django routes this to the `flashcards` app)


## Repo map (where to edit what)

### Backend (Django)

- **Project settings / root URLs**: `anki_web_app/spanish_anki_project/`
  - `urls.py` mounts flashcards API at `/api/flashcards/`
- **Main app**: `anki_web_app/flashcards/`
  - **Models + SRS logic**: `models.py`
  - **API views**: `views.py`
  - **Serializers**: `serializers.py`
  - **Routes**: `urls.py`
  - **Auth** (Supabase/JWT integration): see `middleware.py`, `auth_backend.py`, `drf_auth.py` (and related settings)
  - **Management commands**: `management/commands/`
    - `import_csv.py` (legacy Sentence import)
    - `seed_e2e_data.py` (seeds data for Cypress)
    - `create_test_user.py` (local/dev helper)
- **DB**: SQLite. In Docker dev, `./data` is mounted into `/app/data` for persistence (see `docker-compose.yml`).

### Frontend (Vue)

- **App code**: `anki_web_app/spanish_anki_frontend/src/`
  - **Routes**: `router/index.js`
  - **API clients**: `services/ApiService.js`, `services/SupabaseService.js`
  - **Views**: `views/` (page components)
- **E2E tests**: `anki_web_app/spanish_anki_frontend/cypress/e2e/`
- **Unit tests**: `anki_web_app/spanish_anki_frontend/tests/unit/`


## API surface (high level)

All endpoints are under `/api/flashcards/` (see `anki_web_app/spanish_anki_project/urls.py` and `anki_web_app/flashcards/urls.py`).

Notable endpoints include:
- **Legacy Sentence flow**:
  - `GET /api/flashcards/next-card/`
  - `POST /api/flashcards/submit-review/`
  - `GET /api/flashcards/statistics/`
  - `GET /api/flashcards/sentences/`
  - `GET /api/flashcards/sentences/<id>/`
- **Card flow**:
  - `GET /api/flashcards/cards/`
  - `POST /api/flashcards/cards/`
  - `GET /api/flashcards/cards/<id>/`
  - `POST /api/flashcards/cards/import/`
  - `GET /api/flashcards/cards/next-card/`
  - `POST /api/flashcards/cards/submit-review/`
  - `GET /api/flashcards/cards/statistics/`
- **Study sessions**:
  - `GET /api/flashcards/sessions/`
  - `POST /api/flashcards/sessions/start/`
  - `POST /api/flashcards/sessions/heartbeat/`
  - `POST /api/flashcards/sessions/end/`
- **Reader (LingQ-style)**:
  - `GET /api/flashcards/reader/lessons/`
  - `POST /api/flashcards/reader/lessons/`
  - `GET /api/flashcards/reader/lessons/<id>/`
  - `POST /api/flashcards/reader/translate/`
  - `GET /api/flashcards/reader/tokens/<id>/click/`
  - `POST /api/flashcards/reader/add-to-flashcards/`
  - `POST /api/flashcards/reader/generate-tts/`
- **Auth sanity check**:
  - `GET /api/flashcards/current-user/`


## Running the app (recommended: Docker)

This repo is set up so you generally don’t need local Python/Node installs.

- **Start everything (clean rebuild)**:

```bash
./run.sh
```

- **Stop services** (Compose v2 plugin shown; `docker-compose` also supported):

```bash
docker compose down -v
```

- **Logs**:

```bash
docker compose logs -f
docker compose logs -f backend
docker compose logs -f frontend
```

Notes:
- `docker-compose.yml` maps **backend 8000** and **frontend 8080**.
- If you see the classic `kwargs_from_env() got an unexpected keyword argument 'ssl_version'`, you’re likely using the old Python `docker-compose` v1 binary—install the Compose v2 plugin instead.


## Running tests

- **Run all tests (backend + frontend unit + Cypress E2E)**:

```bash
./run_all_tests.sh
```

This script will:
- bring up Compose services,
- run backend tests with coverage,
- seed E2E data,
- run frontend Jest unit tests,
- run Cypress E2E from the host,
- then tear everything down.


## Auth / Supabase (production + debugging)

The deployed version uses **Supabase** for authentication; the frontend sends a **Bearer token** and the backend validates it.

- **Prod env vars template**: `env.prod.example` (copy to `.env.prod` on the server)
- **Quick “am I logged in?” docs**:
  - `AUTHENTICATION_CHECK.md`
  - `verify-auth.md`

If you’re debugging auth:
- confirm the frontend has a Supabase session,
- confirm requests include `Authorization: Bearer <token>`,
- hit `GET /api/flashcards/current-user/` to verify backend auth end-to-end.


## Data import notes

There are **two concepts** in the codebase:
- **Legacy `Sentence` model** imported via management command (`import_csv.py`)
- **Newer `Card` model** typically imported via the **web UI** (`/api/flashcards/cards/import/`)

When modifying import logic, be explicit about which path you’re changing.


## Reader Feature (LingQ-style)

A reader feature is being added to allow importing text (and eventually YouTube), translating words/sentences, generating TTS audio, and easily adding words/phrases to the existing Card flashcard system.

- **Documentation**: See `LINGQ_READER_PLAN.md` for detailed implementation plan
- **Quick Start**: See `LINGQ_READER_QUICKSTART.md` for overview
- **Key Point**: Reader integrates with existing Card system via `/api/flashcards/cards/` endpoint. No changes to Card model or existing flashcard functionality.

## Working conventions (important)

- **Make minimal diffs**: do not rewrite large files unless requested.
- **Do not delete comments or TODOs.**
- **Keep two blank lines between top-level functions/classes** in Python files (PEP8-style spacing).
- **When running locally outside Docker**, verify you're in the correct **conda/venv** first (this repo often uses Docker, but local runs happen too).
- Prefer updating docs when you introduce new env vars, endpoints, scripts, or workflows.

