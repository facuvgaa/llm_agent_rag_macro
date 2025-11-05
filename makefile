etl-up:
	docker compose -f infra/docker-compose.etl.yml up -d --build 

etl-down:
	docker compose -f infra/docker-compose.etl.yml down

rag-up:
	docker compose -f infra/docker-compose.rag.yml up -d --build 

rag-down:
	docker compose -f infra/docker-compose.rag.yml down