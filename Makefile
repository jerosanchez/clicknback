run:
	. .venv/bin/activate && uvicorn app.main:app --reload

.PHONY: run
