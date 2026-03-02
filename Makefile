VENV_ACTIVATE = source .venv/bin/activate &&
MAX_LINE_LENGTH = 88

# CI/CD tasks:

install: ## Install dependencies
	@if [ ! -d ".venv" ]; then \
		python3 -m venv .venv; \
	fi
	@bash -c "$(VENV_ACTIVATE) pip install -e '.[dev]'"

lint: ## Run linting
	@markdownlint "**/*.md"
	@bash -c "$(VENV_ACTIVATE) flake8 app/ --max-line-length=$(MAX_LINE_LENGTH)"
	@bash -c "$(VENV_ACTIVATE) isort --check-only app/ --profile=black --line-length=$(MAX_LINE_LENGTH)"
	@bash -c "$(VENV_ACTIVATE) black --check app/ --line-length=$(MAX_LINE_LENGTH)"

test: ## Run tests
	@bash -c "$(VENV_ACTIVATE) python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml"

coverage: ## Run tests, generate coverage reports, and print emoji grade (exits non-zero below 70%)
	@$(MAKE) --no-print-directory test > coverage.txt 2>&1; bash scripts/coverage-grade.sh

security: ## Run Bandit security scan on app/ (medium and high severity only)
	@bash -c "$(VENV_ACTIVATE) bandit -r app/ -ll"

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
	docker compose up -d

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

.PHONY: install lint test coverage security clean up down db-reset dev logs
