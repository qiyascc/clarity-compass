# Clarity Compass

Clarity Compass visits a website in a real browser, scrolls and explores it like
a person would, predicts where visitors look and click, audits the experience
the way a senior UX designer would, and pins every finding directly onto the
page it belongs to.

Nothing has to be installed on the audited site.

## What it does

- **Explores** - Playwright drives Chromium through the site: full-height
  scroll, page discovery from sitemaps and internal links, desktop / tablet /
  mobile viewports, console and network capture.
- **Predicts attention** - an ensemble of UI-trained saliency models
  (Foveacast, MediaAttention) estimates where eyes land at 1, 3 and 7 seconds.
- **Predicts clicks** - scored separately from attention, using DOM geometry,
  affordance and visual prominence.
- **Audits** - an LLM-backed UX designer reviews each page against its purpose;
  a functional auditor actually clicks, opens and types to confirm what is
  broken. Anything not reproduced in the browser is labelled as a prediction.
- **Overlays** - findings, heatmaps and click scores are drawn on a replay of
  the captured page or on the live site through the browser extension.

## Status

Early development. See [docs/roadmap.md](docs/roadmap.md) and
[docs/architecture.md](docs/architecture.md).

## Development

Requirements: Python 3.12 with [uv](https://docs.astral.sh/uv/), Node 24 with
pnpm, PostgreSQL 16.

```sh
cp .env.example .env            # fill in database URLs and secrets
make sync
uv run playwright install chromium
make build                      # probe bundles and the panel
(cd packages/persistence && uv run alembic upgrade head)

uv run uvicorn clarity_api.main:app --port 8000
uv run python -m clarity_worker
pnpm --filter @clarity-compass/panel dev
```

`make check` runs linters, type checkers and all tests.

## Deployment

Docker Compose on a single host. See [docs/deployment.md](docs/deployment.md).

## License

Apache-2.0 with an attribution requirement. See [LICENSE](LICENSE) and
[NOTICE](NOTICE).
