# ADR 0006: Give the Editor Control Over Crawler and AI Use

Date: 2026-09-27
Status: Accepted
Decided by: website maintainer

## Context

Western Friend follows an open publication model. New magazine content is
available only to subscribers for a limited time and then becomes free to
read, and the archive is public all the way back to 1929.

Crawlers, including AI crawlers, were already reading the public site and
could use what they read however they chose. Western Friend had never stated
a policy. In practice, the decision about how our content was used had been
made by crawler operators and by the defaults of the platforms we use, not by
Western Friend. Nobody reading the site, and nobody at Western Friend, could
see what the policy was.

AI models and agents increasingly shape how people find and understand
religious and spiritual traditions. Quakers are a small community, and the
many perspectives Friends hold are easily drowned out. How Western Friend's
writing reaches AI, or doesn't, is a question about the publication's voice.
That makes it an editorial question, not only a technical one.

We considered these options:

- **Leave the policy implicit.** Crawlers keep deciding for us, and nobody
  can see or question the result.
- **Rely on a platform's managed setting,** such as Cloudflare's option to
  block AI training. The choice would follow a vendor's defaults and live
  outside Western Friend's editorial workflow.
- **Fix a policy in code or edge settings.** This is explicit, but the
  decision would sit with whoever maintains the site, and changing it would
  need a developer.
- **Give the Editor explicit control through simple settings, defaulting to
  the observed status quo.** We chose this option.

## Decision

How crawlers and AI systems may use Western Friend's public content is an
editorial decision, owned by the Editor.

Preservation by the Internet Archive isn't part of this policy. It stays
broadly allowed, as ADR 0005 describes.

- **Simple choices, not rules.** The Editor controls the site-wide policy
  with plain options in the Wagtail admin: whether content may be used for
  search, for AI answers, and for AI training, and whether the site publishes
  guides that help agents find their way around. The Editor doesn't write
  patterns, rules or configuration files (#1288, #1291).
- **Per-work exceptions.** The Editor can exclude an individual work, for
  example when a contributor asks. An excluded work carries its own
  machine-readable preference against AI use, and stays available to readers
  and, if the site allows, to search engines (#1289, #1293).
- **Exceptions only restrict.** A per-work exception can narrow the site-wide
  policy but never widen it. For example, an excluded work's search
  preference follows the site's search choice.
- **Exceptions are signals, not blocking.** We don't keep lists of named AI
  crawlers to shut out of excluded works. Blocking is enforcement, which
  belongs with the safeguards below, and such lists go stale as crawlers are
  added and renamed.
- **Defaults match the status quo.** Everything was already being read and
  used, so every option defaults to open. Stating that default makes current
  practice visible. Any change from it is a deliberate editorial act.
- **The policy is published.** Crawlers and readers can see it, in
  machine-readable form, at predictable addresses.
- **Public means what an anonymous visitor can read.** Subscriber-only
  content isn't offered to crawlers until it becomes free.
- **The signals state Western Friend's preference, not a licence.** Much of
  our content is by outside writers, artists and photographers. They can ask
  the Editor to exclude their work, and Western Friend tells them how where
  they submit work.
- **Safeguards stay separate from policy.** Protecting the site from
  disguised or overloading traffic, and keeping private and transactional
  areas such as accounts and checkout out of reach, remains the maintainer's
  job. Crawlers and agents that identify themselves and crawl at a reasonable
  rate are served according to the Editor's policy.

At the time of writing, the Editor sets the policy in the "Crawlers and AI"
site setting, and can exclude a magazine article with a checkbox on the
article. `docs/ai-opt-out.md` describes the signals the site publishes.

## Consequences

- **Positive:** transparency. Western Friend's position on crawler and AI use
  is stated openly instead of being implied by whatever crawlers do.
- **Positive:** governance and agency. The people responsible for the
  publication decide how it's used, can change that decision without a
  developer, and can make exceptions for individual contributors.
- **Positive:** with the default policy, Quaker perspectives from Western
  Friend can reach search engines, AI assistants and the models behind them,
  consistent with how we already publish.
- **Negative:** signals are requests, not enforcement. Crawlers that ignore
  them aren't stopped by the policy. Few crawlers read per-work preferences
  yet, so today an exclusion is mostly a stated wish.
- **Negative:** any change applies only to future use. Content already
  collected for training can't be withdrawn.
- **Negative:** with the default policy, pages that name real people, such
  as memorials and directory contacts, are included. Anything that shouldn't
  enter AI training shouldn't be public on the site.
- **Negative:** AI models may paraphrase Friends inaccurately, merge distinct
  Quaker traditions, or not credit Western Friend. AI answers may also mean
  fewer visits, and visits are how readers find subscriptions and donations.
  Some Friends object to AI itself. The Editor weighs these when setting the
  policy.
- **Negative:** the Editor takes on a new responsibility and needs clear,
  plain-language explanations of what each option means.
- **Negative:** serving crawlers costs server capacity. Edge caching
  (ADR 0004) keeps that cost down.
- **Future:** revisit if agents gain reliable ways to prove who they are, or
  if paid access for crawlers becomes practical, since either could add new
  options for the Editor. Supersede this ADR if responsibility for the policy
  moves elsewhere, for example to the board.
