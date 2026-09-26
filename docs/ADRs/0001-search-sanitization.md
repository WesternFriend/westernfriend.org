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

Replace every character that is not an ASCII letter or digit in user-supplied
search queries with a space, in the view layer (`search/views.py`), before the
query reaches the search backend.  This whitelist approach (`[^a-zA-Z0-9]`)
covers all punctuation, including tsquery operators (`( ) & | ! : * \`) as well
as other characters such as hyphens and commas that are not operators but are
equally invalid as standalone tsquery lexemes.

Replacement with a space (rather than deletion) preserves word boundaries, so a
query like `"foo-bar"` becomes `"foo bar"` (two searchable terms) rather than
`"foobar"` (one unrecognised term).

Digits are kept so that year-qualified queries (`PYM 2025`) work correctly.

This is implemented as a compiled regex constant (`_NON_WORD_CHARS`) and applied
at the start of the existing sanitization block, alongside the existing length
and word-count limits.  If replacement renders the query empty (e.g. the entire
input was punctuation), it is treated as no query (returns no results).

## Consequences

- **Positive:** Prevents `SyntaxError` crashes for any query containing
  characters that are invalid as tsquery lexemes. Provably complete — no unknown
  punctuation can pass through a whitelist.
- **Positive:** Simpler than a blacklist — one pattern covers all cases, with no
  risk of missing future problematic characters.
- **Negative:** Hyphens, apostrophes, and other punctuation that users might
  type are silently stripped. This is acceptable since the search UI does not
  advertise or support advanced syntax.
- **Future:** If `modelsearch` adds proper escaping in a future version, this
  sanitization can be removed.
