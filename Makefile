.PHONY: install dev test lint run clean

install:
	python -m pip install -r requirements.txt

dev:
	python -m pip install -r requirements-dev.txt

test:
	python -m pytest -q

lint:
	python -m ruff check .
	python -m ruff format --check .

run:
	python -m uvicorn src.app:app --reload --port 8000

clean:
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov
