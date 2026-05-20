#!/usr/bin/env python3
"""
holo_update_check.py — single source of truth for project ↔ plugin drift.

Invoked by:
- /holo:update: full check + optional auto-fix flow (--check / --fix).
- /holo:init Step 1.2: imports `expected_mirror_content` for mirror generation.

CLI:
    python3 scripts/holo_update_check.py --json
    python3 scripts/holo_update_check.py --fix --json

Skill bodies MUST NOT reimplement these checks; if a rule needs to change,
change it here and update the dependent skills per
ai_context/conventions.md §Cross-File Alignment.

See ai_context/decisions.md §Skill Implementation #5 for rationale.
"""

import argparse
import difflib
import glob
import json
import os
import re
import shutil
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Plugin root resolution
# ---------------------------------------------------------------------------

def find_plugin_root(override: str | None = None) -> str:
    """Resolve plugin root: --plugin-root flag > env > derive from this file.

    All three branches must point at a directory holding
    `.claude-plugin/plugin.json`. The --plugin-root override is validated
    the same way as the env / auto-detect branches so a typo or stale CI
    path cannot silently mask drift findings as `total_drift = 0`.
    """
    if override:
        candidate = Path(os.path.abspath(override))
        if not (candidate / ".claude-plugin" / "plugin.json").exists():
            sys.exit(
                f"--plugin-root {override!r} is not a plugin root "
                "(missing .claude-plugin/plugin.json)"
            )
        return str(candidate)
    pr = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if pr:
        return pr
    # Derive: this script lives in <plugin_root>/scripts/
    candidate = Path(__file__).resolve().parent.parent
    if (candidate / ".claude-plugin" / "plugin.json").exists():
        return str(candidate)
    sys.exit(
        "CLAUDE_PLUGIN_ROOT not set and cannot auto-detect plugin root from "
        "script location; pass --plugin-root explicitly"
    )


# ---------------------------------------------------------------------------
# Pure function: expected mirror content
# ---------------------------------------------------------------------------

def expected_mirror_content(source_path: str, name: str, source_type: str) -> str:
    """
    Compute the expected `.agents/skills/<name>/SKILL.md` content.

    SINGLE SOURCE OF TRUTH — used both for /holo:update drift detection and
    for /holo:init Step 1.2 initial mirror generation. Do not reimplement.

    source_type:
        'command' — frontmatter is injected with `name: <name>` (commands/*.md
                    do not declare it; Claude Code derives from filename).
        'skill'   — byte-for-byte copy (skills/*/SKILL.md already has frontmatter).

    Source files are read as UTF-8 with BOM tolerated (`utf-8-sig`) and
    line endings normalised to LF before the frontmatter regex runs.
    Without this normalisation, CRLF-saved sources fall through to the
    duplicate-frontmatter fallback and STALE churn never clears.
    """
    with open(source_path, "r", encoding="utf-8-sig", newline="") as f:
        content = f.read().replace("\r\n", "\n").replace("\r", "\n")
    if source_type == "skill":
        return content
    if source_type != "command":
        raise ValueError(f"unknown source_type: {source_type!r}")
    m = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if m:
        front, body = m.group(1), content[m.end():]
        if not re.search(r"^name:\s", front, re.MULTILINE):
            front = f"name: {name}\n{front}"
        return f"---\n{front}\n---\n{body}"
    return f"---\nname: {name}\n---\n{content}"


# ---------------------------------------------------------------------------
# Detection functions
# ---------------------------------------------------------------------------

def agents_sync_check(plugin_root: str, target_root: str) -> dict:
    """Detect `.agents/skills/` mirror drift (STALE / MISSING / ORPHAN)."""
    agents_dir = os.path.join(target_root, ".agents/skills")
    if not os.path.isdir(agents_dir):
        return {"skipped": True, "stale": [], "missing": [], "orphan": []}

    stale: list[dict] = []
    missing: list[dict] = []
    orphan: list[dict] = []
    plugin_names: set[str] = set()

    def check_source(source_path: str, name: str, source_type: str) -> None:
        target = os.path.join(agents_dir, name, "SKILL.md")
        item = {
            "name": name,
            "source_path": source_path,
            "source_type": source_type,
            "target_path": target,
        }
        if not os.path.exists(target):
            missing.append(item)
            return
        if open(target, encoding="utf-8").read() != expected_mirror_content(source_path, name, source_type):
            stale.append(item)

    for cmd in sorted(glob.glob(f"{plugin_root}/commands/*.md")):
        name = os.path.splitext(os.path.basename(cmd))[0]
        plugin_names.add(name)
        check_source(cmd, name, "command")
    for sk in sorted(glob.glob(f"{plugin_root}/skills/*/SKILL.md")):
        name = os.path.basename(os.path.dirname(sk))
        plugin_names.add(name)
        check_source(sk, name, "skill")

    for d in sorted(glob.glob(f"{agents_dir}/*/SKILL.md")):
        name = os.path.basename(os.path.dirname(d))
        if name not in plugin_names:
            orphan.append({"name": name, "target_path": d})

    return {"skipped": False, "stale": stale, "missing": missing, "orphan": orphan}


# ---------------------------------------------------------------------------
# Consumer-language-aware baseline resolution
# ---------------------------------------------------------------------------
#
# Consumer projects may set `content_language: <lang>` in their
# `ai_context/skills_config.md §Language`. When `<lang>` is not English
# and the plugin ships a `templates/project-skeleton.<lang>/` variant,
# section-level checks (template_section_check, claude_agents_check)
# must compare against that variant — otherwise the checks report
# headers / lines from the canonical EN baseline as missing in a
# legitimate non-EN consumer file, and Auto-fix appends EN content
# into a translated file, corrupting it.

# Wide capture: any backtick-quoted token under `content_language:` so
# we can fail loud on invalid values (e.g. `cn`, `zh-CN`) rather than
# silently fall through to `en`. The ISO 639-1 lock is enforced
# explicitly below.
_CONTENT_LANG_RE = re.compile(
    r"^\s*-\s*`content_language:\s*([A-Za-z0-9-]+)`", re.MULTILINE
)


def _consumer_content_lang(target_root: str) -> str:
    """Read `content_language` from consumer's skills_config.md §Language.

    Returns the 2-letter ISO 639-1 value (lowercase). Fails loud on
    invalid values to prevent silent ZH→EN baseline corruption:
    - `cn` (country code, not ISO 639-1) → fail with hint to use `zh`.
    - `zh-CN` / locale variants → fail per §15 ("reserved for future
      regional splits").
    - any non-2-letter or uppercase value → fail with §15 citation.

    Missing file / section / field returns 'en' (canonical fallback)
    — that branch is the legitimate "consumer has not configured
    §Language yet" case, not user-typed bad data.
    """
    cfg = os.path.join(target_root, "ai_context", "skills_config.md")
    if not os.path.isfile(cfg):
        return "en"
    try:
        with open(cfg, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return "en"
    m = _CONTENT_LANG_RE.search(text)
    if not m:
        return "en"
    value = m.group(1)
    if value == "cn":
        sys.exit(
            "ai_context/skills_config.md §Language: content_language='cn' "
            "is not ISO 639-1; use 'zh' per docs/requirements.md §15."
        )
    if "-" in value:
        sys.exit(
            f"ai_context/skills_config.md §Language: content_language="
            f"'{value}' is a locale variant; locale variants are "
            "reserved for future regional splits per "
            "docs/requirements.md §15. Use a bare ISO 639-1 code."
        )
    if not re.fullmatch(r"[a-z]{2}", value):
        sys.exit(
            f"ai_context/skills_config.md §Language: content_language="
            f"'{value}' is not a valid ISO 639-1 code (expected 2 "
            "lowercase letters per docs/requirements.md §15)."
        )
    return value


def _skeleton_root(plugin_root: str, content_lang: str) -> str:
    """Resolve the active project-skeleton root for the consumer's language.

    For `content_lang == 'en'` (or when no variant exists) → canonical
    `templates/project-skeleton/`. Otherwise → `templates/project-skeleton.<lang>/`
    if present, else fall back to canonical (graceful degrade — the
    `missing_template` finding will then flag the file as needing
    creation, but at least won't corrupt content via section diff).
    """
    canonical = os.path.join(plugin_root, "templates/project-skeleton")
    if content_lang == "en":
        return canonical
    variant = os.path.join(plugin_root, f"templates/project-skeleton.{content_lang}")
    return variant if os.path.isdir(variant) else canonical


def template_file_check(plugin_root: str, target_root: str) -> list[dict]:
    """Files present in templates/project-skeleton[.<lang>]/ but absent from project."""
    skel = _skeleton_root(plugin_root, _consumer_content_lang(target_root))
    missing: list[dict] = []
    for f in glob.glob(f"{skel}/**/*", recursive=True):
        if not os.path.isfile(f):
            continue
        rel = os.path.relpath(f, skel)
        target = os.path.join(target_root, rel)
        if not os.path.exists(target):
            missing.append({"rel": rel, "source_path": f, "target_path": target})
    return missing


def _md_headers(path: str) -> set[str]:
    """Return the set of `^## ` headers in a markdown file, ignoring
    headers that appear inside fenced code blocks (``` / ~~~) or HTML
    comments (<!-- ... -->). Without these skips, code-block `## `
    examples are harvested as real headers and corrupt the
    template-vs-project diff in either direction (false negative when
    the example is in both files, false positive when the consumer's
    file has a code-block heading and the template does not).
    """
    headers: set[str] = set()
    in_fence = False
    in_html_comment = False
    fence_marker = ""
    with open(path, encoding="utf-8") as f:
        for raw in f:
            stripped = raw.lstrip()
            # Code fence toggle: a line starting with ``` or ~~~ flips
            # state; closing fence must match the opener's marker.
            if not in_html_comment:
                if not in_fence and (stripped.startswith("```") or stripped.startswith("~~~")):
                    in_fence = True
                    fence_marker = stripped[:3]
                    continue
                if in_fence and stripped.startswith(fence_marker):
                    in_fence = False
                    fence_marker = ""
                    continue
            if in_fence:
                continue
            # HTML comment: may span multiple lines; toggle on open/close.
            if not in_html_comment and "<!--" in raw:
                in_html_comment = True
            if in_html_comment:
                if "-->" in raw:
                    in_html_comment = False
                continue
            if re.match(r"^## ", raw):
                headers.add(raw.rstrip())
    return headers


def template_section_check(plugin_root: str, target_root: str) -> list[dict]:
    """For .md files present in both, find `^## ` headers in template[.<lang>] missing from project."""
    skel = _skeleton_root(plugin_root, _consumer_content_lang(target_root))
    missing: list[dict] = []
    for f in glob.glob(f"{skel}/**/*.md", recursive=True):
        rel = os.path.relpath(f, skel)
        target = os.path.join(target_root, rel)
        if not os.path.exists(target):
            continue  # covered by template_file_check
        for h in sorted(_md_headers(f) - _md_headers(target)):
            missing.append({"rel": rel, "header": h, "source_path": f})
    return missing


# ---------------------------------------------------------------------------
# Field-level drift inside ai_context/skills_config.md
# ---------------------------------------------------------------------------
#
# Scope is intentionally narrow (decisions.md §Skill Implementation #13):
# only the consumer's ai_context/skills_config.md is parsed for top-level
# `<key>: <value>` bullets, and only those bullets are diffable as
# "fields". Other bullet shapes in skills_config.md — trailing-colon
# sub-block labels (`- pgrep patterns:` and their indented children),
# freestanding value-only bullets (`- `(none)`` under §Source directories)
# — are intentionally not parsed and cannot trigger findings.

# Backticked field: `<key>: <value>` (used by §Language for content_language
# / conversation_language). Key must be identifier-like (starts with a
# letter, then word chars / spaces / hyphens) so prose lines containing
# inline code spans like `- `content_language` governs ...` do not match
# (no colon inside the backticks).
_FIELD_BACKTICKED_RE = re.compile(r"^`([A-Za-z_][\w\s-]*?):\s*([^`]*)`")

# Plain field: <Capitalized Key>: <value> (used by §Main branch policy,
# §Timezone). Key must start uppercase and contain only letters / digits /
# spaces / underscores / hyphens, ≤ 40 chars, to filter out prose lines
# that happen to contain a colon ("Language codes follow ISO 639-1 (`zh`, ..."
# has no colon at all; "Notes:" is not a bullet). Value must start with a
# non-whitespace character — bullets like `- Change logs:` (trailing colon,
# no value) fall through to the trailing-colon skip below.
_FIELD_PLAIN_RE = re.compile(r"^([A-Z][A-Za-z0-9 _-]{0,40}?):\s+\S.*$")

# Trailing-colon sub-block label: `- pgrep patterns:` / `- Change logs:`.
# Must NOT contain backticks, angle brackets, or a colon before the trailing
# colon — those shapes are field values, not labels.
_FIELD_TRAILING_RE = re.compile(r"^[^:`<>]+?:\s*$")


def _skills_config_fields(path: str) -> dict[str, dict[str, str]]:
    """Parse a skills_config.md file into {section_header: {key: form}}.

    Returns one entry per `## ` section (even sections with zero fields,
    so the diff against the baseline knows the section exists in the
    consumer). Section headers include the `## ` prefix verbatim for
    direct equality with `_md_headers`-style headers.

    `form` is `"backticked"` or `"plain"`, recording how the baseline
    wrote the key:value bullet so the fixer can append a new field in
    the matching style (e.g. `## Language` fields land as
    `` `conversation_language: _(TODO ...)_` `` rather than the plain
    form `conversation_language: _(TODO ...)_`, which the parser would
    not re-recognize on the next `--check` pass — plain bullets require
    a capital first letter to filter prose).

    Field recognition rules: see module-level _FIELD_*_RE comments above.
    """
    sections: dict[str, dict[str, str]] = {}
    current_section: str | None = None
    in_fence = False
    in_html_comment = False
    fence_marker = ""

    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return sections

    for raw in lines:
        stripped = raw.lstrip()
        if not in_html_comment:
            if not in_fence and (stripped.startswith("```") or stripped.startswith("~~~")):
                in_fence = True
                fence_marker = stripped[:3]
                continue
            if in_fence and stripped.startswith(fence_marker):
                in_fence = False
                fence_marker = ""
                continue
        if in_fence:
            continue
        if not in_html_comment and "<!--" in raw:
            in_html_comment = True
        if in_html_comment:
            if "-->" in raw:
                in_html_comment = False
            continue
        m = re.match(r"^(## .+?)\s*$", raw)
        if m:
            current_section = m.group(1)
            sections.setdefault(current_section, {})
            continue
        if current_section is None:
            continue
        if not raw.startswith("- "):
            # Top-level bullets only — indented `  - Path: ...` lines are
            # part of an outer sub-block, never fields in their own right.
            continue
        rest = raw[2:].rstrip("\n").rstrip()
        if _FIELD_TRAILING_RE.match(rest):
            # Sub-block label like `- Change logs:` — has indented
            # children, never a field on its own.
            continue
        m = _FIELD_BACKTICKED_RE.match(rest)
        if m:
            sections[current_section].setdefault(m.group(1).strip(), "backticked")
            continue
        m = _FIELD_PLAIN_RE.match(rest)
        if m:
            sections[current_section].setdefault(m.group(1).strip(), "plain")
            continue
        # Otherwise: value-only bullet (`- `(none)`` / `- `commands/``) or
        # a prose line that survived the bullet check. Skip — not a field.

    return sections


def missing_field_check(plugin_root: str, target_root: str) -> list[dict]:
    """Compare ai_context/skills_config.md fields baseline vs consumer.

    Returns one finding per missing field. Skipped when:
    - Baseline or consumer file does not exist (covered by other checks).
    - The owning section is absent from the consumer entirely (covered
      by `missing_section`; avoid double-flagging the same drift).
    """
    skel = _skeleton_root(plugin_root, _consumer_content_lang(target_root))
    rel = "ai_context/skills_config.md"
    source_path = os.path.join(skel, rel)
    target_path = os.path.join(target_root, rel)
    if not os.path.isfile(source_path) or not os.path.isfile(target_path):
        return []
    baseline = _skills_config_fields(source_path)
    consumer = _skills_config_fields(target_path)
    findings: list[dict] = []
    for section, baseline_fields in baseline.items():
        if section not in consumer:
            continue  # missing_section owns this case
        consumer_keys = set(consumer[section].keys())
        for key, form in baseline_fields.items():
            if key not in consumer_keys:
                findings.append(
                    {
                        "rel": rel,
                        "section": section,
                        "key": key,
                        "form": form,
                        "source_path": source_path,
                    }
                )
    return findings


def _find_section_bounds(lines: list[str], header: str) -> tuple[int, int] | None:
    """Return (body_start, body_end) line indices for the section whose
    header line equals `header` (e.g. `## Language`). body_start points at
    the line right after the header; body_end is the index of the next
    `^## ` line or len(lines). Returns None if header not found.
    """
    for i, line in enumerate(lines):
        if line.rstrip() == header:
            body_start = i + 1
            body_end = len(lines)
            for j in range(body_start, len(lines)):
                if lines[j].startswith("## "):
                    body_end = j
                    break
            return (body_start, body_end)
    return None


def fix_missing_field(target_root: str, findings: list[dict]) -> int:
    """Append each missing field as a `<key>: _(TODO ...)_` bullet at the
    tail of its owning section's top-level bullet list. Returns the count
    of fields appended.

    Placement: immediately after the last `^- ` bullet within the section.
    When the section has no existing top-level bullets, insert at the end
    of the section body, ensuring a leading blank line.

    Never modifies the value of an existing field (decisions.md §Skill
    Implementation #13): the parser de-duplicates by key, so a re-run after
    a successful fix produces no further findings for the same key even if
    the user later edited the auto-inserted value.
    """
    todo_marker = "_(TODO — added by /holo:update; fill via /go or direct edit)_"

    def _render(key: str, form: str) -> str:
        # Backticked: `<key>: <value>` — matches the §Language form so the
        # parser re-recognizes it on the next --check pass.
        # Plain: <Capitalized Key>: <value> — matches §Main branch policy /
        # §Timezone form. Keys that came in as "plain" already start with
        # a capital (the parser only accepts that shape), so the rendered
        # line round-trips through the plain regex on re-check.
        if form == "backticked":
            return f"- `{key}: {todo_marker}`\n"
        return f"- {key}: {todo_marker}\n"

    count = 0
    by_file: dict[str, list[dict]] = {}
    for item in findings:
        by_file.setdefault(item["rel"], []).append(item)
    for rel, items in by_file.items():
        target = os.path.join(target_root, rel)
        with open(target, encoding="utf-8") as f:
            lines = f.readlines()
        # Batch by section so each section's bounds are resolved once on
        # the as-yet-unmodified buffer; process sections latest-first so
        # earlier insertions don't shift later section start indices.
        by_section: dict[str, list[tuple[str, str]]] = {}
        for item in items:
            by_section.setdefault(item["section"], []).append(
                (item["key"], item.get("form", "plain"))
            )
        ordered: list[tuple[int, int, list[tuple[str, str]]]] = []
        for section, pairs in by_section.items():
            bounds = _find_section_bounds(lines, section)
            if bounds is None:
                continue  # section absent: missing_section's job
            ordered.append((bounds[0], bounds[1], pairs))
        ordered.sort(key=lambda t: t[0], reverse=True)
        for body_start, body_end, pairs in ordered:
            insert_at = None
            for i in range(body_end - 1, body_start - 1, -1):
                if lines[i].startswith("- "):
                    insert_at = i + 1
                    break
            if insert_at is None:
                # Empty section: place at body end, with a leading blank
                # line if the previous line isn't already blank.
                insert_at = body_end
                if insert_at > 0 and lines[insert_at - 1].strip():
                    lines.insert(insert_at, "\n")
                    insert_at += 1
            new_lines = [_render(k, fm) for k, fm in pairs]
            for j, nl in enumerate(new_lines):
                lines.insert(insert_at + j, nl)
            count += len(pairs)
        with open(target, "w", encoding="utf-8") as f:
            f.writelines(lines)
    return count


def _derive_expected_pairs(skel_root: str) -> list[tuple[str, str]] | None:
    """Build expected_pairs from a skeleton's CLAUDE.md ↔ AGENTS.md line diff.

    Returns the list of (CLAUDE-side substring, AGENTS-side substring) tuples
    formed by aligning the two files line-by-line and recording every position
    where they differ. Returns None when either file is absent in this
    skeleton (caller should fall back to the EN-canonical hardcoded list).
    """
    cl_path = os.path.join(skel_root, "CLAUDE.md")
    ag_path = os.path.join(skel_root, "AGENTS.md")
    if not (os.path.isfile(cl_path) and os.path.isfile(ag_path)):
        return None
    cl = open(cl_path, encoding="utf-8").read().splitlines()
    ag = open(ag_path, encoding="utf-8").read().splitlines()
    pairs: list[tuple[str, str]] = []
    for i in range(min(len(cl), len(ag))):
        if cl[i] != ag[i] and cl[i].strip() and ag[i].strip():
            pairs.append((cl[i].strip(), ag[i].strip()))
    return pairs


# Canonical EN pairs — used when consumer is EN or when a variant skeleton
# has no CLAUDE/AGENTS pair to derive from.
_EN_EXPECTED_PAIRS = [
    ("Claude Entry Point", "Agent Entry Point"),
    ("auto-loaded by Claude", "auto-loaded by coding agents"),
    ("Sync with AGENTS.md", "Sync with CLAUDE.md"),
    ("This file and `AGENTS.md`", "This file and `CLAUDE.md`"),
    ('"Claude Entry Point"', '"Agent Entry Point"'),
]


def claude_agents_check(target_root: str, plugin_root: str | None = None) -> dict:
    """CLAUDE.md / AGENTS.md placeholder + cross-sync diff (report only — never auto-merged).

    Consumer-language-aware: when the consumer's `content_language` is
    non-EN and a matching `templates/project-skeleton.<lang>/` ships in
    the plugin, the expected-diff pairs are derived dynamically from that
    variant's CLAUDE.md ↔ AGENTS.md. Without this, a ZH consumer's
    legitimate translated entry-point lines would be reported as
    `unexpected_diffs` (and a user-blind Auto-fix could corrupt them).
    """
    cl_path = os.path.join(target_root, "CLAUDE.md")
    ag_path = os.path.join(target_root, "AGENTS.md")
    result: dict = {
        "present": False,
        "first_line_placeholder": False,
        "unexpected_diffs": [],
        "unexpected_diffs_truncated": 0,
    }
    if not (os.path.exists(cl_path) and os.path.exists(ag_path)):
        return result
    result["present"] = True

    cl_first = open(cl_path, encoding="utf-8").readline().rstrip()
    ag_first = open(ag_path, encoding="utf-8").readline().rstrip()
    if "<project-name>" in cl_first or "<project-name>" in ag_first:
        result["first_line_placeholder"] = True

    expected_pairs = _EN_EXPECTED_PAIRS
    if plugin_root is not None:
        lang = _consumer_content_lang(target_root)
        if lang != "en":
            skel = _skeleton_root(plugin_root, lang)
            derived = _derive_expected_pairs(skel)
            if derived:
                expected_pairs = derived

    cl = open(cl_path, encoding="utf-8").read().splitlines()
    ag = open(ag_path, encoding="utf-8").read().splitlines()

    # Use SequenceMatcher rather than a positional `for i in range(max(...))`
    # loop: one inserted/removed line should not cascade every subsequent
    # line into `unexpected_diffs`. Each replace/insert/delete block is
    # reported on its anchor line; the expected_pairs filter still runs
    # per pair, so the entry-point labels ("Claude Entry Point" vs
    # "Agent Entry Point", etc.) remain expected.
    matcher = difflib.SequenceMatcher(a=cl, b=ag, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "replace":
            block_size = max(i2 - i1, j2 - j1)
            for k in range(block_size):
                l1 = cl[i1 + k] if i1 + k < i2 else None
                l2 = ag[j1 + k] if j1 + k < j2 else None
                if l1 is None or l2 is None:
                    is_expected = False
                else:
                    is_expected = any(
                        (s1 in l1 and s2 in l2) or (s2 in l1 and s1 in l2)
                        for s1, s2 in expected_pairs
                    )
                if not is_expected:
                    result["unexpected_diffs"].append(
                        {"line": i1 + k + 1, "CLAUDE": l1, "AGENTS": l2}
                    )
        elif tag == "insert":
            # Lines present only in AGENTS.md (CLAUDE side absent).
            for k in range(j2 - j1):
                result["unexpected_diffs"].append(
                    {"line": i1 + 1, "CLAUDE": None, "AGENTS": ag[j1 + k]}
                )
        elif tag == "delete":
            # Lines present only in CLAUDE.md (AGENTS side absent).
            for k in range(i2 - i1):
                result["unexpected_diffs"].append(
                    {"line": i1 + k + 1, "CLAUDE": cl[i1 + k], "AGENTS": None}
                )

    # Cap reported diffs to keep the report readable when a consumer has
    # heavily asymmetric CLAUDE.md / AGENTS.md (legitimate use case: one
    # side carries Claude-specific or codex-specific guidance the other
    # side should not). Without the cap, `total_drift` would drown
    # actionable findings (STALE / MISSING) in dozens of report-only
    # CLAUDE/AGENTS line items.
    _UNEXPECTED_DIFFS_CAP = 10
    if len(result["unexpected_diffs"]) > _UNEXPECTED_DIFFS_CAP:
        result["unexpected_diffs_truncated"] = (
            len(result["unexpected_diffs"]) - _UNEXPECTED_DIFFS_CAP
        )
        result["unexpected_diffs"] = result["unexpected_diffs"][:_UNEXPECTED_DIFFS_CAP]
    return result


# ---------------------------------------------------------------------------
# L1 language directive presence check (per Phase 5 of T-LANG-CONFIG-SYSTEM)
# ---------------------------------------------------------------------------

_L1_PATTERN = "> **Language**:"

# Canonical structural elements every L1 directive blockquote must carry.
# Per-skill parenthetical examples legitimately vary (Decision #10 anchor
# design: L1 anchors the skill's specific disk-bound outputs); strict
# text-equality would false-positive on every customized L1. This tuple
# captures only the structural invariants — references the §Language
# section by name, names both buckets + both axes, retains the
# "stay English" immutable-identifiers clause that V2 (Decision #10)
# reinforced. Edits to a skill's parenthetical content do not trip the
# lint; renaming a bucket label, dropping an axis, or omitting the
# immutable clause does.
_L1_REQUIRED_SUBSTRINGS: tuple[str, ...] = (
    "ai_context/skills_config.md §Language",
    "disk-bound",
    "content_language",
    "user-facing",
    "conversation_language",
    "stay English",
)


def _l1_targets(plugin_root: str) -> list[tuple[str, str]]:
    """Enumerate every commands/*.md and skills/*/SKILL.md target — shared by
    `l1_directive_check` and `l1_directive_drift_check`.
    """
    commands_dir = os.path.join(plugin_root, "commands")
    skills_dir = os.path.join(plugin_root, "skills")

    targets: list[tuple[str, str]] = []
    if os.path.isdir(commands_dir):
        for name in sorted(os.listdir(commands_dir)):
            if name.endswith(".md"):
                targets.append((os.path.join(commands_dir, name), f"commands/{name}"))
    if os.path.isdir(skills_dir):
        for name in sorted(os.listdir(skills_dir)):
            sk = os.path.join(skills_dir, name, "SKILL.md")
            if os.path.isfile(sk):
                targets.append((sk, f"skills/{name}/SKILL.md"))
    return targets


def _l1_scan_start(lines: list[str]) -> int:
    """Find the line index right after the YAML frontmatter close (the second
    `---` line). If no frontmatter, return 0.
    """
    if lines and lines[0].rstrip() == "---":
        for i in range(1, min(len(lines), 50)):
            if lines[i].rstrip() == "---":
                return i + 1
    return 0


def _l1_blockquote_text(lines: list[str], scan_start: int) -> str | None:
    """Locate the L1 blockquote within 12 lines after frontmatter close and
    return the full blockquote text (the `> **Language**:` line plus every
    immediately-following continuation line that starts with `>`). Returns
    `None` if the blockquote prefix is not found in the scan window.
    """
    l1_start = None
    for i in range(scan_start, min(len(lines), scan_start + 12)):
        if _L1_PATTERN in lines[i]:
            l1_start = i
            break
    if l1_start is None:
        return None
    chunks = [lines[l1_start]]
    j = l1_start + 1
    while j < len(lines) and lines[j].lstrip().startswith(">"):
        chunks.append(lines[j])
        j += 1
    return "".join(chunks)


def l1_directive_check(plugin_root: str) -> list[dict]:
    """Verify every commands/*.md and skills/*/SKILL.md carries the L1 language directive blockquote.

    Scans within the first 12 lines after the frontmatter close (``---`` line),
    looking for a line that starts with ``> **Language**:``. Missing files are
    reported. Report-only — auto-inserting prose into a skill body is risky
    enough that the maintainer should /go-edit it manually.
    """
    findings: list[dict] = []
    for path, rel in _l1_targets(plugin_root):
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except OSError as e:
            findings.append({"rel": rel, "reason": f"read error: {e}"})
            continue
        scan_start = _l1_scan_start(lines)
        window = lines[scan_start:scan_start + 12]
        if not any(_L1_PATTERN in ln for ln in window):
            findings.append({"rel": rel, "reason": "L1 directive blockquote not found within 12 lines after frontmatter"})
    return findings


def l1_directive_drift_check(plugin_root: str) -> list[dict]:
    """Verify each L1 directive blockquote contains the canonical structural
    substrings declared in ``_L1_REQUIRED_SUBSTRINGS``.

    Files whose L1 blockquote prefix is not found in the scan window are
    skipped here — `l1_directive_check` is the presence lint and reports
    those cases. Files that have an L1 blockquote but miss one or more
    required substrings produce a drift finding listing the missing pieces.
    Report-only — L1 prose is LLM-authored; auto-edit is too risky.
    """
    findings: list[dict] = []
    for path, rel in _l1_targets(plugin_root):
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except OSError:
            # Read errors already reported by l1_directive_check; do not
            # double-flag here.
            continue
        scan_start = _l1_scan_start(lines)
        text = _l1_blockquote_text(lines, scan_start)
        if text is None:
            # Presence failure — out of scope for this drift lint.
            continue
        missing = [s for s in _L1_REQUIRED_SUBSTRINGS if s not in text]
        if missing:
            findings.append({"rel": rel, "missing_substrings": missing})
    return findings


# ---------------------------------------------------------------------------
# Language-variant template mirror drift check (per Phase 5 of T-LANG-CONFIG-SYSTEM)
# ---------------------------------------------------------------------------

def lang_mirror_check(plugin_root: str) -> list[dict]:
    """Scan templates/project-skeleton.<lang>/ variants for structural drift vs canonical.

    For each ``templates/project-skeleton.<lang>/`` directory (e.g.
    ``.zh/`` / ``.ja/``), compare its file tree against the canonical
    ``templates/project-skeleton/`` (English source of truth):

    - ``MISSING`` — file present in canonical but not in this variant.
    - ``ORPHAN``  — file present in this variant but not in canonical.

    Content drift (``STALE``) is intentionally NOT detected here: variant
    files differ in content by design (they are translations). Structural
    consistency is the cheap, useful check; semantic drift requires the
    four-agent review chain of `/holo:init` and is out of scope for the lint.

    Report-only: variant content is translation work; auto-overwrite would
    destroy human translations.

    When no ``.<lang>/`` variant exists, returns an empty list (no-op).
    """
    findings: list[dict] = []
    templates_dir = os.path.join(plugin_root, "templates")
    if not os.path.isdir(templates_dir):
        return findings

    canonical_root = os.path.join(templates_dir, "project-skeleton")
    if not os.path.isdir(canonical_root):
        return findings

    # Discover variant dirs: project-skeleton.<ISO 639-1 code>
    # Tight whitelist (2 lowercase a-z) avoids picking up noise like
    # project-skeleton.bak / .old / .tmp / .orig as if they were locale
    # variants. Future locale variants (zh-CN) will need an explicit
    # widening of this pattern.
    iso_re = re.compile(r"^project-skeleton\.[a-z]{2}$")
    variants: list[str] = []
    for name in sorted(os.listdir(templates_dir)):
        path = os.path.join(templates_dir, name)
        if os.path.isdir(path) and iso_re.match(name):
            variants.append(name)
    if not variants:
        return findings

    canonical_files = _walk_files_relative(canonical_root)

    for variant in variants:
        variant_root = os.path.join(templates_dir, variant)
        variant_files = _walk_files_relative(variant_root)

        for rel in sorted(canonical_files - variant_files):
            findings.append({"variant": variant, "rel": rel, "kind": "MISSING"})
        for rel in sorted(variant_files - canonical_files):
            findings.append({"variant": variant, "rel": rel, "kind": "ORPHAN"})

    return findings


def _walk_files_relative(root: str) -> set[str]:
    out: set[str] = set()
    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            full = os.path.join(dirpath, f)
            out.add(os.path.relpath(full, root))
    return out


# ---------------------------------------------------------------------------
# `.gitignore` smart-merge: three-phase pipeline
# ---------------------------------------------------------------------------
#
# Phase 1 (gitignore_compute_union): deterministic union of pattern lines.
#   Used by /holo:init CONFLICT as input to the LLM step + fallback content
#   on gate failure; used by /holo:update --fix as the direct output (no LLM).
# Phase 2 (LLM reorganize): runs only at /holo:init CONFLICT, in the skill
#   body's AI-agent context. The agent invokes its own LLM with a prompt that
#   requires preserving the exact pattern set and using only the seven
#   whitelisted section headers below.
# Phase 3 (gitignore_verify_reorganize): strict gate; LLM output must preserve
#   pattern set AND restrict comment-prefix lines to the whitelist (plus the
#   sentinel banner). Failure triggers fallback to the Phase 1 raw union.
#
# See ai_context/decisions.md §Skill Implementation #14 for rationale.

_GITIGNORE_SECTION_WHITELIST: frozenset[str] = frozenset({
    "# Editor / IDE",
    "# Python",
    "# Node",
    "# OS",
    "# Local config",
    "# Build outputs / caches",
    "# Project-specific",
})

_LEGACY_SKIP_MARKER_RE = re.compile(
    r"_\(TODO\s*[—-]\s*skipped\s*at\s*/holo:init;\s*fill\s*via\s*later\s*/go\s*or\s*directly\s*edit\)_"
)


def legacy_skip_marker_check(target_root: str) -> list[dict]:
    """Scan consumer top-level + ``ai_context/`` + ``docs/`` ``.md`` files
    for legacy ``_(TODO — skipped at /holo:init; fill via later /go or
    directly edit)_`` markers left over from the pre-three-bucket-schema
    init (Round 3 Skip path, deleted in T-INIT-SKIP-SEMANTICS / see
    ``ai_context/decisions.md`` §Skill Implementation #15).

    Informational only — NO ``--fix`` branch. The correct replacement
    depends on the section's intent (delete + copy canonical ``<...>``
    guidance back from the template / write real content / leave the
    section empty via PROGRESSIVE ``_(none yet — ...)_`` marker), which a
    deterministic script cannot decide. The user (or ``/go``) handles it
    manually.

    Findings shape: ``[{"rel": "...", "line": N, "snippet": "..."}, ...]``
    where ``snippet`` is the line content truncated at 200 chars.

    Excluded from ``total_drift`` for the same reason as
    ``claude_agents.unexpected_diffs``: counting historical / report-only
    items would drown actionable findings (STALE / MISSING / etc.).
    """
    findings: list[dict] = []
    targets: list[str] = []
    for name in ("CLAUDE.md", "AGENTS.md", "README.md"):
        path = os.path.join(target_root, name)
        if os.path.isfile(path):
            targets.append(path)
    for sub in ("ai_context", "docs"):
        sub_root = os.path.join(target_root, sub)
        if not os.path.isdir(sub_root):
            continue
        for root, _dirs, files in os.walk(sub_root):
            for fn in files:
                if fn.endswith(".md"):
                    targets.append(os.path.join(root, fn))
    for path in sorted(targets):
        try:
            with open(path, encoding="utf-8") as fh:
                for i, line in enumerate(fh, 1):
                    if _LEGACY_SKIP_MARKER_RE.search(line):
                        rel = os.path.relpath(path, target_root)
                        findings.append({
                            "rel": rel,
                            "line": i,
                            "snippet": line.rstrip("\n")[:200],
                        })
        except OSError:
            continue
    return findings


_GITIGNORE_BANNER = "# ↓ plugin-skeleton template additions ↓"


def gitignore_pattern_lines(content: str) -> set[str]:
    """Extract canonical pattern lines from .gitignore content.

    A line starting with `#` (after optional leading whitespace) is a
    comment; blank lines are ignored. Everything else is a pattern,
    stripped of surrounding whitespace. The escape `\\#` at start of
    line stays escaped in the canonical form (NOT decoded to `#`)
    so the value round-trips through write-back: a decoded `#foo`
    written to disk would be re-parsed as a comment on the next
    check pass, the pattern would reappear as missing, and `--fix`
    would loop. Inline `#` mid-pattern is part of the pattern (git
    treats the whole line as the pattern in that case).

    A leading UTF-8 BOM is stripped before parsing. Without this,
    an editor-injected BOM (Windows Notepad, some IDE saves) would
    bind to the first pattern (`\\ufeff*.swp`) and never match the
    consumer's clean `*.swp` — the pattern would report as missing
    forever and `--fix` would append a BOM-prefixed duplicate every
    run.

    Used by `gitignore_compute_union` (Phase 1) and
    `gitignore_verify_reorganize` (Phase 3) for set-equality
    comparisons. The canonical form (stripped, escape preserved) is
    also what `gitignore_missing_lines_check` returns in its
    `pattern` field and what `--fix` appends to disk.
    """
    content = content.lstrip("﻿")
    out: set[str] = set()
    for raw in content.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        out.add(stripped)
    return out


def gitignore_compute_union(template_content: str, target_content: str) -> tuple[str, list[str]]:
    """Compute the deterministic Phase 1 union of two .gitignore contents.

    Returns ``(merged_content, missing_patterns)`` where:

    - ``merged_content`` = ``target_content`` verbatim + a blank separator +
      the banner sentinel + each missing pattern (in the template's original
      line order) + trailing newline. Suitable both as the fallback output
      when the LLM reorganize gate fails (`/holo:init`) and as the direct
      append-only output for `/holo:update --fix`. When ``missing_patterns``
      is empty, ``merged_content`` is ``target_content`` verbatim.
    - ``missing_patterns`` = patterns present in the template but absent
      from the target (canonical / stripped form, deduplicated, original
      order from the template).

    Template comment lines and section headers are NOT propagated; only
    pattern lines. The init Step 3.1 LLM step is responsible for grouping
    the union pattern set under whitelisted headers; the update `--fix`
    writes the raw banner-separated append shape.
    """
    # Strip leading BOM defensively (mirrors `gitignore_pattern_lines`
    # — same hazard if an editor-injected BOM survives into the union
    # pass: the first template pattern would bind to `﻿…` and
    # never match the consumer's clean form).
    template_content = template_content.lstrip("﻿")
    target_content = target_content.lstrip("﻿")

    template_patterns_ordered: list[str] = []
    seen: set[str] = set()
    for raw in template_content.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped in seen:
            continue
        seen.add(stripped)
        template_patterns_ordered.append(stripped)

    target_patterns = gitignore_pattern_lines(target_content)
    missing = [p for p in template_patterns_ordered if p not in target_patterns]

    if not missing:
        return (target_content, [])

    if target_content == "":
        prefix = ""
    elif target_content.endswith("\n"):
        prefix = target_content
    else:
        prefix = target_content + "\n"
    if prefix:
        prefix = prefix + "\n"

    merged = prefix + _GITIGNORE_BANNER + "\n" + "\n".join(missing) + "\n"
    return (merged, missing)


def gitignore_verify_reorganize(
    reorganized: str,
    expected_patterns: set[str],
    allowed_headers: frozenset[str] | None = None,
) -> tuple[bool, list[str]]:
    """Verify an LLM-reorganized .gitignore output (Phase 3).

    Two strict gates:

    1. **Pattern set equality** — ``gitignore_pattern_lines(reorganized) ==
       expected_patterns``. No pattern may be missing, added, or rewritten
       (even a whitespace tweak counts as rewrite). This is the
       load-bearing correctness check; gate failure triggers fallback to
       the Phase 1 deterministic union.
    2. **Section header whitelist** — every `#`-prefix comment line in
       the reorganized output must appear in ``allowed_headers`` (default:
       :data:`_GITIGNORE_SECTION_WHITELIST`). The Phase 1 banner sentinel
       is implicitly allowed regardless of the whitelist.

    Returns ``(passed, violations)``. ``violations`` enumerates failure
    reasons in human-readable form (empty when ``passed=True``). Each
    violation truncates long lists to the first five entries for
    readability.
    """
    if allowed_headers is None:
        allowed_headers = _GITIGNORE_SECTION_WHITELIST

    violations: list[str] = []

    actual_patterns = gitignore_pattern_lines(reorganized)
    missing = expected_patterns - actual_patterns
    extra = actual_patterns - expected_patterns
    if missing:
        sample = sorted(missing)[:5]
        suffix = " ..." if len(missing) > 5 else ""
        violations.append(
            f"pattern set: {len(missing)} missing from LLM output (sample: {sample}{suffix})"
        )
    if extra:
        sample = sorted(extra)[:5]
        suffix = " ..." if len(extra) > 5 else ""
        violations.append(
            f"pattern set: {len(extra)} unexpected in LLM output (sample: {sample}{suffix})"
        )

    invalid_headers: list[str] = []
    seen_invalid: set[str] = set()
    for raw in reorganized.splitlines():
        line = raw.strip()
        if not line.startswith("#"):
            continue
        if line == _GITIGNORE_BANNER:
            continue
        if line in allowed_headers:
            continue
        if line in seen_invalid:
            continue
        seen_invalid.add(line)
        invalid_headers.append(line)
    if invalid_headers:
        sample = invalid_headers[:5]
        suffix = " ..." if len(invalid_headers) > 5 else ""
        violations.append(
            f"non-whitelisted header(s): {len(invalid_headers)} found "
            f"(sample: {sample}{suffix}; whitelist: {sorted(allowed_headers)})"
        )

    return (not violations, violations)


def gitignore_missing_lines_check(plugin_root: str, target_root: str) -> list[dict]:
    """Detect .gitignore pattern lines present in template but missing from consumer.

    One finding per missing pattern (mirrors ``missing_section``'s
    one-finding-per-header shape so ``total_drift`` counts patterns,
    not files). Orphan lines (in consumer but not in template) are
    intentionally NOT detected — extending `.gitignore` is normal
    consumer behaviour.

    Returns empty when:

    - Template `.gitignore` absent in the active project-skeleton root
      (covered by ``missing_template`` if the consumer also lacks the
      file).
    - Consumer `.gitignore` absent (covered by ``missing_template``).
    - No patterns missing.
    """
    skel = _skeleton_root(plugin_root, _consumer_content_lang(target_root))
    template_path = os.path.join(skel, ".gitignore")
    target_path = os.path.join(target_root, ".gitignore")

    if not os.path.isfile(template_path) or not os.path.isfile(target_path):
        return []

    with open(template_path, encoding="utf-8") as f:
        template_content = f.read().lstrip("﻿")
    with open(target_path, encoding="utf-8") as f:
        target_content = f.read().lstrip("﻿")

    target_patterns = gitignore_pattern_lines(target_content)

    seen: set[str] = set()
    findings: list[dict] = []
    for raw in template_content.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped in seen:
            continue
        seen.add(stripped)
        if stripped not in target_patterns:
            findings.append({
                "rel": ".gitignore",
                "pattern": stripped,
                "source_path": template_path,
                "target_path": target_path,
            })
    return findings


# ---------------------------------------------------------------------------
# Aggregate runner + fix application
# ---------------------------------------------------------------------------

def run_check(plugin_root: str, target_root: str) -> dict:
    return {
        "plugin_root": plugin_root,
        "target_root": os.path.abspath(target_root),
        "consumer_content_lang": _consumer_content_lang(target_root),
        "agents_sync": agents_sync_check(plugin_root, target_root),
        "missing_template": template_file_check(plugin_root, target_root),
        "missing_section": template_section_check(plugin_root, target_root),
        "missing_field": missing_field_check(plugin_root, target_root),
        "gitignore_missing_lines": gitignore_missing_lines_check(plugin_root, target_root),
        "claude_agents": claude_agents_check(target_root, plugin_root),
        "missing_l1_directive": l1_directive_check(plugin_root),
        "l1_directive_drift": l1_directive_drift_check(plugin_root),
        "lang_mirror_drift": lang_mirror_check(plugin_root),
        "legacy_skip_marker": legacy_skip_marker_check(target_root),
    }


def total_drift(findings: dict) -> int:
    """Count actionable + report-only drift items, EXCLUDING CLAUDE/AGENTS
    `unexpected_diffs`. The CLAUDE/AGENTS bucket is report-only by design
    (never auto-fixable) and can grow large on consumers with legitimate
    asymmetric guidance — counting it would drown actionable findings
    (STALE / MISSING) in noise. See `claude_agents_check` cap logic.
    `commands/update.md` Step 3.1 surfaces the CLAUDE/AGENTS bucket as a
    separate row so the user still sees the count without it inflating
    the main total.
    """
    a = findings["agents_sync"]
    base = (
        len(findings["missing_template"])
        + len(findings["missing_section"])
        + len(findings.get("missing_field", []))
        + len(findings.get("gitignore_missing_lines", []))
        + len(findings.get("missing_l1_directive", []))
        + len(findings.get("l1_directive_drift", []))
        + len(findings.get("lang_mirror_drift", []))
    )
    if a.get("skipped"):
        return base
    return base + len(a["stale"]) + len(a["missing"]) + len(a["orphan"])


def run_fix(findings: dict, target_root: str) -> dict:
    """Apply auto-fixes for STALE / MISSING / ORPHAN / MISSING_TEMPLATE /
    MISSING_SECTION / MISSING_FIELD / GITIGNORE_MISSING_LINES.

    CLAUDE / AGENTS findings are never touched here — they require manual merge.
    The `.gitignore` smart-merge LLM-reorganize pipeline (Phases 2 + 3) is
    NOT invoked here either — `/holo:update --fix` is append-only Phase 1
    by design, see ai_context/decisions.md §Skill Implementation #14.

    Returns a dict with counts (`regenerated` / `created` / `deleted` /
    `template_copied` / `section_appended` / `field_appended` /
    `gitignore_appended`) plus `orphan_siblings_left`: a list of
    `{"name", "parent", "siblings"}` entries for any orphan whose parent
    directory still holds non-SKILL.md files after the fix. JSON consumers
    (e.g. `/holo:update`) surface these so the user knows manual sibling
    cleanup is required — otherwise the deletion appears silent (violates
    §14 #1 "No silent overwrite").
    """
    counts: dict = {
        "regenerated": 0, "created": 0, "deleted": 0,
        "template_copied": 0, "section_appended": 0,
        "field_appended": 0,
        "gitignore_appended": 0,
        "orphan_siblings_left": [],
    }

    a = findings.get("agents_sync", {})
    for item in a.get("stale", []):
        content = expected_mirror_content(item["source_path"], item["name"], item["source_type"])
        os.makedirs(os.path.dirname(item["target_path"]), exist_ok=True)
        with open(item["target_path"], "w", encoding="utf-8") as f:
            f.write(content)
        counts["regenerated"] += 1
    for item in a.get("missing", []):
        content = expected_mirror_content(item["source_path"], item["name"], item["source_type"])
        os.makedirs(os.path.dirname(item["target_path"]), exist_ok=True)
        with open(item["target_path"], "w", encoding="utf-8") as f:
            f.write(content)
        counts["created"] += 1
    for item in a.get("orphan", []):
        # Only delete the orphaned SKILL.md itself. Sibling files
        # (notes, extensions, local overrides) under <name>/ are user
        # content and must not be wiped by a single "Auto-fix all"
        # click — violates §14 #1 "No silent overwrite". The directory
        # is removed only if it becomes empty.
        skill_md = item["target_path"]
        parent = os.path.dirname(skill_md)
        if os.path.isfile(skill_md):
            os.remove(skill_md)
        try:
            os.rmdir(parent)
        except OSError:
            # Directory still has sibling files — record them so the
            # JSON consumer can surface a manual-cleanup prompt.
            try:
                siblings = sorted(os.listdir(parent))
            except OSError:
                siblings = []
            if siblings:
                counts["orphan_siblings_left"].append({
                    "name": item["name"],
                    "parent": parent,
                    "siblings": siblings,
                })
        counts["deleted"] += 1

    for item in findings.get("missing_template", []):
        os.makedirs(os.path.dirname(item["target_path"]), exist_ok=True)
        shutil.copy2(item["source_path"], item["target_path"])
        counts["template_copied"] += 1

    todo_marker = "_(TODO — added by /holo:update; fill via /go or direct edit)_"
    for item in findings.get("missing_section", []):
        target = os.path.join(target_root, item["rel"])
        with open(target, "a", encoding="utf-8") as f:
            f.write(f"\n\n{item['header']}\n\n{todo_marker}\n")
        counts["section_appended"] += 1

    counts["field_appended"] = fix_missing_field(target_root, findings.get("missing_field", []))

    # `gitignore_missing_lines`: append-only Phase 1 (no LLM). Patterns
    # are grouped by (source_path, target_path) so multi-pattern drift
    # produces one banner block per file, not N stacked banners. The
    # per-pattern list inside the finding is recomputed from the source
    # files via `gitignore_compute_union` so the dedup + canonical-form
    # rules stay in one place; this set just captures the unique
    # (source, target) pairs to iterate.
    gitignore_pairs: set[tuple[str, str]] = {
        (item["source_path"], item["target_path"])
        for item in findings.get("gitignore_missing_lines", [])
    }
    for source_path, target_path in gitignore_pairs:
        with open(source_path, encoding="utf-8") as f:
            template_content = f.read()
        with open(target_path, encoding="utf-8") as f:
            target_content = f.read()
        merged, appended = gitignore_compute_union(template_content, target_content)
        if appended:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(merged)
            counts["gitignore_appended"] += len(appended)

    return counts


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_human(findings: dict, fix_counts: dict | None) -> None:
    a = findings["agents_sync"]
    print(f"plugin_root: {findings['plugin_root']}")
    print(f"target_root: {findings['target_root']}")
    print(f"consumer_content_lang: {findings.get('consumer_content_lang', 'en')}")
    if a.get("skipped"):
        print(".agents/skills/: skipped (directory not present in target)")
    else:
        print(
            f".agents/skills/: stale={len(a['stale'])} | "
            f"missing={len(a['missing'])} | orphan={len(a['orphan'])}"
        )
        for label, items in [("STALE", a["stale"]), ("MISSING", a["missing"]), ("ORPHAN", a["orphan"])]:
            for item in items:
                line = f"  {label}: {item['name']}"
                if label == "ORPHAN":
                    parent = os.path.dirname(item["target_path"])
                    try:
                        siblings = [
                            f for f in os.listdir(parent) if f != "SKILL.md"
                        ]
                    except OSError:
                        siblings = []
                    if siblings:
                        line += (
                            f"  (auto-fix: removes only SKILL.md; "
                            f"{len(siblings)} sibling file(s) kept: "
                            f"{', '.join(sorted(siblings))})"
                        )
                print(line)
    print(f"missing_template: {len(findings['missing_template'])}")
    for item in findings["missing_template"]:
        print(f"  {item['rel']}")
    print(f"missing_section:  {len(findings['missing_section'])}")
    for item in findings["missing_section"]:
        print(f"  {item['rel']}: {item['header']}")
    mf = findings.get("missing_field", [])
    print(f"missing_field:    {len(mf)}")
    for item in mf:
        print(f"  {item['rel']}: {item['section']} → {item['key']}")
    gml = findings.get("gitignore_missing_lines", [])
    print(f"gitignore_missing_lines: {len(gml)}")
    for item in gml:
        print(f"  {item['rel']}: {item['pattern']}")
    ca = findings["claude_agents"]
    if ca["present"]:
        truncated = ca.get("unexpected_diffs_truncated", 0)
        suffix = f" (+{truncated} more truncated)" if truncated else ""
        print(
            f"claude_agents: first_line_placeholder={ca['first_line_placeholder']} "
            f"unexpected_diffs={len(ca['unexpected_diffs'])}{suffix}"
        )
    l1 = findings.get("missing_l1_directive", [])
    print(f"missing_l1_directive: {len(l1)}")
    for item in l1:
        print(f"  {item['rel']}: {item.get('reason', 'missing')}")
    l1d = findings.get("l1_directive_drift", [])
    print(f"l1_directive_drift: {len(l1d)}")
    for item in l1d:
        missing = ", ".join(item.get("missing_substrings", []))
        print(f"  {item['rel']}: missing {missing}")
    lmd = findings.get("lang_mirror_drift", [])
    print(f"lang_mirror_drift: {len(lmd)}")
    for item in lmd:
        print(f"  {item['variant']}/{item['rel']}: {item['kind']}")
    lsm = findings.get("legacy_skip_marker", [])
    print(f"legacy_skip_marker (informational; not in total_drift): {len(lsm)}")
    for item in lsm:
        print(f"  {item['rel']}:{item['line']}: {item['snippet']}")
    if fix_counts is not None:
        print("---")
        print(
            f"fix: regenerated={fix_counts.get('regenerated', 0)} "
            f"created={fix_counts.get('created', 0)} "
            f"deleted={fix_counts.get('deleted', 0)} "
            f"template_copied={fix_counts.get('template_copied', 0)} "
            f"section_appended={fix_counts.get('section_appended', 0)} "
            f"field_appended={fix_counts.get('field_appended', 0)} "
            f"gitignore_appended={fix_counts.get('gitignore_appended', 0)}"
        )
        for entry in fix_counts.get("orphan_siblings_left", []):
            print(
                f"  orphan sibling files kept under {entry['parent']}: "
                f"{', '.join(entry['siblings'])} (manual cleanup required)"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="project ↔ plugin drift check + fix")
    parser.add_argument("--plugin-root", default=None, help="override CLAUDE_PLUGIN_ROOT")
    parser.add_argument("--target", default=".", help="target project root (default: cwd)")
    parser.add_argument("--fix", action="store_true", help="apply auto-fixes after check")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    plugin_root = find_plugin_root(args.plugin_root)
    findings = run_check(plugin_root, args.target)
    fix_counts = None
    if args.fix:
        fix_counts = run_fix(findings, args.target)
        findings["fix_counts"] = fix_counts

    if args.json:
        print(json.dumps(findings, indent=2, ensure_ascii=False))
    else:
        _print_human(findings, fix_counts)


if __name__ == "__main__":
    main()
