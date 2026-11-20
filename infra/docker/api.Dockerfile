FROM python:3.12-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.13 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY packages/core/pyproject.toml packages/core/
COPY packages/persistence/pyproject.toml packages/persistence/
COPY apps/api/pyproject.toml apps/api/
COPY apps/worker/pyproject.toml apps/worker/
RUN uv sync --frozen --no-dev --no-install-workspace --package clarity-api

COPY packages/core packages/core
COPY packages/persistence packages/persistence
COPY apps/api apps/api
RUN uv sync --frozen --no-dev --package clarity-api

ENV PATH="/app/.venv/bin:$PATH"
RUN useradd --system --uid 10001 clarity && mkdir -p /data/artifacts && chown clarity /data/artifacts
USER clarity
EXPOSE 8000
CMD ["uvicorn", "clarity_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
