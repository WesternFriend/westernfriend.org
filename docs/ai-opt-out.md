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
  saying no AI training and no AI use, but yes to search. It also adds a group
  for known AI crawlers (`AI_CRAWLER_USER_AGENTS` in
  `common/ai_preferences.py`) that disallows the article's path. That group
  leaves out search crawlers such as Googlebot and Bingbot.
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

Few crawlers read `Content-Usage` yet, while the major AI crawlers do honour
`Disallow`. The extra group makes the request effective today, without
affecting search. The crawler list needs occasional review as AI companies add
or rename crawlers.
