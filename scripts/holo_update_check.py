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
from datetime import datetime, timezone
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
# Snapshot helper (T-SECTION-VERSION-SENTINEL Phase 4)
# ---------------------------------------------------------------------------

def take_snapshot(target_root: str, slug: str, file_paths: list[str]) -> str:
    """Copy each file in ``file_paths`` to a per-run snapshot directory.

    The snapshot lives at
    ``<target_root>/logs/file_snapshots/<YYYY-MM-DD>_<HHMMSS>_<slug>/<rel_path>``.
    UTC timestamp via ``datetime.now(timezone.utc)``; ``logs/`` is
    gitignored on consumer projects (per the plugin's shipped
    ``.gitignore``) so snapshots stay local and never reach
    ``main`` or any commit.

    Used by:

    - ``/holo:update --fix`` ``section_content_drift`` auto-fix branch
      (snapshot consumer file before overwriting its sentinel block
      with plugin canonical body).
    - ``/holo:init`` Step 3.1 CONFLICT ``overwrite`` path for ``.md``
      files (snapshot consumer file before replacing with template).

    ``file_paths`` may be absolute or relative to ``target_root``;
    absolute paths get rebased to the target_root-relative form
    before placement under the snapshot dir, so a consumer's
    ``ai_context/decisions.md`` becomes
    ``<snapshot_dir>/ai_context/decisions.md``. Files that do not
    exist on disk are silently skipped (caller already validated
    paths; this helper is a defensive no-op for stragglers).

    ``shutil.copy2`` preserves mtime + mode + xattrs where supported.

    Returns the snapshot directory path as a string (e.g.
    ``/path/to/target/logs/file_snapshots/2026-05-21_023045_holo-update``).
    Callers surface this path so the user knows where to restore from
    if the auto-fix overwrote something they wanted to keep. Snapshot
    dir is created lazily — when ``file_paths`` is empty, the
    function still returns the would-be path but does NOT create the
    directory (no-op).
    """
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d_%H%M%S")
    snapshot_dir = os.path.join(
        target_root, "logs", "file_snapshots", f"{stamp}_{slug}"
    )

    if not file_paths:
        return snapshot_dir

    os.makedirs(snapshot_dir, exist_ok=True)
    for path in file_paths:
        if os.path.isabs(path):
            rel = os.path.relpath(path, target_root)
            src = path
        else:
            rel = path
            src = os.path.join(target_root, rel)
        if not os.path.isfile(src):
            continue
        dest = os.path.join(snapshot_dir, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest)
    return snapshot_dir


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

# Sibling regex for `conversation_language`. Distinct from
# `_CONTENT_LANG_RE` because the accepted value set differs (`auto`
# additionally permitted) — `_consumer_conversation_lang` handles
# that branch. Used by `claude_agents_lang_drift_check` and by
# `_consumer_conversation_lang`.
_CONVERSATION_LANG_RE = re.compile(
    r"^\s*-\s*`conversation_language:\s*([A-Za-z0-9-]+)`", re.MULTILINE
)

# Sentinel marker constants (must match `scripts/sentinel_bootstrap.py` +
# `docs/architecture/section-version-sentinel.md`). The dual-marker
# mechanism — `<!-- holo:heading -->` on H2 lines + `<!-- holo:section
# start --> ... <!-- holo:section end -->` around plugin canonical body —
# is consumed by `_md_headers` (marker stripping for the legacy
# `missing_section` check), `_parse_sentinel_blocks` (Phase 3 sentinel
# parser), `heading_drift_check`, and `section_content_drift_check`.
_HOLO_HEADING_MARKER = "<!-- holo:heading -->"
_HOLO_SECTION_START = "<!-- holo:section start -->"
_HOLO_SECTION_END = "<!-- holo:section end -->"
_HOLO_HEADING_MARKER_RE = re.compile(r"\s*<!-- holo:heading -->\s*$")

# PROGRESSIVE marker (per `ai_context/decisions.md` §Skill Implementation
# #15). Excluded from `section_content_drift` byte-diff because consumer
# legitimately deletes it when adding real content (per the marker's own
# instruction). Stripping both sides leaves only the prose content for
# byte-diff so a consumer who has correctly removed the placeholder does
# not register as drift. Pattern matches the marker line as-emitted by
# templates / `/holo:init` and tolerates trailing whitespace.
_PROGRESSIVE_MARKER_RE = re.compile(
    r"^_\(none yet — delete this marker once content is added\)_\s*$",
    re.MULTILINE,
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


def _consumer_conversation_lang(target_root: str) -> str:
    """Read `conversation_language` from consumer's skills_config.md §Language.

    Returns the value (lowercase). Accepts `auto` (per-turn mode) plus
    any 2-letter ISO 639-1 code; same invalid-value gates as
    `_consumer_content_lang` for parity (no `cn`, no locale variants,
    no uppercase). Missing file / section / field returns `'auto'` —
    the template-default fallback per decisions.md §Language
    Configuration #17.
    """
    cfg = os.path.join(target_root, "ai_context", "skills_config.md")
    if not os.path.isfile(cfg):
        return "auto"
    try:
        with open(cfg, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return "auto"
    m = _CONVERSATION_LANG_RE.search(text)
    if not m:
        return "auto"
    value = m.group(1)
    if value == "auto":
        return "auto"
    if value == "cn":
        sys.exit(
            "ai_context/skills_config.md §Language: conversation_language='cn' "
            "is not ISO 639-1; use 'zh' per docs/requirements.md §15."
        )
    if "-" in value:
        sys.exit(
            f"ai_context/skills_config.md §Language: conversation_language="
            f"'{value}' is a locale variant; locale variants are "
            "reserved for future regional splits per "
            "docs/requirements.md §15. Use a bare ISO 639-1 code or 'auto'."
        )
    if not re.fullmatch(r"[a-z]{2}", value):
        sys.exit(
            f"ai_context/skills_config.md §Language: conversation_language="
            f"'{value}' is not a valid ISO 639-1 code (expected 2 "
            "lowercase letters or 'auto' per docs/requirements.md §15)."
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
    """Return the set of `^## ` H2 headers in a markdown file, ignoring
    headers that appear inside fenced code blocks (``` / ~~~) and
    skipping multi-line HTML comment blocks (e.g. the file-top
    MAINTENANCE block). H1 headers are tracked separately by
    `_md_h1_header`.

    H2 detection happens BEFORE the multi-line HTML comment toggle so
    that a heading carrying the inline sentinel marker
    (`## Foo <!-- holo:heading -->`, injected by the sentinel bootstrap
    into plugin templates) is still recognised as a heading rather
    than swallowed as a comment block. The trailing
    `<!-- holo:heading -->` marker is stripped before storage so
    plugin-side (marker-bearing) headers compare equal to consumer-side
    pre-sentinel headers (no marker) and post-sentinel consumer headers
    (also marker-bearing) alike — the marker presence is an ownership
    signal, not part of the header identity.
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
            # H2 detection FIRST (before the multi-line HTML comment
            # toggle below) so heading lines carrying the inline sentinel
            # marker are recognised. Single-line HTML comments inside a
            # heading line (open + close on the same line, which the
            # marker IS) do not affect block state.
            if not in_html_comment and re.match(r"^## ", raw):
                header = raw.rstrip()
                header = _HOLO_HEADING_MARKER_RE.sub("", header).rstrip()
                headers.add(header)
                continue
            # Multi-line HTML comment block (typical: file-top MAINTENANCE
            # block). Toggle on open/close, skip everything in between.
            if not in_html_comment and "<!--" in raw:
                in_html_comment = True
            if in_html_comment:
                if "-->" in raw:
                    in_html_comment = False
                continue
    return headers


def _md_h1_header(path: str) -> str | None:
    """Return the file's H1 line as `"# Title"` (marker stripped), or
    None if no H1 exists / file is missing.

    Fence-aware (skips H1-looking lines inside ```/~~~ blocks).
    Multi-line HTML comments (MAINTENANCE block) are also skipped.
    Stops at the first H1 found (files typically have one H1 at most).
    """
    in_fence = False
    in_html_comment = False
    fence_marker = ""
    try:
        with open(path, encoding="utf-8") as f:
            for raw in f:
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
                if not in_html_comment and re.match(r"^# (?!#)", raw):
                    header = raw.rstrip()
                    header = _HOLO_HEADING_MARKER_RE.sub("", header).rstrip()
                    return header
                if not in_html_comment and "<!--" in raw:
                    in_html_comment = True
                if in_html_comment:
                    if "-->" in raw:
                        in_html_comment = False
                    continue
    except OSError:
        return None
    return None


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
# CLAUDE.md / AGENTS.md §Language hardcoded-values drift (per decisions.md
# §Language Configuration #17)
# ---------------------------------------------------------------------------
#
# `CLAUDE.md` / `AGENTS.md` §Language carries `content_language` +
# `conversation_language` as hardcoded literal bullets, acting as a
# read-cache for the AI's session-start awareness (no
# `ai_context/skills_config.md` read needed). The canonical source is
# skills_config.md; this check enforces sync from canonical → cache.

def claude_agents_lang_drift_check(target_root: str) -> list[dict]:
    """Compare CLAUDE.md / AGENTS.md §Language hardcoded values against
    `ai_context/skills_config.md §Language`.

    One finding per (file, axis) pair where the file's hardcoded value
    differs from skills_config, OR where the axis bullet is missing from
    the file's §Language block.

    Findings shape::

        {
          "rel":      "CLAUDE.md" | "AGENTS.md",
          "axis":     "content_language" | "conversation_language",
          "expected": "<skills_config value>",   # canonical
          "actual":   "<file value>" | None,     # None = bullet absent
        }

    When `CLAUDE.md` / `AGENTS.md` don't exist (consumer not yet
    initialized) the relevant file is skipped silently. When
    skills_config.md is missing / has no §Language values the helpers
    fall back to template defaults (`en` / `auto`) — drift findings
    under that fallback reflect "you should set skills_config
    explicitly" rather than auto-tuning.
    """
    findings: list[dict] = []
    expected_content = _consumer_content_lang(target_root)
    expected_conv = _consumer_conversation_lang(target_root)
    for rel in ("CLAUDE.md", "AGENTS.md"):
        path = os.path.join(target_root, rel)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except OSError:
            continue
        cm = _CONTENT_LANG_RE.search(text)
        cvm = _CONVERSATION_LANG_RE.search(text)
        actual_content = cm.group(1) if cm else None
        actual_conv = cvm.group(1) if cvm else None
        if actual_content != expected_content:
            findings.append({
                "rel": rel,
                "axis": "content_language",
                "expected": expected_content,
                "actual": actual_content,
            })
        if actual_conv != expected_conv:
            findings.append({
                "rel": rel,
                "axis": "conversation_language",
                "expected": expected_conv,
                "actual": actual_conv,
            })
    return findings


def fix_claude_agents_lang_drift(target_root: str, findings: list[dict]) -> int:
    """Sync CLAUDE.md / AGENTS.md §Language axis bullets toward
    skills_config.md per the findings returned by
    `claude_agents_lang_drift_check`.

    Per-finding behaviour:

    - `actual is not None and actual != expected` → overwrite the value
      portion of the existing backticked bullet (``- `<axis>: …` ``) in
      place. Surrounding prose (em-dash + description) is preserved
      verbatim.
    - `actual is None` → the axis bullet is absent from the §Language
      block. If the sibling axis bullet is present, insert a canonical
      bullet (``- `<axis>: <expected>` ``) immediately before it,
      matching the sibling's indentation. If neither bullet is
      present, the §Language block is structurally pre-#17
      (pointer-prose format) — skip; the user re-runs `/holo:init` or
      manually upgrades the block.

    Returns the count of (file, axis) pairs successfully fixed.
    Skipped findings (no sibling anchor) are NOT counted; the next
    `--check` pass will still surface them as drift, prompting the user
    toward a manual upgrade.
    """
    by_file: dict[str, list[dict]] = {}
    for f in findings:
        by_file.setdefault(f["rel"], []).append(f)

    fixed = 0
    for rel, items in by_file.items():
        path = os.path.join(target_root, rel)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as f:
            text = f.read()

        for item in items:
            axis = item["axis"]
            expected = item["expected"]
            actual = item["actual"]
            if actual is not None:
                pattern = re.compile(
                    rf"(^\s*-\s*`{axis}:\s*)([A-Za-z0-9-]+)(`)", re.MULTILINE
                )
                new_text, n = pattern.subn(
                    rf"\g<1>{expected}\g<3>", text, count=1
                )
                if n == 1:
                    text = new_text
                    fixed += 1
                continue
            # actual is None — try to insert before the sibling axis bullet
            anchor_axis = (
                "conversation_language" if axis == "content_language"
                else "content_language"
            )
            anchor_re = re.compile(
                rf"^([ \t]*-)\s*`{anchor_axis}:", re.MULTILINE
            )
            am = anchor_re.search(text)
            if am is None:
                continue
            anchor_line_start = text.rfind("\n", 0, am.start()) + 1
            indent_prefix = am.group(1)
            insertion = f"{indent_prefix} `{axis}: {expected}`\n"
            text = (
                text[:anchor_line_start] + insertion + text[anchor_line_start:]
            )
            fixed += 1

        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    return fixed


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


# ---------------------------------------------------------------------------
# Sentinel-aware drift detection (Phase 3 of T-SECTION-VERSION-SENTINEL)
# ---------------------------------------------------------------------------
#
# Parses files that have been Phase-2-bootstrapped (plugin templates) /
# Phase-4-initialized (consumers) and surfaces two new finding kinds:
#
# - `heading_drift` — consumer carries `<!-- holo:heading -->` markers
#   on H2 lines that no longer match the plugin template heading list.
#   Reports only the consumer-orphan direction (consumer marker, no
#   plugin counterpart); the opposite direction is covered by
#   `missing_section` after the `_md_headers` marker-stripping fix.
# - `section_content_drift` — sentinel-bracketed plugin canonical block
#   bodies differ byte-for-byte between plugin template and consumer.
#   PROGRESSIVE markers are stripped from both sides before comparison
#   so consumer-side "delete the marker, add real content" does not
#   register as drift.
#
# Both checks are report-only for Phase 3; auto-fix branches land in
# Phase 4 once the snapshot path (`logs/file_snapshots/`) is wired.
# Multi-block-per-section handling is deferred to Phase 5's
# `scripts/sentinel_parse.py` canonical API; Phase 3's helpers handle
# the one-block-per-section shape that `scripts/sentinel_bootstrap.py`
# emits.

def _parse_sentinel_blocks(path: str) -> dict:
    """Parse a markdown file and extract plugin-owned sentinel structure.

    Returns a dict with six keys::

        has_heading_markers: bool   # any `<!-- holo:heading -->` present
        has_section_markers: bool   # any `<!-- holo:section start -->` present
        h1_marked:           str | None
            # If the file's H1 line carries `<!-- holo:heading -->`,
            # the H1 text (without `# ` prefix, marker stripped); else
            # None. Files without an H1 also return None.
        heading_marked:      list[str]
            # H2 lines bearing the heading marker (marker stripped, in
            # source order). Pre-sentinel consumers return [].
        preamble_blocks:     list[str]
            # Plugin-canonical block bodies appearing BEFORE the first
            # H2 line (file-top region; includes MAINTENANCE wrapper +
            # any post-H1 intro wrap).
        section_blocks:      dict[str, list[str]]
            # Maps heading text (with marker stripped) to its sentinel
            # blocks in source order. Headings without a marker (user
            # sections) are tracked as the `current_heading` for
            # block-attribution purposes but their entries are not
            # included in `heading_marked`.

    Block bodies are the lines BETWEEN the start and end markers, joined
    with `\\n`, without trimming. Trimming happens at byte-diff time via
    `_normalize_block_for_diff`.

    Fence-aware: lines inside ``` / ~~~ code fences are skipped for
    sentinel + heading detection so a tutorial section that quotes the
    marker syntax in a code block does not corrupt parsing.
    """
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return {
            "has_heading_markers": False,
            "has_section_markers": False,
            "h1_marked": None,
            "heading_marked": [],
            "preamble_blocks": [],
            "section_blocks": {},
        }

    # First pass: precompute fence state per line so the second-pass
    # sentinel/heading detection can cheaply skip in-fence lines.
    in_fence_per_line: list[bool] = []
    cur_in_fence = False
    cur_marker = ""
    for raw in lines:
        stripped = raw.lstrip()
        in_fence_per_line.append(cur_in_fence)
        if not cur_in_fence and (stripped.startswith("```") or stripped.startswith("~~~")):
            cur_in_fence = True
            cur_marker = stripped[:3]
        elif cur_in_fence and stripped.startswith(cur_marker):
            cur_in_fence = False
            cur_marker = ""

    heading_marked: list[str] = []
    preamble_blocks: list[str] = []
    section_blocks: dict[str, list[str]] = {}
    current_heading: str | None = None  # None = preamble region
    in_block = False
    block_start_idx = -1
    has_heading_marker_flag = False
    has_section_marker_flag = False
    h1_marked: str | None = None

    for i, raw in enumerate(lines):
        if in_fence_per_line[i]:
            continue
        # Normalize for sentinel/heading detection; keep `raw` for body capture.
        line_no_nl = raw.rstrip("\n")
        stripped_line = line_no_nl.strip()

        if stripped_line == _HOLO_SECTION_START:
            in_block = True
            block_start_idx = i + 1
            has_section_marker_flag = True
            continue
        if stripped_line == _HOLO_SECTION_END:
            if in_block:
                body_lines = [lines[j].rstrip("\n") for j in range(block_start_idx, i)]
                body = "\n".join(body_lines)
                if current_heading is None:
                    preamble_blocks.append(body)
                else:
                    section_blocks.setdefault(current_heading, []).append(body)
            in_block = False
            block_start_idx = -1
            continue

        if in_block:
            continue  # block body captured on close

        # Outside any block — track H2 heading transitions.
        if re.match(r"^## ", line_no_nl):
            stripped_header = _HOLO_HEADING_MARKER_RE.sub("", line_no_nl.rstrip()).rstrip()
            if _HOLO_HEADING_MARKER in line_no_nl:
                has_heading_marker_flag = True
                heading_marked.append(stripped_header)
            current_heading = stripped_header
            continue

        # H1 heading (one hash + space + non-hash). Track only the
        # FIRST H1 in source order; files typically have at most one.
        if h1_marked is None and re.match(r"^# (?!#)", line_no_nl):
            stripped_h1 = _HOLO_HEADING_MARKER_RE.sub("", line_no_nl.rstrip()).rstrip()
            if _HOLO_HEADING_MARKER in line_no_nl:
                has_heading_marker_flag = True
                h1_marked = stripped_h1

    return {
        "has_heading_markers": has_heading_marker_flag,
        "has_section_markers": has_section_marker_flag,
        "h1_marked": h1_marked,
        "heading_marked": heading_marked,
        "preamble_blocks": preamble_blocks,
        "section_blocks": section_blocks,
    }


def _normalize_block_for_diff(body: str) -> str:
    """Prepare a sentinel block body for byte-diff comparison.

    Per `ai_context/decisions.md` §Skill Implementation #15, PROGRESSIVE
    markers (`_(none yet — delete this marker once content is added)_`)
    are intentional empty placeholders; a consumer who has deleted the
    marker and written real content per the marker's own instruction is
    not drifting — the body change is by design. Stripping the marker
    from BOTH sides before comparison reduces the diff to just the
    prose, so legitimate user fill-in is invisible to
    `section_content_drift`.

    Also trims surrounding blank lines and per-line trailing whitespace
    so cosmetic whitespace changes (e.g. an editor adding a trailing
    space) do not register as drift.
    """
    text = _PROGRESSIVE_MARKER_RE.sub("", body)
    lines = [l.rstrip() for l in text.split("\n")]
    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def _block_excerpt(text: str, max_lines: int = 3, max_chars: int = 200) -> str:
    """First few non-blank lines joined with ` / ` for chat display."""
    lines = [l.strip() for l in text.split("\n") if l.strip()][:max_lines]
    s = " / ".join(lines)
    if len(s) > max_chars:
        s = s[:max_chars] + "..."
    return s


def _block_unified_diff_summary(plugin: str, consumer: str, max_lines: int = 6) -> str:
    """Short unified-diff-style summary for chat display.

    Generated with `difflib.unified_diff` over the normalized block bodies.
    `fromfile=consumer`, `tofile=plugin` so `-`/`+` reads as "consumer
    loses → plugin canonical adds". Truncated to `max_lines` for chat
    readability; users open the actual files for the full picture.
    """
    diff_lines = list(
        difflib.unified_diff(
            consumer.split("\n"),
            plugin.split("\n"),
            fromfile="consumer",
            tofile="plugin",
            lineterm="",
            n=1,
        )
    )
    # Drop the `---` / `+++` header pair, keep only hunks.
    body = [l for l in diff_lines if not l.startswith("---") and not l.startswith("+++")]
    truncated = len(body) > max_lines
    body = body[:max_lines]
    if truncated:
        body.append("...")
    return "\n".join(body) if body else "(diff empty)"


def heading_drift_check(plugin_root: str, target_root: str) -> list[dict]:
    """Sentinel-aware: find consumer marker-bearing H2s not in plugin template.

    For each plugin template `.md` whose consumer counterpart exists AND
    whose consumer contains at least one `<!-- holo:heading -->` marker
    (the Phase-4 consumer signal), compare the consumer's marker-bearing
    heading list against the plugin template's marker-bearing heading
    list. Report headings present in the consumer with marker but absent
    from the plugin canonical set as `consumer_orphan_heading` — most
    likely: plugin v2 renamed or removed the heading, and the consumer's
    marker is now stale.

    The reverse direction (plugin has a heading, consumer doesn't) is
    covered by `missing_section` after the `_md_headers` marker-stripping
    fix; this check intentionally only carries the consumer-orphan
    direction so the two checks do not double-flag.

    Pre-Phase-4 consumers (no markers) → check skips the file silently
    and `missing_section` handles plugin→consumer alone, preserving
    backward-compatibility for consumers that have not been Phase 4
    bootstrapped.

    Rename detection (plugin renamed `## Foo` → `## Bar`, which presents
    as a `missing_section` for `## Bar` + a `consumer_orphan_heading` for
    `## Foo`) is the LLM's job in `/holo:update`; the script reports raw
    set diff only. See `docs/architecture/section-version-sentinel.md`
    §Edge cases §Heading rename.
    """
    skel = _skeleton_root(plugin_root, _consumer_content_lang(target_root))
    findings: list[dict] = []
    for f in sorted(glob.glob(f"{skel}/**/*.md", recursive=True)):
        rel = os.path.relpath(f, skel)
        target = os.path.join(target_root, rel)
        if not os.path.exists(target):
            continue  # missing_template covers absent files
        consumer_parsed = _parse_sentinel_blocks(target)
        if not consumer_parsed["has_heading_markers"]:
            continue  # pre-sentinel consumer; defer to missing_section
        plugin_parsed = _parse_sentinel_blocks(f)
        # H1 drift: consumer's marker-bearing H1 vs plugin's marker-bearing H1.
        plugin_h1 = plugin_parsed.get("h1_marked")
        consumer_h1 = consumer_parsed.get("h1_marked")
        if consumer_h1 is not None and consumer_h1 != plugin_h1:
            findings.append({
                "rel": rel,
                "kind": "consumer_orphan_heading",
                "level": 1,
                "header": consumer_h1,
                "source_path": f,
            })
        # H2 drift: consumer-orphan marker-bearing H2 lines.
        plugin_heading_set = set(plugin_parsed["heading_marked"])
        for header in consumer_parsed["heading_marked"]:
            if header in plugin_heading_set:
                continue
            findings.append({
                "rel": rel,
                "kind": "consumer_orphan_heading",
                "level": 2,
                "header": header,
                "source_path": f,
            })
    return findings


def section_content_drift_check(plugin_root: str, target_root: str) -> list[dict]:
    """Sentinel-aware: byte-diff plugin canonical blocks vs consumer's.

    Fires only when BOTH plugin template and consumer have at least one
    `<!-- holo:section start -->` marker (otherwise at least one side is
    pre-Phase-4 and there is no canonical block content to compare). For
    each H2 section + preamble region present in both files, position-
    aligned block-by-block byte-diff is performed; differences (after
    PROGRESSIVE-marker stripping and trailing-whitespace normalization
    via `_normalize_block_for_diff`) produce a finding.

    Phase 3 handles the one-block-per-section shape that
    `scripts/sentinel_bootstrap.py` emits. Multi-block per section is
    Phase 5's `scripts/sentinel_parse.py` canonical parser API; until
    then, this check pairs by position (`block_index=0` vs `0`, `1` vs
    `1`, etc.) and silently ignores per-side excess blocks. Report-only
    for Phase 3 — Phase 4 wires snapshot-then-overwrite once
    `logs/file_snapshots/` is in place.

    Returns one finding per drifted block::

        {
            "rel":              "ai_context/decisions.md",
            "section":          "## Format" | "preamble",
            "block_index":      0,
            "plugin_excerpt":   "...",   # first 3 non-blank lines, ≤ 200 chars
            "consumer_excerpt": "...",
            "diff_summary":     "...",   # unified diff snippet, ≤ 6 lines
        }
    """
    skel = _skeleton_root(plugin_root, _consumer_content_lang(target_root))
    findings: list[dict] = []
    for f in sorted(glob.glob(f"{skel}/**/*.md", recursive=True)):
        rel = os.path.relpath(f, skel)
        target = os.path.join(target_root, rel)
        if not os.path.exists(target):
            continue
        plugin_parsed = _parse_sentinel_blocks(f)
        consumer_parsed = _parse_sentinel_blocks(target)
        if not plugin_parsed["has_section_markers"] or not consumer_parsed["has_section_markers"]:
            continue  # at least one side is pre-Phase-4; skip silently
        # Preamble blocks (position-aligned).
        pp = plugin_parsed["preamble_blocks"]
        cp = consumer_parsed["preamble_blocks"]
        for idx in range(min(len(pp), len(cp))):
            plugin_body = _normalize_block_for_diff(pp[idx])
            consumer_body = _normalize_block_for_diff(cp[idx])
            # Plugin block normalizes to empty → PROGRESSIVE-marker-only
            # plugin block, no canonical content to enforce; consumer-side
            # content is intentional user fill, not drift. Skip silently.
            if plugin_body == "":
                continue
            if plugin_body == consumer_body:
                continue
            findings.append({
                "rel": rel,
                "section": "preamble",
                "block_index": idx,
                "plugin_excerpt": _block_excerpt(pp[idx]),
                "consumer_excerpt": _block_excerpt(cp[idx]),
                "diff_summary": _block_unified_diff_summary(plugin_body, consumer_body),
                "source_path": f,
            })
        # Per-section blocks (position-aligned within each shared heading).
        for header in sorted(plugin_parsed["section_blocks"].keys()):
            plugin_blocks = plugin_parsed["section_blocks"][header]
            consumer_blocks = consumer_parsed["section_blocks"].get(header, [])
            for idx in range(min(len(plugin_blocks), len(consumer_blocks))):
                plugin_body = _normalize_block_for_diff(plugin_blocks[idx])
                consumer_body = _normalize_block_for_diff(consumer_blocks[idx])
                # Same PROGRESSIVE-only skip as preamble loop above —
                # see comment there for rationale.
                if plugin_body == "":
                    continue
                if plugin_body == consumer_body:
                    continue
                findings.append({
                    "rel": rel,
                    "section": header,
                    "block_index": idx,
                    "plugin_excerpt": _block_excerpt(plugin_blocks[idx]),
                    "consumer_excerpt": _block_excerpt(consumer_blocks[idx]),
                    "diff_summary": _block_unified_diff_summary(plugin_body, consumer_body),
                    "source_path": f,
                })
    return findings


def _rewrite_sentinel_block(
    consumer_path: str,
    section: str,
    block_index: int,
    new_body: str,
) -> bool:
    """Overwrite the (`section`, `block_index`)th sentinel block in
    ``consumer_path`` with ``new_body``.

    Locates the consumer's sentinel pair by walking the file and
    tracking (current_heading, block_index_within_heading). When the
    target pair is found, replaces the lines between
    ``<!-- holo:section start -->`` and ``<!-- holo:section end -->``
    (exclusive of both markers) with the lines of ``new_body``
    (`\\n`-split).

    Returns ``True`` if the block was located and replaced, ``False``
    otherwise (corrupt file, drifted index, etc.). Caller is
    responsible for snapshotting before invocation; this helper does
    NOT take its own snapshot.

    Fence-aware via the same precomputation pattern as
    ``_parse_sentinel_blocks``.

    ``section`` is the marker-stripped heading text (e.g.
    ``"## Format"``) or ``"preamble"`` for blocks before the first
    H2. ``block_index`` is the zero-based position within that
    section (or preamble) — Phase 4 emits one block per section so
    ``block_index`` is typically 0, but multi-block files are handled
    correctly.
    """
    try:
        with open(consumer_path, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return False

    # Fence-state precomputation (same as _parse_sentinel_blocks).
    in_fence_per_line: list[bool] = []
    cur_in_fence = False
    cur_marker = ""
    for raw in lines:
        stripped = raw.lstrip()
        in_fence_per_line.append(cur_in_fence)
        if not cur_in_fence and (stripped.startswith("```") or stripped.startswith("~~~")):
            cur_in_fence = True
            cur_marker = stripped[:3]
        elif cur_in_fence and stripped.startswith(cur_marker):
            cur_in_fence = False
            cur_marker = ""

    current_heading: str | None = None  # None = preamble
    block_index_in_section: dict[str | None, int] = {}
    in_block = False
    block_start_line = -1

    for i, raw in enumerate(lines):
        if in_fence_per_line[i]:
            continue
        line_no_nl = raw.rstrip("\n")
        stripped_line = line_no_nl.strip()

        if stripped_line == _HOLO_SECTION_START:
            in_block = True
            block_start_line = i
            continue

        if stripped_line == _HOLO_SECTION_END and in_block:
            key = current_heading
            idx = block_index_in_section.get(key, 0)
            block_index_in_section[key] = idx + 1
            in_block = False
            section_key = key if key is not None else "preamble"
            if section_key == section and idx == block_index:
                # Replace lines (block_start_line + 1) ... (i - 1) with new_body.
                new_body_lines = [l + "\n" for l in new_body.split("\n")]
                new_lines = (
                    lines[: block_start_line + 1]
                    + new_body_lines
                    + lines[i:]
                )
                with open(consumer_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                return True
            continue

        if in_block:
            continue

        if re.match(r"^## ", line_no_nl):
            current_heading = _HOLO_HEADING_MARKER_RE.sub(
                "", line_no_nl.rstrip()
            ).rstrip()

    return False


def fix_section_content_drift(
    target_root: str, findings: list[dict]
) -> tuple[int, str | None]:
    """Apply ``section_content_drift`` block-rewrite.

    **NOT wired into `run_fix`. Also NOT currently called by smart-merge**
    (Agent 1 merger generates the merged output as full markdown,
    not as block-by-block rewrites). Kept defined here as a reusable
    primitive — should a future variant of smart-merge or another
    skill need to rewrite a single sentinel block without regenerating
    the whole file, this function and its companion
    ``_rewrite_sentinel_block`` are the building blocks. The earlier
    "snapshot + overwrite consumer block with plugin canonical"
    auto-fix wiring (Phase 4 of T-SECTION-VERSION-SENTINEL) was
    reverted as over-engineering per `ai_context/decisions.md` #18 —
    that model loses user-added content inside sentinel blocks; the
    correct model is extract-and-reformat (Agent 1 reads the full
    consumer file, extracts user info, refills into the new plugin
    sentinel structure as a single full-file rewrite). Smart-merge
    SOP: `docs/architecture/smart-merge.md`.

    For each finding, look up the plugin canonical block body, rewrite
    the consumer's sentinel block at the same (rel, section,
    block_index) coordinates. **Snapshot first**: before any overwrite,
    ``take_snapshot()`` copies every affected consumer file to
    ``<target_root>/logs/file_snapshots/<YYYY-MM-DD>_<HHMMSS>_holo-update/<rel>``
    so the rewrite is reversible.

    Returns ``(replaced_count, snapshot_dir)`` where:

    - ``replaced_count`` = number of sentinel blocks successfully
      rewritten. A finding may be skipped if ``_rewrite_sentinel_block``
      fails to locate the target block (file changed between detect
      and fix, drifted indices) — those are not counted but do not
      raise; the next ``--check`` will surface the residual drift.
    - ``snapshot_dir`` = path to the snapshot directory; ``None`` if
      ``findings`` is empty.

    To compute plugin canonical block content, this function re-parses
    each plugin source file via ``_parse_sentinel_blocks``. That is
    cheap (one file read per affected source) and avoids carrying
    rich content in the finding dict.
    """
    if not findings:
        return (0, None)

    affected_files = sorted({item["rel"] for item in findings})
    snapshot_dir = take_snapshot(target_root, "holo-update", affected_files)

    # Pre-compute plugin canonical content per (rel, section, block_index)
    # by parsing each plugin source file once.
    plugin_blocks: dict[tuple[str, str, int], str] = {}
    plugin_sources = sorted({(item["rel"], item.get("source_path") or _infer_source_path(item)) for item in findings})
    for rel, source_path in plugin_sources:
        if not source_path or not os.path.isfile(source_path):
            continue
        parsed = _parse_sentinel_blocks(source_path)
        for idx, body in enumerate(parsed["preamble_blocks"]):
            plugin_blocks[(rel, "preamble", idx)] = body
        for section, blocks in parsed["section_blocks"].items():
            for idx, body in enumerate(blocks):
                plugin_blocks[(rel, section, idx)] = body

    replaced = 0
    for item in findings:
        key = (item["rel"], item["section"], item["block_index"])
        canonical_body = plugin_blocks.get(key)
        if canonical_body is None:
            continue
        consumer_path = os.path.join(target_root, item["rel"])
        if _rewrite_sentinel_block(
            consumer_path, item["section"], item["block_index"], canonical_body
        ):
            replaced += 1

    return (replaced, snapshot_dir)


def _infer_source_path(item: dict) -> str | None:
    """Defensive helper: section_content_drift findings always carry
    `source_path` in the shape Phase 3 emits, but in case a caller
    constructs a finding without it (synthetic tests / migrations),
    return None so the caller skips that entry rather than KeyError-ing.
    """
    return item.get("source_path")


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
        "claude_agents_lang_drift": claude_agents_lang_drift_check(target_root),
        "missing_l1_directive": l1_directive_check(plugin_root),
        "l1_directive_drift": l1_directive_drift_check(plugin_root),
        "lang_mirror_drift": lang_mirror_check(plugin_root),
        "legacy_skip_marker": legacy_skip_marker_check(target_root),
        "heading_drift": heading_drift_check(plugin_root, target_root),
        "section_content_drift": section_content_drift_check(plugin_root, target_root),
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
    # NOTE: `heading_drift` and `section_content_drift` are intentionally
    # excluded from `total_drift` — their fix path is the smart-merge
    # ask flow (`docs/architecture/smart-merge.md`), driven by
    # `/holo:update` post-detection conflict handling, not the
    # deterministic `run_fix` path that `total_drift` tracks. Earlier
    # auto-fix wiring (section_content_drift snapshot+overwrite,
    # apply_heading_rename) was reverted as over-engineering per
    # `ai_context/decisions.md` #18 — the correct update model is
    # extract-and-reformat (Agent 1 merger generates full-file
    # rewrites that preserve user content under the new plugin
    # template structure).
    base = (
        len(findings["missing_template"])
        + len(findings["missing_section"])
        + len(findings.get("missing_field", []))
        + len(findings.get("gitignore_missing_lines", []))
        + len(findings.get("missing_l1_directive", []))
        + len(findings.get("l1_directive_drift", []))
        + len(findings.get("lang_mirror_drift", []))
        + len(findings.get("claude_agents_lang_drift", []))
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
        "claude_agents_lang_fixed": 0,
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

    counts["claude_agents_lang_fixed"] = fix_claude_agents_lang_drift(
        target_root, findings.get("claude_agents_lang_drift", [])
    )

    # NOTE: `section_content_drift` and `heading_drift` are NOT
    # auto-fixed here. Their fix path is the smart-merge ask flow
    # (`docs/architecture/smart-merge.md`) driven by `/holo:update`
    # post-detection conflict handling — Agent 1 merger generates
    # full-file rewrites that preserve user content under the new
    # plugin template structure. `fix_section_content_drift` +
    # `_rewrite_sentinel_block` stay defined in this module as
    # primitive building blocks for any future skill that needs
    # single-block rewrites without full-file regeneration, but are
    # NOT currently called by anything.
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
    cald = findings.get("claude_agents_lang_drift", [])
    print(f"claude_agents_lang_drift: {len(cald)}")
    for item in cald:
        actual = item["actual"] if item["actual"] is not None else "<missing>"
        print(
            f"  {item['rel']}: {item['axis']} expected={item['expected']} "
            f"actual={actual}"
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
    hd = findings.get("heading_drift", [])
    print(f"heading_drift (smart-merge trigger; not in total_drift): {len(hd)}")
    for item in hd:
        print(f"  {item['rel']}: {item['header']} ({item['kind']})")
    scd = findings.get("section_content_drift", [])
    print(f"section_content_drift (smart-merge trigger; not in total_drift): {len(scd)}")
    for item in scd:
        print(f"  {item['rel']}: {item['section']} [block {item['block_index']}]")
        # Indent the diff snippet so it reads as a sub-entry under the
        # finding line; truncated already by _block_unified_diff_summary.
        for diff_line in item["diff_summary"].split("\n"):
            print(f"    {diff_line}")
    if fix_counts is not None:
        print("---")
        print(
            f"fix: regenerated={fix_counts.get('regenerated', 0)} "
            f"created={fix_counts.get('created', 0)} "
            f"deleted={fix_counts.get('deleted', 0)} "
            f"template_copied={fix_counts.get('template_copied', 0)} "
            f"section_appended={fix_counts.get('section_appended', 0)} "
            f"field_appended={fix_counts.get('field_appended', 0)} "
            f"gitignore_appended={fix_counts.get('gitignore_appended', 0)} "
            f"claude_agents_lang_fixed={fix_counts.get('claude_agents_lang_fixed', 0)}"
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
