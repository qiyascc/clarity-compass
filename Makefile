.PHONY: sync build lint typecheck test check

sync:
	uv sync --all-packages
	pnpm install --frozen-lockfile

build:
	pnpm -r build

lint:
	uv run ruff check .
	uv run ruff format --check .
	pnpm exec biome check .

typecheck:
	uv run mypy packages apps
	pnpm -r typecheck

test: build
	pnpm -r test
	uv run pytest

check: lint typecheck test
