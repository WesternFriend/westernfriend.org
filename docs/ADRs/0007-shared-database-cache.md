# ADR 0007: Shared database cache

Date: 2026-10-06
Status: Accepted

## Context

Before #1219, Django used its default `LocMemCache`. Each Gunicorn worker had
an isolated cache that disappeared on restart, so workers could disagree about
cached values such as PayPal subscription status. Wagtail's cache-backed
features and future application caching also needed a backend shared across
workers.

Two shared backends were considered:

- **Redis:** Django's `RedisCache` offers a purpose-built, fast cache and avoids
  adding cache reads to PostgreSQL. It requires provisioning and maintaining a
  managed Redis service, however, and the production deployment had PostgreSQL
  but no Redis service.
- **Database cache:** Django's `DatabaseCache` stores entries in a table in the
  existing PostgreSQL database. It adds no infrastructure, but every cache
  lookup is a database query and cache traffic competes with application data
  for database resources.

This decision is about Django's shared application cache, not HTTP response
caching at the CDN. The separate
[ADR 0004: Edge caching for anonymous visitors](0004-edge-caching-for-anonymous-visitors.md)
covers Cloudflare's cache of eligible anonymous HTML responses. The two layers
have different contents, lifetimes, and invalidation behavior.

## Decision

Use Django's `DatabaseCache` when `DJANGO_CACHE_TABLE` is set in a deployed
environment. The setting names the cache table (currently `wf_cache`); Django
uses its default `LocMemCache` when the variable is unset, including local
development and tests. This preserves existing defaults while allowing
production workers to share cache entries without another service.

Create the database table with Django's `createcachetable` management command
during deployment. The Procfile uses its release phase; the DigitalOcean app
spec runs it with the deployment command because App Platform has no release
phase. With the current single-instance deployment, creating the table there
is adequate. If deployment scales beyond one instance, run table creation once
in a pre-deploy job: concurrent instances can both observe a missing table and
race while creating it.

## Consequences

- **Positive:** Cache entries are shared among workers and survive process
  restarts, without provisioning infrastructure beyond the existing database.
  The backend can be changed to Django's `RedisCache` if the database becomes
  an unsuitable place for cache traffic.
- **Negative:** Every cache hit makes a database query. Cache reads therefore
  add load and latency to the same database serving application data. The
  database cache also defaults to a maximum of 300 entries; Django culls entries
  when the table grows beyond that limit, so a workload needing a larger stable
  working set may see more cache misses.
- **Future:** Revisit if cache-query load or latency becomes material, if the
  application needs more than the default 300-entry working set, if deployment
  scales to multiple instances (move table creation to a one-time pre-deploy
  step), or if a managed Redis add-on becomes inexpensive enough to justify its
  operational cost. This follows the shared-cache choice in #1219 and supports
  follow-on work such as #1246.
