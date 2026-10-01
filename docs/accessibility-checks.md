# Automated accessibility checks

CI runs [axe-core](https://github.com/dequelabs/axe-core) against a seeded
development site on every pull request (the `Accessibility checks` job in
`.github/workflows/ci.yml`), so a template change that regresses WCAG 2.2 AA
fails CI instead of waiting for a reader to write in. This implements
[#1282](https://github.com/WesternFriend/westernfriend.org/issues/1282).

## What it checks

- **Standard:** WCAG 2.2 level AA (axe tags `wcag2a`, `wcag2aa`, `wcag21a`,
  `wcag21aa`, `wcag22aa`). No best-practice rules: every failure maps to a
  success criterion the site has committed to.
- **Pages:** one live page of every major template — home, a magazine issue,
  an article, a library item, an event, a memorial, search results, subscribe,
  and login. The list comes from `./manage.py a11y_urls`, which reads the
  seeded database rather than hard-coding slugs, and **fails if any page type
  is missing** — silently scanning fewer templates would let a regression
  through while CI stayed green.
- **Failure threshold:** any violation axe rates `serious` or `critical`
  fails the run. `moderate` and `minor` violations are printed but do not
  fail, so the check stays strict without crying wolf.

## Tool choice (recorded per the issue)

`axe-core` driven by `puppeteer-core`, both plain npm packages with no native
binaries and no browser download — the browser is whatever Chrome the
environment already has. `pa11y-ci` was considered and rejected: it brings a
full puppeteer-plus-Chromium download into a repository whose only other
JavaScript is the Tailwind build. `Lighthouse` audits performance and SEO as
well, which is more than this check should gate PRs on.

## Running it locally

```sh
# One-time: install the two checker packages
npm ci

# Seed a development database, if you haven't (see getting-started docs)
./manage.py migrate
./manage.py seed_dev_content --scale small --seed 1234

# Serve it (DEBUG so the committed Tailwind CSS is served; axe's
# color-contrast rules are meaningless against unstyled pages)
DJANGO_DEBUG=true ./manage.py runserver 8000

# In another shell: scan the representative pages. Two steps, so a failure
# from a11y_urls is seen rather than swallowed by the $() substitution.
./manage.py a11y_urls > /tmp/a11y-urls.txt
node scripts/a11y-check.mjs $(cat /tmp/a11y-urls.txt)
```

If Chrome is somewhere unusual, point the script at it with
`CHROME_PATH=/path/to/chrome`.

## Scope and honest limits

Automated checks catch roughly a third of WCAG issues (missing alt text,
contrast, names/roles, document structure). They cannot judge whether alt text
is *good*, whether focus order makes sense, or how a screen reader actually
reads a page — that is the manual pass tracked in
[#1304](https://github.com/WesternFriend/westernfriend.org/issues/1304), which
this check complements rather than replaces. Captions and transcripts
([#1303](https://github.com/WesternFriend/westernfriend.org/issues/1303)) are
likewise out of automated reach.

At the time this check landed, all nine representative pages passed with zero
WCAG 2.2 AA violations — the September 2026 audit and its follow-up fixes are
what it is protecting.
