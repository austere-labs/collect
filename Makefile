PROJECT_NAME := collect

upgradecodex:
	npm install -g @openai/codex@latest

marimo:
	uv run marimo edit

.PHONY: sync
movetools:
	./synctools

.PHONY: buildsrc
buildsrc: 
	 buildsrc --with-descriptions --verbose --parallel-workers 16

.PHONY: buildsrc
tree:
	buildsrc --tree

.PHONY: ensuregithub
ensuregithub:
	ensure-github-url

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
	make sync
	make ensuregithub
	make buildsrc
	make tree

migrate:
	uv run yoyo apply --config yoyo.ini --batch

restartapi:
	curl -X POST http://localhost:8081/restart
	sleep 2 && curl -X GET http://localhost:8081/health



