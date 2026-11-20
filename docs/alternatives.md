# Clarity Compass as an open source alternative

People usually find Clarity Compass while looking for a **Plerdy alternative**,
a **Hotjar alternative**, a **Microsoft Clarity alternative** or a free,
self-hosted **AI heatmap tool**. This page explains where it fits next to
those products and where it does not.

## The short version

Most heatmap and UX analytics tools record real visitors. You add a tracking
script to the site, wait for traffic, then read heatmaps and session replays
built from that traffic.

Clarity Compass works the other way round. It opens the site in a real
browser, explores it like a visitor would and **predicts** where people look
and click with saliency models, then runs an AI UX review and a functional
audit that actually clicks, types and opens things. Nothing is installed on
the audited site and no visitor data is collected.

That makes it useful when:

- the site is new, in staging or has too little traffic for a heatmap;
- you cannot add a third party tracking script (privacy, consent, client
  sites, regulated industries);
- you want an audit of a competitor's or a prospect's site;
- you want the results on your own server, under your own AI key.

It is not a replacement for session replay, funnels or surveys built from
real visits. Many teams run both: predicted attention before launch, recorded
behaviour after it.

## Compared with popular tools

| | Clarity Compass | Plerdy | Hotjar | Microsoft Clarity | Attention Insight |
|---|---|---|---|---|---|
| Source of the heatmap | Predicted | Recorded visitors | Recorded visitors | Recorded visitors | Predicted |
| Tracking script on the site | Not needed | Required | Required | Required | Not needed |
| Works without traffic | Yes | No | No | No | Yes |
| Session replay | No | Yes | Yes | Yes | No |
| Self-hosted | Yes | No | No | No | No |
| Open source | Yes, Apache-2.0 | No | No | No | No |

On top of the heatmap, Clarity Compass adds:

- **click prediction**, scored separately from attention;
- an **AI UX review** of every page against its purpose, using Claude;
- a **functional audit** in a real browser: broken links, dead buttons,
  failing forms, console and network errors, with every confirmed issue
  marked as verified and everything else as a prediction;
- a **browser extension** that draws the findings on the live site;
- **free** use: you pay only for your own AI usage.

Feature sets of other products change; check their own sites for the current
details.

### Plerdy alternative

Plerdy combines click heatmaps, session replay, an SEO checker and conversion
reports, all fed by its tracking code. Clarity Compass covers the audit side
without the tracking code: predicted attention and clicks, an AI design review
and a functional audit, viewable on a replay of the page or on the live site
through the browser extension.

### Hotjar alternative

Hotjar is built around recordings, heatmaps and on-site surveys from real
visitors. If what you need is an expert opinion of a page before or without
traffic, Clarity Compass gives you that, self-hosted and free.

### Microsoft Clarity alternative

Microsoft Clarity is free but runs on Microsoft's servers and needs its script
on every page. Clarity Compass keeps everything on your own machine or server
and needs no script at all. The two are unrelated projects despite the similar
name.

### Attention Insight and other predictive heatmap tools

Predictive attention tools estimate where eyes land from a screenshot or a
design. Clarity Compass does the same with an ensemble of UI-trained saliency
models (attention at 1, 3 and 7 seconds), and adds click prediction, a full
site crawl across desktop, tablet and mobile, an AI review and a functional
audit.

## Try it

- Run it locally or on your own domain: [deployment guide](deployment.md).
- How it is built: [architecture](architecture.md).

Plerdy, Hotjar, Microsoft Clarity, Attention Insight and other names on this
page are trademarks of their owners. Clarity Compass is not affiliated with
or endorsed by any of them.
