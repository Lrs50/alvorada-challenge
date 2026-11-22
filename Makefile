-include .env
.EXPORT_ALL_VARIABLES:

.PHONY: setup lint test up down migrate load run report

setup:
	uv sync

lint:
	uv run ruff check .
	uv run ruff format --check .

report: up
	uv run python -m olist_pipeline.report

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

run: up
	uv run python -m olist_pipeline.run
