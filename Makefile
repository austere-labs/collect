PROJECT_NAME := collect

lint:
	ruff check .

format:
	black .

test: 
	pytest -v -s

check: 
	make lint
	make format
	make test


