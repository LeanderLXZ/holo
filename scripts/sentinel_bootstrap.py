#!/usr/bin/env python3
"""
sentinel_bootstrap.py — one-shot injector for plugin-template sentinel markers.

Walks the plugin's template directories and injects two HTML-comment markers
defined in `docs/architecture/section-version-sentinel.md`:

1. `<!-- holo:heading -->` appended to every plugin canonical H2 line.
2. `<!-- holo:section start --> ... <!-- holo:section end -->` wrapping
   plugin canonical body content (preamble + each H2 section body).
   The file-top MAINTENANCE HTML comment uses the three-adjacent-comments
   encoding (`start sentinel + MAINTENANCE comment + end sentinel`, three
   independent comments) because nested HTML comments are invalid.

Idempotent: if a file already contains `holo:heading`, it is skipped.

CLI:
    python3 scripts/sentinel_bootstrap.py                 # default targets
    python3 scripts/sentinel_bootstrap.py --dry-run       # preview only
    python3 scripts/sentinel_bootstrap.py --verbose       # per-file log
    python3 scripts/sentinel_bootstrap.py --target <dir>  # override target (repeatable)
    python3 scripts/sentinel_bootstrap.py --self-test     # built-in unit tests

Default targets (relative to plugin root):
    templates/project-skeleton/
    templates/project-skeleton.zh/

See `docs/architecture/section-version-sentinel.md` for the mechanism + edge
cases. See `ai_context/decisions.md` §Skill Implementation #18 for rationale.
"""

import argparse
import re
import sys
from pathlib import Path


HEADING_MARKER = "<!-- holo:heading -->"
SECTION_START = "<!-- holo:section start -->"
SECTION_END = "<!-- holo:section end -->"

# H1 line: starts with exactly `# ` (one hash + space + non-hash content).
H1_RE = re.compile(r"^#\s+(?!#)")
# H2 line: starts with exactly `## ` (two hashes + space + non-hash content).
H2_RE = re.compile(r"^##\s+(?!#)")

# Fence open: three+ backticks or tildes at line start (any trailing info string).
FENCE_OPEN_RE = re.compile(r"^(`{3,}|~{3,})")

# User-territory marker line regexes (lines that the consumer fills in;
# they MUST NOT live inside a `<!-- holo:section start/end -->` block).
# Bootstrap splits the section body around these markers so the prose
# above + below each marker is wrapped in separate sentinel blocks,
# with the marker line itself sitting as bare gap content.
#
# PROGRESSIVE marker: `_(none yet — delete this marker once content is added)_`
# (literal line; tolerates trailing whitespace).
PROGRESSIVE_MARKER_RE = re.compile(
    r"^_\(none yet — delete this marker once content is added\)_\s*$"
)
# Standalone `<placeholder>` line: entire line is a single `<...>` token
# (init Round 1 / Step 0 / Step 4.4 substitutes a real value). Excludes
# HTML comments by rejecting `<!` at line start — `<!-- ... -->` is
# plugin canonical prose (e.g. MAINTENANCE block, todo_list maintainer
# guidance comments), NOT a user-territory placeholder.
#
# Inline `<...>` (mixed with canonical prose on the same line, e.g.
# `# <project-name> — Claude Entry Point` H1) is intentionally NOT
# matched — those stay inside their containing element; placeholder-
# aware substitution is the extract-and-reformat smart-merge's job,
# not bootstrap's. Multi-line standalone `<...>` (placeholder text
# spans multiple lines, occupying the WHOLE body of a section) is
# handled by `_is_multiline_standalone_placeholder_body()` below.
STANDALONE_PLACEHOLDER_RE = re.compile(r"^<[^!][^>]*>\s*$")


def is_user_territory_marker(line: str) -> bool:
    """True iff `line` is a standalone user-territory marker (PROGRESSIVE
    or single-line `<placeholder>`). Used by bootstrap to split section
    bodies around these markers.
    """
    return bool(
        PROGRESSIVE_MARKER_RE.match(line) or STANDALONE_PLACEHOLDER_RE.match(line)
    )


def _is_multiline_standalone_placeholder_body(body: list[str]) -> bool:
    """True iff the trimmed body is exactly ONE multi-line `<...>`
    placeholder (no surrounding canonical prose).

    Conservative match — fires only when the WHOLE body is the
    placeholder:
    - First non-blank line starts with `<` but NOT `<!` (i.e. not an
      HTML comment).
    - Last non-blank line ends with `>`.
    - The body contains exactly one `<` (at the start) and exactly one
      `>` (at the end) — no other angle brackets anywhere, defending
      against false-positives in prose that happens to mix `<` / `>`.
    - The body spans 2+ non-blank lines (single-line case is the
      `STANDALONE_PLACEHOLDER_RE` path).

    Used by `_wrap_body_with_markers` to keep these multi-line
    placeholders in gap territory (parallel to single-line standalone
    `<...>` and PROGRESSIVE marker treatment).
    """
    trimmed = trim_blanks(body)
    if len(trimmed) < 2:
        return False
    joined = "\n".join(trimmed)
    if not joined.startswith("<") or joined.startswith("<!"):
        return False
    if not joined.endswith(">"):
        return False
    if joined.count("<") != 1 or joined.count(">") != 1:
        return False
    return True


def find_plugin_root() -> Path:
    """Locate plugin root by walking up from this file until .claude-plugin/."""
    here = Path(__file__).resolve().parent
    candidate = here
    while candidate != candidate.parent:
        if (candidate / ".claude-plugin" / "plugin.json").exists():
            return candidate
        candidate = candidate.parent
    sys.exit("could not locate plugin root (no .claude-plugin/plugin.json found above this file)")


def fence_aware_h2_indices(lines: list[str]) -> list[int]:
    """Return indices of H2 lines NOT inside a fenced code block."""
    out: list[int] = []
    in_fence = False
    fence_char: str | None = None
    for i, line in enumerate(lines):
        if not in_fence:
            m = FENCE_OPEN_RE.match(line)
            if m:
                in_fence = True
                fence_char = m.group(1)[0]
                continue
            if H2_RE.match(line):
                out.append(i)
        else:
            stripped = line.rstrip()
            m = FENCE_OPEN_RE.match(stripped)
            if m and m.group(1)[0] == fence_char and stripped == m.group(1):
                in_fence = False
                fence_char = None
    return out


def fence_aware_h1_index(lines: list[str]) -> int | None:
    """Return the index of the first H1 line NOT inside a fenced code
    block, or None if no H1 exists. Files typically have at most one
    H1 (the title); this returns the first only.
    """
    in_fence = False
    fence_char: str | None = None
    for i, line in enumerate(lines):
        if not in_fence:
            m = FENCE_OPEN_RE.match(line)
            if m:
                in_fence = True
                fence_char = m.group(1)[0]
                continue
            if H1_RE.match(line):
                return i
        else:
            stripped = line.rstrip()
            m = FENCE_OPEN_RE.match(stripped)
            if m and m.group(1)[0] == fence_char and stripped == m.group(1):
                in_fence = False
                fence_char = None
    return None


def find_html_comment_end(lines: list[str], start: int) -> int:
    """Return index of line containing the closing `-->` for a comment opened at `start`.

    Assumes lines[start] begins with `<!--`. Returns `start` itself if the
    opening line also contains `-->`.
    """
    if "-->" in lines[start]:
        return start
    for j in range(start + 1, len(lines)):
        if "-->" in lines[j]:
            return j
    return len(lines) - 1  # unclosed comment — degrade to EOF


def trim_blanks(lines: list[str]) -> list[str]:
    """Strip leading and trailing blank lines; preserve internal blanks."""
    a, b = 0, len(lines)
    while a < b and lines[a].strip() == "":
        a += 1
    while b > a and lines[b - 1].strip() == "":
        b -= 1
    return lines[a:b]


def _wrap_body_with_markers(body: list[str]) -> list[str]:
    """Wrap body content in sentinel pairs, splitting around user-territory
    marker lines (PROGRESSIVE / standalone-`<...>` / multi-line standalone
    `<...>`).

    Walks the body line-by-line. Prose chunks between markers become
    sentinel-wrapped blocks; marker lines themselves emit as bare gap
    content (no sentinel wrapper). Result preserves the original line
    sequence + adds sentinels around prose chunks.

    Special case: when the whole trimmed body is a single multi-line
    `<...>` placeholder (no surrounding canonical prose), the entire
    placeholder emits as bare gap content (no sentinel wrapping). See
    `_is_multiline_standalone_placeholder_body` for the match rule.

    Empty / whitespace-only body returns []; trailing/leading blanks are
    trimmed.
    """
    trimmed = trim_blanks(body)
    if not trimmed:
        return []

    # Multi-line standalone `<...>` placeholder occupying the whole body
    # → emit as bare gap (no sentinel wrap), parallel to single-line
    # standalone placeholder + PROGRESSIVE marker handling.
    if _is_multiline_standalone_placeholder_body(trimmed):
        return list(trimmed)

    out: list[str] = []
    prose_buf: list[str] = []

    def flush_prose() -> None:
        if not prose_buf:
            return
        # Strip leading + trailing blank lines from the prose chunk so
        # the sentinel hugs the actual content (matches H2 body
        # convention: sentinel `start` / content / sentinel `end` with
        # no inner blank-line padding).
        chunk = trim_blanks(prose_buf)
        if chunk:
            if out and out[-1] != "":
                out.append("")
            out.append(SECTION_START)
            out.extend(chunk)
            out.append(SECTION_END)
        prose_buf.clear()

    for line in trimmed:
        if is_user_territory_marker(line):
            flush_prose()
            if out and out[-1] != "":
                out.append("")
            out.append(line)
        else:
            prose_buf.append(line)
    flush_prose()
    return out


def emit_preamble(preamble: list[str], h1_local_index: int | None) -> list[str]:
    """Wrap preamble content with sentinels under the new H1-marker model.

    Layout:
    1. **Pre-H1 region** (lines 0 .. h1_local_index-1 if h1 exists; else
       all lines): typical content here is the file-top MAINTENANCE HTML
       comment block. The first HTML comment found at top-of-region
       wraps with the three-adjacent encoding (`SECTION_START` line +
       comment lines verbatim + `SECTION_END` line). Anything after the
       comment but before H1 wraps in a normal sentinel pair (rare in
       templates).
    2. **H1 line** (at `h1_local_index`): emitted as its own line with
       `<!-- holo:heading -->` marker appended. NOT wrapped in a sentinel
       block — H1 is parallel to H2 in ownership semantics.
    3. **Post-H1 / pre-first-H2 region** (lines h1_local_index+1 .. end):
       intro paragraphs etc. Wrap in sentinel pairs via
       `_wrap_body_with_markers` so any standalone `<...>` placeholder
       (e.g. the README's `<one or two sentences naming the primary
       goal>`) sits in a gap, not inside a sentinel block.
    """
    out: list[str] = []
    i = 0

    # Determine the split point for region 1 (pre-H1).
    region1_end = h1_local_index if h1_local_index is not None else len(preamble)

    # Skip leading blanks (defensive).
    while i < region1_end and preamble[i].strip() == "":
        i += 1

    # Region 1a: optional file-top HTML comment block (MAINTENANCE).
    if i < region1_end and preamble[i].lstrip().startswith("<!--"):
        end = find_html_comment_end(preamble, i)
        if end < region1_end:
            comment_lines = preamble[i : end + 1]
            out.append(SECTION_START)
            out.extend(comment_lines)
            out.append(SECTION_END)
            i = end + 1
            if i < region1_end and preamble[i].strip() == "":
                i += 1  # consume one blank separator (not emitted yet)

    # Region 1b: any other pre-H1 content (rare) wraps as a normal block.
    rest_pre_h1 = trim_blanks(preamble[i:region1_end])
    if rest_pre_h1:
        if out and out[-1] != "":
            out.append("")
        out.append(SECTION_START)
        out.extend(rest_pre_h1)
        out.append(SECTION_END)

    # Region 2: H1 line with marker (no sentinel wrap).
    if h1_local_index is not None:
        if out and out[-1] != "":
            out.append("")
        h1_line = preamble[h1_local_index]
        out.append(h1_line.rstrip() + " " + HEADING_MARKER)

        # Region 3: post-H1 / pre-first-H2 intro paragraphs.
        post_h1 = preamble[h1_local_index + 1 :]
        wrapped = _wrap_body_with_markers(post_h1)
        if wrapped:
            if out and out[-1] != "":
                out.append("")
            out.extend(wrapped)

    return out


def emit_section(heading_line: str, body: list[str]) -> list[str]:
    """Wrap one H2 section with sentinels.

    - Heading line: append ` <!-- holo:heading -->` (separated by a single space).
    - Body: split around user-territory markers via `_wrap_body_with_markers`
      (PROGRESSIVE / standalone-`<...>` markers sit in gaps, not inside
      sentinel blocks). Empty / whitespace-only body → just emit the
      heading line.
    """
    new_heading = heading_line.rstrip() + " " + HEADING_MARKER
    out = [new_heading]
    wrapped = _wrap_body_with_markers(body)
    if wrapped:
        out.append("")
        out.extend(wrapped)
    return out


def bootstrap_file_content(content: str) -> str:
    """Apply sentinel markers to a markdown file's content.

    Idempotent: if a standalone sentinel marker already appears,
    returns content unchanged. A "standalone" marker is either a line
    whose stripped content equals `<!-- holo:section start -->` (or
    `end`), or a line that ENDS with ` <!-- holo:heading -->` (the
    H1/H2-marker pattern). Mid-line occurrences of the marker text
    inside prose / blockquotes / code fences do NOT trigger
    idempotency — those are legitimate documentation references to
    the marker syntax, not actual sentinel state.

    Files without any H2 still produce a `holo:section` marker pair
    on first bootstrap (the preamble region), so checking either
    standalone marker covers both cases.
    """
    for raw_line in content.split("\n"):
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped == SECTION_START or stripped == SECTION_END:
            return content
        if line.endswith(" " + HEADING_MARKER):
            return content

    lines = content.split("\n")
    # If file ends with a trailing newline, split() leaves an empty string at end.
    # Track this so we can restore it on emit.
    had_trailing_newline = content.endswith("\n")
    if had_trailing_newline:
        lines = lines[:-1]  # drop the empty string

    h2_indices = fence_aware_h2_indices(lines)

    if not h2_indices:
        preamble = lines
        sections: list[tuple[str, list[str]]] = []
    else:
        first_h2 = h2_indices[0]
        preamble = lines[:first_h2]
        sections = []
        for k, h2_idx in enumerate(h2_indices):
            next_h2 = h2_indices[k + 1] if k + 1 < len(h2_indices) else len(lines)
            heading_line = lines[h2_idx]
            body = lines[h2_idx + 1 : next_h2]
            sections.append((heading_line, body))

    # Locate H1 within the preamble (file-wide H1 search would catch the
    # same line since H1 lives before first H2 by definition).
    h1_idx = fence_aware_h1_index(preamble)

    out: list[str] = []
    preamble_emitted = emit_preamble(preamble, h1_idx)
    if preamble_emitted:
        out.extend(preamble_emitted)

    for k, (heading_line, body) in enumerate(sections):
        if out and out[-1] != "":
            out.append("")
        out.extend(emit_section(heading_line, body))

    result = "\n".join(out)
    if had_trailing_newline:
        result += "\n"
    return result


def list_template_files(targets: list[Path]) -> list[Path]:
    """Walk targets and return sorted list of *.md files."""
    files: list[Path] = []
    for t in targets:
        if not t.exists():
            sys.exit(f"target {t} does not exist")
        if t.is_file() and t.suffix == ".md":
            files.append(t)
            continue
        for p in t.rglob("*.md"):
            if p.is_file():
                files.append(p)
    return sorted(set(files))


def run_bootstrap(targets: list[Path], dry_run: bool, verbose: bool) -> int:
    """Bootstrap all *.md files under targets. Returns exit code."""
    files = list_template_files(targets)
    if not files:
        print(f"no *.md files found under {targets}", file=sys.stderr)
        return 1

    changed = 0
    skipped = 0
    for f in files:
        original = f.read_text(encoding="utf-8")
        new = bootstrap_file_content(original)
        if new == original:
            skipped += 1
            if verbose:
                print(f"SKIP {f}")
            continue
        changed += 1
        if dry_run:
            if verbose:
                print(f"WOULD-WRITE {f}")
            else:
                print(f"would-write {f}")
        else:
            f.write_text(new, encoding="utf-8")
            if verbose:
                print(f"WRITE {f}")
            else:
                print(f"wrote {f}")

    summary = f"{changed} changed, {skipped} skipped (already bootstrapped)"
    if dry_run:
        summary = f"DRY-RUN: {summary}"
    print(summary)
    return 0


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------


def _self_test() -> int:
    """Built-in tests. Returns 0 on pass, 1 on fail."""
    failures: list[str] = []

    def check(name: str, got: str, want: str) -> None:
        if got != want:
            failures.append(
                f"FAIL {name}\n--- got ---\n{got!r}\n--- want ---\n{want!r}\n"
            )

    # Test 1: empty preamble + one section.
    inp = "## Foo\n\nbody line\n"
    want = (
        "## Foo " + HEADING_MARKER + "\n"
        "\n"
        + SECTION_START + "\n"
        "body line\n"
        + SECTION_END + "\n"
    )
    check("one_section_no_preamble", bootstrap_file_content(inp), want)

    # Test 2: H1 only, no H2 (H1 gets marker; intro wraps in sentinel).
    inp = "# Title\n\nintro paragraph\n"
    want = (
        "# Title " + HEADING_MARKER + "\n"
        "\n"
        + SECTION_START + "\n"
        "intro paragraph\n"
        + SECTION_END + "\n"
    )
    check("h1_only", bootstrap_file_content(inp), want)

    # Test 3: MAINTENANCE block + H1 + H2 (H1 marker, NOT in preamble block).
    inp = (
        "<!--\n"
        "MAINTENANCE — do not edit.\n"
        "-->\n"
        "\n"
        "# Title\n"
        "\n"
        "intro\n"
        "\n"
        "## Section\n"
        "\n"
        "body\n"
    )
    want = (
        SECTION_START + "\n"
        "<!--\n"
        "MAINTENANCE — do not edit.\n"
        "-->\n"
        + SECTION_END + "\n"
        "\n"
        "# Title " + HEADING_MARKER + "\n"
        "\n"
        + SECTION_START + "\n"
        "intro\n"
        + SECTION_END + "\n"
        "\n"
        "## Section " + HEADING_MARKER + "\n"
        "\n"
        + SECTION_START + "\n"
        "body\n"
        + SECTION_END + "\n"
    )
    check("maintenance_h1_h2", bootstrap_file_content(inp), want)

    # Test 4: idempotency — re-run is a no-op.
    inp = (
        "## Section " + HEADING_MARKER + "\n"
        "\n"
        + SECTION_START + "\n"
        "body\n"
        + SECTION_END + "\n"
    )
    check("idempotent_already_marked", bootstrap_file_content(inp), inp)

    # Test 5: empty section body (no body, just heading).
    inp = "## Section\n"
    want = "## Section " + HEADING_MARKER + "\n"
    check("empty_section", bootstrap_file_content(inp), want)

    # Test 6: section body that is only whitespace.
    inp = "## Section\n\n\n"
    want = "## Section " + HEADING_MARKER + "\n"
    check("whitespace_only_body", bootstrap_file_content(inp), want)

    # Test 7: fence-aware — `## ` inside code fence is NOT an H2;
    # `# Title` inside fence is NOT an H1.
    inp = (
        "# Title\n"
        "\n"
        "```\n"
        "## not a heading\n"
        "```\n"
        "\n"
        "## Real Heading\n"
        "\n"
        "body\n"
    )
    want = (
        "# Title " + HEADING_MARKER + "\n"
        "\n"
        + SECTION_START + "\n"
        "```\n"
        "## not a heading\n"
        "```\n"
        + SECTION_END + "\n"
        "\n"
        "## Real Heading " + HEADING_MARKER + "\n"
        "\n"
        + SECTION_START + "\n"
        "body\n"
        + SECTION_END + "\n"
    )
    check("fence_aware_h1_h2", bootstrap_file_content(inp), want)

    # Test 8: H3 stays inside parent H2's body sentinel.
    inp = (
        "## Parent\n"
        "\n"
        "intro\n"
        "\n"
        "### Sub\n"
        "\n"
        "detail\n"
    )
    want = (
        "## Parent " + HEADING_MARKER + "\n"
        "\n"
        + SECTION_START + "\n"
        "intro\n"
        "\n"
        "### Sub\n"
        "\n"
        "detail\n"
        + SECTION_END + "\n"
    )
    check("h3_inside_h2_body", bootstrap_file_content(inp), want)

    # Test 9: file with no trailing newline.
    inp = "## Foo\n\nbody"
    want = (
        "## Foo " + HEADING_MARKER + "\n"
        "\n"
        + SECTION_START + "\n"
        "body\n"
        + SECTION_END
    )
    check("no_trailing_newline", bootstrap_file_content(inp), want)

    # Test 10: multiple H2s in a row with no body in between.
    inp = "## A\n## B\nbody\n"
    want = (
        "## A " + HEADING_MARKER + "\n"
        "\n"
        "## B " + HEADING_MARKER + "\n"
        "\n"
        + SECTION_START + "\n"
        "body\n"
        + SECTION_END + "\n"
    )
    check("adjacent_h2_no_body", bootstrap_file_content(inp), want)

    # Test 11: ### H3 line is NOT picked up as H2.
    inp = "### Not H2\n\nbody\n"
    want = (
        SECTION_START + "\n"
        "### Not H2\n"
        "\n"
        "body\n"
        + SECTION_END + "\n"
    )
    check("h3_not_h2", bootstrap_file_content(inp), want)

    # Test 12: idempotency for H1-marker files (preamble-only files).
    inp = (
        "# Title " + HEADING_MARKER + "\n"
        "\n"
        + SECTION_START + "\n"
        "intro\n"
        + SECTION_END + "\n"
    )
    check("idempotent_preamble_only", bootstrap_file_content(inp), inp)

    # Test 13: PROGRESSIVE marker splits section body around the marker.
    inp = (
        "## Section\n"
        "\n"
        "prose before\n"
        "\n"
        "_(none yet — delete this marker once content is added)_\n"
        "\n"
        "prose after\n"
    )
    want = (
        "## Section " + HEADING_MARKER + "\n"
        "\n"
        + SECTION_START + "\n"
        "prose before\n"
        + SECTION_END + "\n"
        "\n"
        "_(none yet — delete this marker once content is added)_\n"
        "\n"
        + SECTION_START + "\n"
        "prose after\n"
        + SECTION_END + "\n"
    )
    check("progressive_marker_splits_body", bootstrap_file_content(inp), want)

    # Test 14: PROGRESSIVE-only section (no prose around) emits just heading + marker.
    inp = (
        "## Empty Section\n"
        "\n"
        "_(none yet — delete this marker once content is added)_\n"
    )
    want = (
        "## Empty Section " + HEADING_MARKER + "\n"
        "\n"
        "_(none yet — delete this marker once content is added)_\n"
    )
    check("progressive_only_section", bootstrap_file_content(inp), want)

    # Test 15: standalone `<...>` placeholder splits body like PROGRESSIVE.
    inp = (
        "## Slot\n"
        "\n"
        "intro prose\n"
        "\n"
        "<one or two sentences naming the goal>\n"
        "\n"
        "outro prose\n"
    )
    want = (
        "## Slot " + HEADING_MARKER + "\n"
        "\n"
        + SECTION_START + "\n"
        "intro prose\n"
        + SECTION_END + "\n"
        "\n"
        "<one or two sentences naming the goal>\n"
        "\n"
        + SECTION_START + "\n"
        "outro prose\n"
        + SECTION_END + "\n"
    )
    check("standalone_placeholder_splits_body", bootstrap_file_content(inp), want)

    # Test 16: standalone `<...>` in preamble (post-H1 intro) lands in gap too.
    inp = (
        "# <project-name>\n"
        "\n"
        "<one or two sentences naming the goal>\n"
        "\n"
        "Start here:\n"
        "\n"
        "- bullet\n"
    )
    want = (
        "# <project-name> " + HEADING_MARKER + "\n"
        "\n"
        "<one or two sentences naming the goal>\n"
        "\n"
        + SECTION_START + "\n"
        "Start here:\n"
        "\n"
        "- bullet\n"
        + SECTION_END + "\n"
    )
    check("standalone_placeholder_in_preamble", bootstrap_file_content(inp), want)

    # Test 17: inline `<...>` (mixed with prose on same line) stays put — no
    # splitting because it's not a standalone-marker line.
    inp = (
        "## Header\n"
        "\n"
        "Prose with inline `<project-name>` placeholder mid-sentence.\n"
    )
    want = (
        "## Header " + HEADING_MARKER + "\n"
        "\n"
        + SECTION_START + "\n"
        "Prose with inline `<project-name>` placeholder mid-sentence.\n"
        + SECTION_END + "\n"
    )
    check("inline_placeholder_not_split", bootstrap_file_content(inp), want)

    # Test 18: idempotency must look at STANDALONE markers only. Prose
    # that QUOTES the marker syntax (e.g. an explainer blockquote
    # describing the sentinel contract) MUST NOT trigger false-skip.
    inp = (
        "# Title\n"
        "\n"
        "> Sentinel notice: headings carrying `" + HEADING_MARKER + "` are\n"
        "> plugin-managed; bodies wrapped in `" + SECTION_START + "` and\n"
        "> `" + SECTION_END + "` likewise.\n"
        "\n"
        "## Section\n"
        "\n"
        "body\n"
    )
    out = bootstrap_file_content(inp)
    # The H1 + H2 lines should have gained the marker; the blockquote
    # prose stays inside a sentinel block.
    if (
        ("# Title " + HEADING_MARKER not in out)
        or ("## Section " + HEADING_MARKER not in out)
    ):
        failures.append(
            f"FAIL idempotency_no_falsepos_on_quoted_markers — H1 or H2 missing marker:\n{out!r}"
        )

    # Test 19: multi-line standalone `<...>` placeholder occupying the
    # whole body emits as bare gap (no sentinel wrap), parallel to
    # single-line standalone placeholder + PROGRESSIVE marker handling.
    inp = (
        "## Top-Level Structure\n"
        "\n"
        "<bulleted list naming each top-level directory and what it holds in one\n"
        "line. New top-level directories get a row here.>\n"
    )
    want = (
        "## Top-Level Structure " + HEADING_MARKER + "\n"
        "\n"
        "<bulleted list naming each top-level directory and what it holds in one\n"
        "line. New top-level directories get a row here.>\n"
    )
    check("multiline_standalone_placeholder_in_gap", bootstrap_file_content(inp), want)

    # Test 20: `<!` prefix (HTML comment-style line) is NOT treated as a
    # user-territory standalone placeholder — it's plugin canonical prose
    # (typical: todo_list `<!-- Single-slot. ... -->` maintainer
    # guidance, or any other inline HTML comment). Body stays wrapped
    # in a normal sentinel block.
    inp = (
        "## Section\n"
        "\n"
        "<!-- maintainer guidance about this section -->\n"
    )
    want = (
        "## Section " + HEADING_MARKER + "\n"
        "\n"
        + SECTION_START + "\n"
        "<!-- maintainer guidance about this section -->\n"
        + SECTION_END + "\n"
    )
    check("html_comment_not_treated_as_placeholder", bootstrap_file_content(inp), want)

    if failures:
        for f in failures:
            print(f)
        print(f"FAILED {len(failures)} test(s)")
        return 1
    print("OK 20 tests")
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Inject sentinel markers into plugin template *.md files."
    )
    parser.add_argument(
        "--target",
        action="append",
        type=Path,
        help="Target directory or file to bootstrap (repeatable). "
        "Default: templates/project-skeleton/ + templates/project-skeleton.zh/ "
        "under the plugin root.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview only; do not write.")
    parser.add_argument("--verbose", action="store_true", help="Per-file action log.")
    parser.add_argument("--self-test", action="store_true", help="Run built-in unit tests and exit.")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    if args.target:
        targets = args.target
    else:
        plugin_root = find_plugin_root()
        targets = [
            plugin_root / "templates" / "project-skeleton",
            plugin_root / "templates" / "project-skeleton.zh",
        ]

    return run_bootstrap(targets, dry_run=args.dry_run, verbose=args.verbose)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
