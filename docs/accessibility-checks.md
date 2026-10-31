# Automated accessibility checks

CI runs [axe-core](https://github.com/dequelabs/axe-core) against a seeded
development site on every pull request (the `Accessibility checks` job in
`.github/workflows/ci.yml`), so a template change that regresses WCAG 2.2 AA
fails CI instead of waiting for a reader to write in. This implements
[#1282](https://github.com/WesternFriend/westernfriend.org/issues/1282).

## What it checks

- **Standard:** WCAG 2.2 level AA (axe tags `wcag2a`, `wcag2aa`, `wcag21a`,
  `wcag21aa`, `wcag22a`, `wcag22aa`; no axe-core 4.10 rule carries `wcag22a`
  yet, so it is listed for rules added later). No best-practice rules: every
  failure maps to a success criterion the site has committed to.
- **Pages:** one live page of every major template — home, a magazine issue,
  an article, a library item, an event, a memorial, search results, subscribe,
  and login. The list comes from `./manage.py a11y_urls`, which reads the
  seeded database rather than hard-coding slugs, and **fails if any page type
  is missing** — silently scanning fewer templates would let a regression
  through while CI stayed green.
- **Failure threshold:** any violation axe rates `serious` or `critical`
  fails the run. `moderate` and `minor` violations are printed but do not
  fail, so the check stays strict without crying wolf.
- **Stylesheets:** every stylesheet a page requests has to load as CSS
  before axe runs, because a page missing its styles can pass contrast and
  layout rules the real page fails. A stylesheet fails its page, with its
  URL and the reason, when it returns an error status, fails on the
  network or partway through, is still loading once the page has loaded,
  or is served as a type Chrome won't apply as CSS. Chrome applies
  `text/css`, and also a missing Content-Type or the placeholder
  `application/x-unknown-content-type` (unless the response says
  `X-Content-Type-Options: nosniff`); with a repeated Content-Type, it goes
  by the last one. Redirects are followed, and a `304` counts as loaded
  only when Chrome asked to revalidate a copy it already had. None is
  optional, including the Bootstrap Icons stylesheet from jsDelivr; if one
  ever needs to be, it should get an explicit exception in
  `scripts/a11y-check.mjs`, with the reason.
  `scripts/a11y-check.test.mjs` checks each of these cases against a local
  test server, and CI installs the checker and runs these as their own
  check, before seeding.

## Tool choice (recorded per the issue)

`axe-core` driven by `puppeteer-core` (`scripts/a11y-check.mjs`), both plain
npm packages with no native binaries and no browser download. The browser is
whatever Chrome the environment already has.

The two packages are pinned to exact versions in `scripts/package.json`,
and `scripts/package-lock.json` locks everything they depend on, so every
run executes the same code. They are kept apart from the site's own
`package.json`, so the deploy and the test job never install them; only
the `Accessibility checks` job runs `npm ci --prefix scripts`. Dependabot's
npm updates cover `/scripts` too.
`axe-core` decides what counts as a violation, so an update to it is a rule
change: review it as one, and expect it to find things the old version
didn't.

Alternatives considered and rejected:

- `@axe-core/cli`: its `--exit` flag fails on any violation, with no way to
  fail only on serious and critical ones. It drives Chrome through
  ChromeDriver, which has to match the runner's Chrome version, and it
  depends on `axe-core` and `chromedriver` through version ranges, so the
  rules could change without a commit here.
- `pa11y-ci`: it brings a full puppeteer-plus-Chromium download.
- `Lighthouse`: it audits performance and SEO as well, which is more than this
  check should gate PRs on.

## Running it locally

```sh
# Build the CSS and install the checker, if you haven't: axe's
# color-contrast rules need the CSS. Node.js 24, as package.json says.
npm ci --include=dev
npm run build:css
npm ci --prefix scripts

# Seed a development database, if you haven't (see getting-started docs).
# DJANGO_DEBUG because the seeder refuses to run against a production setup.
./manage.py migrate
DJANGO_DEBUG=true ./manage.py seed_dev_content --scale small --seed 1234

# Serve it (DEBUG so the built CSS is served; axe's color-contrast rules
# are meaningless against unstyled pages)
DJANGO_DEBUG=true ./manage.py runserver 8000

# In another shell: scan the representative pages. Two steps, so a failure
# from a11y_urls is seen rather than swallowed by the $() substitution.
./manage.py a11y_urls > /tmp/a11y-urls.txt
node scripts/a11y-check.mjs $(cat /tmp/a11y-urls.txt)

# The checker's own tests (no server or database needed)
node --test scripts/a11y-check.test.mjs
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
