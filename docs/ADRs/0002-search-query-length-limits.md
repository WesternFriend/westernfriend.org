# ADR 0002: Search Query Length and Word Count Limits

Date: 2026-03-10
Status: Accepted

## Context

The site search was being abused by spambots submitting paragraphs of arbitrary
text as search queries. Each word in the query becomes a separate term in a
PostgreSQL `OR`-based tsquery expression, so a 200-word submission generates a
200-term tsquery. This caused excessive database load and slow response times.

Wagtail's `modelsearch` library imposes a 255-character internal limit
(`MAX_QUERY_STRING_LENGTH` in `modelsearch/utils.py`), but this is far too
permissive to protect against multi-sentence bot submissions.

## Decision

Enforce two independent limits in the view layer (`search/views.py`) before the
query reaches the search backend:

- **Character limit:** 30 characters (`MAX_QUERY_LENGTH`)
- **Word limit:** 5 words (`MAX_QUERY_WORDS`)

Either limit triggers truncation. When truncation occurs, the view sets
`query_truncated = True`, which the template uses to display an informational
alert showing the user what they're actually searching for.

The HTML input field also sets `maxlength="{{ max_query_length }}"` to prevent
entry beyond 30 characters in compliant browsers, providing a first line of
defence for human users.

## Consequences

- **Positive:** Eliminates runaway tsquery complexity from bot-submitted
  paragraph-length queries, protecting database performance.
- **Positive:** Legitimate users are unaffected — real search queries are almost
  always under 5 words.
- **Positive:** Transparent feedback: truncated queries show a "Search query
  shortened" alert so users know what was searched.
- **Negative:** Users with genuinely long queries (e.g., pasting a phrase) will
  have them silently truncated beyond the character limit. The alert mitigates
  confusion.
- **Note:** The `maxlength` HTML attribute is client-side only and easily
  bypassed; the server-side limits are the authoritative enforcement.
