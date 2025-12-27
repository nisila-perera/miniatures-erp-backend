# Miniatures.lk ERP System - Backend Docker Management
# ====================================================

.PHONY: help dev prod build-dev build-prod up-dev up-prod down logs clean migrate test

# Default target
help:
	@echo "Miniatures.lk ERP System - Backend Commands"
	@echo "============================================"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start development environment"
	@echo "  make build-dev    - Build development containers"
	@echo "  make logs-dev     - View development logs"
	@echo ""
	@echo "Production:"
	@echo "  make prod         - Start production environment"
	@echo "  make build-prod   - Build production containers"
	@echo "  make logs-prod    - View production logs"
	@echo ""
	@echo "Common:"
	@echo "  make down         - Stop all containers"
	@echo "  make clean        - Remove all containers and volumes"
	@echo "  make migrate      - Run database migrations"
	@echo "  make test         - Run backend tests"
	@echo "  make shell        - Open shell in backend container"
	@echo "  make shell-db     - Open PostgreSQL shell"

# Development commands
dev: build-dev up-dev

build-dev:
	docker compose build

up-dev:
	docker compose up -d
	@echo "Development environment started!"
	@echo "Backend:  http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

logs-dev:
	docker compose logs -f

# Production commands
prod: build-prod up-prod

build-prod:
	docker compose -f docker-compose.prod.yml build

up-prod:
	docker compose -f docker-compose.prod.yml up -d
	@echo "Production environment started!"
	@echo "Backend: http://localhost"

logs-prod:
	docker compose -f docker-compose.prod.yml logs -f

# Stop containers
down:
	docker compose down
	docker compose -f docker-compose.prod.yml down

# Clean everything
clean:
	docker compose down -v --remove-orphans
	docker compose -f docker-compose.prod.yml down -v --remove-orphans
	docker system prune -f

# Database migrations
migrate:
	docker compose exec backend alembic upgrade head

migrate-prod:
	docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Run tests
test:
	docker compose exec backend pytest -v

test-property:
	docker compose exec backend pytest -v -k "property"

# Shell access
shell:
	docker compose exec backend /bin/bash

shell-prod:
	docker compose -f docker-compose.prod.yml exec backend /bin/bash

shell-db:
	docker compose exec postgres psql -U postgres -d miniatures_erp

shell-db-prod:
	docker compose -f docker-compose.prod.yml exec postgres psql -U $${POSTGRES_USER} -d $${POSTGRES_DB}

# Health checks
health:
	@echo "Checking backend health..."
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "Backend not responding"

health-prod:
	@echo "Checking production backend health..."
	@curl -s http://localhost/health || echo "Backend not responding"

# Restart services
restart:
	docker compose restart backend

restart-prod:
	docker compose -f docker-compose.prod.yml restart backend

# Local development (without Docker)
run-local:
	./run_backend.sh

install:
	pip install -r requirements.txt

venv:
	python -m venv venv
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

