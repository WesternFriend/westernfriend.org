# Edge Caching Specification

Status: **Draft for review** · Issue: [#1239](https://github.com/WesternFriend/westernfriend.org/issues/1239) ·
ADR: [0004](../ADRs/0004-edge-caching-for-anonymous-visitors.md)

This document specifies how public pages are served from Cloudflare's edge
cache to anonymous visitors, and how the cache is kept fresh. Once implemented,
it is the authoritative description of the caching rules: update it when a rule
changes.

---

## 1. Findings

### 1.1 What adds `Cache-Control: private`

Django sends no `Cache-Control` header on public pages, and the project has no
code that adds one. The header appears in production only, alongside
DigitalOcean's `x-do-orig-status` and `x-do-app-origin` headers:

```text
GET https://westernfriend.org/robots.txt
cache-control: private
cf-cache-status: BYPASS
x-do-orig-status: 200
x-do-app-origin: 61415a11-…
```

The request passes through two Cloudflare layers: our `westernfriend.org`
zone, then App Platform's own edge, which also runs on Cloudflare. App Platform
does not cache responses from services by default, and marks a response
`private` when the app sends no `Cache-Control` header. Our zone then honours
`private` and bypasses its cache.

**Consequence:** If Django sends an explicit `Cache-Control` header, App
Platform no longer adds `private`. Rollout step 1 (§6) confirms this before we
rely on it.

### 1.2 Per-visitor content on public pages

| Content | Where | Anonymous output | Cache-safe? |
| --- | --- | --- | --- |
| Login / Register links or Log out form | `common/templates/navbar.html` | Login and Register links. `?next=` is the request path, so it matches the URL | Yes |
| Log out form CSRF token | `navbar.html` | Rendered only for authenticated users | Yes (never anonymous) |
| Magazine paywall | `MagazineArticle.get_context` | Full text only when public or featured; otherwise a teaser | Yes, for anonymous visitors |
| Add-to-cart forms | `store/…/book.html`, `add_to_cart.html` | Per-visitor CSRF token | No. Stays uncached until §2.4 is done |
| PayPal subscribe button | `paypal/…/paypal_subscription_plan_button.html` | Per-visitor CSRF token in inline JS | No. The subscription page stays uncached (§2.2 rule 5) |
| Flash messages | `common/templates/base.html` | Only when a message is pending | Guarded by §2.2 rules 5–6 |
| Cart contents | `cart/`, `orders/` | Session-backed | Excluded by path and by session cookie |
| Subscription redirect | `SubscriptionIndexPage.serve` | Redirects only authenticated subscribers | Yes |
| Wagtail view-restricted pages | Wagtail core | Password or login form | Guarded by rules 4–6 |

There is **no cart count** in the navbar, so it needs no change.

**CSRF and cookies:** In Django 6, any `get_token()` call, for example
rendering `{% csrf_token %}`, sets `CSRF_COOKIE_NEEDS_UPDATE`. Django then
sends `Set-Cookie: csrftoken` on that response, even when the visitor already
has the cookie. So "the response sets no cookies" reliably detects a page with
a CSRF token. The same check catches message-cookie updates and new sessions.

---

## 2. Origin changes

### 2.1 Middleware

`common.middleware.PublicCacheControlMiddleware` decides the caching headers
for every response. It sits **directly after `SecurityMiddleware`**. Middleware
response phases run in reverse order, so it runs after the Session, CSRF,
Messages and Auth middleware have added their cookies and `Vary` headers.

### 2.2 Rules

A response is **public** when *all* of these hold:

1. `PUBLIC_CACHE_EDGE_TTL > 0` (feature switch)
2. The request method is `GET` or `HEAD`
3. The response status is `200`
4. The response has no `Cache-Control` header yet. Headers set by views and
   by Wagtail, such as those on restricted pages or previews, are left alone.
5. The response sets **no cookies** (`response.cookies` is empty)
6. The request carries **no session cookie** (`settings.SESSION_COOKIE_NAME`)
7. `request.user` is not authenticated (defence in depth)
8. The path does not start with an excluded prefix:
   `/admin/`, `/accounts/`, `/cart/`, `/orders/`, `/payment/`, `/paypal/`,
   `/documents/`, `/__reload__/`
   (the Cloudflare cache rule's exclusions, plus Wagtail documents and dev tooling)

Public responses get:

```http
Cache-Control: public, max-age=<PUBLIC_CACHE_BROWSER_TTL>, s-maxage=<PUBLIC_CACHE_EDGE_TTL>, private="Set-Cookie"
```

`private="Set-Cookie"` tells shared caches not to store the `Set-Cookie`
header; the rest of the response stays cacheable. It is needed because our zone
reaches Django through App Platform's own Cloudflare layer (an
"orange-to-orange" setup). That layer adds a `__cf_bm` bot-management cookie
to every response, and Cloudflare [won't cache a response that sets a
cookie](https://developers.cloudflare.com/cache/troubleshooting/bot-management-o2o-cache-bypass/).
With the directive, Cloudflare drops only that header and caches the page.
This is safe because of rule 5: a response that Django itself sets a cookie on
is never public.

Every other response that has no `Cache-Control` header gets
`Cache-Control: private`. This keeps today's behaviour, but set explicitly, so
it no longer depends on App Platform.

### 2.3 Settings

| Setting | Env var | Default | Production |
| --- | --- | --- | --- |
| `PUBLIC_CACHE_EDGE_TTL` | `DJANGO_PUBLIC_CACHE_EDGE_TTL` | `0` (off) | `900` (15 minutes) |
| `PUBLIC_CACHE_BROWSER_TTL` | `DJANGO_PUBLIC_CACHE_BROWSER_TTL` | `60` | `60` |

**Why 15 minutes:** Wagtail purges an edited page as soon as it is published
(§3), so the TTL only limits staleness for content that is *not* purged:
listing pages, pagination, and site-wide settings (§3.3). Pages rarely change,
so nearly every request inside the window is a cache hit. Fifteen minutes is
also the upper end of the range in the issue. Browsers keep pages for only a
minute because we cannot purge them.

`Vary: Cookie` stays as Django sets it. Cloudflare ignores it, and the rules
above make that safe.

### 2.4 Cacheable store pages (proposed, not yet implemented)

Tracked in [#1252](https://github.com/WesternFriend/westernfriend.org/issues/1252).

Store pages carry add-to-cart forms, so they are among the pages worth
caching. Today each form renders `{% csrf_token %}`, which sets a cookie and
keeps the page out of the cache (rule 5). Store pages therefore stay private
until the change below lands in a follow-up. It replaces a CSRF token with an
origin check, so it needs its own security review.

- Remove `{% csrf_token %}` from `store/templates/store/book.html` and
  `store/templates/store/add_to_cart.html`.
- Mark `cart.views.cart_add` `@csrf_exempt`. In its place, reject the `POST`
  with 403 unless it is same-origin: the `Sec-Fetch-Site` header is
  `same-origin`, or, when that header is missing, the `Origin` header matches
  the request host.
- **Why this is safe:** the only effect is adding an item to the visitor's own
  session cart. The session cookie is `SameSite=Lax`, so browsers do not send
  it on a cross-site `POST`. The origin check blocks cross-site form posts even
  without that cookie. The form still works without JavaScript.

---

## 3. Purging (freshness)

### 3.1 Wagtail front-end cache, as shipped

- Add `wagtail.contrib.frontend_cache` to `INSTALLED_APPS`. Custom purge code
  only covers view restrictions (§3.2).
- Configure `WAGTAILFRONTENDCACHE` with `CloudflareBackend` **only when**
  `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ZONE_ID` are set, so local development
  and tests never call Cloudflare:

  ```python
  if os.getenv("CLOUDFLARE_API_TOKEN") and os.getenv("CLOUDFLARE_ZONE_ID"):
      WAGTAILFRONTENDCACHE = {
          "cloudflare": {
              "BACKEND": "wagtail.contrib.frontend_cache.backends.CloudflareBackend",
              "BEARER_TOKEN": os.environ["CLOUDFLARE_API_TOKEN"],
              "ZONEID": os.environ["CLOUDFLARE_ZONE_ID"],
          },
      }
  ```

- Use an API token scoped to **Zone → Cache Purge** on `westernfriend.org`
  only, stored as an App Platform secret. Do not use the global API key. An
  account API token (prefix `cfat_`, created under **Manage Account → Account
  API Tokens**) works: it supports Cache, and Wagtail sends it as
  `Authorization: Bearer <token>` to `POST /zones/<zone>/purge_cache`.
- Before deploying, check the token is active, then that it can purge one URL:

  ```bash
  # Account API token (prefix cfat_)
  curl "https://api.cloudflare.com/client/v4/accounts/78e20e36a31af4c118ea41a51efe6f81/tokens/verify" \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"

  # User API token
  curl "https://api.cloudflare.com/client/v4/user/tokens/verify" \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"

  # Either token type: purge one URL
  curl -X POST "https://api.cloudflare.com/client/v4/zones/3f1f299fe6c461d6e331665f9e758cc7/purge_cache" \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
    -H "Content-Type: application/json" \
    --data '{"files": ["https://westernfriend.org/"]}'
  ```

  Run the verify command for your token type, then the purge. Each should
  return `"success": true`. A verify command for the wrong token type fails
  even when the token is valid.
- Wagtail purges a page's URL whenever it is published, including a page's
  first publish, when the purge is harmless, and when it is unpublished. It
  sends the purge as a Django task. Until #1246 lands, the task runs inline,
  adding about 100–300 ms to Publish. That delay is accepted.
- Wagtail's backend sends up to 30 URLs per API call.

### 3.2 View restrictions

Wagtail's purge covers publishing only. Adding a view restriction to a page
does not publish it, so a public copy already in Cloudflare would stay visible
to anonymous visitors until the TTL expires.
`common.signal_handlers.purge_restricted_pages` fixes this: when a
`PageViewRestriction` is saved or deleted, it purges the page and all its live
descendants, because a restriction covers the whole subtree. The purge runs
after the transaction commits, so no request can re-cache the old public copy
in between.

### 3.3 What is not purged

The TTL alone limits how stale these can get (at most 15 minutes):

- Listing pages that show a new or edited page: the home page, magazine index,
  issues, library, news, events and memorials
- Paginated and filtered variants (`?page=2`, facets, `/search/?query=…`)
- Site settings and snippets that appear on every page (navigation menu, footer)
- Tag pages (`/tags/…`), `/sitemap.xml`, and pages that were deleted or moved

When a change must appear at once, use Cloudflare's *Purge Everything* or
*Custom Purge* in the dashboard.

---

## 4. Infrastructure

1. **Disable App Platform edge caching** by setting `disable_edge_cache: true`
   in the live app spec and in `.do/deploy.template.yaml`. Otherwise a second
   cache, which we cannot purge by URL, can sit between our zone and Django and
   serve old pages after a Wagtail purge.
2. **Cloudflare cache rule:** keep the current rule, which skips excluded paths
   and requests with a `sessionid` cookie. Set it to *respect origin
   `Cache-Control`* rather than override the Edge TTL, so Django stays the
   single source of truth.
3. Optional: exclude tracking parameters (`utm_*`, `fbclid`, `gclid`) from the
   cache key so that one page does not produce many cache entries.
4. Add two App Platform variables when Cloudflare purging is set up:
   `CLOUDFLARE_API_TOKEN` (encrypted) and `CLOUDFLARE_ZONE_ID`. Leave them
   unset until then; purging stays off without them.

---

## 5. Tests

Unit tests for the middleware (`common/tests/test_middleware.py`):

| Case | Expected |
| --- | --- |
| Anonymous `GET` 200, TTL > 0 | `public, max-age=60, s-maxage=900, private="Set-Cookie"` |
| TTL = 0 | `private` |
| Authenticated user | `private` |
| Request has session cookie | `private` |
| Response sets a cookie (CSRF form) | `private` |
| `POST`, 302, 404, 500 | `private` |
| Excluded prefix (`/cart/`, `/admin/`, …) | `private` |
| Response already has `Cache-Control` | unchanged |

Integration tests with the Django test client:

- Anonymous home page: `public`, no `Set-Cookie`
- Same page while logged in: `private`
- Anonymous store product page (CSRF form): `private`, sets `csrftoken`

When §2.4 lands, also test that store pages become `public`, and that
`POST /cart/add/<id>/` is accepted with `Sec-Fetch-Site: same-origin` or a
matching `Origin`, and rejected with 403 for `cross-site` or a foreign `Origin`.

---

## 6. Rollout

| Step | Change | Check |
| --- | --- | --- |
| 0 | Record a baseline from Cloudflare Analytics | Done: see [Cloudflare Analytics](../cloudflare-analytics.md#baseline-before-edge-caching) |
| 1 | Deploy the middleware and purge config with TTL `0` (off). In **Settings → Sites**, make sure the default site's hostname is `westernfriend.org` on port `443`: Wagtail builds purge URLs from it | Production returns `private`; publishing a page logs a successful purge |
| 2 | Disable App Platform edge caching | Headers unchanged, site works |
| 3 | Set `DJANGO_PUBLIC_CACHE_EDGE_TTL=900` | Anonymous `curl -I` returns `public …`, then `cf-cache-status: HIT`; a logged-in browser still gets `private` / `BYPASS`; publishing an edit shows it at once |
| 4 | After a week, compare with the baseline | Success measures (§7) |

**Rollback:** set `DJANGO_PUBLIC_CACHE_EDGE_TTL=0`, then *Purge Everything* in
Cloudflare. No deploy is needed.

---

## 7. Success measures

Measured as described in [Cloudflare Analytics](../cloudflare-analytics.md).

- Cloudflare edge hit ratio for HTML at or above 60% (today 0%)
- Origin HTML requests per day down at least 50% from about 23,500. The
  issue's 110,000 counts every HTML response, but Cloudflare already answers
  about 88,000 a day itself with HTTPS redirects, bot challenges and rate
  limits.
- Average origin response time for HTML 200s is 700 ms today, so each cache
  hit saves roughly that much server time
- No reports of personal content (logged-in navbar, subscriber articles, cart)
  shown to the wrong visitor. Spot-check with a logged-in browser and an
  anonymous `curl` after step 3.

---

## 8. Out of scope and follow-ups

- **Background purges:** once #1246 adds a task worker, purges stop delaying
  Publish without any change here.
- **Origin-side page cache** (Django per-site cache or `wagtail-cache` on the
  `DatabaseCache` from #1219): this would complement the edge cache on misses
  and crawler floods. Measure first.
- **`stale-while-revalidate`:** RFC 9111 says `s-maxage` disables it. To serve
  stale pages while Cloudflare revalidates, we would need to move the edge TTL
  into `Cloudflare-CDN-Cache-Control`. Try this after the basics are proven.
- **Short-TTL caching of 404s and 301s** for crawler traffic
- **Cacheable subscription page:** the PayPal button would fetch its CSRF token
  at click time instead of rendering it into the page
