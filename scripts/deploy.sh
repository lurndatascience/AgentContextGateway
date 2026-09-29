#!/usr/bin/env bash
# Deploy to the droplet: rsync the repo, copy .env, build and start, publish the Caddy snippet.
# Idempotent. Usage: scripts/deploy.sh   (env: REMOTE_HOST, REMOTE_DIR)
set -euo pipefail

REMOTE_HOST="${REMOTE_HOST:-deploy@68.183.216.121}"
REMOTE_DIR="${REMOTE_DIR:-/opt/contextgateway}"
EDGE_DIR="${EDGE_DIR:-/opt/edge}"
here="$(cd "$(dirname "$0")/.." && pwd)"

[[ -f "${here}/.env" ]] || { echo "ERROR: ${here}/.env missing (copy .env.example)" >&2; exit 1; }

echo "==> Syncing repo to ${REMOTE_HOST}:${REMOTE_DIR}"
ssh "${REMOTE_HOST}" "sudo install -d -o \$(id -u) -g \$(id -g) '${REMOTE_DIR}'"
rsync -az --delete --exclude '.git' --exclude 'Use-case' --exclude '.idea' --exclude '.DS_Store' \
  --exclude '__pycache__' --exclude '.env' "${here}/" "${REMOTE_HOST}:${REMOTE_DIR}/"
scp -q "${here}/.env" "${REMOTE_HOST}:${REMOTE_DIR}/.env"

echo "==> Building and starting on the droplet"
ssh "${REMOTE_HOST}" bash -s <<REMOTE
set -euo pipefail
cd '${REMOTE_DIR}'
sudo docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build --remove-orphans
sudo install -m 0644 -o root -g root Caddyfile.snippet '${EDGE_DIR}/snippets/contextgateway.caddy'
sudo docker exec edge-caddy caddy validate --config /etc/caddy/Caddyfile
sudo docker exec edge-caddy caddy reload --config /etc/caddy/Caddyfile
sudo docker image prune -f
sudo docker compose ps
REMOTE
echo "==> Done: https://contextgateway.vaibhavkadam.online"
