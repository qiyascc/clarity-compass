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

## Configure

```sh
cp .env.example .env
uv run python -m clarity_api generate-secret   # CLARITY_SECRET_KEY
uv run python -m clarity_api generate-secret   # CLARITY_CREDENTIALS_KEY
uv run python -m clarity_api hash-password     # CLARITY_ADMIN_PASSWORD_HASH
```

Set `CLARITY_ADMIN_USERNAME` to the name you sign in with. The password hash
contains `$` characters, so wrap it in single quotes in `.env`:
`CLARITY_ADMIN_PASSWORD_HASH='$argon2id$v=19$...'`. Also set a real
`POSTGRES_PASSWORD` and, for the design review, `ANTHROPIC_API_KEY`.

To let more people sign in, hash a password for each of them and list them in
`CLARITY_USERS` as JSON, again in single quotes:
`CLARITY_USERS='{"alex": "$argon2id$v=19$..."}'`. Every account has full
access. Removing a name from the list signs that person out on their next
request.

## Run it locally

```sh
docker compose -f infra/compose.yaml --env-file .env up -d --build
```

Open <http://127.0.0.1:8080>. Without HTTPS the browser drops secure cookies,
so keep `CLARITY_SECURE_COOKIES=false` for a local run.

## Deploy on your own domain

The panel listens on `CLARITY_HTTP_PORT`, which defaults to `127.0.0.1:8080` so
Docker does not publish it past the host firewall. A reverse proxy on the host
terminates TLS and forwards to it.

1. Point an `A` (and `AAAA`) record for your domain at the server.
2. Copy [`infra/nginx/host.conf.example`](../infra/nginx/host.conf.example) to
   `/etc/nginx/sites-available/`, replace `panel.example.com` with your domain
   and enable it.
3. Get a certificate, for example with
   `certbot certonly --webroot -w /var/www/letsencrypt -d your.domain`, then
   `nginx -t && systemctl reload nginx`.
4. Set `CLARITY_SECURE_COOKIES=true` and restart the stack.

Any other TLS proxy works as long as it forwards to `127.0.0.1:8080` and
overwrites `X-Forwarded-For` with the client address: the panel uses it to
throttle failed sign-ins per visitor.

Visitors who are not signed in see a public page that links to the
repository; the admin area lives behind `/login`.

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
