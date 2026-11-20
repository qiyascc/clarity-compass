# Architecture

Clarity Compass is a modular monolith split into processes only where isolation
requires it.

```
panel ──► api ──► postgres ◄── worker ──► egress proxy ──► audited site
                     ▲            │
                     └─ job queue ┘
```

## Packages

| Path                   | Purpose                                                     |
| ---------------------- | ----------------------------------------------------------- |
| `packages/core`        | Domain model (profiles, captures, findings) and URL safety  |
| `packages/persistence` | SQLAlchemy models, repositories, migrations, job app        |
| `packages/probe`       | TypeScript bundles injected into pages: DOM probe, snapshot |
| `apps/api`             | FastAPI backend, single-admin auth                          |
| `apps/worker`          | Exploration, capture and analysis pipeline                  |

## Analysis pipeline

1. **Explore** — one isolated browser context per viewport; the start page,
   its sitemap and internal links feed a bounded frontier.
2. **Capture** — each page is scrolled to load lazy content, then captured as
   viewport-sized sections plus a full-page image, a probe of the rendered DOM
   and a replayable snapshot. Console errors and failed requests are kept.
3. **Predict** — attention and click predictions per section _(phase 2)_.
4. **Audit** — design, UX, content and functional review _(phases 3–4)_.

## Safety rules

- Every browser request passes the request policy: non-public destinations and
  mutating methods (`POST`, `PUT`, `PATCH`, `DELETE`) are aborted unless a run
  explicitly allows them.
- In production all browser traffic also leaves through Smokescreen.
- Site credentials are encrypted at rest and never sent to a language model.
- A finding marked `verified` must carry evidence; a verified functional
  finding must carry the trace of the browser action that reproduced it.
