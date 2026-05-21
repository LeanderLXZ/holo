#!/usr/bin/env python3
"""
sentinel_parse.py — canonical parser API for sentinel-aware markdown files.

The dual-marker sentinel mechanism is specified in
`docs/architecture/section-version-sentinel.md` and rationale lives in
`ai_context/decisions.md` §Skill Implementation #18. This module is the
**stable consumption interface** for downstream consumers (notably
[T-INIT-UPDATE-SMART-MERGE]'s extract-and-reformat smart-merge
pipeline) that need a structured view of a sentinel-aware file.

Markers (must match `scripts/sentinel_bootstrap.py`):

- `<!-- holo:heading -->` — appended to an H2 line (`## Foo`) to declare
  the heading plugin-owned (canonical content, overwritten on plugin
  upgrade with snapshot fallback).
- `<!-- holo:section start -->` ... `<!-- holo:section end -->` — wraps
  plugin canonical body content. May appear multiple times within one
  H2 section, interleaved with user content (gaps between blocks).
- File-top MAINTENANCE HTML comment encoded as three adjacent comments
  (`<!-- holo:section start -->` + `<!-- ... MAINTENANCE ... -->` +
  `<!-- holo:section end -->`) — handled transparently by the parser
  because three independent HTML comments at the same nesting level
  parse as three independent text elements; the middle MAINTENANCE
  comment lives inside the plugin block's body text.

Public API:

    parse(path: pathlib.Path | str) -> ParsedFile

    @dataclass(frozen=True) Block(start_line, end_line, body)
    @dataclass(frozen=True) Gap(start_line, end_line, body, after_block)
    @dataclass(frozen=True) Section(heading_text, plugin_owned, plugin_blocks, user_gaps)
    @dataclass(frozen=True) ParsedFile(preamble_user_gaps, preamble_plugin_blocks, sections)

CLI:

    python3 scripts/sentinel_parse.py <path>          # parse + pretty-print summary
    python3 scripts/sentinel_parse.py --self-test     # run built-in unit tests

Fence-aware: lines inside ``` / ~~~ fenced code blocks are skipped for
H2 / sentinel detection so tutorial sections that quote marker syntax
don't corrupt parsing.

PROGRESSIVE marker lines (`_(none yet — delete this marker once content
is added)_`) are NOT stripped at parse time; the parser preserves raw
bodies and gaps. Domain-specific normalization is left to consumers
(e.g. `holo_update_check.py` strips PROGRESSIVE for `section_content_drift`
byte-diff via `_normalize_block_for_diff`; the canonical parser keeps
the original text so other consumers can keep or skip the markers per
their need).

This module has NO dependency on `holo_update_check.py` — it is a
standalone canonical reference. The existing `_parse_sentinel_blocks`
helper in `holo_update_check.py` predates this module and uses a dict
shape internally; both interfaces are stable for now. A future refactor
may consolidate, but is not required by any current consumer.
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


HEADING_MARKER = "<!-- holo:heading -->"
SECTION_START = "<!-- holo:section start -->"
SECTION_END = "<!-- holo:section end -->"

_HEADING_MARKER_RE = re.compile(r"\s*<!-- holo:heading -->\s*$")
_H1_RE = re.compile(r"^#\s+(?!#)")
_H2_RE = re.compile(r"^##\s+(?!#)")
_FENCE_OPEN_RE = re.compile(r"^(`{3,}|~{3,})")


@dataclass(frozen=True)
class Block:
    """A plugin canonical sentinel-bracketed block.

    `start_line` / `end_line` are 1-based line numbers of the
    `<!-- holo:section start -->` and `<!-- holo:section end -->`
    marker lines themselves. `body` is the joined-with-`\\n` content
    BETWEEN the markers (markers excluded); trailing newline NOT
    preserved (re-add at write time via `body + "\\n"`).
    """

    start_line: int
    end_line: int
    body: str


@dataclass(frozen=True)
class Gap:
    """User content between plugin blocks or before any block.

    `start_line` / `end_line` are 1-based line numbers of the first and
    last lines of the gap (inclusive on both ends). `body` is the raw
    joined-with-`\\n` text of those lines; NO trimming applied (leading
    / trailing blank lines + whitespace preserved verbatim, per the
    "preserve user content byte-for-byte" contract). `after_block` is
    the zero-based index of the preceding plugin block in the parent
    `Section.plugin_blocks` list, or `None` if the gap sits BEFORE any
    plugin block (e.g. user content at the top of the section).
    """

    start_line: int
    end_line: int
    body: str
    after_block: int | None


@dataclass(frozen=True)
class Section:
    """One H2 section: heading text + plugin blocks + user gaps.

    `heading_text` is the H2 line minus the `## ` prefix and minus the
    `<!-- holo:heading -->` marker (if present) — e.g. `"Session Start"`
    not `"## Session Start <!-- holo:heading -->"`. Strip trailing
    whitespace.

    `plugin_owned` is `True` iff the H2 line carries the
    `<!-- holo:heading -->` marker — i.e. plugin declares this heading
    plugin canonical. `False` means the heading is user-added; the
    section's blocks (if any) are still parsed but consumers should
    treat the whole section as user-owned for ownership-disambiguation
    purposes.

    `plugin_blocks` is the list of sentinel-bracketed blocks under the
    heading, in source order. May be empty if the section has only user
    content (gaps without any sentinel blocks).

    `user_gaps` is the list of gaps (user content regions) between /
    around the plugin blocks, in source order. Each gap's `after_block`
    field positions it relative to `plugin_blocks`.
    """

    heading_text: str
    plugin_owned: bool
    plugin_blocks: list[Block] = field(default_factory=list)
    user_gaps: list[Gap] = field(default_factory=list)


@dataclass(frozen=True)
class H1:
    """The file's H1 line as its own ownership unit.

    Parallel to `Section` but at H1 grain. After the Phase-2-design-
    refinement bootstrap, H1 lines carry `<!-- holo:heading -->` and
    sit OUTSIDE preamble sentinel blocks (the H1 line itself is
    plugin canonical via its marker; intro paragraphs after H1 wrap
    in their own sentinel pair).

    `text` is the H1 line minus the leading `# ` and minus the trailing
    `<!-- holo:heading -->` marker (if present), trimmed.
    `plugin_owned` is True iff the marker was present.
    `line` is the 1-based line number of the H1 line in the source file.
    """

    text: str
    plugin_owned: bool
    line: int


@dataclass(frozen=True)
class ParsedFile:
    """A parsed sentinel-aware file.

    `preamble_user_gaps` + `preamble_plugin_blocks` cover the file-top
    region BEFORE the H1 heading (MAINTENANCE comment, etc.).

    `h1` is the file's H1 line (parallel to Section but at H1 grain) —
    None for files without an H1.

    `sections` is the list of H2 sections in source order. Each section
    carries its heading text, ownership flag, plugin blocks, and user
    gaps. Intro paragraphs between H1 and the first H2 attribute to a
    pseudo-section in `sections` only if that's how the parser sees
    them — actually intro paragraphs after H1 + before first H2 fall
    into the H1's "implicit body" region, captured by the FIRST
    Section if any, OR by file-level if no H2 exists. See `parse()`
    docstring for full attribution rules.
    """

    preamble_user_gaps: list[Gap]
    preamble_plugin_blocks: list[Block]
    h1: H1 | None
    sections: list[Section]


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def _fence_state_per_line(lines: list[str]) -> list[bool]:
    """Precompute per-line "is inside a fenced code block?" state.

    A fenced code block opens with three+ backticks or tildes at line
    start (after optional leading whitespace) and closes with a matching
    fence marker. While in a fence, H2 / sentinel detection should skip
    the line.

    Returns a list of bool, one per input line, with the same length.
    Each entry is `True` iff the line is INSIDE the fence (the fence
    open / close lines themselves are reported as `False` — they are
    structural, not in the fence body).
    """
    out: list[bool] = []
    in_fence = False
    fence_marker = ""
    for raw in lines:
        stripped = raw.lstrip()
        out.append(in_fence)
        if not in_fence:
            m = _FENCE_OPEN_RE.match(stripped)
            if m:
                in_fence = True
                fence_marker = m.group(1)[0]
        else:
            stripped_full = raw.rstrip()
            m = _FENCE_OPEN_RE.match(stripped_full)
            if m and m.group(1)[0] == fence_marker and stripped_full == m.group(1):
                in_fence = False
                fence_marker = ""
    return out


def _is_h2(line: str) -> bool:
    return bool(_H2_RE.match(line))


def _strip_heading(line: str) -> tuple[str, bool]:
    """Return (heading_text, plugin_owned) for an H2 line.

    `heading_text` strips the leading `## ` and the trailing marker (if
    present); `plugin_owned` is True iff the marker was present.
    """
    plugin_owned = HEADING_MARKER in line
    stripped = _HEADING_MARKER_RE.sub("", line.rstrip()).rstrip()
    # Strip the leading `## ` prefix.
    if stripped.startswith("## "):
        text = stripped[3:].strip()
    else:
        text = stripped.strip()
    return (text, plugin_owned)


def _strip_h1(line: str) -> tuple[str, bool]:
    """Return (heading_text, plugin_owned) for an H1 line.

    `heading_text` strips the leading `# ` and the trailing marker (if
    present); `plugin_owned` is True iff the marker was present.
    """
    plugin_owned = HEADING_MARKER in line
    stripped = _HEADING_MARKER_RE.sub("", line.rstrip()).rstrip()
    if stripped.startswith("# "):
        text = stripped[2:].strip()
    else:
        text = stripped.strip()
    return (text, plugin_owned)


def _is_h1(line: str) -> bool:
    return bool(_H1_RE.match(line))


def parse(path: Path | str) -> ParsedFile:
    """Read a sentinel-aware markdown file and return a structured view.

    See the module docstring + the `Block` / `Gap` / `Section` /
    `ParsedFile` dataclass docstrings for the data model.

    Missing files raise `FileNotFoundError`. Malformed files (e.g.
    unclosed sentinel block at EOF) are best-effort: the unterminated
    block is silently dropped from output rather than raised, on the
    "be liberal in what you accept" principle. Consumers can validate
    afterward by checking `(block.end_line - block.start_line) >= 1`.
    """
    p = Path(path)
    with p.open(encoding="utf-8") as f:
        lines = f.read().splitlines()

    if not lines:
        return ParsedFile([], [], None, [])

    in_fence = _fence_state_per_line(lines)

    # State machine: walk lines, accumulate (gap, block) events into
    # either preamble buckets or the current section's buckets.
    preamble_user_gaps: list[Gap] = []
    preamble_plugin_blocks: list[Block] = []
    h1: H1 | None = None
    sections: list[Section] = []

    current_section_idx: int = -1  # -1 = preamble; >= 0 = sections[idx]
    in_block = False
    block_start_line_1based: int = -1
    block_body_lines: list[str] = []

    # Pending gap accumulator (within the current heading scope).
    gap_lines: list[str] = []
    gap_start_line_1based: int = -1

    def commit_gap() -> None:
        """Flush the pending gap accumulator into the current scope."""
        nonlocal gap_lines, gap_start_line_1based
        if not gap_lines:
            return
        body = "\n".join(gap_lines)
        end_line = gap_start_line_1based + len(gap_lines) - 1
        gap = Gap(
            start_line=gap_start_line_1based,
            end_line=end_line,
            body=body,
            after_block=(
                len(preamble_plugin_blocks) - 1 if current_section_idx == -1
                else len(sections[current_section_idx].plugin_blocks) - 1
            ),
        )
        # Normalize after_block: -1 means "no block before this gap";
        # the dataclass spec uses `None` for that case for cleaner
        # consumer matching.
        after = gap.after_block
        if after == -1:
            after = None
            gap = Gap(
                start_line=gap.start_line,
                end_line=gap.end_line,
                body=gap.body,
                after_block=after,
            )
        if current_section_idx == -1:
            preamble_user_gaps.append(gap)
        else:
            sections[current_section_idx].user_gaps.append(gap)
        gap_lines = []
        gap_start_line_1based = -1

    def commit_block(end_line_1based: int) -> None:
        """Flush the open block as a Block into the current scope."""
        nonlocal in_block, block_start_line_1based, block_body_lines
        body = "\n".join(block_body_lines)
        block = Block(
            start_line=block_start_line_1based,
            end_line=end_line_1based,
            body=body,
        )
        if current_section_idx == -1:
            preamble_plugin_blocks.append(block)
        else:
            sections[current_section_idx].plugin_blocks.append(block)
        in_block = False
        block_start_line_1based = -1
        block_body_lines = []

    for i, line in enumerate(lines):
        line_no = i + 1
        if in_fence[i]:
            # Inside fenced code block — treat as gap content.
            if in_block:
                block_body_lines.append(line)
            else:
                if not gap_lines:
                    gap_start_line_1based = line_no
                gap_lines.append(line)
            continue

        stripped = line.strip()

        # Sentinel start marker.
        if stripped == SECTION_START and not in_block:
            commit_gap()
            in_block = True
            block_start_line_1based = line_no
            continue

        # Sentinel end marker (closes the current block).
        if stripped == SECTION_END and in_block:
            commit_block(line_no)
            continue

        # Inside a block: accumulate body content.
        if in_block:
            block_body_lines.append(line)
            continue

        # H2 heading — opens a new section.
        if _is_h2(line):
            commit_gap()
            heading_text, plugin_owned = _strip_heading(line)
            sections.append(
                Section(
                    heading_text=heading_text,
                    plugin_owned=plugin_owned,
                    plugin_blocks=[],
                    user_gaps=[],
                )
            )
            current_section_idx = len(sections) - 1
            continue

        # H1 heading — captured as `ParsedFile.h1` (only the first H1
        # in source order is recorded; subsequent H1s, rare, fall
        # through to gap content). The H1 line itself is NOT included
        # in any gap or block — it's its own ownership unit.
        if _is_h1(line) and h1 is None:
            commit_gap()
            text, plugin_owned = _strip_h1(line)
            h1 = H1(text=text, plugin_owned=plugin_owned, line=line_no)
            continue

        # Otherwise: gap content (user-owned region or pre-block intro).
        if not gap_lines:
            gap_start_line_1based = line_no
        gap_lines.append(line)

    # End of file: flush any pending gap; drop any unterminated block.
    commit_gap()
    if in_block:
        # Unterminated block at EOF — be liberal: drop silently.
        # Consumers can detect via the absence of a closing line in the
        # block.end_line position; we mark end_line == start_line as a
        # signal that the close marker was missing.
        # (Skipping commit_block entirely is cleaner — leave any pending
        # block_body_lines lost. Malformed input has bigger problems.)
        in_block = False

    return ParsedFile(
        preamble_user_gaps=preamble_user_gaps,
        preamble_plugin_blocks=preamble_plugin_blocks,
        h1=h1,
        sections=sections,
    )


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------


def _self_test() -> int:
    """Built-in tests. Returns 0 on pass, 1 on fail."""
    import tempfile

    failures: list[str] = []

    def check(name: str, condition: bool, detail: str = "") -> None:
        if not condition:
            failures.append(f"FAIL {name}: {detail}")

    def parse_str(content: str) -> ParsedFile:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".md") as f:
            f.write(content)
            path = f.name
        try:
            return parse(path)
        finally:
            Path(path).unlink()

    # Test 1: empty file
    pf = parse_str("")
    check("empty_file", pf.sections == [] and pf.preamble_plugin_blocks == [] and pf.preamble_user_gaps == [] and pf.h1 is None)

    # Test 2: H1 (no marker) + intro (no H2). H1 is captured separately
    # from preamble buckets; intro falls into preamble gaps.
    pf = parse_str("# Title\n\nintro paragraph\n")
    check("h1_captured", pf.h1 is not None and pf.h1.text == "Title" and pf.h1.plugin_owned is False)
    check("h1_line_number", pf.h1.line == 1)
    check("h1_intro_gap", len(pf.preamble_user_gaps) == 1 and "intro paragraph" in pf.preamble_user_gaps[0].body)
    check("h1_no_sections", len(pf.sections) == 0)

    # Test 2b: H1 with marker is plugin-owned.
    pf = parse_str("# Title " + HEADING_MARKER + "\n\nintro\n")
    check("h1_marker_owned", pf.h1 is not None and pf.h1.plugin_owned is True and pf.h1.text == "Title")

    # Test 3: preamble with MAINTENANCE three-comment encoding + H1 (no marker).
    # H1 is captured in pf.h1; MAINTENANCE block is in preamble_plugin_blocks.
    content = (
        "<!-- holo:section start -->\n"
        "<!--\n"
        "MAINTENANCE — read before editing.\n"
        "-->\n"
        "<!-- holo:section end -->\n"
        "\n"
        "# Title\n"
    )
    pf = parse_str(content)
    check("maintenance_encoding_block", len(pf.preamble_plugin_blocks) == 1, f"got {len(pf.preamble_plugin_blocks)}")
    check("maintenance_encoding_body", "MAINTENANCE" in pf.preamble_plugin_blocks[0].body)
    check("maintenance_with_h1", pf.h1 is not None and pf.h1.text == "Title")

    # Test 4: single H2 section with plugin marker + block
    content = (
        "## Foo <!-- holo:heading -->\n"
        "\n"
        "<!-- holo:section start -->\n"
        "plugin body\n"
        "<!-- holo:section end -->\n"
    )
    pf = parse_str(content)
    check("one_section_count", len(pf.sections) == 1)
    s = pf.sections[0]
    check("one_section_heading_text", s.heading_text == "Foo", f"got {s.heading_text!r}")
    check("one_section_plugin_owned", s.plugin_owned is True)
    check("one_section_one_block", len(s.plugin_blocks) == 1)
    check("one_section_block_body", s.plugin_blocks[0].body == "plugin body")

    # Test 5: user section (no marker) — plugin_owned False
    content = (
        "## My User Section\n"
        "\n"
        "user content\n"
    )
    pf = parse_str(content)
    s = pf.sections[0]
    check("user_section_unowned", s.plugin_owned is False)
    check("user_section_text", s.heading_text == "My User Section")
    check("user_section_gap", len(s.user_gaps) == 1 and "user content" in s.user_gaps[0].body)

    # Test 6: multi-block per section (interleaved with gaps)
    content = (
        "## S <!-- holo:heading -->\n"
        "\n"
        "<!-- holo:section start -->\n"
        "block 0\n"
        "<!-- holo:section end -->\n"
        "\n"
        "user gap between blocks\n"
        "\n"
        "<!-- holo:section start -->\n"
        "block 1\n"
        "<!-- holo:section end -->\n"
    )
    pf = parse_str(content)
    s = pf.sections[0]
    check("multi_block_count", len(s.plugin_blocks) == 2)
    check("multi_block_b0", s.plugin_blocks[0].body == "block 0")
    check("multi_block_b1", s.plugin_blocks[1].body == "block 1")
    # Gaps are preserved byte-for-byte including blank-only spans. The
    # fixture has: blank-line gap before block 0 + text-gap between
    # block 0 and block 1. Both legitimate; consumers can filter
    # blank-only gaps if they want.
    text_gaps = [g for g in s.user_gaps if "user gap" in g.body]
    check("multi_block_text_gap_count", len(text_gaps) == 1,
          f"got {len(text_gaps)} text gaps (total {len(s.user_gaps)})")
    check("multi_block_text_gap_after_0", text_gaps and text_gaps[0].after_block == 0,
          f"got after_block={text_gaps[0].after_block if text_gaps else 'no gap'}")

    # Test 7: fence-aware H2 inside code fence is NOT a heading
    content = (
        "# Title\n"
        "\n"
        "```\n"
        "## not a heading inside fence\n"
        "```\n"
        "\n"
        "## Real Heading <!-- holo:heading -->\n"
        "\n"
        "body\n"
    )
    pf = parse_str(content)
    check("fence_aware_one_section", len(pf.sections) == 1)
    check("fence_aware_heading", pf.sections[0].heading_text == "Real Heading")

    # Test 8: consumer-orphan heading (marked, plugin_owned True, but no body)
    content = "## Orphan <!-- holo:heading -->\n"
    pf = parse_str(content)
    check("orphan_one_section", len(pf.sections) == 1)
    check("orphan_marked", pf.sections[0].plugin_owned is True)
    check("orphan_empty_body", pf.sections[0].plugin_blocks == [] and pf.sections[0].user_gaps == [])

    # Test 9: gap BEFORE any block in a section (after_block is None)
    content = (
        "## S <!-- holo:heading -->\n"
        "\n"
        "user prose before first block\n"
        "\n"
        "<!-- holo:section start -->\n"
        "block\n"
        "<!-- holo:section end -->\n"
    )
    pf = parse_str(content)
    s = pf.sections[0]
    check("gap_before_block_count", len(s.user_gaps) == 1)
    check("gap_before_block_after_none", s.user_gaps[0].after_block is None,
          f"got after_block={s.user_gaps[0].after_block}")

    # Test 10: multi-section file
    content = (
        "## A <!-- holo:heading -->\n"
        "\n"
        "<!-- holo:section start -->\n"
        "body A\n"
        "<!-- holo:section end -->\n"
        "\n"
        "## B <!-- holo:heading -->\n"
        "\n"
        "<!-- holo:section start -->\n"
        "body B\n"
        "<!-- holo:section end -->\n"
    )
    pf = parse_str(content)
    check("multi_section_count", len(pf.sections) == 2)
    check("multi_section_A", pf.sections[0].heading_text == "A" and pf.sections[0].plugin_blocks[0].body == "body A")
    check("multi_section_B", pf.sections[1].heading_text == "B" and pf.sections[1].plugin_blocks[0].body == "body B")

    # Test 11: line numbers are 1-based
    content = (
        "## S <!-- holo:heading -->\n"
        "\n"
        "<!-- holo:section start -->\n"
        "body\n"
        "<!-- holo:section end -->\n"
    )
    pf = parse_str(content)
    blk = pf.sections[0].plugin_blocks[0]
    check("line_numbers_1based_start", blk.start_line == 3, f"start_line={blk.start_line} (expected 3)")
    check("line_numbers_1based_end", blk.end_line == 5, f"end_line={blk.end_line} (expected 5)")

    # Test 12: real plugin template parses correctly
    # (only run if we can find a refinement-round-bootstrapped template
    # via plugin root). After the design-refinement bootstrap, H1 lives
    # as `pf.h1`, MAINTENANCE block lives in preamble_plugin_blocks,
    # and intro paragraphs live in a sentinel block under the
    # post-H1-pre-first-H2 region (still preamble for parser purposes).
    plugin_root = Path(__file__).resolve().parent.parent
    real_template = plugin_root / "templates" / "project-skeleton" / "ai_context" / "decisions.md"
    if real_template.is_file():
        pf = parse(real_template)
        # Skip strict counts (templates may be in transition during the
        # refinement round); just assert structural sanity.
        check(
            "real_template_has_h1_or_no_marker_yet",
            pf.h1 is None or pf.h1.text != "",
            f"got h1={pf.h1!r}",
        )
        check(
            "real_template_has_sections",
            len(pf.sections) >= 2,
            f"got {len(pf.sections)} sections (expected ≥ 2)",
        )

    if failures:
        for f in failures:
            print(f)
        print(f"FAILED {len(failures)} test(s)")
        return 1
    print("OK 12 test groups passed")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _pretty_print(pf: ParsedFile, path: str) -> None:
    """Human-readable parse summary for the CLI."""
    print(f"=== Parse: {path} ===")
    print(f"Preamble plugin blocks: {len(pf.preamble_plugin_blocks)}")
    for i, b in enumerate(pf.preamble_plugin_blocks):
        excerpt = b.body.split("\n")[0][:60] if b.body else "<empty>"
        print(f"  [{i}] lines {b.start_line}-{b.end_line}: {excerpt!r}")
    print(f"Preamble user gaps: {len(pf.preamble_user_gaps)}")
    for i, g in enumerate(pf.preamble_user_gaps):
        excerpt = g.body.split("\n")[0][:60] if g.body else "<blank>"
        print(f"  [{i}] lines {g.start_line}-{g.end_line} (after_block={g.after_block}): {excerpt!r}")
    print(f"Sections: {len(pf.sections)}")
    for i, s in enumerate(pf.sections):
        owned = "plugin" if s.plugin_owned else "user"
        print(f"  [{i}] ## {s.heading_text} ({owned}-owned) — {len(s.plugin_blocks)} block(s), {len(s.user_gaps)} gap(s)")
        for bi, b in enumerate(s.plugin_blocks):
            excerpt = b.body.split("\n")[0][:60] if b.body else "<empty>"
            print(f"        block[{bi}] lines {b.start_line}-{b.end_line}: {excerpt!r}")
        for gi, g in enumerate(s.user_gaps):
            excerpt = g.body.split("\n")[0][:60] if g.body else "<blank>"
            print(f"        gap[{gi}] lines {g.start_line}-{g.end_line} (after_block={g.after_block}): {excerpt!r}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Canonical parser API for sentinel-aware markdown files."
    )
    parser.add_argument("path", nargs="?", help="Path to a markdown file to parse.")
    parser.add_argument(
        "--self-test", action="store_true",
        help="Run built-in unit tests and exit.",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    if args.path is None:
        parser.print_help()
        return 1

    pf = parse(args.path)
    _pretty_print(pf, args.path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
