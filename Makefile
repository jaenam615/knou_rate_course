.PHONY: local local-db local-api prod build clean logs

# Local development
local: local-db local-api

local-db:
	docker-compose --env-file .env.local up -d db
	@echo "Waiting for database to be ready..."
	@sleep 2

local-api:
	set -a && source .env.local && set +a && \
	uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Local with everything in Docker
local-docker:
	docker-compose --env-file .env.local up --build

# Production
prod:
	docker-compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Utilities
build:
	docker-compose build

clean:
	docker-compose down -v
	docker system prune -f

logs:
	docker-compose logs -f

logs-api:
	docker-compose logs -f api

logs-db:
	docker-compose logs -f db

# Database
db-shell:
	docker-compose exec db psql -U postgres -d knou_rate_course
