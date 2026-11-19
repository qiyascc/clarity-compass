.PHONY: sync lint typecheck test check

sync:
	uv sync --all-packages

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy packages apps

test:
	uv run pytest

check: lint typecheck test
