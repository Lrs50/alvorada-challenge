-include .env
.EXPORT_ALL_VARIABLES:

.PHONY: setup lint test up down migrate load

setup:
	uv sync

lint:
	uv run ruff check .
	uv run ruff format --check .

test: up
	uv run pytest

up:
	docker compose up -d --wait

down:
	docker compose down

migrate:
	uv run python -m olist_pipeline.migrate

load:
	uv run python -m olist_pipeline.load
