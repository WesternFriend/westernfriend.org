# ADR 0005: Let the Editor Decide Whether the Internet Archive Preserves the Site

Date: 2026-09-27
Status: Accepted
Decided by: website maintainer

## Context

Western Friend follows an open publication model: new magazine content is
subscriber-only for a limited time and then free to read, and the archive is
public back to 1929. The magazine, library and memorials form a public record
of Quaker life in the western United States.

Web pages move, change and disappear, especially across platform migrations.
The Internet Archive's Wayback Machine keeps dated copies independently of
us, so readers, researchers and anyone citing Western Friend can still reach a
page as it was, even if our site changes or goes away.

Whether the Archive could preserve the site had never been decided by anyone
at Western Friend. It depended on technical settings. The site's
`robots.txt` has always allowed the Archive, but in September 2026 we found
that our bot protection was challenging its crawlers, so captures were
failing without anyone having chosen that.

We considered these options:

- **Leave it to technical settings.** This is how we got here: an
  unintended side effect decided the outcome.
- **Make archiving a fixed technical rule.** This is reliable, but the
  choice would sit with whoever maintains the site rather than with the
  people responsible for what Western Friend publishes.
- **Make archiving an editorial choice, defaulting to what was already
  intended.** We chose this option.

## Decision

Whether the Internet Archive may preserve Western Friend's public pages is an
editorial decision, owned by the Editor.

- **The default is on.** Our `robots.txt` has always allowed the Archive, so
  allowing it matches existing practice. Changing it is a deliberate
  editorial act.
- **Public means what an anonymous visitor can read.** Subscriber-only
  content is archived only once it becomes free.
- **When archiving is on, it must actually work.** Bot protection and rate
  limits must not stop the Archive's crawlers or people using the Wayback
  Machine's "Save Page Now". Making that happen is the maintainer's job, not
  the Editor's.
- **The Archive is identified by means that are hard to fake,** such as its
  verified crawler status and the network it operates, never by a user agent
  string alone, since any scraper can copy one.

At the time of writing, archiving is on through `robots.txt` and a
Cloudflare skip rule named **Allow Internet Archive**. The Editor's choice is
applied by the maintainer until it's available in the Wagtail admin.

## Consequences

- **Positive:** there is a durable, independent copy of our publishing
  history that doesn't depend on this site or its hosting, and whether it
  exists is Western Friend's decision rather than an accident of
  configuration.
- **Negative:** when archiving is on, we trust the Internet Archive more than
  other automated traffic. If abusive traffic ever came from its network, the
  exemption would let it through.
- **Negative:** archived copies outlive our own edits, and turning archiving
  off doesn't remove them. A page we later correct, unpublish or remove stays
  visible in the Archive. The likeliest case is a memorial or directory entry
  about a real person, changed at a family's or member's request. Removing an
  archived copy depends on the Internet Archive's own removal process.
- **Future:** revisit if the Archive changes how it identifies itself, or if
  captures start failing again.
