#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
ENV_FILE="${1:-.env.prod}"
[ -f "$ENV_FILE" ] || { echo "Missing $ENV_FILE"; exit 1; }
set -a; . "$ENV_FILE"; set +a

: "${GATEWAY_PORT:=8095}"
: "${TRAEFIK_BASIC_USER:=apiuser}"
: "${TRAEFIK_BASIC_PASS:=apipass-CHANGE-ME}"

code="$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${GATEWAY_PORT}/api/healthz")"
[ "$code" = "401" ] || { echo "Expected 401 unauthenticated, got $code"; exit 1; }
curl -fsS -u "${TRAEFIK_BASIC_USER}:${TRAEFIK_BASIC_PASS}" "http://localhost:${GATEWAY_PORT}/api/healthz" >/dev/null
curl -fsS "http://localhost:${GATEWAY_PORT}/" | grep -q "Citizen Science Tracker"
echo "PROD VERIFY OK"
