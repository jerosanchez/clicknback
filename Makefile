VENV_ACTIVATE = source .venv/bin/activate &&
MAX_LINE_LENGTH = 88
TEST_DATABASE_URL ?= postgresql+asyncpg://user:password@localhost:5433/clicknback_test

# CI/CD tasks:

install: ## Install dependencies
	@if [ ! -d ".venv" ]; then \
		python3.13 -m venv .venv; \
	fi
	@bash -c "$(VENV_ACTIVATE) pip install -e '.[dev]'"

lint: ## Run linting
	@markdownlint "**/*.md"
	@bash -c "$(VENV_ACTIVATE) flake8 app/ --max-line-length=$(MAX_LINE_LENGTH)"
	@bash -c "$(VENV_ACTIVATE) isort --check-only app/ --profile=black --line-length=$(MAX_LINE_LENGTH)"
	@bash -c "$(VENV_ACTIVATE) black --check app/ --line-length=$(MAX_LINE_LENGTH)"

test: ## Run unit tests
	@bash -c "$(VENV_ACTIVATE) python -m pytest tests/unit/ --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml"

test-integration: ## Run integration tests (auto-manages test DB lifecycle)
	@$(MAKE) --no-print-directory test-db-up
	@bash -c "$(VENV_ACTIVATE) TEST_DATABASE_URL=$(TEST_DATABASE_URL) python -m pytest tests/integration/ -v"; \
	EXIT=$$?; $(MAKE) --no-print-directory test-db-down || true; exit $$EXIT

test-db-up: ## Start the integration-test PostgreSQL container
	docker compose -f docker-compose.test.yml up -d --wait

test-db-down: ## Stop and remove the integration-test PostgreSQL container
	docker compose -f docker-compose.test.yml down -v

test-e2e: ## Run end-to-end tests (requires full Docker Compose stack)
	@bash -c "$(VENV_ACTIVATE) python -m pytest tests/e2e/ -v"

coverage: ## Run tests & generate coverage reports (exits non-zero below 85%)
	@$(MAKE) --no-print-directory test > coverage.txt 2>&1; bash scripts/coverage-grade.sh

security: ## Run Bandit security scan on app/ (exclude low severity)
	@bash -c "$(VENV_ACTIVATE) bandit -r app/ -ll"

migrate: ## Apply all pending Alembic migrations
	@bash -c "$(VENV_ACTIVATE) alembic upgrade head"

# Development lifecycle:

clean: ## Clean up development environment
	rm -rf .venv
	rm -rf __pycache__
	rm -rf */__pycache__
	rm -rf */*/__pycache__
	rm -rf *.pyc
	rm -rf *.pyo
	rm -rf .mypy_cache
	rm -rf .pytest_cache
	rm -rf *.egg-info
	rm -rf */*.egg-info
	rm -rf */*/.egg-info

up: ## Start development environment
	@if ! docker network ls --format '{{.Name}}' | grep -wq clicknback-nw; then \
		docker network create clicknback-nw; \
	fi
	docker compose up -d --build

down: ## Stop development environment
	docker compose down
	docker network rm clicknback-nw

db-reset: ## Reset the database
	alembic downgrade base
	alembic upgrade head
	docker exec -i clicknback-clicknback-db-1 \
		psql -U user -d db < seeds/all.sql

dev: ## Run the application locally with hot-reload (no Docker)
	@bash -c "$(VENV_ACTIVATE) uvicorn app.main:app --reload"

logs: ## Tail container logs for clicknback-app
	docker compose logs -f clicknback-app

.PHONY: install lint test test-integration test-db-up test-db-down test-e2e coverage security migrate clean up down db-reset dev logs
