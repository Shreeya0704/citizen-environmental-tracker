#!/usr/bin/env bash
set -euo pipefail
[[ -f .env ]] && set -a && . .env && set +a

: "${GATEWAY_PORT:=8090}"
: "${PROMETHEUS_PORT:=9090}"
: "${GRAFANA_PORT:=3001}"
: "${TRAEFIK_BASIC_USER:=apiuser}"
: "${TRAEFIK_BASIC_PASS:=apipass-CHANGE-ME}"

echo "Frontend:   http://localhost:${GATEWAY_PORT}/"
echo "API (auth): http://localhost:${GATEWAY_PORT}/api/healthz   user=${TRAEFIK_BASIC_USER}"
echo "Prometheus: http://127.0.0.1:${PROMETHEUS_PORT}/  (localhost only)"
echo "Grafana:    http://127.0.0.1:${GRAFANA_PORT}/  (localhost only)"

if [[ "${1:-}" == "--check" ]]; then
  code="$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${GATEWAY_PORT}/api/healthz")"
  [[ "$code" == "401" ]] || { echo "Expected 401 unauthenticated, got $code"; exit 1; }
  curl -fsS -u "${TRAEFIK_BASIC_USER}:${TRAEFIK_BASIC_PASS}" "http://localhost:${GATEWAY_PORT}/api/healthz" >/dev/null
  curl -fsS "http://127.0.0.1:${PROMETHEUS_PORT}/-/ready" >/dev/null
  curl -fsS "http://127.0.0.1:${GRAFANA_PORT}/login" >/dev/null
  echo "DEMO CHECK OK"
fi
