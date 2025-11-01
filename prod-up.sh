#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
ENV_FILE="${1:-.env.prod}"
[ -f "$ENV_FILE" ] || { echo "Missing $ENV_FILE"; exit 1; }
set -a; . "$ENV_FILE"; set +a
export COMPOSE_PROJECT_NAME=cstr-prod

docker compose --env-file "$ENV_FILE" \
  -f docker-compose.dev.yml \
  -f docker-compose.services.yml \
  -f docker-compose.gateway.yml \
  -f docker-compose.observability.yml \
  -f docker-compose.prod-override.yml \
  up -d --build
