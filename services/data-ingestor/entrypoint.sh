#!/usr/bin/env sh
set -eu

INTERVAL_SECONDS="${INTERVAL_SECONDS:-600}"  # default: 10 minutes

# First run immediately, then sleep-loop
while true; do
  if python -m ingestor.run_once 2>&1; then
    :
  else
    echo "INGEST RUN ERROR" >&2
  fi
  sleep "${INTERVAL_SECONDS}"
done
