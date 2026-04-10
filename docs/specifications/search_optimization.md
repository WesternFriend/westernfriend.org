# Search Optimization Specification

This document is the authoritative specification for search performance
optimizations in the site search view (`search/views.py`). It describes every
active protection and optimization in implementation order. When adding or
removing a protection, update this document to match.

Related ADRs: [ADR 0001](../ADRs/0001-search-sanitization.md) ·
[ADR 0002](../ADRs/0002-search-query-length-limits.md) ·
[ADR 0003](../ADRs/0003-search-stopword-filtering.md)

---

## 1. Non-Alphanumeric Character Sanitization

**ADR:** [0001](../ADRs/0001-search-sanitization.md)

Every character that is not an ASCII letter or digit is replaced with a space
before the query reaches the search backend.  This whitelist approach covers all
tsquery operators (`( ) & | ! : * \`) as well as any other punctuation (hyphens,
commas, etc.) that the PostgreSQL `modelsearch` backend cannot safely convert to
a tsquery lexeme.  Replacement with a space preserves word boundaries so that
`"foo-bar"` becomes two searchable terms (`foo bar`) rather than one (`foobar`).
Digits are preserved so that year-qualified queries such as `PYM 2025` work.

If the entire query consists of non-alphanumeric characters, the sanitised
result is empty and is treated as no query (returns no results).

**Implementation:** `_NON_WORD_CHARS` compiled regex constant (`[^a-zA-Z0-9]`)
applied via `.sub(" ", search_query).strip()`.

---

## 2. Length and Word-Count Limits

**ADR:** [0002](../ADRs/0002-search-query-length-limits.md)

Two independent upper bounds are enforced before the query reaches the search
backend:

| Limit            | Constant           | Value |
| ---------------- | ------------------ | ----- |
| Character length | `MAX_QUERY_LENGTH` | 30    |
| Word count       | `MAX_QUERY_WORDS`  | 5     |

Either limit triggers truncation. When truncation occurs, `query_truncated` is
set to `True` and the template displays an informational alert showing the user
the actual query being searched.

The HTML `<input>` element also carries `maxlength="{{ max_query_length }}"` as
a first line of defence for human users.

---

## 3. Stopword Filtering

**ADR:** [0003](../ADRs/0003-search-stopword-filtering.md)

PostgreSQL's English full-text search configuration discards common words
(stopwords) during both indexing and querying. Including them as OR terms in a
`tsquery` inflates intermediate result sets without narrowing matches, causing
slow `COUNT` and `SELECT` queries.

After word-splitting, every word is checked case-insensitively against the
`STOPWORDS` frozenset. Words that appear in the list are removed before
word-count enforcement. If all words are stopwords the query is treated as empty
(returns no results).

Filtering occurs **before** the word-count limit so the limit applies to
meaningful terms only.

**Implementation:** `STOPWORDS` module-level `frozenset[str]` constant;
filter applied as `[w for w in words if w.lower() not in STOPWORDS]`.

---

## 4. Pagination Depth Limit

Requests for pages beyond `max_page_limit = 50` are rejected immediately with a
rendered response that sets `page_limit_exceeded = True` in the template
context. No search query is executed for out-of-range page numbers. This
prevents bots from iterating through thousands of result pages and generating
repeated expensive database queries.

---

## 5. Post-Pagination N+1 Optimizations

Wagtail's `.search()` returns generic `Page` objects. Resolving specific page
types, related data, and parent pages for URL construction would trigger one
query per result if handled naively. The view implements a bulk-fetch strategy
after pagination has narrowed the result set to `number_per_page = 25` items.

### 5a. Magazine Articles — Optimized Specific Fetch

`MagazineArticle` pages are identified by content type and fetched via
`MagazineArticle.get_queryset()`, which applies:

- `defer_streamfields()` — avoids loading large `body`/`body_migrated` fields
- `select_related("department")`
- `prefetch_related("authors__author", "tags")`

### 5b. Magazine Articles — Parent Issue Prefetch

`MagazineArticle.prefetch_parent_issues(magazine_articles)` bulk-annotates each
article with its parent `MagazineIssue` instance, preventing N+1 queries when
templates access `article.parent_issue`.

### 5c. Other Page Types — Bulk `.specific()` Fetch

All non-`MagazineArticle` pages in the current result page are fetched as a
single queryset via `Page.objects.filter(id__in=...).select_related("content_type").specific()`.

### 5d. Parent-Page Caching for `{% pageurl %}`

Wagtail's `{% pageurl %}` template tag calls `page.get_parent()` for every
result. The view bulk-fetches all unique parent pages for the current result
page and caches them by overriding `get_parent()` on each instance with a
closure that returns the pre-fetched parent. This eliminates one query per
result that would otherwise be triggered by the template layer.

---

## Sanitization Pipeline Order

The full query sanitization pipeline executes in this order:

```text
raw query string
  → strip tsquery special characters       (§1)
  → truncate to MAX_QUERY_LENGTH chars      (§2)
  → split into words
  → remove stopwords                        (§3)
  → truncate to MAX_QUERY_WORDS words       (§2)
  → rejoin into sanitised query string
```

---

## Testing

The relevant test case is `SearchOptimizationTestCase` in `search/tests.py`.

Key tests:

- `test_search_query_optimization` — verifies the view does not trigger the
  severe N+1 query problem (total query count stays within a defined threshold)
- `test_search_results_include_authors` — verifies author data is accessible on
  search results without additional per-result queries

**Wagtail architectural note:** Calling `.specific()` on a `Page` object creates
a new model instance that does not preserve Django's prefetch cache. This is by
design in Wagtail and is accounted for in the bulk-fetch strategy above (§5).
The test thresholds reflect this reality rather than expecting perfect
zero-overhead access.
