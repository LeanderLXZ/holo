#!/usr/bin/env bash
# SessionStart hook: branch banner + anomaly warning.
#
# Prints a one-line status every session. Reads optional project config
# from `ai_context/skills_config.md` to know:
#   - which branch is "main" (from `## Main branch policy` → `- Main branch:`)
#   - which pgrep patterns identify a live orchestrator
#     (from `## Background processes` → `- pgrep patterns:` list)
#
# Behavior:
#   * On the main branch  → plain banner, no process check.
#   * On any other branch:
#       - if any configured pgrep pattern matches a live process → banner
#         + "orchestrator running" note.
#       - else → banner + ⚠ warning that the branch may be abandoned.
#   * If `ai_context/skills_config.md` is absent or sections are missing,
#     defaults are: main = `main`, no pgrep patterns (so non-main branches
#     get a plain banner without a warning).
#
# Exit code is always 0 — a non-zero here would block Claude Code startup.

set -u

config_file="ai_context/skills_config.md"

# --- Helpers ---------------------------------------------------------------
# Extract the body of a `## <header>` section, stopping at the next `## `
# header or EOF. Prints nothing if header not found or file missing.
section_body() {
    local file="$1" header="$2"
    [ -f "$file" ] || return 0
    awk -v hdr="## $header" '
        $0 == hdr        { in_section = 1; next }
        /^## /           { if (in_section) exit }
        in_section       { print }
    ' "$file"
}

# --- Resolve main branch name ---------------------------------------------
main_branch=$(section_body "$config_file" "Main branch policy" \
    | sed -n 's/^[[:space:]]*-[[:space:]]*Main branch:[[:space:]]*//p' \
    | head -n1 \
    | tr -d '`' \
    | awk '{print $1}')
[ -z "$main_branch" ] && main_branch="main"

# --- Resolve pgrep patterns (one per line under `- pgrep patterns:`) ------
pgrep_patterns=$(section_body "$config_file" "Background processes" \
    | awk '
        /^[[:space:]]*-[[:space:]]*pgrep patterns:[[:space:]]*$/ { collect = 1; next }
        /^[[:space:]]*-[[:space:]]*[A-Za-z]/                    { collect = 0 }
        collect && /^[[:space:]]*-[[:space:]]*/ {
            sub(/^[[:space:]]*-[[:space:]]*/, "")
            gsub(/`/, "")
            if (length($0)) print
        }
    ')

# --- Current branch -------------------------------------------------------
branch=$(git branch --show-current 2>/dev/null)
[ -z "$branch" ] && branch="(detached HEAD)"

if [ "$branch" = "$main_branch" ]; then
    printf "[git] branch: %s\n" "$branch"
    exit 0
fi

# Non-main branch: check orchestrator processes if any patterns are configured.
if [ -n "$pgrep_patterns" ]; then
    # Combine patterns with alternation for a single pgrep call.
    alt=$(printf '%s\n' "$pgrep_patterns" | paste -sd'|' -)
    if pgrep -f "$alt" >/dev/null 2>&1; then
        printf "[git] branch: %s  (orchestrator running — work in progress)\n" "$branch"
        exit 0
    fi
    printf "[git] branch: %s  ⚠ no orchestrator process detected — possibly abandoned after crash; check and 'git checkout %s'\n" "$branch" "$main_branch"
    exit 0
fi

# No pgrep patterns configured → just print the banner, no check.
printf "[git] branch: %s\n" "$branch"
exit 0
