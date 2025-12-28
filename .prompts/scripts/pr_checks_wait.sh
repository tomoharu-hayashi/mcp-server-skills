#!/bin/bash
set -euo pipefail

PR="${PR:-}"
WAIT="${WAIT:-30}"
TIMEOUT="${TIMEOUT:-1800}"

if [ -z "$PR" ]; then
    PR="$(gh pr view --json number --jq .number 2>/dev/null || true)"
fi

if [ -z "$PR" ]; then
    echo "PR not found. Set PR=<number> or checkout a PR branch." >&2
    exit 1
fi

REPO="$(gh repo view --json name,owner --jq '.owner.login + "/" + .name')"

start_time=$(date +%s)
printf 'Polling CI checks for PR #%s (%s) every %ss (timeout: %ss)\n' "$PR" "$REPO" "$WAIT" "$TIMEOUT"

while :; do
    now=$(date +%s)
    elapsed=$((now - start_time))
    if [ "$elapsed" -ge "$TIMEOUT" ]; then
        echo "Timed out after ${TIMEOUT}s waiting for CI."
        exit 1
    fi

    checks_json=$(gh pr checks "$PR" --json name,bucket,link)
    pending_count=$(echo "$checks_json" | jq '[.[] | select(.bucket=="pending")] | length')
    fail_count=$(echo "$checks_json" | jq '[.[] | select(.bucket=="fail" or .bucket=="cancel")] | length')

    if [ "$pending_count" -eq 0 ]; then
        echo "---"
        echo "$checks_json" | jq -r '.[] | "\(.bucket)\t\(.name)\t\(.link)"'

        if [ "$fail_count" -gt 0 ]; then
            echo "CI failed or canceled."
            exit 1
        fi

        echo "CI completed."
        exit 0
    fi

    echo "Pending checks: $pending_count"
    sleep "$WAIT"
done
