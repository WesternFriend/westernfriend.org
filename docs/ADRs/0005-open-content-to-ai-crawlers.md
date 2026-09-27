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

In September 2026 we found that, in practice, crawlers and agents couldn't
reliably reach the site. Our bot protection was challenging them, including
their requests for the files that tell them what the site contains.

We considered three options:

- **Allow search and AI answers, but not training.** This would withhold
  content from training data, which the open publication model doesn't call
  for. Training is also where lasting representation in models comes from.
- **Remove bot protection entirely.** This is simplest for agents, but most
  of the automated traffic we block is scrapers posing as browsers, not
  crawlers or agents. Serving it would load the site for no benefit.
- **Open public content for any use, and keep protecting against traffic
  that hides what it is.** We chose this option.

## Decision

Public Western Friend content may be used for any purpose, including search,
AI answers and AI training.

- We say so explicitly to crawlers, in machine-readable form, rather than
  leaving it unstated.
- We make the site easy for crawlers and agents to discover and read.
- Crawlers and agents that identify themselves are welcome. Bot protection
  stays in place for automated traffic that disguises itself, and for private
  and transactional parts of the site such as accounts and checkout.

At the time of writing this is carried out through `robots.txt` content
signals, `/llms.txt`, discovery links on each page, and Cloudflare bot
settings and skip rules. Those details will change. This decision should
not.

## Consequences

- **Positive:** Quaker perspectives from Western Friend can reach search
  engines, AI assistants and the models behind them, consistent with how we
  already publish.
- **Negative:** content used for training can't be withdrawn later, so
  reversing this decision would only affect future use. We also receive
  nothing in return from AI companies.
- **Negative:** agents that disguise themselves as browsers may still be
  challenged. We accept that to protect the site from scrapers.
- **Future:** revisit if crawlers can pay for access, which could let us
  relax bot protection without subsidizing scrapers (#1242). Supersede this
  ADR if the organization changes its open publication model or its position
  on AI training. ADR 0004 covers preservation by the Internet Archive.
