# Citizen Science Tracker — Monorepo

This repo hosts multiple services:
- `submission-api`: receives submissions (human or API-fed "sensor" data)
- `validation-worker`: async validations (rules, dedup, enrichment)
- `data-ingestor`: pulls remote data (OpenAQ, iNaturalist, OpenWeather) and publishes to DB/queue
- `gateway`: reverse proxy / rate limiting (to be added)

## Local Infra (dev)
`docker-compose.dev.yml` provides Postgres, MinIO (S3), and RabbitMQ for development.
Bring-up and service wiring will be added step-by-step.

