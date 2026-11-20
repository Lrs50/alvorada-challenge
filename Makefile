.PHONY: setup lint up down

setup:
	uv sync

lint:
	uv run ruff check .
	uv run ruff format --check .

up:
	docker compose up -d --wait

down:
	docker compose down
