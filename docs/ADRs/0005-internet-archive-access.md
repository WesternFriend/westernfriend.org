# ADR 0005: Let the Internet Archive Preserve Every Public Page

Date: 2026-09-27
Status: Accepted

## Context

Western Friend follows an open publication model: new magazine content is
subscriber-only for a limited time and then free to read, and the archive is
public back to 1929. The magazine, library and memorials form a public record of
Quaker life in the western United States.

Web pages move, change and disappear, especially across platform migrations.
The Internet Archive's Wayback Machine keeps dated copies independently of
us, so readers, researchers and anyone citing Western Friend can still reach a
page as it was, even if our site changes or goes away.

In September 2026 we found that the Archive couldn't reliably capture our
pages, because our bot protection was challenging its crawlers.

## Decision

Every public page should be archivable by the Internet Archive. Bot
protection and rate limits must not stop the Archive's crawlers or people
using the Wayback Machine's "Save Page Now".

We identify the Archive by means that are hard to fake, such as its verified
crawler status and the network it operates. We don't trust a user agent
string alone, since any scraper can copy one.

At the time of writing this is a Cloudflare WAF skip rule named
**Allow Internet Archive**.

## Consequences

- **Positive:** there is a durable, independent copy of our publishing
  history that doesn't depend on this site or its hosting.
- **Negative:** we extend more trust to the Internet Archive than to other
  automated traffic. If abusive traffic ever came from its network, the
  exemption would let it through.
- **Negative:** archived copies outlive our own edits. A page we later
  correct, unpublish or remove stays visible in the Archive, and removing it
  depends on the Internet Archive's own process.
- **Future:** revisit if the Archive changes how it identifies itself, or if
  captures start failing again.
