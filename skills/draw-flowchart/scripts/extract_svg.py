#!/usr/bin/env python3
"""Convert a draw-flowchart HTML source file to a standalone .svg deliverable.

Usage:
    extract_svg.py <input.html> [<output.svg>]
    extract_svg.py --refresh-examples         # rebuild the 3 preset examples

The HTML has <style> in <head> + <svg> in <body>. For standalone .svg, we
move the <style> INTO the <svg> (wrapped in CDATA so any `&` / `<` inside
CSS comments / @import URLs don't trip XML parsing), and we add a background
rect that fills the entire viewBox (the HTML's body background isn't
available in standalone SVG).
"""
import re
import sys
from pathlib import Path


def extract(html_path: Path, svg_path: Path) -> None:
    html = html_path.read_text()

    # Extract the <style>...</style> block from <head>
    style_match = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
    if not style_match:
        sys.exit(f"no <style> in {html_path}")
    css = style_match.group(1).strip()

    # Drop html/body rules (no html/body in standalone SVG)
    css = re.sub(r"html, body \{[^}]*\}\s*", "", css)
    css = re.sub(r"body \{[^}]*\}\s*", "", css)
    css = re.sub(r"\.diagram \{[^}]*\}\s*", "", css)
    css = re.sub(r"svg \{[^}]*\}\s*", "", css)

    # The HTML version sets font-family on body. Dropping body removes that
    # inheritance, so SVG <text> elements fall back to the browser default
    # (serif on most platforms). Add an explicit rule for ALL text in the SVG
    # so it inherits the var(--font) stack.
    css = (
        "text { font-family: var(--font); }\n"
        + css
    )

    # Prepend Google Fonts @import (SVG can't use <link>; @import works in <style>).
    # Raw `&` is fine here because the whole CSS is wrapped in CDATA below.
    css = (
        '@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap");\n'
        + css
    )

    # Extract <svg>...</svg> block
    svg_match = re.search(r"(<svg[^>]*>)(.*?)(</svg>)", html, re.DOTALL)
    if not svg_match:
        sys.exit(f"no <svg> in {html_path}")
    svg_open, svg_inner, svg_close = svg_match.groups()

    # Build standalone SVG. Wrap CSS in CDATA so any "&" / "<" inside CSS
    # comments or selectors won't be parsed as XML entities.
    standalone = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f"{svg_open}\n"
        '  <style type="text/css"><![CDATA[\n'
        f"{css}\n"
        "]]></style>\n"
        '  <rect width="100%" height="100%" fill="var(--bg)" />\n'
        f"{svg_inner}\n"
        f"{svg_close}\n"
    )

    svg_path.write_text(standalone)
    print(f"wrote {svg_path}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--refresh-examples"]:
        examples = Path(__file__).resolve().parent.parent / "examples"
        for name in ("light", "dark", "mono-print", "bridge-crossover", "fan-in-out", "content-card"):
            extract(examples / f"{name}.html", examples / f"{name}.svg")
    elif len(args) in (1, 2):
        html = Path(args[0])
        svg = Path(args[1]) if len(args) == 2 else html.with_suffix(".svg")
        extract(html, svg)
    else:
        sys.exit(__doc__)
