.PHONY: up down logs ps build restart sh-db sh-backend backup

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build --pull

restart:
	docker compose restart

ps:
	docker compose ps

logs:
	docker compose logs -f --tail=200

sh-db:
	docker compose exec db psql -U crm -d crm

sh-backend:
	docker compose exec backend bash

backup:
	mkdir -p backups
	docker compose exec -T db pg_dump -U crm -d crm | gzip > backups/crm_$(shell date +%Y%m%d_%H%M%S).sql.gz
