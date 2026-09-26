# Backlog conventions

These are the shared facts every write operation relies on. Where something can change on GitHub (labels, board options, milestones), prefer a live lookup over this file. If they disagree, trust GitHub and tell the user this file is stale.

## Where things live

| Thing | Where | How to change |
|---|---|---|
| Issues | `WesternFriend/westernfriend.org` | `gh issue create`, `gh issue edit --body-file` |
| Labels | Repo labels | `gh issue create --label`, `gh issue edit --add-label` |
| Milestone | Repo milestones | `scripts/set_fields.sh N Milestone "3. Post-launch"` |
| Priority, Size, Status | Org project **#2 "WesternFriend.org"** (single-select fields) | `scripts/set_fields.sh N Priority High` |
| Dependencies and hierarchy | GitHub's native blocked-by/blocking relationships and sub-issues | Web UI or `gh api`. Never labels. |

Look these up live when needed:

```bash
gh label list --repo WesternFriend/westernfriend.org --limit 200
gh api repos/WesternFriend/westernfriend.org/milestones --jq '.[].title'
gh project field-list 2 --owner WesternFriend --format json \
  | jq -r '.fields[] | select(.options) | "\(.name): \([.options[].name] | join(", "))"'
```

## Kind of work

WesternFriend doesn't use GitHub issue types. Mark the kind of work with a label:

| Kind | Use for | Label |
|---|---|---|
| Bug | Something broken that should work | `bug` |
| Feature | A new capability for readers, subscribers, editors, or admins | `enhancement` |
| Task | Refactor, dependency upgrade, docs, research, CI, or ops work with no new user-facing capability | none, or an area label such as `documentation` |

## Labels

Add every label that genuinely applies. Don't create new ones. If a batch keeps wanting a label that doesn't exist, raise it with the user.

- **Area:** `Home Page`, `Magazine`, `Accounts`, `User Profile`, `Content Migration`, `security`, `documentation`
- **Process:** `UX Review` (needs a UX or accessibility pass), `help wanted`, `good first issue`, `hacktoberfest` (only during a Hacktoberfest campaign, and only when the user asks)
- **Dependabot and PR-only:** `dependencies`, `python`, `javascript`, `github_actions`, `devcontainers_package_manager`. Don't put these on hand-filed issues.

Most Django apps (`events`, `library`, `store`, `subscription`, `search`, and the rest) have no label. Name the app in the title or body instead, for example "Events: show timezone on event detail page".

### `good first issue` (all must apply)

- Bounded to one app, template, or file area
- Needs no knowledge of the Wagtail page tree, the content-migration pipeline, or payment and subscription flows
- Has a clear definition of done and a pointer to the relevant file(s)
- Size `Small`

Pair it with `help wanted` when outside contributors are welcome.

## Priority (board field)

Base priority on impact on the site and its readers, not on how interesting the work is.

| Value | Meaning |
|---|---|
| `Critical` | The site or a core flow is broken: pages erroring, subscriptions, donations, or checkout failing, data loss, or an exploitable security hole. Drop other work. |
| `High` | A significant defect or barrier for many readers or subscribers (an accessibility blocker, broken search, wrong content), or work blocking the current milestone |
| `Medium` | Valuable improvement or moderate defect with a workaround |
| `Low` | Polish, nice-to-have, or speculative work |

## Size (board field)

| Value | Meaning |
|---|---|
| `Small` | About a day or less. One app or template, with an obvious approach. |
| `Medium` | A few days. Several files or apps, or needs a migration, a design decision, or new tests across modules. |
| `Large` | More than a week, or uncertain. Propose splitting into sub-issues under a parent issue before anyone picks it up. |

## Milestone

Milestones are repo milestones, not a text field, and a PR's issue shows up under one. Assign one only when the issue clearly belongs to that phase. Leaving an issue without a milestone is fine and better than a guess. Never create a new milestone without asking the user.

## Issue title and body

- **Title:** imperative, sentence case, no trailing period, no ticket prefixes. Prefix with the app name when no area label covers it.
- **Body:** plain Markdown, no HTML. Two to four sentences on *what* and *why*, and who is affected (readers, subscribers, editors in the Wagtail admin, or contributors). Follow with:

```markdown
**Checklist:**
- [ ] …

**Related:** #N (blocked by / follows on from / overlaps)   ← only if any
```

Batch operations (`gaps`, `retro`) replace the checklist heading with `**Acceptance criteria:**` and add a provenance line, either `**Grounding:** …` or `**Noticed in:** #PR …`, so a later reader can trace why the issue exists.

Always create and edit issues with `--body-file <path>`, never inline `--body`. Write body files to the session scratchpad directory, since backticks, quotes, and newlines break inline bodies.

## Project context worth knowing when judging work

- **Stack:** Django and Wagtail, managed with `uv`. Tests use Django's test runner (`uv run python manage.py test <app>`), not pytest. Linting and formatting are pre-commit hooks (ruff, djhtml, djade, curlylint, pyupgrade, and others). CI also runs `manage.py check --fail-level WARNING` and `makemigrations --check`.
- **Front end:** new styles use Tailwind CSS 4 with daisyUI 5, and global styles live in `theme/static_src/src/styles.css`. Leftover Bootstrap is being removed gradually. Icons use Bootstrap Icons (`bi bi-*`).
- **Accessibility and semantic HTML** are first-class requirements. See `.github/copilot-instructions.md`.
- **Decisions** worth recording go in `docs/ADRs/`, using the template and numbering in `docs/ADRs/README.md`.
- **AI crawlers:** the site is intentionally open to AI crawlers and agents for any purpose, including training. Don't file "block AI bots" as a security or bug issue.
