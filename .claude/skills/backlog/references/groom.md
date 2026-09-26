# `groom` and `dod` — keep issues pickup-ready

A backlog drifts quietly. Issues close while their milestone stays open, cards land on the board with no Priority, and "done" lives in one person's head. None of that shows up as a bug. It shows up months later as the team disagreeing about what is next or what finished means. Grooming makes small, continuous corrections so a big reconciliation is never needed.

All writes go through `scripts/set_fields.sh` (board fields and Milestone) or `gh issue edit --body-file` (bodies), and only after confirmation.

## `groom` with no target — hygiene audit

1. Gather the data:

   ```bash
   gh issue list --repo WesternFriend/westernfriend.org --state open --limit 300 \
     --json number,title,labels,milestone,body,updatedAt
   gh project item-list 2 --owner WesternFriend --format json --limit 500
   gh api repos/WesternFriend/westernfriend.org/milestones?state=all --jq \
     '.[] | {title, state, open_issues, closed_issues, due_on}'
   ```

2. Flag each of these:
   - Open issues **not on the board**, or on it with no **Priority** or **Size**
   - Issues with no labels at all, or an obvious defect missing `bug`
   - Board items whose Status is `Done` but whose issue is still open, or whose issue is closed but Status is not `Done`
   - `Large` issues with no sub-issues, which are candidates to split
   - Open milestones with zero open issues, which could be closed, or with a past `due_on`
   - Issues untouched for more than 12 months, and issues naming files or functions that no longer exist (check with `rg`), which could be closed as stale
   - Likely duplicates, meaning titles or bodies that describe the same work
3. Present a compact table: `#N | Title | Problem | Proposed fix`. For missing Priority or Size, give a proposed value and a one-line reason (see [conventions.md](conventions.md)).
4. Get **one** go-ahead for the batch, letting the user strike rows. Then apply every field change in a single `set_fields.sh` call on stdin. Closing issues or milestones is a separate, explicitly confirmed step, and every close gets a comment explaining why.

## `groom #N [#M...]` or `groom <keyword>`

1. Resolve the issues. A keyword means search first and confirm which issues are meant.
2. For each issue, read the body and comments, then propose **Priority**, **Size**, any missing labels, and, only when the fit is clear, **Milestone**. Tie the reasoning to something concrete, for example: "Critical — checkout 500s for every subscriber (see comment from the editor)", or "Large — touches `store`, `orders`, and `paypal` plus a migration; suggest splitting into…".
3. Show the proposal, confirm, and apply:

   ```bash
   .claude/skills/backlog/scripts/set_fields.sh 1234 Priority High
   printf '1234\tSize\tMedium\n1234\tMilestone\t3. Post-launch\n' | .claude/skills/backlog/scripts/set_fields.sh
   ```

   Use a single stdin call for anything beyond one or two writes. The script caches the board lookups and paces its mutations to avoid tripping GitHub's secondary GraphQL rate limit, which can lock out calls for several minutes.

## `dod <#N>`

1. Read the issue body, labels (`bug` means Bug, `enhancement` means Feature, anything else is usually a Task), and the app(s) it touches.
2. Build a checklist from [dod-templates.md](dod-templates.md): take the base template for the kind of work, then add the area additions that apply. Drop anything irrelevant; for example, a docs-only Task doesn't need a regression test.
3. Show the checklist. Ask whether to append it as a `## Definition of done` section, replacing any stale section with that heading, and leave the rest of the body untouched.
4. After confirmation, fetch the current body (`gh issue view N --json body --jq .body`), make the edit in a scratchpad file, and apply it:

   ```bash
   gh issue edit N --repo WesternFriend/westernfriend.org --body-file "<scratchpad>/body.md"
   ```
