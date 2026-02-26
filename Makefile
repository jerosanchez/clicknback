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
	@bash -c "$(VENV_ACTIVATE) python -m pytest tests/ --cov=app --cov-report=html"

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

format: ## Format code
	@bash -c "$(VENV_ACTIVATE) isort app/ --profile=black --line-length=$(MAX_LINE_LENGTH)"
	@bash -c "$(VENV_ACTIVATE) black app/ --line-length=$(MAX_LINE_LENGTH)"
	
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

run: ## Run the application (non-docker)
	@bash -c "$(VENV_ACTIVATE) uvicorn app.main:app --reload"

.PHONY: install lint test clean format up down db-reset run
