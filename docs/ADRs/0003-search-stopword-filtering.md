# ADR 0003: Search Stopword Filtering

Date: 2026-04-04
Status: Accepted

## Context

Wagtail's database search backend uses PostgreSQL full-text search with an
`OR`-based `tsquery` when `operator="or"` is specified. Every word in the
sanitised search query becomes a separate OR term. When common words — known as
stopwords — appear in the query, the situation is subtly worse than it first
appears:

- PostgreSQL's English FTS configuration (`pg_catalog.english`) discards
  stopwords such as "and", "the", and "or" during both indexing and querying.
  A query like `'word1' | 'and' | 'word2'` is therefore equivalent to
  `'word1' | 'word2'` from the engine's perspective.
- Despite being ignored, stopword terms still contribute to the `tsquery`
  string passed to the search index, which can cause the query planner to
  produce a larger intermediate result set than the semantically equivalent
  stopword-free query.
- Bots and crawlers (e.g. SemrushBot) frequently submit queries that happen to
  contain stopwords, producing expensive database work with no benefit to users.

Production evidence: a request to `/search/?query=some+words+and+more` generated
a 299 ms `COUNT(*)` query followed by a 1 010 ms `SELECT` query against
`wagtailcore_page / wagtailsearch_indexentry`, primarily due to the large
OR-based result set. The word "and" was the key stopword present.

Prior sanitization (ADR 0001 — special-character stripping; ADR 0002 — length
and word-count limits) did not address stopwords because "and" is a valid
alphanumeric word that survives both passes unchanged.

## Decision

Filter PostgreSQL English stopwords from the search query in the view layer
(`search/views.py`), after special-character sanitization and before word-count
truncation.

The implementation:

```python
# After splitting into words and before enforcing MAX_QUERY_WORDS:
words = [w for w in words if w.lower() not in STOPWORDS]
if not words:
    search_query = None
```

The `STOPWORDS` constant is a `frozenset[str]` defined as a module-level
constant in `search/views.py`, containing the words from PostgreSQL's
`pg_catalog.english` stopword list. Filtering happens **before** the word-count
limit (`MAX_QUERY_WORDS`) so that the limit applies to meaningful terms only.

If all words in the query are stopwords, the query is treated as empty and no
database search is executed.

## Consequences

- **Positive:** Removes stopword terms from the tsquery, reducing the size of
  intermediate result sets and improving response time for queries that contain
  common English words.
- **Positive:** Consistent with the existing sanitization pipeline — stopword
  filtering is one more step in the same block, following the same guard
  structure.
- **Positive:** The word-count limit now applies to meaningful words, so a
  5-word query composed of 3 stopwords and 2 content words still uses both
  content words as search terms instead of being truncated arbitrarily.
- **Negative:** A user who searches exclusively for stopwords (e.g. "the and
  or") will see no results. This is the correct and expected behaviour — those
  words carry no signal for FTS — but it may be surprising without UI feedback.
  The existing `query_truncated` mechanism does not cover this case; if this
  becomes a user experience concern, a separate `query_empty_after_filtering`
  flag could be added.
- **Future:** If Wagtail or `modelsearch` adds native stopword awareness, the
  `STOPWORDS` constant and filter step can be removed. The stopword list should
  be reviewed if the site adds support for non-English content or switches FTS
  configuration.
