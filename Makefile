PROJECT_NAME := collect

lint:
	ruff check .

format:
	black .

test: 
	uv run pytest -v -s

check: 
	make lint
	make format
	make test


