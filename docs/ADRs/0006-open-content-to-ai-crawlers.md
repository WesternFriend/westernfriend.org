# ADR 0006: Open Site Content to AI Crawlers and Agents

Date: 2026-09-27
Status: Accepted
Decided by: website maintainer

## Context

Western Friend follows an open publication model. New magazine content is
available only to subscribers for a limited time and then becomes free to
read, and the archive is public all the way back to 1929. Earlier decisions
followed from that model, and this one extends it to a new kind of reader.

AI models and agents increasingly shape how people find and understand
religious and spiritual traditions. Quakers are a small community, and the
many perspectives Friends hold are easily drowned out. If Western Friend
content is missing from AI training data and agent answers, those
perspectives are missing too.

Crawlers, including AI crawlers, were already reading the public site. We
had never stated a policy on how they could use what they read, so in
practice the rule was implicit. In September 2026 we also found that our bot
protection was stopping many crawlers and agents, including their requests
for the files that describe the site.

We considered these options:

- **Withhold content from AI training, but allow search and AI answers.**
  Cloudflare offers this as a managed setting. We rejected it because the
  open publication model doesn't call for withholding public content.
  Answers that fetch pages on demand disappear when a provider stops
  fetching, while training data lasts, so training is where lasting
  representation comes from.
- **Open some kinds of content but not others,** for example the magazine
  but not memorials or the directory. We rejected this because those pages
  are already public to any reader. Treating AI differently from other
  readers would add complexity without really protecting anyone.
- **Charge crawlers for access now.** Paid crawling is at an early stage,
  and few crawlers support it. Charging would also turn away the readers we
  most want to reach.
- **Remove bot protection entirely.** This is simplest for agents, but most
  of the automated traffic we block is scrapers posing as browsers, not
  crawlers or agents. Serving it would load the site for no benefit.
- **Open public content for any use, and keep protecting against traffic
  that hides what it is or overloads the site.** We chose this option.

## Decision

Public Western Friend content may be used for any purpose, including search,
AI answers and AI training.

- **Public means what an anonymous visitor can read.** Subscriber-only
  content isn't offered to crawlers until it becomes free under the open
  publication model.
- **We state the policy explicitly** to crawlers, in machine-readable form,
  instead of leaving it implicit. Because it's explicit, it can be changed
  explicitly too.
- **The policy stays adjustable without code changes.** Editors should be
  able to change each part of the site-wide policy (search, AI answers, AI
  training) with simple choices in the Wagtail admin, not by writing rules
  (#1288).
- **This is Western Friend's stated preference, not a licence.** Much of our
  content is by outside writers, artists and photographers. Contributors who
  don't want their work offered for AI use can ask Western Friend to exclude
  it. Editors should be able to mark an individual work as excluded, and an
  excluded work must carry its own machine-readable exception so crawlers
  aren't told it's available (#1289). Exclusion applies only to future use;
  copies already collected can't be recalled.
- **We make the site easy for crawlers and agents to discover and read.**
  Machine-readable guides to the site are generated from its own navigation
  and content, so they don't drift from what people see. They list only
  public pages. Some of these conventions (for example llms.txt) are new and
  may be ignored by AI providers. We adopt them because they cost little,
  but readable pages, sitemaps and structured data remain the foundation.
- **Crawlers and agents that identify themselves are welcome if they crawl
  at a reasonable rate.** Bot protection stays in place for automated traffic
  that disguises itself or overloads the site, and for private and
  transactional areas such as accounts and checkout.

At the time of writing this is carried out through `robots.txt` content
signals, `/llms.txt`, discovery links on each page, and Cloudflare bot
settings and skip rules. Those details will change. This decision should
not.

## Consequences

- **Positive:** Quaker perspectives from Western Friend can reach search
  engines, AI assistants and the models behind them, consistent with how we
  already publish. Crawlers get a clear answer instead of an implicit one.
- **Negative:** content used for training can't be withdrawn later.
  Reversing this decision would only affect future use.
- **Negative:** pages that name real people, such as memorials and directory
  contacts, are included. We accept this risk. Anything that shouldn't enter
  AI training shouldn't be public on the site.
- **Negative:** AI models may paraphrase Friends inaccurately, merge distinct
  Quaker traditions, or not credit Western Friend. Being present in AI is
  not the same as being represented well. Some Friends also object to AI
  itself.
- **Negative:** when an AI answer summarizes an article, the reader may never
  visit the site. Visits are how readers find subscriptions and donations,
  which fund open publishing. We receive nothing in return from AI
  companies. We accept this knowingly.
- **Negative:** serving crawlers costs server capacity. Edge caching
  (ADR 0004) keeps that cost down.
- **Negative:** agents that disguise themselves as browsers may still be
  challenged. We accept that to protect the site from scrapers.
- **Mitigation:** the risks above are reduced by keeping choices open.
  Contributors can have individual works excluded, and the organization can
  narrow or withdraw the site-wide policy at any time, affecting all future
  use. Both become editor tasks in the admin once #1288 and #1289 are done. Clear bylines and structured data help AI
  systems credit Western Friend and its writers.
- **Future:** revisit if agents gain reliable ways to prove who they are,
  which would let us admit them without admitting scrapers, or if paid
  access becomes practical. Supersede this ADR if the organization changes
  its open publication model or its position on AI training. ADR 0005 covers
  preservation by the Internet Archive.
