# Deployment

The stack runs on a single host with Docker Compose.

| Service    | Role                                                | Networks         |
| ---------- | --------------------------------------------------- | ---------------- |
| `postgres` | Application data and the Procrastinate job queue    | internal         |
| `migrate`  | Applies Alembic migrations, then exits              | internal         |
| `api`      | FastAPI backend for the admin panel                 | internal         |
| `worker`   | Playwright / Chromium analysis worker               | internal         |
| `egress`   | Smokescreen proxy, the only way out to the internet | internal, public |

The `internal` network has no route to the outside. The worker reaches audited
sites only through Smokescreen, which refuses loopback, private, link-local and
other non-public destinations after DNS resolution, so redirects and
subresources cannot be used to reach the host or the internal network.

## First start

```sh
cp .env.example .env
uv run python -m clarity_api generate-secret   # CLARITY_SECRET_KEY
uv run python -m clarity_api generate-secret   # CLARITY_CREDENTIALS_KEY
uv run python -m clarity_api hash-password     # CLARITY_ADMIN_PASSWORD_HASH
docker compose -f infra/compose.yaml --env-file .env up -d --build
```

The panel is served on `CLARITY_HTTP_PORT` (default `8080`). Put it behind a
TLS-terminating reverse proxy and keep `CLARITY_SECURE_COOKIES=true`.

`CLARITY_CREDENTIALS_KEY` encrypts stored site logins. Changing it makes
existing credentials unreadable; re-enter them in the panel afterwards.
