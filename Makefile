-include .env
.EXPORT_ALL_VARIABLES:

.PHONY: up down run test lint

up:
	docker compose up -d --wait
down:
	docker compose down
run: up
	uv run python -m olist_pipeline run
test: up
	uv run pytest
lint:
	uv run ruff check .
	uv run ruff format --check .
