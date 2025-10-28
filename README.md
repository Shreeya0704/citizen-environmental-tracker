# Citizen Science Tracker (MVP)

End-to-end pipeline:
- **Ingest**: OpenAQ + iNaturalist → MinIO (S3) → RabbitMQ
- **Validate/Normalize**: validation-worker → Postgres
- **API**: FastAPI (`/healthz`, `/measurements`, `/observations`, `/ingestions/latest`, `/stats/*`)
- **UI**: Static Nginx site behind Traefik (`/`), API proxied at `/api/*` (BasicAuth)
- **Ops**: Prometheus + Grafana, Alertmanager, db-maint (retention + matview refresh)
- **CI (optional)**: Jenkins + SonarQube, Trivy image scans

## Quick start
1) Copy env and edit secrets/ports:
```bash
cp .env.example .env
# set TRAEFIK_BASIC_PASS, then generate hash:
docker run --rm httpd:2.4-alpine sh -lc 'htpasswd -nbB "$TRAEFIK_BASIC_USER" "$TRAEFIK_BASIC_PASS"' | cut -d: -f2
# put the result into TRAEFIK_BASIC_AUTH_USERS as user:hash (escape $ as $$ if used inside compose labels)
```

2. Bring up everything for local dev:

```bash
make up
```

3. Open the app via gateway:

* Frontend: `http://localhost:${GATEWAY_PORT}/`
* API (BasicAuth): `http://localhost:${GATEWAY_PORT}/api/healthz` (`$TRAEFIK_BASIC_USER` / `$TRAEFIK_BASIC_PASS`)
* Prometheus (localhost only): `http://127.0.0.1:${PROMETHEUS_PORT}/`
* Grafana (localhost only): `http://127.0.0.1:${GRAFANA_PORT}/`
* Traefik dashboard: `http://localhost:${TRAEFIK_DASHBOARD_PORT}/`

4. Useful targets:

```bash
make status     # running containers
make logs       # tail logs
make refresh    # force db-maint retention + matview refresh once
make down       # stop core stack
make nuke       # stop + remove vols (DANGEROUS; wipes data)
make ci-up      # start Jenkins + SonarQube
make ci-down    # stop CI services
```

5. Demo/health:

```bash
./demo.sh --check
```

## Notes

* Prometheus/Grafana are bound to localhost; adjust compose if you need remote access.
* Change all placeholder passwords before sharing.
* MinIO lifecycle expires `openaq/raw/*` and `inat/raw/*` after 14 days.
