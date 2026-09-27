# Excluding an article from AI use

ADR 0006 treats Western Friend's AI-use signal as a stated preference, not a
licence. Contributors who don't want their work offered for AI use can ask to
have it excluded. An excluded article stays open to readers and search engines.

## For editors

1. In the Wagtail admin, open the magazine article.
2. Under **Article information**, tick **Exclude from AI use**.
3. Publish the article.

The exclusion takes effect when the article is published. It follows the
article if its slug changes or it moves to another issue. Untick the box and
publish again to lift it.

Signals are requests, not enforcement. They only affect future use, so content
that AI systems have already gathered can't be recalled.

### Telling contributors

Contributors learn they can ask on the
[Future Issues](https://westernfriend.org/future-issues/) page, under "Can I
keep my writing out of AI systems?". That page is edited in the Wagtail admin.
If the process changes, update that section too.

## What the site publishes

When an article is excluded:

- **robots.txt** adds a path-scoped `Content-Usage` rule for all crawlers,
  saying no AI training and no AI use. Search follows the site's "Search
  engines" choice in the "Crawlers and AI" setting.
- **llms.txt** leaves the article out.
- **The article page** is served with the same preference in a `Content-Usage`
  HTTP header.

### Why this form

The site-wide `Content-Signal` line uses Cloudflare's
[Content Signals](https://contentsignals.org/), which has no documented form
for a single path. A crawler might misread a path-scoped `Content-Signal` line
as a site-wide "no", so the per-article preference uses the IETF AI
Preferences drafts instead
([vocabulary](https://datatracker.ietf.org/doc/draft-ietf-aipref-vocab/),
[attachment](https://datatracker.ietf.org/doc/draft-ietf-aipref-attach/)).
Those drafts define path-scoped rules for robots.txt and a matching HTTP
header.

We don't disallow excluded articles for a list of AI crawlers. Such a list
goes stale as AI companies add and rename crawlers. Few crawlers read
`Content-Usage` yet, so today the exclusion is mostly a statement of the
contributor's wishes. Blocking AI crawlers from an article would be
enforcement, which ADR 0006 keeps separate from policy. If it's ever needed,
Cloudflare's own bot categories are the place to do it.
