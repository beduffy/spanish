#!/bin/bash
#
# IP-only deploy (no domain / no SSL) to Hetzner.
#
# Goal: one command you can remember that:
# - rsyncs this repo to the server (excluding secrets + heavy local dirs)
# - rebuilds/restarts the production stack (docker-compose.prod.yml)
# - verifies the nginx /health endpoint
#
# Usage:
#   ./deploy-ip-only.sh
#   ./deploy-ip-only.sh --server-ip 5.75.174.115 --server-user root --server-path /opt/spanish-anki
#   ./deploy-ip-only.sh --delete   # WARNING: deletes files on server not present locally
#
# Notes:
# - This script intentionally does NOT copy .env.prod (server keeps its own secrets).
# - The server must already have a valid /opt/spanish-anki/.env.prod configured for IP-only:
#     ALLOWED_HOSTS=5.75.174.115,localhost,127.0.0.1
#     CORS_ALLOWED_ORIGINS=http://5.75.174.115:8080,http://localhost:8080
#
set -euo pipefail


SERVER_IP="5.75.174.115"
SERVER_USER="root"
SERVER_PATH="/opt/spanish-anki"
DO_DELETE="false"


while [[ $# -gt 0 ]]; do
  case "$1" in
    --server-ip)
      SERVER_IP="$2"
      shift 2
      ;;
    --server-user)
      SERVER_USER="$2"
      shift 2
      ;;
    --server-path)
      SERVER_PATH="$2"
      shift 2
      ;;
    --delete)
      DO_DELETE="true"
      shift 1
      ;;
    -h|--help)
      sed -n '1,80p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 2
      ;;
  esac
done


REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"


RSYNC_ARGS=(
  -avz
  --progress
  --exclude 'node_modules'
  --exclude '__pycache__'
  --exclude '.git'
  --exclude '*.pyc'
  --exclude '.env'
  --exclude '.env.prod'
  --exclude 'db.sqlite3'
  --exclude 'coverage.xml'
  --exclude '*.log'
)

if [[ "$DO_DELETE" == "true" ]]; then
  RSYNC_ARGS+=(--delete)
fi


echo "Deploying (IP-only) to ${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}"
echo "Repo: ${REPO_ROOT}"


echo ""
echo "==> Rsync code to server..."
rsync "${RSYNC_ARGS[@]}" "${REPO_ROOT}/" "${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/"


echo ""
echo "==> Rebuild/restart production stack on server..."
ssh "${SERVER_USER}@${SERVER_IP}" 'set -euo pipefail
cd '"${SERVER_PATH}"'

# Detect docker compose command on server.
if docker compose version >/dev/null 2>&1; then
  DC="docker compose"
elif command -v docker-compose >/dev/null 2>&1 && docker-compose version >/dev/null 2>&1; then
  DC="docker-compose"
else
  echo "Error: Docker Compose not found on server" >&2
  exit 1
fi

echo "Using: ${DC}"

# Export .env.prod into the shell so compose build args (${SUPABASE_URL}, ${SUPABASE_ANON_KEY}) resolve.
set -a
. ./.env.prod
set +a

${DC} -f docker-compose.prod.yml up -d --build
${DC} -f docker-compose.prod.yml ps

echo "--- health"
curl -fsS http://localhost:8080/health | head -n 5
'


echo ""
echo "✅ Deploy finished. App should be reachable at: http://${SERVER_IP}:8080"

