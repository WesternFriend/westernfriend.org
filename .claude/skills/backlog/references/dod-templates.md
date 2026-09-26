# Definition of done templates

Start from the base template for the kind of work (`bug` label → Bug, `enhancement` → Feature, otherwise Task), then add the area additions that apply. Leave out anything that doesn't fit: a docs-only change needs no regression test, and a backend Task needs no browser check.

## Feature

- [ ] Acceptance criteria in the issue body are all met
- [ ] Django tests cover the new behavior (`uv run python manage.py test <app>`), matching how the touched app is already tested
- [ ] `pre-commit run --all-files` passes
- [ ] `manage.py check --fail-level WARNING` passes, and `makemigrations --check` shows no missing migrations
- [ ] User-facing behavior manually verified in the browser, including the Wagtail admin where editors are affected
- [ ] Docs updated if setup, configuration, deployment, or an editor workflow changed (`docs/`, `README.md`)

## Bug

- [ ] Root cause stated in the PR, not just the symptom patched
- [ ] Regression test that fails before the fix and passes after
- [ ] Original reproduction steps no longer reproduce the bug
- [ ] Other places with the same root cause checked (`rg` for the pattern)

## Task

- [ ] The deliverable named in the issue is complete (refactor, upgrade, docs, CI, or research write-up)
- [ ] No behavior regression where running code was touched: the full test suite passes
- [ ] Follow-on work discovered along the way is filed as issues, not left implicit
- [ ] A non-obvious decision made along the way is recorded as an ADR in `docs/ADRs/`

## Area additions

**Any template, page, or UI change** (including the `UX Review`, `Home Page`, and `Magazine` labels):

- [ ] Semantic HTML: a logical heading order, landmarks, and real buttons and links
- [ ] Keyboard-operable with visible focus. Images have meaningful `alt` text, and form fields have labels.
- [ ] Styled with Tailwind/daisyUI and the global styles in `theme/static_src/src/styles.css`, with no new Bootstrap classes
- [ ] Works at phone width. Canonical, Open Graph, and structured data are still valid on affected public pages.

**`security`**, or anything touching authentication, forms, uploads, or user input:

- [ ] Input is validated and escaped on output, with no new `|safe` or `mark_safe` on user-controlled data
- [ ] Permission checks cover every new view or endpoint, with a test for unauthorized access
- [ ] No secrets in code or fixtures. Settings come from the environment.

**`Accounts` / `User Profile`**, or any new personal data:

- [ ] Only the personal data the feature needs is collected, and it appears only where the user expects
- [ ] Any new stored personal data has a stated retention and deletion story

**Store, subscriptions, donations, or payments** (`store`, `cart`, `orders`, `payment`, `paypal`, `shipping`, `subscription`):

- [ ] Verified end to end against the payment provider's sandbox, including failure and cancel paths
- [ ] No card or payment credentials are stored or logged
- [ ] Order and subscription state stays consistent if a webhook or callback arrives late or twice

**`Content Migration`**:

- [ ] The migration command is idempotent: re-running it doesn't duplicate content
- [ ] Run against representative sample data, with the results spot-checked in the Wagtail admin
- [ ] `docs/CONTENT_MIGRATION.md` updated if steps or inputs changed
