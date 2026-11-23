FROM node:24-slim AS bundles
RUN corepack enable
WORKDIR /src
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml tsconfig.base.json ./
COPY packages/probe/package.json packages/probe/
RUN pnpm install --frozen-lockfile --filter @clarity-compass/probe
COPY packages/probe packages/probe
RUN pnpm --filter @clarity-compass/probe build

FROM mcr.microsoft.com/playwright/python:v1.65.2-noble
COPY --from=ghcr.io/astral-sh/uv:0.13 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY packages/core/pyproject.toml packages/core/
COPY packages/persistence/pyproject.toml packages/persistence/
COPY packages/saliency/pyproject.toml packages/saliency/
COPY packages/ai/pyproject.toml packages/ai/
COPY apps/api/pyproject.toml apps/api/
COPY apps/worker/pyproject.toml apps/worker/
RUN uv sync --frozen --no-dev --no-install-workspace --package clarity-worker

COPY packages/core packages/core
COPY packages/persistence packages/persistence
COPY packages/saliency packages/saliency
COPY packages/ai packages/ai
COPY apps/worker apps/worker
RUN uv sync --frozen --no-dev --package clarity-worker
RUN /app/.venv/bin/python -m clarity_saliency fetch /app/models
COPY --from=bundles /src/packages/probe/dist /app/bundles

ENV PATH="/app/.venv/bin:$PATH" CLARITY_BUNDLE_DIR=/app/bundles CLARITY_MODEL_DIR=/app/models
RUN mkdir -p /data/artifacts && chown pwuser /data/artifacts
COPY --chmod=755 infra/docker/worker-entrypoint.sh /usr/local/bin/worker-entrypoint
USER pwuser
ENTRYPOINT ["worker-entrypoint"]
CMD ["python", "-m", "clarity_worker"]
