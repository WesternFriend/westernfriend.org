# ADR 0008: Rendition cache and per-request site root paths

Date: 2026-10-17
Status: Accepted

Supersedes [ADR 0007: Shared database cache](0007-shared-database-cache.md).

## Context

ADR 0007 chose Django's `DatabaseCache` as the shared application cache, gated
by an environment variable and stored in a PostgreSQL table. After #1340 the
switch is `DJANGO_DATABASE_CACHE` and the table is `django_cache`. ADR 0007
still names the earlier `DJANGO_CACHE_TABLE` setting and `wf_cache` table.

Production now runs with that cache on. Every cache read or write is a SQL
query. Two workloads made that cost show up as N+1s in Sentry (#1353):

- **Image renditions.** Wagtail stores rendition lookups in `caches["renditions"]`
  when that alias exists, and otherwise in the default cache. With no alias,
  every `{% image %}` or `{% srcset_image %}` lookup reads `django_cache`, and
  every miss writes. `DatabaseCache.set()` also runs `COUNT(*)` to decide
  whether to cull. Rendition rows already live in `wagtailimages_rendition`,
  so the cache adds queries instead of saving them, and those rows compete
  for the default 300-entry cap with values the shared cache exists for, such
  as PayPal subscription status.
- **Page URLs built without a request.** `Site.get_site_root_paths()` caches
  its result in Django's cache. Wagtail stores that result on the request when
  a request is passed (`{% pageurl %}`, `{% fullpageurl %}`). Without one
  (`page.url`, `page.full_url`, rich text's `PageLinkHandler`), it stores the
  result on the page instance, so each distinct page does its own cache read.
  Rich text cannot pass a request into the link handler.

Redis was considered again for the rendition alias and for the default cache.
It is still not provisioned. Moving only renditions to Redis would add a
service for a cache that is allowed to be wrong for a short time. Moving the
default cache to Redis remains the follow-up if shared-cache query load is
still material after renditions leave the table.

## Decision

Keep the default cache as `DatabaseCache` on `django_cache` when
`DJANGO_DATABASE_CACHE` is true. Local development and tests still use
Django's default `LocMemCache` because `CACHES` stays unset.

When the database cache is on, `core/settings.py` also defines a `renditions`
alias: process-local `LocMemCache`, `LOCATION` `"renditions"`, `TIMEOUT` 60
seconds. Wagtail's `Rendition.cache_backend` then uses that alias. A worker
that did not handle an image edit can serve a stale rendition URL until the
entry expires. Sixty seconds keeps that window short. The rendition row in
`wagtailimages_rendition` remains the source of truth on a miss.

`common/apps.py` memoizes `Site.get_site_root_paths()` for the length of each
HTTP request, the same way it already memoizes `LocaleManager.get_for_language`.
The first call inside a request runs the original method (one cache read, or
a miss plus a write). Later calls return that list. `request_finished` drops
the memo. `Site.clear_site_root_paths_cache()` drops it too, so a site save
during a request is visible to the next call. Outside a request the original
method runs uncached, so tests and management commands do not keep a stale
list across database resets.

Templates that can see the request use `{% pageurl %}` and `{% fullpageurl %}`
so Wagtail caches site root paths on the request object. Sitemap generation
calls `get_sitemap_urls()` with no request; the memoization covers those
`full_url` lookups for the sitemap request.

## Consequences

- **Positive:** Rendition lookups no longer read or write `django_cache` or
  count toward its entry cap. Page URL construction costs one site-root-paths
  cache read per request, including rich text and the sitemap. The shared
  database cache remains for values that must agree across workers.
- **Negative:** Each worker keeps its own rendition cache, so an edited image
  can briefly have a stale rendition URL on workers that did not handle the
  edit. The memoized site root paths can be stale for the rest of a request
  until `clear_site_root_paths_cache()` runs. Every remaining default-cache
  hit is still a database query.
- **Future:** Revisit Redis (`django.core.cache.backends.redis.RedisCache`)
  if `django_cache` query volume or latency is still material after renditions
  leave the table, or if the shared working set needs more than the default
  300 entries. This follows #1353.
