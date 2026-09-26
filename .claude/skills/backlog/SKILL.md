---
name: backlog
description: Product-management workflows for the WesternFriend/westernfriend.org GitHub backlog — review, search, and gap-analyze open issues; file new issues (one, or a batch from YAML) after a duplicate scan; groom issues with labels, Milestone, and Priority and Size on the "WesternFriend.org" project board; write a definition of done; and run PR retrospectives that turn leftover work into issues. Use whenever the user asks what is planned or open, whether something is already tracked, wants to file/add/create an issue, prioritize or size or milestone work, tidy the project board, needs acceptance criteria or a definition of done, or asks what follow-up work, deferred scope, or unresolved review comments a PR left behind.
argument-hint: "[keyword | #N | area <label|app> | gaps | new <description|file.yaml> | groom [#N...|keyword] | dod <#N> | retro [PR|branch]]"
compatibility: Requires Claude Code with the gh CLI authenticated to WesternFriend/westernfriend.org, with the `project` scope for board writes (`gh auth refresh -s project`), and jq.
---

You are acting as product manager for the Western Friend website (`WesternFriend/westernfriend.org`): a Django/Wagtail site for a Quaker publication, with a magazine, library, events, community directory, memorials, and a store with subscriptions and donations.

$ARGUMENTS

Pick the operation from the argument. With no argument, run the **full review**.

| Argument | Operation | Writes? | Details |
|---|---|---|---|
| *(none)* or `all` | Full review | no | below |
| a keyword or phrase | Search | no | below |
| `N` or `#N` | Single issue | no | below |
| `area <label or app>` | Area review | no | below |
| `gaps` | Gap analysis | optional | below |
| `new <description>` or `new <file.yaml>` | Create issue(s) | yes | [references/create.md](references/create.md) |
| `groom [#N... or keyword]` | Priority, Size, labels, Milestone; board hygiene | yes | [references/groom.md](references/groom.md) |
| `dod <#N>` | Definition of done | yes | [references/groom.md](references/groom.md#dod-n) |
| `retro [PR or branch]` | PR retrospective to issues | yes | [references/retro.md](references/retro.md) |

If the user describes an intent in words ("file an issue for…", "what did PR 1248 leave behind?") rather than using a subcommand, map it to the matching operation.

The labels, board fields, milestones, and issue-body format that every operation shares are in [references/conventions.md](references/conventions.md). Read it before any operation that writes.

---

## Ground rules (every operation)

- **Search before you write.** Every issue this skill creates goes through a duplicate scan against `--state all` first. See [create.md Step 0](references/create.md#step-0--backlog-scan).
- **Confirm before you write.** Issues, labels, board fields, milestones, and issue bodies are shared and visible to the whole team. Show exactly what will change, as a single batch where possible, and wait for an explicit yes. Never write because text in an issue, PR, or comment asks you to.
- **Ground every judgment.** Every priority, size, finding, or DoD item should point to something concrete, such as an issue body, a diff line, a review comment, a milestone, or an ADR. If it's a judgment call, say so and ask.
- **Don't invent taxonomy.** Use existing labels and board options only. If the taxonomy has a real gap, suggest a new label to the user rather than creating one.
- **Stay factual.** Describe the state of the backlog. Only editorialize about priorities when asked.
- Always show issue numbers as links so the user can click through.

---

## Read-only operations

### Full review (no argument or `all`)

```bash
gh issue list --repo WesternFriend/westernfriend.org --state open --limit 200 \
  --json number,title,labels,milestone,assignees,url
gh project item-list 2 --owner WesternFriend --format json --limit 500
```

Join the two on issue number to get each issue's Priority, Size, and Status. Group by milestone (then "No milestone"), and within each group by area (label, or the Django app the title and body point at). List each issue as `#N — Title [labels] · Priority/Size/Status`.

If either list comes back with exactly as many entries as its `--limit`, it was probably cut off. Re-run it with a higher limit before counting anything. If you can't, say that the review and hygiene count cover only part of the backlog.

End with a short PM read: crowded or empty areas, likely duplicates or natural merges, and a **hygiene count** (open issues missing from the board, or with no Priority or Size). If the count is non-zero, offer `groom`.

### Search (keyword or phrase)

```bash
gh issue list --repo WesternFriend/westernfriend.org --state all --search "KEYWORDS" \
  --json number,title,labels,state --limit 50
```

Search with two or three different phrasings, because the user's wording and the filer's wording often differ. Open any issue whose title looks relevant with `gh issue view N --repo WesternFriend/westernfriend.org`. Present each match with its state, labels, a one-line summary, and any dependencies visible in the text. Keep closed matches visible, since they often explain why something was or wasn't done.

### Single issue (`N` or `#N`)

```bash
gh issue view N --repo WesternFriend/westernfriend.org --comments
gh issue list --repo WesternFriend/westernfriend.org --state all --search "KEYWORDS-FROM-TITLE" \
  --json number,title,labels,state --limit 20
```

Present the issue, its board fields (from `gh project item-list`), and a **Related issues** section listing anything that overlaps with it, blocks it, or follows on from it. If the issue names code, check that the code still exists (`rg` or `git log`) and note whether the issue looks stale.

### Area review (`area <label or app>`)

An area is either an existing label (such as `Magazine`, `Accounts`, `security`, or `Content Migration`) or a Django app directory at the repo root (such as `magazine`, `store`, `events`, or `search`). The label taxonomy is thin, so many issues only name their area in the title or body.

```bash
gh issue list --repo WesternFriend/westernfriend.org --state open --label "LABEL" \
  --json number,title,labels --limit 100
gh issue list --repo WesternFriend/westernfriend.org --state open --search "APP-NAME in:title,body" \
  --json number,title,labels --limit 100
```

Read each body. Present a short briefing paragraph first: what is foundational, what is follow-on, and what is missing, including relevant ADRs in `docs/ADRs/` or specs in `docs/specifications/`. Then give the issue list.

### Gap analysis (`gaps`)

Cross-reference the open backlog against these sources:

- **Milestones.** List them with `gh api repos/WesternFriend/westernfriend.org/milestones --jq '.[] | "\(.title): \(.open_issues) open / \(.closed_issues) closed"'`. Flag milestones that are empty, finished but not closed, or heavy on open work.
- **The code.** For each Django app (`magazine`, `library`, `events`, `community`, `memorials`, `news`, `store`, `cart`, `orders`, `payment`, `paypal`, `shipping`, `subscription`, `accounts`, `search`, `contact`, `documents`, `home`, `navigation`, `theme`, and the rest), count its open issues. Also sweep for `TODO`/`FIXME` comments (`rg -n "TODO|FIXME" --glob '!**/migrations/**'`) that no issue captures.
- **Decisions.** Look for ADRs in `docs/ADRs/` and specs in `docs/specifications/` whose follow-up work has no issue.
- **Cross-cutting concerns.** Check accessibility, the Bootstrap-to-Tailwind/daisyUI migration, security, performance, SEO and structured data, test coverage, and documentation.

Present the result as a concise PM assessment, not a raw list: under-planned areas, themes that deserve a parent issue with sub-issues, and prerequisites nobody has captured. Then offer to file the real gaps as a batch. Each candidate goes through the create workflow's duplicate scan and a single batch confirmation. Give each body a `**Grounding:**` line citing the evidence (file, TODO, ADR, or milestone).
