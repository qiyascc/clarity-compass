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

## Language model

The design review, the prioritised plan and fix simulations use a language
model; checks, attention prediction and the functional audit do not.

| Variable              | Meaning                                                                 |
| --------------------- | ----------------------------------------------------------------------- |
| `CLARITY_AI_PROVIDER` | `anthropic` (default), `openai` or `none`                               |
| `CLARITY_AI_MODEL`    | Model id; Claude defaults to `claude-opus-5-5`                          |
| `CLARITY_AI_BASE_URL` | For `openai`: any OpenAI-compatible endpoint, e.g. vLLM serving Qwen-VL |
| `ANTHROPIC_API_KEY`   | Claude API key                                                          |
| `OPENAI_API_KEY`      | Key for the OpenAI-compatible endpoint, if it needs one                 |

The worker reaches the model through the egress proxy like everything else.

## Logins

Site logins entered in the panel are encrypted with `CLARITY_CREDENTIALS_KEY`,
which both the API and the worker need. The worker submits the login form with
writes allowed to that site only for the submission, and never sends the
password to a language model.

## Browser extension

Build it with `pnpm --filter @clarity-compass/extension build` and load
`apps/extension/dist` as an unpacked extension. It talks to the panel address
you enter, using a per-site key generated on the site's page.
