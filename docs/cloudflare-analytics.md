# Cloudflare Analytics

Cloudflare records analytics for the `westernfriend.org` zone automatically;
there is nothing to turn on. The zone is on the Business plan, so request-level
analytics (cache status, origin status, path, bot decision) are kept for 30
days, and daily totals for longer.

Use these numbers to measure edge caching
([specification](specifications/edge_caching.md)). Compare the same days of the
week, because traffic varies a lot from day to day.

## In the dashboard

**Analytics & Logs → HTTP Traffic** for the `westernfriend.org` zone.

1. Set the time range, for example *Previous 7 days*.
2. Add the filter **Edge response content type** equals `html`.
3. Read these breakdowns:
   - **Cache status:** `hit` is served from the edge; `bypass`, `miss` and
     `dynamic` reached Django; `none` was answered by Cloudflare itself, as a
     redirect, bot challenge or rate limit.
   - **Origin response status:** `0` means the request never reached Django.
   - **Path** with the filter *Origin response status > 0*: the pages that
     cost the server the most.

**Caching → Overview** shows the cache hit ratio over time.

## From the GraphQL API

Create an API token with **Zone → Analytics → Read** for `westernfriend.org`,
then run the query below. It covers the last 24 hours; request-level data can
cover at most one day per query.

```bash
ZONE_ID=3f1f299fe6c461d6e331665f9e758cc7
SINCE=$(date -u -v-24H +%Y-%m-%dT%H:%M:%SZ)  # on Linux: date -u -d '24 hours ago' ...
UNTIL=$(date -u +%Y-%m-%dT%H:%M:%SZ)

curl -s https://api.cloudflare.com/client/v4/graphql \
  -H "Authorization: Bearer $CLOUDFLARE_ANALYTICS_TOKEN" \
  -H "Content-Type: application/json" \
  --data @- <<EOF | jq
{"query": "query { viewer { zones(filter: {zoneTag: \"$ZONE_ID\"}) {
  byCache: httpRequestsAdaptiveGroups(limit: 20, orderBy: [count_DESC],
    filter: {datetime_geq: \"$SINCE\", datetime_lt: \"$UNTIL\", edgeResponseContentTypeName: \"html\"}) {
    count dimensions { cacheStatus edgeResponseStatus } }
  origin: httpRequestsAdaptiveGroups(limit: 1,
    filter: {datetime_geq: \"$SINCE\", datetime_lt: \"$UNTIL\", edgeResponseContentTypeName: \"html\", originResponseStatus_gt: 0}) {
    count avg { originResponseDurationMs } }
  topPaths: httpRequestsAdaptiveGroups(limit: 15, orderBy: [count_DESC],
    filter: {datetime_geq: \"$SINCE\", datetime_lt: \"$UNTIL\", edgeResponseContentTypeName: \"html\", originResponseStatus_gt: 0}) {
    count dimensions { clientRequestPath } }
} } }"}
EOF
```

- **Origin HTML requests** = `origin.count`
- **Edge hit ratio** = `hit` ÷ (`hit` + `miss` + `bypass` + `dynamic`) from
  `byCache`

## Baseline before edge caching

Recorded on 2026-09-26, before any public page was cacheable.

**Daily totals** (`httpRequests1dGroups`):

| Date | All requests | HTML responses | Cached |
| --- | ---: | ---: | ---: |
| 2026-09-18 | 177,754 | 160,495 | 0 |
| 2026-09-19 | 163,961 | 156,212 | 0 |
| 2026-09-20 | 161,942 | 153,925 | 0 |
| 2026-09-21 | 106,508 | 98,897 | 0 |
| 2026-09-22 | 105,456 | 96,812 | 0 |
| 2026-09-23 | 217,817 | 209,921 | 0 |
| 2026-09-24 | 118,757 | 108,458 | 0 |
| 2026-09-25 | 115,671 | 106,488 | 0 |

**HTML responses, 24 hours to 2026-09-26 20:00 UTC** (about 112,000):

| Where the response came from | Requests |
| --- | ---: |
| Cloudflare edge, redirect (301), almost all `http://westernfriend.org/` → HTTPS | 54,843 |
| Cloudflare edge, bot challenge or block (403) | 26,158 |
| Cloudflare edge, rate limit (429) | 5,949 |
| **Django (origin)** | **23,550** |
| of which 200 OK | 17,379 |
| of which 404 | 2,906 |
| of which 301 / 302 | 3,220 |

- Average Django response time for HTML 200s: **700 ms**
- Edge cache hits: **0**. Every origin response was `bypass` because of
  `Cache-Control: private`.
- Who reached Django: verified bots 13,154; likely human 7,683; likely or
  definitely automated 2,718
- Busiest origin paths: `/search/` (about 3,800 including `/search`),
  `/accounts/login/` (2,010), `/favicon.ico` (1,634), `/` (960), then
  magazine department and article pages at about 100–200 each

So the load that edge caching can remove is about **23,500 origin HTML
requests a day**, not the 110,000 in the issue: Cloudflare already answers the
rest. `/accounts/login/` is never cached.

## After edge caching

Once `DJANGO_PUBLIC_CACHE_EDGE_TTL` is on, run the same query daily for a week
and add a table here. Targets from the specification:

- Edge hit ratio for HTML at or above 60%
- Origin HTML requests down at least 50% from the baseline above
