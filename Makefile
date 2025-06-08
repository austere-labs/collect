PROJECT_NAME := collect

lint:
	ruff check .

format:
	black .

test: 
	uv run pytest -v -s -n auto

test-fast:
	uv run pytest -v -n auto -m "not slow"

test-slow:
	uv run pytest -v -s -m slow

test-single:
	uv run pytest -v -s

check: 
	make lint
	make format
	make test


