#!/usr/bin/env bash
# Sets planning fields on WesternFriend/westernfriend.org issues.
#
#   Priority, Size, Status  single-select fields on org project #2 "WesternFriend.org"
#   Milestone               the repo milestone, by exact title
#
# Usage, for one write:
#   set_fields.sh <issue-number> <field> <value>
#   set_fields.sh 1234 Priority High
# Or for a batch, feed "<issue>\t<field>\t<value>" lines on stdin:
#   printf '1234\tPriority\tHigh\n1234\tSize\tSmall\n' | set_fields.sh
#
# The board's projects, fields, and items are looked up at most once per run, not once per
# write, and mutations are spaced out. A loop of one-off calls re-fetches the
# same data every time and can trip GitHub's secondary GraphQL rate limit, which
# locks out further calls for several minutes. An issue missing from the board
# is added to it. Option names are matched exactly (case-sensitive) against the
# live board, so a renamed option fails loudly instead of silently mis-setting.
#
# Invalid rows are reported as "SKIP ..." on stderr and the rest still run; the
# exit status is 1 if any row was skipped.
set -euo pipefail

OWNER="WesternFriend"
PROJECT_NUMBER=2
REPO="WesternFriend/westernfriend.org"
DELAY_SECONDS=0.5

if [[ $# -eq 3 ]]; then
  INPUT=$(printf '%s\t%s\t%s\n' "$1" "$2" "$3")
elif [[ $# -eq 0 ]]; then
  INPUT=$(cat)
else
  echo "usage: set_fields.sh <issue-number> <Priority|Size|Status|Milestone> <value>" >&2
  echo "   or: printf '<issue>\\t<field>\\t<value>\\n...' | set_fields.sh" >&2
  exit 2
fi

PROJECT_ID="" FIELDS_JSON="" ITEMS_JSON=""
FAILED=0

skip() {
  echo "SKIP #$1 $2: $3" >&2
  FAILED=1
  return 1
}

load_board() {
  [[ -n "$PROJECT_ID" ]] && return
  PROJECT_ID=$(gh project view "$PROJECT_NUMBER" --owner "$OWNER" --format json --jq '.id')
  FIELDS_JSON=$(gh project field-list "$PROJECT_NUMBER" --owner "$OWNER" --format json)
  ITEMS_JSON=$(gh project item-list "$PROJECT_NUMBER" --owner "$OWNER" --format json --limit 1000)
}

board_item_id() {
  local num=$1 id
  id=$(jq -r --arg repo "$REPO" --argjson num "$num" \
    '.items[] | select(.content.repository == $repo and .content.number == $num) | .id' <<<"$ITEMS_JSON")
  if [[ -z "$id" ]]; then
    id=$(gh project item-add "$PROJECT_NUMBER" --owner "$OWNER" \
      --url "https://github.com/$REPO/issues/$num" --format json --jq '.id')
    echo "Added issue #$num to the project board." >&2
  fi
  echo "$id"
}

set_board_field() {
  local num=$1 field=$2 value=$3 field_json field_id option_id item_id
  load_board
  field_json=$(jq -c --arg name "$field" '.fields[] | select(.name == $name)' <<<"$FIELDS_JSON")
  if [[ -z "$field_json" ]]; then
    skip "$num" "$field" "no project field named '$field'"
    return 1
  fi
  option_id=$(jq -r --arg val "$value" '.options[]? | select(.name == $val) | .id' <<<"$field_json")
  if [[ -z "$option_id" ]]; then
    skip "$num" "$field" "'$value' is not an option (valid: $(jq -r '[.options[]?.name] | join(", ")' <<<"$field_json"))"
    return 1
  fi
  field_id=$(jq -r '.id' <<<"$field_json")
  item_id=$(board_item_id "$num") || { skip "$num" "$field" "could not find or add the board item"; return 1; }
  gh project item-edit --id "$item_id" --field-id "$field_id" --project-id "$PROJECT_ID" \
    --single-select-option-id "$option_id" >/dev/null
}


while IFS=$'\t' read -r NUM FIELD VALUE; do
  [[ -z "${NUM:-}" ]] && continue
  NUM=${NUM#\#}
  if ! [[ "$NUM" =~ ^[0-9]+$ ]] || [[ -z "${FIELD:-}" || -z "${VALUE:-}" ]]; then
    skip "${NUM:-?}" "${FIELD:-?}" "malformed row; expected <issue>\\t<field>\\t<value>" || continue
  fi
  case "$FIELD" in
    Priority | Size | Status) set_board_field "$NUM" "$FIELD" "$VALUE" || { FAILED=1; continue; } ;;
    Milestone) gh issue edit "$NUM" --repo "$REPO" --milestone "$VALUE" >/dev/null ||
      { skip "$NUM" Milestone "could not set '$VALUE' (does the milestone exist?)" || continue; } ;;
    *) skip "$NUM" "$FIELD" "unsupported field (use Priority, Size, Status, or Milestone)" || continue ;;
  esac
  echo "Set $FIELD = $VALUE on #$NUM."
  sleep "$DELAY_SECONDS"
done <<<"$INPUT"

exit "$FAILED"
