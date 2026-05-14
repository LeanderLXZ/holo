#!/usr/bin/env bash
# SessionStart hook: print current git branch as a one-line banner.
# Exit code is always 0 — non-zero would block Claude Code startup.

set -u

branch=$(git branch --show-current 2>/dev/null)
[ -z "$branch" ] && branch="(detached HEAD)"

printf "[git] branch: %s\n" "$branch"
exit 0
