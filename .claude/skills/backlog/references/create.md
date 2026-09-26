# `new` — create issue(s)

Turn a free-form description, or a YAML planning file, into well-formed issues. Every batch operation (`gaps`, `retro`) also reuses Step 0 and the conventions here.

## Step 0 — Backlog scan

This step is not optional. Run it even when the request looks novel.

1. Pull two or three keyword phrasings from the description and search open *and* closed issues:

   ```bash
   gh issue list --repo WesternFriend/westernfriend.org --state all --search "KEYWORDS" \
     --json number,title,labels,state --limit 30
   ```

2. Read any issue whose title overlaps with the request: `gh issue view N --repo WesternFriend/westernfriend.org`.
3. Report briefly:
   - **Duplicates:** if the request is already captured by an open issue, say so and stop. Offer to add a comment or update that issue instead. If a *closed* issue covers it, show how it was closed (fixed, or won't-fix) and ask before refiling.
   - **Related:** list issues with one-line summaries.
   - **Dependencies:** note whether the new issue would be blocked by, or would block, something already open.

For a batch, group similar candidates into one search each. Drop covered candidates silently, and mark partial overlaps as "related to #N".

## Step 1 — Derive the fields

Use [conventions.md](conventions.md) to work out the title, the labels (kind, area, and process), and the body. Then propose values, optionally, for:

- **Priority** and **Size**, with a one-line reason for each
- **Milestone**, only if the fit is clear

If the description names code, check that it exists (`rg`) and link the file or line in the body, since that is what makes an issue pickup-ready.

## Step 2 — Show and confirm

```text
Title:     <title>
Labels:    <comma,separated>
Priority:  <value or —>   Size: <value or —>   Milestone: <value or —>
Related:   <#N — title, or "none">
---
<issue body>
```

Ask: "Look right? (y to create / edit any field)". Re-confirm after any edit. For a batch, show one table (`# | Title | Labels | Priority | Size | Related`) plus the bodies, and get a single go-ahead. Let the user drop rows.

## Step 3 — Create

Write each body to a file in the scratchpad directory, then:

```bash
gh issue create --repo WesternFriend/westernfriend.org \
  --title "<title>" \
  --body-file "<scratchpad>/issue-body.md" \
  --label "<comma,separated,labels>"
```

Collect the returned issue numbers. Then apply every field in **one** call to the field script. The script adds any issue that isn't on the board yet:

```bash
printf '%s\t%s\t%s\n' \
  1301 Priority Medium  1301 Size Small \
  1302 Priority High    1302 Size Medium  1302 Milestone "3. Post-launch" \
  | .claude/skills/backlog/scripts/set_fields.sh
```

Print the issue URLs along with the fields that were applied, and relay any `SKIP` lines from the script.

## Batch from YAML

If the argument is a path to a `.yaml` file, it follows [issue-schema.yaml](issue-schema.yaml). Run Step 0 for each entry, show the whole batch in one table as in Step 2, then create the issues and apply their fields as in Step 3. Treat the YAML file as a planning scratchpad: once the issues exist, GitHub is the source of truth.
