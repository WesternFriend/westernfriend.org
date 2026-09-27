# ADR 0004: Let the Internet Archive Preserve Every Public Page

Date: 2026-09-27
Status: Accepted

## Context

Western Friend follows an open publication model: new magazine content is
subscriber-only for 90 days and then free to read, and the archive is public
back to 1929. The magazine, library and memorials form a public record of
Quaker life in the western United States. Web pages move, change and
disappear, especially across platform migrations like our move from Drupal to
Wagtail. The Internet Archive's Wayback Machine keeps dated snapshots
independently of us, so readers, researchers and anyone citing Western Friend
can still reach a page as it was, even if our site changes or goes away.

`robots.txt` already allowed the Internet Archive, and Super Bot Fight Mode
lets verified bots through. Even so, three days of Cloudflare logs showed no
traffic from verified archivers or from the Internet Archive's network
(AS7941). The Archive's other fetchers, such as Save Page Now (used when a
person asks the Wayback Machine to capture a page) and its Heritrix crawler,
don't always present as verified bots. Super Bot Fight Mode served them
managed challenges, which automated fetchers can't solve, so their captures
could fail.

We considered:

- **Rely on robots.txt and verified-bot status alone.** This is what we had,
  and the logs showed it wasn't working.
- **Match the Archive's user agents.** User agents are easy to spoof, so
  this would open a hole in bot protection for any scraper that copies one.
- **Exempt verified archivers and the Archive's own network.** We chose this.
  Requests from AS7941 come from infrastructure the Internet Archive runs, so
  they can't be spoofed the way a user agent can.

## Decision

Every public page should be archivable by the Internet Archive.

- `robots.txt` (`common.views.robots_txt`) has no rules against archive
  crawlers. It disallows only private and transactional paths, which aren't
  worth archiving.
- A Cloudflare WAF custom rule, **Allow Internet Archive**, skips Super Bot
  Fight Mode and rate limiting for
  `(cf.verified_bot_category eq "Archiver") or (ip.src.asnum eq 7941)`.
  Other WAF custom rules and managed rules still apply.

If a future rule needs to match the Archive by user agent, use `contains`,
not `eq`. `archive.org_bot` appears inside a longer user-agent string.

## Consequences

- **Positive:** anyone can save a Western Friend page to the Wayback Machine,
  and the Archive's crawlers can capture the whole public site. That keeps a
  durable, independent copy of our publishing history.
- **Negative:** every request from AS7941 bypasses bot protection and rate
  limits. That is acceptable because the Internet Archive runs that network
  itself, but if abusive traffic ever came from it, this rule would let it
  through.
- **Negative:** snapshots outlive our own edits. A page we later correct,
  unpublish or remove stays visible in the Archive. Removing it means asking
  the Internet Archive, which we don't control.
- **Future:** check Cloudflare's security events for Archiver traffic
  now and then to confirm captures still succeed. Revisit if the Internet
  Archive changes its networks or starts signing requests (for example with
  Web Bot Auth), which would let us match it more precisely.
  ADR 0005 covers the broader decision to open content to AI crawlers
  and agents.
