# ADR 0001: Search Query Sanitization Strategy

Date: 2026-03-10
Status: Accepted

## Context

The site search accepts free-text user input and passes it to Wagtail's database
search backend (backed by PostgreSQL full-text search). Wagtail 7.3 delegates
query building to the `modelsearch` library, whose PostgreSQL `Lexeme` class only
escapes single quotes and backslashes — it does not strip PostgreSQL tsquery
operator characters (`( ) & | ! : * \`).

This means a query like `"type(s) of damage(s)"` causes a PostgreSQL
`SyntaxError` at runtime because `(s)` is interpreted as a tsquery grouping
expression rather than literal text.

There is no built-in sanitization utility in Django, Wagtail, or `modelsearch`
for this case. (The MySQL `modelsearch` backend does strip non-word characters
via `re.sub(r"\W+", " ", value)`, but this is internal to that backend and not
reusable.)

## Decision

Strip PostgreSQL tsquery operator characters from user-supplied search queries
in the view layer (`search/views.py`), before the query reaches the search
backend. The stripped characters are: `( ) & | ! : * \`.

This is implemented as a compiled regex constant (`_TSQUERY_SPECIAL_CHARS`) and
applied at the start of the existing sanitization block, alongside the existing
length and word-count limits. If stripping renders the query empty, it is treated
as no query (returns no results).

## Consequences

- **Positive:** Prevents `SyntaxError` crashes for queries containing tsquery
  operators. Consistent with the project's existing defensive sanitization pattern.
- **Positive:** Narrow and targeted — only strips characters that are truly
  problematic for the PostgreSQL backend, preserving hyphens, apostrophes, etc.
- **Negative:** Users who intentionally type tsquery syntax (e.g., `cat & dog`)
  will have the operators silently removed. This is acceptable since the search
  UI does not advertise or support tsquery syntax.
- **Future:** If `modelsearch` adds proper escaping for these characters in a
  future version, this sanitization can be removed.
