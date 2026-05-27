#!/usr/bin/env bash
# SessionStart hook: print current git branch + (optional) project
# language config as one-line banners.
#
# Banner contract:
#   [git] branch: <current-branch>            (always emitted)
#   [lang] content: <X> | conversation: <Y>   (emitted iff parseable)
#
# Sole graceful-degrade clause: the hook runs before the project may
# have been initialised, so it must never fail-loud or block Claude
# Code startup. Missing config / missing §Language section / missing
# fields → the [lang] line is silently skipped. Exit code is always 0.

set -u

# Always-exit-0 contract is enforced at the program level, not via
# control flow — any intermediate failure (awk error, missing tool,
# unset variable under set -u) still exits 0 via the trap.
trap 'exit 0' EXIT

branch=$(git branch --show-current 2>/dev/null)
if [ -z "$branch" ]; then
    # `git branch --show-current` is empty for both detached HEAD AND
    # a brand-new repo with no commits. Disambiguate via rev-parse so
    # the SessionStart banner doesn't mislead users on a fresh
    # `git init`'d project (common for /holo:init's "empty project"
    # path).
    if git rev-parse --verify HEAD >/dev/null 2>&1; then
        branch="(detached HEAD)"
    else
        branch="(no commits yet)"
    fi
fi
printf "[git] branch: %s\n" "$branch"

config="ai_context/skills_config.md"
if [ -f "$config" ]; then
    # Extract the body of the `## Language` section: everything between
    # `## Language` and the next top-level header (or EOF).
    lang_section=$(awk '
        /^## Language[[:space:]]*$/ { in_section = 1; next }
        /^## / { in_section = 0 }
        in_section { print }
    ' "$config")

    if [ -n "$lang_section" ]; then
        content=$(printf '%s\n' "$lang_section" | awk '
            /content_language:/ {
                sub(/.*content_language:[[:space:]]*/, "")
                sub(/`.*/, "")
                print
                exit
            }')
        conv=$(printf '%s\n' "$lang_section" | awk '
            /conversation_language:/ {
                sub(/.*conversation_language:[[:space:]]*/, "")
                sub(/`.*/, "")
                print
                exit
            }')

        if [ -n "$content" ] && [ -n "$conv" ]; then
            printf "[lang] content: %s | conversation: %s\n" "$content" "$conv"
        fi
    fi
fi

exit 0
