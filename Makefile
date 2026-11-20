.PHONY: setup lint

setup:
	uv sync

lint:
	uv run ruff check .
	uv run ruff format --check .
