SHELL := /bin/bash
CF_DEV := docker-compose.dev.yml
CF_SVC := docker-compose.services.yml
CF_GW  := docker-compose.gateway.yml
CF_OBS := docker-compose.observability.yml
CF_CI  := docker-compose.ci.yml

.PHONY: up down status logs refresh nuke ci-up ci-down

up:
	@docker compose -f $(CF_DEV) -f $(CF_SVC) -f $(CF_GW) -f $(CF_OBS) up -d --build

down:
	@docker compose -f $(CF_DEV) -f $(CF_SVC) -f $(CF_GW) -f $(CF_OBS) down

status:
	@docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E '^cstr_' || true

logs:
	@docker compose -f $(CF_DEV) -f $(CF_SVC) -f $(CF_GW) -f $(CF_OBS) logs -f --tail=200

refresh:
	@docker exec -e PYTHONUNBUFFERED=1 cstr_db_maint python /app/refresh.py

nuke:
	@read -p "This will DELETE all volumes (db, minio, rabbitmq, grafana, jenkins, sonar). Continue? [y/N] " yn; \
	[[ "$$yn" == "y" || "$$yn" == "Y" ]] || { echo "Aborted"; exit 1; }; \
	docker compose -f $(CF_DEV) -f $(CF_SVC) -f $(CF_GW) -f $(CF_OBS) -f $(CF_CI) down -v

ci-up:
	@docker compose -f $(CF_CI) up -d --build sonarqube jenkins

ci-down:
	@docker compose -f $(CF_CI) down
