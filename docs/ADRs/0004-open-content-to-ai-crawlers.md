# ADR 0004: Open Site Content to AI Crawlers and Agents

Date: 2026-09-26
Status: Accepted

## Context

AI models and agents increasingly shape how people find and understand
religious and spiritual traditions. Quakers are a small community with a
distinctive perspective (on peace, equality, simplicity and discernment) that
can balance other voices in those models. If Western Friend content is missing
from AI training data and agent answers, that perspective is missing too.

Until September 2026 the site did the opposite. Cloudflare injected a managed
`robots.txt` with `Content-Signal: ai-train=no` and `Disallow: /` for GPTBot,
ClaudeBot, CCBot and other AI crawlers. Its "Block AI bots" rule returned 403
to those crawlers. Super Bot Fight Mode and a site-wide rate limit (about five
requests per ten seconds) challenged most other automated clients, including
`/sitemap.xml` and `/robots.txt` themselves. The
[isitagentready.com](https://isitagentready.com/westernfriend.org) scan scored
the site 19 (Level 0).

We considered three options:

- **Keep blocking AI training, allow search and AI answers**
  (`ai-train=no, ai-input=yes`). This protects the content from being used as
  training data, but training is where lasting representation in models
  comes from.
- **Open everything, including turning off bot protection.** This is simplest
  for agents, but Super Bot Fight Mode challenges about 20,000 spoofed-browser
  scraper requests a day. Those requests are not AI crawlers, and serving them
  would load the origin for no benefit.
- **Open content for any use, and keep bot protection for traffic that isn't
  a declared crawler.** We chose this option.

## Decision

Western Friend content may be used for search, AI answers and AI training.

In the application:

- `robots.txt` (`common.views.robots_txt`) declares
  `Content-Signal: search=yes, ai-input=yes, ai-train=yes`
  (`ROBOTS_CONTENT_SIGNAL`, see [contentsignals.org](https://contentsignals.org/)).
  It disallows only private and transactional paths (`/admin/`, `/accounts/`,
  cart, orders and payment) and `/search/`, whose results are expensive to
  render and endless for crawlers.
- `/llms.txt` (`common.views.llms_txt`) gives agents a Markdown map of the
  site built from the navigation menu ([llmstxt.org](https://llmstxt.org/)).
- HTML responses carry an RFC 8288 `Link` header pointing to `llms.txt` and
  the sitemap (`common.middleware.DiscoveryLinkHeaderMiddleware`).
- The sitemap is cached until pages change, so crawlers with short timeouts
  can fetch it.

At the Cloudflare edge (these settings live outside the repository):

- Cloudflare no longer manages `robots.txt`; the application's file is the
  only source.
- AI crawler blocking and AI Labyrinth are off.
- Super Bot Fight Mode stays on. Narrow WAF Skip rules exempt the discovery
  files (`/robots.txt`, `/sitemap.xml`, `/llms.txt`, `/.well-known/`) and the
  Internet Archive (verified archivers and its network), so they are reachable
  by any client.
- Rate limits apply to transactional paths and POST requests, not to reading
  content pages.

We record the reasons here rather than the live Cloudflare settings, which
change over time. Check the Cloudflare dashboard for the current state.

## Consequences

- **Positive:** declared crawlers and AI agents can discover and read the
  whole public site, and the signals tell them it may be used for any
  purpose. The agent-readiness score rose to 33 (Level 2). The Wayback
  Machine can archive every page.
- **Negative:** content used for training can't be withdrawn later. Changing
  the signal only affects future crawls, so reversing this decision is
  expensive. We also get nothing in return from AI companies for this use.
- **Negative:** agents that pose as browsers or don't identify themselves are
  still challenged by Super Bot Fight Mode on content pages. That is a
  deliberate trade-off against scraper load.
- **Future:** revisit when bots can pay for access (pay-per-crawl or x402,
  #1242). That could let us relax bot protection without subsidizing
  scrapers. Serving Markdown to agents (#1243) and caching public pages at the
  edge (#1239) should make it cheaper to let more automated traffic through.
  Supersede this ADR if the organization changes its position on AI training.
