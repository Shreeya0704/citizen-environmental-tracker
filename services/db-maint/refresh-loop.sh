#!/usr/bin/env sh
set -eu
: "${REFRESH_INTERVAL_SECONDS:=86400}"
python3 /app/refresh.py || echo "refresh failed" >&2
while true; do
  sleep "${REFRESH_INTERVAL_SECONDS}"
  python3 /app/refresh.py || echo "refresh failed" >&2

done
