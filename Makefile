ENV_FILE=.env
COMPOSE=docker-compose --env-file $(ENV_FILE)

API=tt-api
WORKER=tt-worker
REDIS=tt-redis

HF_VOL=hf-cache
TORCH_VOL=torch-cache

.PHONY: dev up down restart logs logs-api logs-worker build rebuild clean shell-api shell-worker

dev:
	$(COMPOSE) up api worker

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

restart: down up

build:
	$(COMPOSE) build

rebuild:
	$(COMPOSE) build --no-cache
	$(COMPOSE) up -d --force-recreate

logs:
	$(COMPOSE) logs -f

logs-api:
	$(COMPOSE) logs -f $(API)

logs-worker:
	$(COMPOSE) logs -f $(WORKER)

shell-api:
	$(COMPOSE) exec $(API) /bin/sh

shell-worker:
	$(COMPOSE) exec $(WORKER) /bin/sh

clean:
	$(COMPOSE) down -v --remove-orphans
	docker volume rm $(HF_VOL) $(TORCH_VOL) || true
