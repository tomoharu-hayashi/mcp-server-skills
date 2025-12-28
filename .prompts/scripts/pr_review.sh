#!/bin/bash
set -euo pipefail

PR="${PR:-}"
if [ -z "$PR" ]; then
    PR="$(gh pr view --json number --jq .number 2>/dev/null || true)"
fi

if [ -z "$PR" ]; then
    echo "PR not found. Set PR=<number> or checkout a PR branch." >&2
    exit 1
fi

REPO="$(gh repo view --json name,owner --jq '.owner.login + "/" + .name')"

printf 'PR: #%s (%s)\n\n' "$PR" "$REPO"

printf '== REVIEWS ==\n'
gh api "repos/${REPO}/pulls/${PR}/reviews" --paginate --jq '.[] | "\(.state)\t\(.user.login)\t\(.submitted_at // "-")\t\(.html_url // "-")\t\(.body // "" | gsub("\r"; " ") | gsub("\n"; " "))"'

printf '\n== REVIEW COMMENTS ==\n'
gh api "repos/${REPO}/pulls/${PR}/comments" --paginate --jq '.[] | "\(.user.login)\t\(.path):\(.line // .original_line // "-")\t\(.created_at)\t\(.html_url)\t\(.body // "" | gsub("\r"; " ") | gsub("\n"; " "))"'

printf '\n== ISSUE COMMENTS ==\n'
gh api "repos/${REPO}/issues/${PR}/comments" --paginate --jq '.[] | "\(.user.login)\t\(.created_at)\t\(.html_url)\t\(.body // "" | gsub("\r"; " ") | gsub("\n"; " "))"'
