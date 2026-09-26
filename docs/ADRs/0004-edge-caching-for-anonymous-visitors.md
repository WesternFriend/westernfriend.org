# ADR 0004: Edge caching for anonymous visitors

Date: 2026-09-26
Status: Proposed

## Context

Every HTML request reaches Django, about 110,000 a day, and much of it is
crawler traffic. Production responses carry `Cache-Control: private`. Django
does not send that header: DigitalOcean App Platform's edge adds it when the
app sends no `Cache-Control`. So our Cloudflare zone caches nothing
([#1239](https://github.com/WesternFriend/westernfriend.org/issues/1239)).

Cloudflare ignores `Vary: Cookie`, so a cached page goes to everyone. Some
public pages differ per visitor: the navbar login state, the magazine paywall,
and forms with CSRF tokens.

Alternatives considered:

- **A Cloudflare rule that overrides the origin TTL:** rejected. Cloudflare
  cannot see which responses are personal; Django can. It would also need a
  second copy of the rules outside the codebase.
- **An origin-side page cache only** (Django per-site cache or
  `wagtail-cache`): rejected as the primary fix. Every request would still
  reach App Platform. It may be added later to handle misses.
- **Per-view decorators** (`cache_control` on each page type): rejected. They
  are easy to miss on new page types, and they cannot see cookies set later by
  middleware.
- **Custom purge handlers** for listing pages or to skip first publish:
  rejected to keep the change small. Wagtail's built-in purge covers edited
  pages, and a 15-minute TTL bounds the rest.

## Decision

- Add `common.middleware.PublicCacheControlMiddleware`. It marks a response
  `public, max-age=60, s-maxage=<TTL>` only for anonymous `GET`/`HEAD` 200
  responses that meet all of these:
  - the request has no session cookie
  - the response sets no cookies
  - the response has no `Cache-Control` header yet
  - the path is not excluded

  Every other response gets an explicit `private`. The TTL comes from
  `DJANGO_PUBLIC_CACHE_EDGE_TTL`: `900` in production, and the default of `0`
  turns this off.
- Make store pages cacheable. Drop the CSRF token from add-to-cart forms and
  protect `cart_add` with a same-origin check (`Sec-Fetch-Site` or `Origin`)
  instead.
- Purge Cloudflare with Wagtail's built-in `wagtail.contrib.frontend_cache`
  (`CloudflareBackend`, with an API token scoped to cache purge). No custom
  purge code.
- Turn off App Platform edge caching, so that only our zone caches pages.

Full rules: [Edge Caching Specification](../specifications/edge_caching.md).

## Consequences

- **Positive:** Most anonymous and crawler traffic, store pages included, is
  served from Cloudflare. One middleware holds the rules. An environment
  variable turns caching on or off with no deploy.
- **Negative:** New or edited pages can take up to 15 minutes to appear on
  listing pages, and the same goes for settings and snippet changes. Publishing
  waits for a Cloudflare API call, about 100–300 ms, until background tasks
  exist (#1246). The subscription page stays uncached because of its PayPal
  button.
- **Future:** Revisit if editors need listing pages to update at once, when
  adding `stale-while-revalidate`, or to cache the subscription page.
