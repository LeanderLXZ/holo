# holo

A Claude Code plugin for AI-paired engineering workflow. Provides slash
commands, query skills, and a project-skeleton scaffold designed
around a small, project-side config file (`ai_context/skills_config.md`)
that lets every skill adapt to the repo it's running in.

## Contents

```
holo/
├── .claude-plugin/plugin.json          # plugin manifest
├── commands/                           # 9 slash commands
│   ├── plan.md                         # discussion-only mode (one turn)
│   ├── go.md                           # 11-step plan → land flow
│   ├── post-check.md                   # two-track audit after /go
│   ├── full-review.md                  # whole-repo alignment audit
│   ├── check-review.md                 # re-validate a stored review report
│   ├── commit.md                       # commit + optional auto-sync
│   ├── push.md                         # fast-forward-only push
│   ├── todo-add.md                     # add/update docs/todo_list.md
│   └── holo-init.md                    # materialize the project skeleton
├── skills/                             # 14 SKILL.md (5 query + 9 mirrors)
│   ├── monitor/                        # background process inventory
│   ├── todo/                           # todo_list index view
│   ├── branch-inventory/               # branch grouping & health
│   ├── recent-activity/                # unified reverse-chrono timeline
│   ├── run-prompt/                     # load & run a prompt file
│   └── <command>/                      # one mirror per command in commands/
├── templates/
│   └── project-skeleton/               # 22 files copied by /holo-init
├── hooks/
│   └── hooks.json                      # SessionStart registration
└── scripts/
    └── session_branch_check.sh         # branch banner + abandoned-work warning
```

## Install

Plugins live under a marketplace or local plugin path configured in
`~/.claude/settings.json`. Quickest local install:

```bash
# from a marketplace dir registered in settings.json
ln -s /home/leander/Leander/holo <marketplace>/holo
```

Then in Claude Code:

```
/plugin install holo
```

## /holo-init — project skeleton scaffolding

Run `/holo-init` from inside a new or existing project. The command:

1. **Detects state** — current dir, git status, conflicting template
   files, project-name / description / main-branch candidates from
   manifests (`package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod`).
2. **Copies template** — silent for new files; interactive for
   conflicts (`keep` / `overwrite` / `merge`).
3. **Asks + fills** — project name, one-line description, main branch,
   timezone, top-level directory classification (source /
   data-contract / example-artifact / do-not-commit). Each answer is
   written immediately so a mid-run interruption preserves progress.
4. **Verifies** — leftover `<...>` placeholders, all required
   `skills_config.md` headers intact, `CLAUDE.md` ↔ `AGENTS.md`
   synced; prints next-step suggestions.

No arguments — repository state is auto-detected.

### Optional `.agents/skills/` mirror

Step 0 asks whether to generate `.agents/skills/<name>/SKILL.md` in the
user's project (14 files copied verbatim from `skills/`). Choose **Yes**
when you cross-validate via Codex / Copilot / other non-Claude runtimes
that don't load Claude Code plugins, or want the project to carry its
own command/skill definitions without depending on the plugin being
installed. Default is **No**.

## Project-side config

Most skills read `ai_context/skills_config.md` in the consuming project
for project-specific anchors. Missing required section → loud fail;
`(none)` body → graceful skip of that anchor's logic.

The 11 required `## <name>` headers (each at top level of
`ai_context/skills_config.md`):

| Section | Used by |
|---|---|
| `## Background processes` | `/commit`, `/go`, `/monitor` (in-flight job detection) |
| `## Protected branch prefixes` | `/commit`, `/go` (branch sync gating) |
| `## Main branch policy` | `/commit`, `/go` (main-branch enforcement) |
| `## Do-not-commit paths` | `/commit`, `/go` (pre-commit safety net) |
| `## Source directories` | `/full-review`, `/post-check` (code scan scope) |
| `## Data contract directories` | `/full-review`, `/post-check` (spec scan scope) |
| `## Example artifact directories` | `/full-review`, `/post-check` (sample scan scope) |
| `## Core component keywords` | `/full-review` (component-alignment audit) |
| `## Sensitive content placeholder rules` | `/go`, `/post-check` (residual scan) |
| `## Timezone` | every skill that writes a timestamp |
| `## Activity sources` | `/recent-activity` |

`scripts/session_branch_check.sh` is the only piece that degrades
gracefully when the config is absent (defaults: main branch = `main`,
no process detection performed).

`/holo-init` materialises a starter `ai_context/skills_config.md` with
all 11 headers present and `(none)` bodies, ready to fill in.

## Mirror enforcement (plugin-internal)

Each `commands/<name>.md` ↔ `skills/<name>/SKILL.md` pair has
**identical body** — from the `# /<name>` heading to the trailing
`**镜像约束**` footer. SKILL.md additionally carries YAML frontmatter
(`name`, `description` — including trigger phrases for harness
matching). Any change to one side must mirror to the other in the
same commit; the footer is identical text on both sides so the rule
is self-evident from either file.

## Design notes

- **Runtime-agnostic with graceful degrade** — every command's
  `<进度工具> 解析` / `<问询工具> 解析` line maps the placeholder to
  the runtime's structured tool (`TodoWrite` / `update_plan` /
  `AskUserQuestion`) and falls back to plain-markdown when none is
  available, so the same command body works in Claude Code, Codex,
  and Copilot agent mode.
- **No automatic git ops** — `/holo-init` does not `git add` or
  commit; persistence is the user's choice via `/commit` or `/go`.
- **`${CLAUDE_PLUGIN_ROOT}`** — commands reference `templates/` and
  `skills/` via this variable; falls back to path-relative discovery
  if the env var is unset (e.g. when copy-pasting a command body
  into a non-plugin chat session).
