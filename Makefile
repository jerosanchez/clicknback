install:
	@if [ ! -d ".venv" ]; then \
		python3 -m venv .venv; \
	fi
	. .venv/bin/activate && pip install -e ".[dev]"

# Development lifecycle targets:

up:
	@if ! docker network ls --format '{{.Name}}' | grep -wq clicknback-nw; then \
		docker network create clicknback-nw; \
	fi
	docker compose up -d

down:
	docker compose down
	docker network rm clicknback-nw

db-reset:
	alembic downgrade base
	alembic upgrade head
	docker exec -i clicknback-clicknback-db-1 \
		psql -U user -d db < seeds/users.sql

clean:
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

run:
	. .venv/bin/activate && uvicorn app.main:app --reload

.PHONY: install up down db-reset clean run
