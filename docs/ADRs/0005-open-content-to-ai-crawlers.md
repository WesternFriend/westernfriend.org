# ADR 0005: Open Site Content to AI Crawlers and Agents

Date: 2026-09-26
Status: Accepted

## Context

Western Friend follows an open publication model. New magazine content is
available only to subscribers for 90 days and then becomes free to read, and
the archive is public all the way back to 1929. Earlier decisions followed
from that model, and this one extends it to a new kind of reader.

AI models and agents increasingly shape how people find and understand
religious and spiritual traditions. Quakers are a small community with a
distinctive perspective (on peace, equality, simplicity and discernment) that
can balance other voices in those models. If Western Friend content is missing
from AI training data and agent answers, that perspective is missing too.

In September 2026 the site was not reachable for these readers in practice.
Super Bot Fight Mode and a site-wide rate limit (about five requests per ten
seconds) challenged most automated clients, including requests for
`/sitemap.xml` and `/robots.txt`. The
[isitagentready.com](https://isitagentready.com/westernfriend.org) scan scored
the site 19 (Level 0). While we investigated, Cloudflare's AI-training block
(a managed `robots.txt` with `ai-train=no`) was switched on by accident for
about 30 minutes. It never reflected policy.

We considered three options:

- **Allow search and AI answers, but not training**
  (`ai-train=no, ai-input=yes`). This would withhold content from training
  data, which the open publication model doesn't call for. Training is also
  where lasting representation in models comes from.
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

- Cloudflare's managed `robots.txt` is off; the application's file is the
  only source.
- AI crawler blocking and AI Labyrinth are off.
- Super Bot Fight Mode stays on. A narrow WAF Skip rule exempts the discovery
  files (`/robots.txt`, `/sitemap.xml`, `/llms.txt`, `/.well-known/`), so any
  client can reach them. The Internet Archive has its own exemption
  (ADR 0004).
- Rate limits apply to transactional paths and POST requests, not to reading
  content pages.
- A few commercial SEO crawlers (such as SemrushBot and AhrefsBot) are blocked
  by user agent. They are neither AI nor archival crawlers, so this decision
  doesn't cover them.

We record the reasons here rather than the live Cloudflare settings, which
change over time. Check the Cloudflare dashboard for the current state.

## Consequences

- **Positive:** declared crawlers and AI agents can discover and read the
  whole public site, and the signals tell them it may be used for any
  purpose. The agent-readiness score rose to 33 (Level 2).
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
  Supersede this ADR if the organization changes its open publication model
  or its position on AI training.
