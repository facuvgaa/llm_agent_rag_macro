etl-up:
	docker compose -f infra/docker-compose.etl.yml up -d

etl-down:
	docker compose -f infra/docker-compose.etl.yml down airflow

rag-up:
	docker compose -f infra/docker-compose.rag.yml up -d
