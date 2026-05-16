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
    """Resolve plugin root: --plugin-root flag > env > derive from this file."""
    if override:
        return os.path.abspath(override)
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
    """
    content = open(source_path).read()
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
        if open(target).read() != expected_mirror_content(source_path, name, source_type):
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


def template_file_check(plugin_root: str, target_root: str) -> list[dict]:
    """Files present in templates/project-skeleton/ but absent from project."""
    skel = os.path.join(plugin_root, "templates/project-skeleton")
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
    return {l.rstrip() for l in open(path) if re.match(r"^## ", l)}


def template_section_check(plugin_root: str, target_root: str) -> list[dict]:
    """For .md files present in both, find `^## ` headers in template missing from project."""
    skel = os.path.join(plugin_root, "templates/project-skeleton")
    missing: list[dict] = []
    for f in glob.glob(f"{skel}/**/*.md", recursive=True):
        rel = os.path.relpath(f, skel)
        target = os.path.join(target_root, rel)
        if not os.path.exists(target):
            continue  # covered by template_file_check
        for h in sorted(_md_headers(f) - _md_headers(target)):
            missing.append({"rel": rel, "header": h})
    return missing


def claude_agents_check(target_root: str) -> dict:
    """CLAUDE.md / AGENTS.md placeholder + cross-sync diff (report only — never auto-merged)."""
    cl_path = os.path.join(target_root, "CLAUDE.md")
    ag_path = os.path.join(target_root, "AGENTS.md")
    result: dict = {"present": False, "first_line_placeholder": False, "unexpected_diffs": []}
    if not (os.path.exists(cl_path) and os.path.exists(ag_path)):
        return result
    result["present"] = True

    cl_first = open(cl_path).readline().rstrip()
    ag_first = open(ag_path).readline().rstrip()
    if "<project-name>" in cl_first or "<project-name>" in ag_first:
        result["first_line_placeholder"] = True

    cl = open(cl_path).read().splitlines()
    ag = open(ag_path).read().splitlines()
    # Expected diff zones: each tuple = (CLAUDE-side substring, AGENTS-side substring).
    expected_pairs = [
        ("Claude Entry Point", "Agent Entry Point"),
        ("auto-loaded by Claude", "auto-loaded by coding agents"),
        ("Sync with AGENTS.md", "Sync with CLAUDE.md"),
        ("This file and `AGENTS.md`", "This file and `CLAUDE.md`"),
        ('"Claude Entry Point"', '"Agent Entry Point"'),
    ]
    for i in range(max(len(cl), len(ag))):
        l1 = cl[i] if i < len(cl) else None
        l2 = ag[i] if i < len(ag) else None
        if l1 == l2:
            continue
        is_expected = False
        if l1 is not None and l2 is not None:
            for s1, s2 in expected_pairs:
                if (s1 in l1 and s2 in l2) or (s2 in l1 and s1 in l2):
                    is_expected = True
                    break
        if not is_expected:
            result["unexpected_diffs"].append({"line": i + 1, "CLAUDE": l1, "AGENTS": l2})
    return result


# ---------------------------------------------------------------------------
# Aggregate runner + fix application
# ---------------------------------------------------------------------------

def run_check(plugin_root: str, target_root: str) -> dict:
    return {
        "plugin_root": plugin_root,
        "target_root": os.path.abspath(target_root),
        "agents_sync": agents_sync_check(plugin_root, target_root),
        "missing_template": template_file_check(plugin_root, target_root),
        "missing_section": template_section_check(plugin_root, target_root),
        "claude_agents": claude_agents_check(target_root),
    }


def total_drift(findings: dict) -> int:
    a = findings["agents_sync"]
    if a.get("skipped"):
        return (
            len(findings["missing_template"])
            + len(findings["missing_section"])
            + len(findings["claude_agents"].get("unexpected_diffs", []))
        )
    return (
        len(a["stale"]) + len(a["missing"]) + len(a["orphan"])
        + len(findings["missing_template"])
        + len(findings["missing_section"])
        + len(findings["claude_agents"].get("unexpected_diffs", []))
    )


def run_fix(findings: dict, target_root: str) -> dict:
    """Apply auto-fixes for STALE / MISSING / ORPHAN / MISSING_TEMPLATE / MISSING_SECTION.

    CLAUDE / AGENTS findings are never touched here — they require manual merge.
    """
    counts = {
        "regenerated": 0, "created": 0, "deleted": 0,
        "template_copied": 0, "section_appended": 0,
    }

    a = findings.get("agents_sync", {})
    for item in a.get("stale", []):
        content = expected_mirror_content(item["source_path"], item["name"], item["source_type"])
        os.makedirs(os.path.dirname(item["target_path"]), exist_ok=True)
        with open(item["target_path"], "w") as f:
            f.write(content)
        counts["regenerated"] += 1
    for item in a.get("missing", []):
        content = expected_mirror_content(item["source_path"], item["name"], item["source_type"])
        os.makedirs(os.path.dirname(item["target_path"]), exist_ok=True)
        with open(item["target_path"], "w") as f:
            f.write(content)
        counts["created"] += 1
    for item in a.get("orphan", []):
        shutil.rmtree(os.path.dirname(item["target_path"]))
        counts["deleted"] += 1

    for item in findings.get("missing_template", []):
        os.makedirs(os.path.dirname(item["target_path"]), exist_ok=True)
        shutil.copy2(item["source_path"], item["target_path"])
        counts["template_copied"] += 1

    todo_marker = "_(TODO — added by /holo:update; fill via /go or direct edit)_"
    for item in findings.get("missing_section", []):
        target = os.path.join(target_root, item["rel"])
        with open(target, "a") as f:
            f.write(f"\n\n{item['header']}\n\n{todo_marker}\n")
        counts["section_appended"] += 1

    return counts


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_human(findings: dict, fix_counts: dict | None) -> None:
    a = findings["agents_sync"]
    print(f"plugin_root: {findings['plugin_root']}")
    print(f"target_root: {findings['target_root']}")
    if a.get("skipped"):
        print(".agents/skills/: skipped (directory not present in target)")
    else:
        print(
            f".agents/skills/: stale={len(a['stale'])} | "
            f"missing={len(a['missing'])} | orphan={len(a['orphan'])}"
        )
        for label, items in [("STALE", a["stale"]), ("MISSING", a["missing"]), ("ORPHAN", a["orphan"])]:
            for item in items:
                print(f"  {label}: {item['name']}")
    print(f"missing_template: {len(findings['missing_template'])}")
    for item in findings["missing_template"]:
        print(f"  {item['rel']}")
    print(f"missing_section:  {len(findings['missing_section'])}")
    for item in findings["missing_section"]:
        print(f"  {item['rel']}: {item['header']}")
    ca = findings["claude_agents"]
    if ca["present"]:
        print(
            f"claude_agents: first_line_placeholder={ca['first_line_placeholder']} "
            f"unexpected_diffs={len(ca['unexpected_diffs'])}"
        )
    if fix_counts is not None:
        print("---")
        print(
            f"fix: regenerated={fix_counts['regenerated']} created={fix_counts['created']} "
            f"deleted={fix_counts['deleted']} template_copied={fix_counts['template_copied']} "
            f"section_appended={fix_counts['section_appended']}"
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
