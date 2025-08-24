PROJECT_NAME := collect

marimo:
	uv run marimo edit

.PHONY: movetools
movetools:
	./movetools

.PHONY: buildsrc
buildsrc: 
	./tools/buildsrc

.PHONY: buildsrc
tree:
	./tools/buildsrc --tree

.PHONY: ensuregithub
ensuregithub:
	./tools/ensure-github-url

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
	make movetools
	make ensuregithub
	make buildsrc
	make tree

migrate:
	uv run yoyo apply --config yoyo.ini --batch

restartapi:
	curl -X POST http://localhost:8081/restart
	sleep 2 && curl -X GET http://localhost:8081/health



