---
name: draw-flowchart
description: Draw Anthropic-style sequential flowcharts / pipeline / process diagrams as standalone SVG / PNG / HTML. Use when the user asks for flowcharts, flow diagrams, pipeline diagrams, agentic-loop diagrams, process diagrams, workflow visualizations, or state-machine diagrams. Three themes — `light` (default, cream + sage), `dark` (Cocoon-inspired slate-950), `mono-print`. NOT for architecture / network topology (use `architecture-diagram`), UML, gantt, org charts.
---

# Flowchart Skill

Draw polished, minimalist flowcharts as standalone SVG (PNG / HTML on request). The visual language is locked — every constant below is mandatory. Improvising is what causes diagram drift across iterations.

The skill writes an HTML intermediate (CSS-in-`<head>` + inline `<svg>` in `<body>` — easier to edit), then **extracts a standalone `.svg`** as the deliverable. The user receives the `.svg`; the `.html` is a temp source that may be kept for re-editing. PNG is **only** used as a temporary raster for subagent visual review (Read tool needs raster) and is deleted after review.

## Design System

### Color Palette

There are **6 node roles** and **3 edge styles**. Roles are deliberately FEW so the diagram doesn't fragment into a rainbow of categories. Most slash commands / steps / functions / actions in any project map to a single `action` color; visual differentiation comes from *shape semantics* (border / no-border), not by sub-categorizing actions.

| Role | Meaning | Project mapping examples |
|---|---|---|
| **action** | Any process step / command / function (the verbs). Decisions, reviews, gates, inventory readers all collapse into action — the topology (multiple labeled outgoing edges) conveys decision semantic, not color. | holo's `/go`, `/post-check`, `/fix`, `/todo`, `/full-review`, `/check-review` — all action |
| **agent** | External person / runtime / sub-agent that participates in but is not OF the flow | holo's `claude`, `codex`; "user", "GitHub webhook", "developer" |
| **terminal** | Entry / exit marker | "Your prompt", "Done", "cart", "delivered" |
| **data** | Persisted info — file / DB / log / queue (always with a border to distinguish from process boxes) | holo's `todo_list`, `logs/change_logs`, `ai_context + docs` |
| **state** | Outcome marker (success / fail / paused — terminal status with sage tint) | holo's `pass`; CI's "green" |
| **callout** | User-interrupt / out-of-band annotation (orange border) | "user can interrupt", "manual override" |

#### Palette — `light` (default, warm earthy)

| Token | Hex | Use |
|---|---|---|
| `--bg` | `#F0EEE6` | Page (Anthropic Bone) |
| `--text` | `#404442` | Primary node text — **deep warm grey, NEVER pure black** |
| `--label-text` | `#6B6E64` | Edge / container / legend text |
| `--action-fill` | `#D5E4CE` | sage — action role (most nodes use this) |
| `--agent-fill` | `#EFE6D2` | cream — agent role |
| `--terminal-fill` | `#E5E1D6` | warm grey — terminal role |
| `--data-fill` / `--data-stroke` | `#ECE7D6` / `#B8AE93` | warm beige + 2px border — data role |
| `--state-fill` / `--state-stroke` | `#DCEAD5` / `#8FB585` | pale sage + 2px sage border — state role |
| `--callout-fill` / `--callout-stroke` / `--callout-text` | `#FBF8EE` / `#D89270` / `#B26C3F` | cream + 2px orange border + orange text |
| `--flow-line` | `#6A6F66` | default forward-flow arrow stroke — **soft warm grey, distinctly NOT black** |
| `--flow-loopback` | `#8FB585` | sage — loop-back / return arrow stroke |
| `--container` / `--container-lbl` | `#B5B2A8` / `#6E6B62` | dashed container border + label |

#### Palette — `dark` (Cocoon-inspired)

Deep slate-950 background with bright accent borders. All roles carry a border in dark mode (semi-transparent fills require edge definition).

| Token | Hex | Use |
|---|---|---|
| `--bg` | `#020617` | slate-950 (deepest) |
| `--text` | `#E2E8F0` | slate-200 — primary text, soft (NOT pure white) |
| `--label-text` | `#94A3B8` | slate-400 — secondary text |
| `--action-fill` / `--action-stroke` | `rgba(6,78,59,0.4)` / `#34D399` | emerald-400 — action role (matches Cocoon "Backend") |
| `--agent-fill` / `--agent-stroke` | `rgba(8,51,68,0.4)` / `#22D3EE` | cyan-400 — agent role (matches Cocoon "Frontend") |
| `--terminal-fill` / `--terminal-stroke` | `rgba(30,41,59,0.5)` / `#94A3B8` | slate-400 — terminal role (matches Cocoon "External") |
| `--data-fill` / `--data-stroke` | `rgba(76,29,149,0.4)` / `#A78BFA` | violet-400 — data role (matches Cocoon "Database") |
| `--state-fill` / `--state-stroke` | `rgba(120,53,15,0.4)` / `#FBBF24` | amber-400 — state role (matches Cocoon "AWS" — success "gold") |
| `--callout-fill` / `--callout-stroke` / `--callout-text` | `rgba(251,146,60,0.25)` / `#FB923C` / `#FDBA74` | orange-400 — callout (matches Cocoon "Message Bus") |
| `--flow-line` | `#94A3B8` | slate-400 |
| `--flow-loopback` | `#34D399` | emerald-400 |
| `--container` / `--container-lbl` | `#475569` / `#94A3B8` | slate-600 dashed + slate-400 label |

#### Palette — `mono-print` (B&W)

| Token | Hex | Use |
|---|---|---|
| `--bg` | `#FFFFFF` | white |
| `--text` | `#1A1A1A` | near-black |
| `--label-text` | `#555555` | mid-grey |
| `--action-fill` | `#D8D8D8` | medium grey |
| `--agent-fill` | `#ECECEC` | pale grey |
| `--terminal-fill` | `#E5E5E5` | very light grey |
| `--data-fill` / `--data-stroke` | `#F2F2F2` / `#888888` | white + grey border |
| `--state-fill` / `--state-stroke` | `#DCDCDC` / `#555555` | light grey + mid border |
| `--callout-fill` / `--callout-stroke` / `--callout-text` | `#FFFFFF` / `#1A1A1A` / `#1A1A1A` | white + black border |
| `--flow-line` | `#3A3A3A` | softer near-black |
| `--flow-loopback` | `#555555` | mid-grey |
| `--container` / `--container-lbl` | `#888888` / `#555555` | mid-grey |

### Typography

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
```

Stack: `"Inter", "Söhne", -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif`

| Role | Size | Weight | Fill |
|---|---|---|---|
| Diagram title | 19px | 600 | `--text` |
| **Node label** (main) | **18px** | **700** | `--text` |
| **Node sublabel** (optional, when context disambiguation adds value) | **12px** | **500** | `--label-text` |
| Container label (e.g., "agentic loop") | 16px | 500 | `--container-lbl` |
| Edge label | 13px | 500 | `--label-text` |
| Callout label (user-interrupt) | **18px** | 500 | `--callout-text` |
| Legend item label | 12px | 500 | `--label-text` |

**CRITICAL — Node labels are uniformly 18px.** If text overflows the box, **widen the box**, NEVER shrink the font.

### Visual Elements

#### Background

Solid `var(--bg)`. No grid. No gradient.

#### Node shapes — rounded rect ONLY

Every role uses the same shape: rounded rectangle with `rx="12"`. NEVER use circles, cylinders, ellipses, pills, diamonds, hexagons.

**Two heights**:
- **60px** — single-line nodes (default)
- **80px** — node with main label + sublabel (Cocoon-style title+description). Use only when context adds value.

**Border policy**:

| Theme | action / agent / terminal | data / state / callout |
|---|---|---|
| `light` | no border | 2px solid `--*-stroke` |
| `dark` | 1.4px `--*-stroke` (all roles bordered) | 2px `--*-stroke` |
| `mono-print` | no border | 2px solid `--*-stroke` |

Width = enough to fit text at 18px with **≥30px padding each side**: `max(120, ceil((text_pixels + 60) / 20) * 20)`.

#### Same-role alignment (CRITICAL)

When two or more nodes of the **same role** appear in the diagram (e.g., 3 data stores; 2 agents), they MUST visually align:

- **Same width** when their labels permit. If `data1` has a 5-char label and `data2` has a 20-char label, you can't force same width — but if both labels fit in 200px, use 200px for both, NOT 140 and 200.
- **Same center-x** when stacked in a column.
- **Same y** when on the same row.

**Wrong:** `todo_list` at x=40 w=180 next to `todo_list_archived` at x=20 w=260 — different widths AND different left edges → reads as misaligned.
**Right:** Both at width 260, both with center-x=150 → visually aligned column.

#### Container fit (CRITICAL)

When a `container` wraps a subset of nodes (e.g., "agentic loop" enclosure), the container's bounding rect MUST fully enclose every contained node with ≥30px padding on each side. A container whose right edge cuts through a contained node is a **glaring visual bug** that subagents have missed in past iterations.

**Wrong:** Container at `x=240 width=800` (right edge x=1040) when contained nodes extend to x=1070 — container right edge cuts through the last node.
**Right:** Container at `x=240 width=880` (right edge x=1120) — fully encloses nodes ending at x=1070 with 50px padding.

#### Loopback origin alignment (CRITICAL)

A loop-back arrow's start point and end point MUST be at the EXACT geometric center of the source node's bottom edge and the destination node's bottom edge respectively. Off-center origins (even by 5-25px) look amateurish — they're the result of misreading box coordinates.

**Wrong:** Loopback exits `Verify results` (x=850, w=220, center=960) at `x=935` — that's 25px off-center. Subtle, but visible.
**Right:** Loopback exits at `x=960` exactly.

#### Arrows — fixed-size markers + line-ends-at-triangle-TAIL

```svg
<marker id="arrow-flow" viewBox="0 0 14 12" refX="0" refY="6"
        markerWidth="14" markerHeight="12"
        markerUnits="userSpaceOnUse" orient="auto">
  <path d="M 0 0 L 14 6 L 0 12 z" />
</marker>
```

**CRITICAL — `markerUnits="userSpaceOnUse"` is mandatory.**

**CRITICAL — `refX=0` is mandatory** (NOT refX=11 or refX=9 or any other). With refX=0, the triangle's BASE sits exactly at the line endpoint, and the triangle extends 14 units past the endpoint to the apex. The line CONNECTS to the triangle's tail; line does NOT pass through the triangle interior.

**Wrong:** `refX="9"` (or "11", "13") — the line endpoint lands deep inside the triangle, so the line OVERLAPS the triangle interior, making the arrowhead look like a tiny spike on top of the line. Square/fat triangles compound this into a "bulge".
**Right:** `refX="0"` — the line stops AT the triangle base; the triangle is a clearly distinct visual element that EXTENDS FORWARD from the line.

**Triangle size:** 14 wide × 12 tall on 4px stroke = 3× stroke height. Big enough to read as a discrete arrow, NOT a tiny spike.

**Stroke widths** (bumped 1.5× from prior to give main flow proper visual weight):

| Arrow type | Stroke | Color | Pattern |
|---|---|---|---|
| Default forward flow | **4px** | `--flow-line` (soft grey) | solid |
| Loop-back / return | **5px** | `--flow-loopback` (sage) | solid |
| Conditional / optional / skip | **3px** | `--flow-line` | dashed `7 5` |
| Callout (user-interrupt) | **3px** | `--callout-stroke` (orange) | dashed `7 5` |

**Arrow tip placement** (with `refX=0`). The triangle extends **14 user units past the line endpoint** in the path direction. For the tip to land EXACTLY on the destination box edge:

- **Rightward arrow → box left edge x=A:** `line_endpoint_x = A − 14`
- **Leftward arrow → box right edge x=A:** `line_endpoint_x = A + 14`
- **Downward arrow → box top edge y=A:** `line_endpoint_y = A − 14`
- **Upward arrow → box bottom edge y=A:** `line_endpoint_y = A + 14`

The visible line stops 14 units short of the destination edge; the triangle fills that gap; the apex touches the edge cleanly.

**Wrong:** `<line x2="319" />` for a rightward arrow into a box left edge x=320 — with the refX=0 marker, the triangle extends from x=319 to x=333, **tip 13px PAST the destination edge** (overshoots into the box).
**Right:** `<line x2="306" />` — line stops at 306; triangle fills 306–320; tip lands exactly on x=320 (box's left edge).

#### Line origin from box center (CRITICAL)

Arrows MUST originate from the **geometric center** of the source box's edge — not from corners or arbitrary offsets.

- One arrow leaving the bottom of a node → origin at `(x_center, y_bottom)`.
- Two arrows leaving the bottom → use a **shared trunk** pattern: both arrows start at `(x_center, y_bottom)` and share the first 30-40px vertical segment before diverging:
  ```svg
  <!-- shared trunk visible as a single line -->
  <line class="flow-arrow" x1="x_center" y1="y_bottom" x2="x_center" y2="y_bottom+30" />
  <!-- branch 1 continues from trunk end -->
  <path class="flow-arrow" d="M x_center,y_bottom+30  ... → target1" />
  <!-- branch 2 continues from trunk end -->
  <path class="flow-arrow" d="M x_center,y_bottom+30  ... → target2" />
  ```
- Two arrows from corners (x=left+10 and x=right−10) is **WRONG** — looks lazy and unaligned.

**Wrong:** `/go` (x=440–540, center=490) sends one arrow down from (478, 140) and another from (520, 140) — neither at center, looks like two corners.
**Right:** Both arrows leave (490, 140), share a 30px trunk to (490, 170), then diverge.

#### Edge labels — consistent placement (CRITICAL)

All edge labels follow the **same rule**: centered on the **midpoint of the longest segment** of the edge, **OFFSET from the line** — above for horizontals, right for verticals. NEVER on the line itself.

**Why off-line, not on-line:** an on-line label with bg cutout works for long arrows but **silently consumes short arrows** (the cutout is wider than the arrow, the arrow disappears under the cutout). Offset labels never have this failure mode.

```svg
<g transform="translate(MIDPOINT_X, MIDPOINT_Y_OFFSET)">
  <rect class="edge-label-bg" x="-(TEXT_W/2 + 3)" y="-9" width="(TEXT_W + 6)" height="18" />
  <text class="edge-label" text-anchor="middle" y="4">label</text>
</g>
```

**Computing position**:
- **Horizontal segment** `(x1,y) → (x2,y)`: text-anchor = `middle`, position = `(midpoint_x, y - 14)`. Cutout = `x="-(W/2+3)" width="(W+6)"`.
- **Vertical segment** `(x,y1) → (x,y2)`: text-anchor = `start`, position = `(x + 6, midpoint_y)`. Cutout = `x="-3" width="(W+6)"`. Critical: `text-anchor="start"` (NOT middle) so the cutout extends RIGHT from the arrow line and never overlaps it.
- **L-shaped path**: pick the LONGEST of the two segments and use its offset midpoint.

**Arrow-length sanity check**: before placing a horizontal label, ensure `label_width + 6 < arrow_length`. If not, EXTEND the arrow (push target node further away) — do not shrink the label.

**Cutout rect** is small (text width + 6px breathing room) and protects text legibility. With offset positioning + correct text-anchor, the cutout never overlaps any arrow line.

**Wrong:** "narrative" label at midpoint `(640, 110)` on the line — cutout 72px wide covers the entire 59px-long arrow.
**Right:** "narrative" label at `(640, 96)` — 14px above the line. Arrow remains fully visible.

#### Container (optional, for enclosing a sub-flow)

```svg
<g class="container">
  <rect class="container-box" x="..." y="..." rx="20" />
  <rect class="container-gap" x="..." y="..." />  <!-- breaks dashed border for label -->
  <text class="container-label" ...>agentic loop</text>
</g>
```

CSS:
```css
.container-box   { fill: none; stroke: var(--container); stroke-width: 2; stroke-dasharray: 6 6; }
.container-gap   { fill: var(--bg); }
.container-label { font-weight: 500; font-size: 16px; fill: var(--container-lbl); }
```

#### Callout (user-interrupt) — orthogonal single-elbow arrow

The callout box sits OUTSIDE any container. **Box height = 60px** (same as all other nodes — uniform). **Label = 18px medium weight, single line** (NOT multi-line; widen the box to fit the text instead).

The arrow from callout box to the loop area is a **single orthogonal elbow** — RIGHT then UP, with ONE rounded corner. NO curves, NO Z-shapes, NO multiple bends.

**Connection points** (CRITICAL):
- **Start**: callout box **RIGHT-CENTER edge** (x = callout_right, y = callout_y_center)
- **End**: container **BOTTOM-CENTER edge** (x = container_x_center, y = container_bottom)
- **Bend**: at `(end_x, start_y)` — one corner, rounded with r=12

```svg
<g class="callout">
  <rect class="callout-box" x="20" y="240" width="380" height="60" rx="12" />
  <text class="callout-label" x="210" y="277" text-anchor="middle">You: interrupt, steer, or add context</text>

  <!-- Single-elbow orthogonal: RIGHT from callout right-center, then UP to container bottom-center.
       Start (400, 270) = callout right-edge, vertical center.
       Bend (680, 270) = corner.
       End line_endpoint (680, 224) → tip at (680, 210) = container bottom-center. -->
  <path class="callout-arrow"
        d="M 400,270
           L 668,270 Q 680,270 680,258
           L 680,224"
        marker-end="url(#arrow-callout)" />
</g>
```

**Wrong:** Multi-line callout text in an 80px-tall box — breaks uniform 60px node height.
**Wrong:** Curved cubic Bezier — looks loose / hand-drawn, inconsistent with the orthogonal flow arrows.
**Wrong:** Z-elbow with multiple bends — clunky.
**Wrong:** Connecting from callout TOP edge or from arbitrary middle of container — should be RIGHT-CENTER to BOTTOM-CENTER.
**Right:** 60px-tall callout with single-line 18px text; single elbow from callout right-center to container bottom-center; one rounded corner at the bend.

### Spacing Rules

| Constant | Value |
|---|---|
| Node height | 60px (single) / 80px (with sublabel) |
| Node corner radius (rx) | 12px (container uses 20px) |
| Min horizontal gap on same row | 60px |
| Min vertical gap between rows | 120px |
| Container inner padding | 50px sides, 60px top/bottom |
| Legend gap from diagram content | 30px |
| **SVG viewBox padding** (around all content) | **20px on EVERY side** |
| Legend swatch size | 22px wide × 12px tall |

**ViewBox padding symmetry rule (CRITICAL)**: top padding (`min_content_y`) and bottom padding (`viewBox_height − max_content_y`) MUST be equal — both 20px. Asymmetric padding (e.g., 20px top + 70px bottom) reads as visually unbalanced and "framed wrong" when embedded in a doc.

**Wrong:** viewBox y=0 to y=410, content y=20 to y=320, legend y=365 → top padding 20, bottom padding 410-377=33. Asymmetric.
**Right:** viewBox y=0 to y=400, content y=20 to y=320, legend y=365 → top padding 20, bottom padding 400-377=23 ≈ 20. Symmetric.

**Legend completeness rule**: BEFORE finalizing viewBox height, compute legend dimensions:
- Legend total width ≈ `sum(swatch_22 + gap_8 + text_width + spacing_24) for each role`
- Legend height ≈ 16px (single-row swatch + text)
- Legend bottom y = content bottom y + 30 (gap)
- ViewBox height must extend to `legend_bottom_y + 20` (padding)
- Render window height must be `viewBox height + 32` (body padding margin)

**Wrong:** viewBox y=400, legend at y=390, render window 432px — legend gets clipped to 8px visible.
**Right:** viewBox y=460, legend at y=425, render window 492px — legend fully visible.

### Routing Rules (CRITICAL)

**All edges are orthogonal — NO EXCEPTIONS.** Every segment is horizontal or vertical. Corners are rounded arcs with **r=12**. NO diagonals. NO cubic bezier curves.

Corner pattern: `... L cx,(cy-12) Q cx,cy (cx+12),cy L ...`

**Crossing avoidance is mandatory.** Reposition nodes to free routing channels rather than letting edges cross. Use diagram perimeter (top/bottom/left/right gutters) for long routes.

### Z-order (back to front)

1. Container
2. Loop-back / return arrows (behind nodes)
3. Forward flow arrows
4. Callout arrow
5. Edge labels (bg cutout interrupts arrows visually)
6. Nodes (rects)
7. Node labels (text)
8. Legend

### Legend — inside SVG with project-aware names

Place inside the SVG at the bottom-left. Use the project's domain vocabulary for each role label, NOT the generic role token name.

- `--agent-fill` swatch → label = "agent" for AI runtimes; "user" for human actors; "service" for microservices. Pick what reads naturally.
- `--data-fill` swatch → "data store"; "log"; "queue"; "database". Pick what reads naturally.
- `--action-fill` swatch → "command", "step", "process", "slash command". Pick what reads naturally for the project.

Include ONLY the roles actually used. Skip swatches that don't appear in the diagram.

```svg
<g class="legend" transform="translate(40, LEGEND_Y)">
  <g transform="translate(0, 0)">
    <rect width="22" height="12" rx="3" fill="var(--action-fill)" />
    <text x="30" y="10" class="legend-label">command</text>  <!-- project-aware label -->
  </g>
  <!-- ... -->
</g>
```

## Layout Reasoning (CRITICAL — think BEFORE placing nodes)

13-point checklist (mostly unchanged from prior; alignment & origin are emphasized):

1. **Dominant flow direction** — pick one (LTR or TTB), don't mix.
2. **Entry on natural side** — left for LTR, top for TTB.
3. **Exit on opposite side.**
4. **Same-role clustering** — group same-role nodes when meaningful.
5. **Critical path on main spine.**
6. **Side branches subordinate to spine.**
7. **Parallel tracks aligned to reveal parallelism.**
8. **Loop-back arrows SHORT** — reposition source/dest if loopback would snake.
9. **Side-branch destinations cluster** — if `/go` fans out to logs + archived, those 2 nodes should be visually adjacent below `/go`.
10. **Edge labels offset from line** — above horizontal segments (−14px), right of vertical segments (+6px, `text-anchor="start"`); centered on the longest segment's midpoint.
11. **Reserve gutters** — top/bottom/left/right edges of viewBox for long routes.
12. **One axis at a time** — boring orthogonal beats clever cramped.
13. **Alignment audit** — same-row Y, same-column X, same-role uniform width, line origin from box center, edge labels on midpoint.

**Same-role color assignment**: when multiple project concepts map to the same role, give them the SAME color. Do NOT sub-categorize within a role (e.g., don't split "workflow command" vs "review command" vs "inventory command" into 3 colors — they're all `action`).

**Legend label naming**: think about what the user would naturally call each role IN THIS PROJECT'S DOMAIN. For an AI agent loop, call agents "agent" not "actor". For an order pipeline, call data "order log" not "data store". The role token in CSS stays generic; the displayed legend label adapts.

**Wrong:** Default to "actor" in legend regardless of context.
**Right:** Use "agent" when nodes are AI runtimes; "user" when they're humans; "external service" when they're third-party APIs.

## Patterns (copy-paste blocks)

### Pattern — Node (no border: action / agent / terminal)

```svg
<rect x="X" y="Y" width="W" height="60" rx="12" ry="12" fill="var(--action-fill)" />
<text class="node-label" x="X+W/2" y="Y+37" text-anchor="middle">label</text>
```

### Pattern — Node (with border: data / state)

```svg
<rect class="data-rect" x="X" y="Y" width="W" height="60" rx="12" ry="12" />
<text class="node-label" x="X+W/2" y="Y+37" text-anchor="middle">label</text>
```

### Pattern — Node with sublabel (title + description)

```svg
<rect x="X" y="Y" width="W" height="80" rx="12" ry="12" fill="var(--action-fill)" />
<text class="node-label"    x="X+W/2" y="Y+33" text-anchor="middle">main label</text>
<text class="node-sublabel" x="X+W/2" y="Y+56" text-anchor="middle">brief description</text>
```

### Pattern — Forward arrow (horizontal)

`A` = source-edge x; `B` = destination-edge x. Line endpoint at `B − 14`; triangle fills the 14px gap so apex lands exactly on `B`.

```svg
<line class="flow-arrow" x1="A" y1="Y" x2="(B-14)" y2="Y" marker-end="url(#arrow-flow)" />
```

### Pattern — Forward arrow (orthogonal elbow, down→right→down)

`y2` = destination top-edge y. Final line segment ends at `y2 − 14`; triangle apex lands on `y2`.

```svg
<path class="flow-arrow"
      d="M x1,y1
         L x1,(yc-12) Q x1,yc (x1+12),yc
         L (x2-12),yc Q x2,yc x2,(yc+12)
         L x2,(y2-14)"
      marker-end="url(#arrow-flow)" />
```

### Pattern — Shared trunk fan-out (2 arrows from one node)

```svg
<!-- shared 30-40px trunk from node center, then diverge.
     target1 / target2_y are the destination box top-edge y values; line endpoints stop 14px short. -->
<line class="flow-arrow" x1="cx" y1="y_bottom" x2="cx" y2="(y_bottom+30)" />
<line class="flow-arrow" x1="cx" y1="(y_bottom+30)" x2="cx" y2="(target1-14)" marker-end="url(#arrow-flow)" />
<path class="flow-arrow"
      d="M cx,(y_bottom+30) L cx,(yc-12) Q cx,yc (cx+12),yc L (target2_x-12),yc Q target2_x,yc target2_x,(yc+12) L target2_x,(target2_y-14)"
      marker-end="url(#arrow-flow)" />
```

### Pattern — Loop-back & dashed conditional (CSS-only)

Path geometry follows §Routing Rules; only the class + marker change.

- Loop-back: `class="loopback-arrow"` + `marker-end="url(#arrow-loopback)"`. CSS: `stroke: var(--flow-loopback); stroke-width: 5; fill: none; stroke-linecap: round; stroke-linejoin: round;`
- Dashed conditional: `class="flow-arrow dashed"`. CSS: `.flow-arrow.dashed { stroke-width: 3; stroke-dasharray: 7 5; }`

### Pattern — Callout arrow (single-elbow RIGHT→UP)

Start at callout right-center, bend once at `(container_cx, callout_cy)`, end at `container_bottom − 14` (so triangle tip lands on container bottom edge).

```svg
<path class="callout-arrow"
      d="M callout_right,callout_cy
         L (container_cx - 12),callout_cy Q container_cx,callout_cy container_cx,(callout_cy - 12)
         L container_cx,(container_bottom - 14)"
      marker-end="url(#arrow-callout)" />
```

CSS: `.callout-arrow { stroke: var(--callout-stroke); stroke-width: 3; fill: none; stroke-dasharray: 7 5; stroke-linecap: round; stroke-linejoin: round; }`

### Pattern — Edge label (offset from line, centered, small bg cutout)

```svg
<!-- For horizontal segment: position 14px ABOVE the arrow -->
<g transform="translate(MIDPOINT_X, ARROW_Y - 14)">
  <rect class="edge-label-bg" x="-(W/2+3)" y="-9" width="(W+6)" height="18" />
  <text class="edge-label" text-anchor="middle" y="4">label text</text>
</g>

<!-- For vertical segment: text-anchor=start, position 6px RIGHT of arrow -->
<g transform="translate(ARROW_X + 6, MIDPOINT_Y)">
  <rect class="edge-label-bg" x="-3" y="-9" width="(W+6)" height="18" />
  <text class="edge-label" text-anchor="start" y="4">label text</text>
</g>
```

### Pattern — Marker defs (3 markers; include all)

```svg
<defs>
  <marker id="arrow-flow" viewBox="0 0 14 12" refX="0" refY="6"
          markerWidth="14" markerHeight="12"
          markerUnits="userSpaceOnUse" orient="auto">
    <path d="M 0 0 L 14 6 L 0 12 z" />
  </marker>
  <marker id="arrow-loopback" viewBox="0 0 14 12" refX="0" refY="6"
          markerWidth="14" markerHeight="12"
          markerUnits="userSpaceOnUse" orient="auto">
    <path d="M 0 0 L 14 6 L 0 12 z" />
  </marker>
  <marker id="arrow-callout" viewBox="0 0 14 12" refX="0" refY="6"
          markerWidth="14" markerHeight="12"
          markerUnits="userSpaceOnUse" orient="auto">
    <path d="M 0 0 L 14 6 L 0 12 z" />
  </marker>
</defs>
```

CSS:
```css
#arrow-flow     path { fill: var(--flow-line); }
#arrow-loopback path { fill: var(--flow-loopback); }
#arrow-callout  path { fill: var(--callout-stroke); }
```

### Pattern — In-SVG Legend (bottom-left, project-aware labels)

```svg
<g class="legend" transform="translate(40, LEGEND_Y)">
  <!-- Repeat for each role actually used; pick a domain-appropriate label -->
  <g transform="translate(0, 0)">
    <rect width="22" height="12" rx="3" fill="var(--action-fill)" />
    <text x="30" y="10" class="legend-label">slash command</text>
  </g>
  <g transform="translate(120, 0)">
    <rect width="22" height="12" rx="3" fill="var(--data-fill)" stroke="var(--data-stroke)" stroke-width="1.2" />
    <text x="30" y="10" class="legend-label">log</text>
  </g>
</g>
```

## Presets

| Preset | Background | Use when |
|---|---|---|
| `light` (default) | cream `#F0EEE6` | docs / blog / light-mode product UI |
| `dark` | slate-950 `#020617` | dark-mode UI / terminal screenshots (Cocoon-inspired) |
| `mono-print` | white | print / academic / no-color |

## Workflow

All artifacts go in `./tmp_diagram/` relative to the current working directory (project root, NOT `/tmp/`). Create the directory if it does not exist: `mkdir -p tmp_diagram`.

1. **Ask output format** (`AskUserQuestion`, single-select, 4 options in order):
   - `svg (recommended)` — standalone SVG, opens in any browser, lossless scaling
   - `png` — rasterized for chat / docs that don't accept SVG
   - `html` — editable source (CSS in `<head>`, inline SVG in `<body>`); keep for re-editing
   - `all three`

   Record the answer; it determines which files survive Step 11. The intermediate workflow always produces HTML → SVG → PNG (PNG is needed for subagent review regardless of user choice).

2. **Understand the diagram** — restate node + edge spec; ask one clarifying question if material ambiguity remains.

3. **Map domain → roles**:
   - List every node + its role (`action` / `agent` / `terminal` / `data` / `state` / `callout`)
   - **All process steps / commands → `action`**. Don't sub-categorize.
   - Decide **legend label** for each used role per project domain (e.g., "agent" for AI runtimes; "log" for log dirs).

4. **Layout reasoning** — apply 13-point checklist before writing coordinates.

5. **Generate v1 HTML** — write to `./tmp_diagram/flowchart-v1-<slug>.html` with inline SVG. Copy the chosen preset's `<style>` block verbatim from `examples/<preset>.html`.

6. **Extract v1 .svg from .html**. The HTML's `<style>` block is moved into the SVG (wrapped in CDATA), with a `var(--bg)` background rect added, and an explicit `text { font-family: var(--font); }` rule injected (otherwise SVG `<text>` elements lose the body's font inheritance and fall back to browser default — usually serif):
   ```bash
   python3 /home/leander/Leander/holo/skills/draw-flowchart/scripts/extract_svg.py \
     ./tmp_diagram/flowchart-v1-<slug>.html \
     ./tmp_diagram/flowchart-v1-<slug>.svg
   ```

7. **Render v1 to PNG** — needed for subagent review (Read tool needs raster):
   ```bash
   google-chrome --headless --disable-gpu --no-sandbox --hide-scrollbars \
     --window-size=<W>,<H> \
     --screenshot=./tmp_diagram/flowchart-v1-<slug>.png \
     "file://$(pwd)/tmp_diagram/flowchart-v1-<slug>.svg"
   ```
   `<W>` = viewBox width + 64; `<H>` = viewBox height + 32.

8. **Dispatch 3 review subagents in PARALLEL** (Visual / Logical / Requirement — see §Subagent Review Prompts). Each subagent reads the PNG.

9. **Synthesize findings** — categorize critical / important / nitpick. **Verify subagent claims against the PNG yourself** (subagents have false-positive rate ~50% on visual claims like "edge crossing"; main thread must verify with Read tool before acting on a finding).

10. **Regenerate v2** — apply real fixes (drop false positives). Write `./tmp_diagram/flowchart-v2-<slug>.html`. Re-extract SVG, re-render PNG for visual confirmation.

11. **Filter outputs per Step 1 choice + Present**:
    - `svg` only → delete `.html` and `.png` (both v1 and v2)
    - `png` only → delete `.html` and `.svg`
    - `html` only → delete `.svg` and `.png`
    - `all three` → delete only the v1 files; keep v2 `.html` + `.svg` + `.png`

    Report: kept paths, preset, node/edge counts, v1→v2 changes.

**Hard cap: 2 iterations.** No infinite loops.

## Subagent Review Prompts

### Subagent 1 — Visual Quality

```
Inputs: PNG <path>, spec /home/leander/Leander/holo/skills/draw-flowchart/SKILL.md

Use Read tool to view PNG. **ALSO Read the user's reference image if one was provided** (path will be in the task prompt) — compare diagram against reference visually.

Check per spec:
1. Edge crossings (ZERO) — trace EVERY arrow and verify
2. Node overlaps (ZERO)
3. **Container fit** — if container exists, does its bounding rect FULLY ENCLOSE all contained nodes with ≥30px padding? Look specifically for container edges cutting through nodes
4. **Arrow tip presence** — count `marker-end` references vs visible arrow triangles in PNG. If a path has marker-end but you can't see a triangle at its endpoint, it's a bug (possibly wrong path direction)
4a. **Edge-through-node collision (CRITICAL)** — for EACH arrow path, list its segments (each L between corners). For EACH segment, check if it passes through ANY node's bounding rect that isn't its source/destination. Example: if a return arrow has vertical at x=130, and a node sits at x=20-260 y=200-260, the vertical at x=130 passes through that node IF its y-range overlaps 200-260. Report every such collision.
5. Arrow tips touching destination edges (gap > 1px = fail; OR overshooting INTO box by >3px also fail)
6. Inconsistent node-label font sizes
7. Any diagonal edges or cubic curves on flow arrows (only callout may use cubic)
8. **Marker geometry** — 14×12 triangle with `refX=0` (triangle BASE at line endpoint, apex extending 14 units forward). Any `refX>0` (9/11/13) puts the line endpoint inside the triangle, making the arrowhead look like a spike on top of the line
9. Spacing anomalies (rows ≥120px, nodes ≥60px horizontal)
10. Text cut-off or overflow
11. Colors not from locked palette
12. Z-order violations
13. Legend missing OR cut off OR misplaced
14. Inconsistent corner radii
15. **ViewBox padding SYMMETRY** — top padding must equal bottom padding (both ~20px). Measure: distance from viewBox top to topmost element vs distance from bottommost element to viewBox bottom
16. **Loopback origin centers** — loopback exit/entry MUST be at exact box center-x. Measure each loopback path's start/end x against source/destination box's center-x. Off by ANY amount = fail
17. **ALIGNMENT AUDIT**: same-row Y / same-column X / same-role uniform width / line origin from box center / edge labels offset above (horizontal) or right (vertical) / shared-trunk fan-out
18. Stroke weights (forward 4px, loopback 5px, dashed 3px)
19. Edge labels positioning (OFFSET from line — 14px above horizontal, 6px right of vertical with text-anchor=start)
20. **Reference image match** — if user provided a reference image, does my render's overall composition / arrow style / box layout match it? Note any divergence

Report HIGH/MEDIUM/LOW findings. Under 350 words. Do NOT propose fixes.
```

### Subagent 2 — Logical Layout

```
Inputs: PNG, user description, node spec.

Use Read tool to view PNG. Think DEEPLY:
1-12: standard checklist (flow direction, role clustering, critical path, parallel alignment, loop-back length, re-ordering, entry/exit, adjacency, balance, alternate topology, edge label clarity, alignment audit)

Specifically verify:
- Are SAME-ROLE nodes given the SAME color? (e.g., all slash commands → action; don't split into 3 sub-colors)
- Is the LEGEND LABEL project-domain-appropriate? (e.g., "agent" for AI runtimes, not "actor")
- Do data store siblings share width when their labels permit?
- Do arrows from a node leave from the box CENTER, not from corners?

Report findings. Under 400 words.
```

### Subagent 3 — Requirement Match

```
Inputs: PNG, original user description (mermaid source / prose).

Verify per source:
1. All nodes present
2. All edges present (count)
3. No wiring errors
4. Edge labels match source exactly
5. Node labels match source exactly (including paths like "logs/review_reports" if source uses that)
6. No extras
7. Role assignments per project semantic

Report findings. Under 200 words.
```

## Output

All artifacts live in `./tmp_diagram/` (relative to the cwd, NOT `/tmp/`). What survives Step 11 depends on the user's Step 1 format choice:

| Format choice | Kept in `./tmp_diagram/` |
|---|---|
| `svg` (default) | `flowchart-v2-<slug>.svg` |
| `png` | `flowchart-v2-<slug>.png` |
| `html` | `flowchart-v2-<slug>.html` |
| `all three` | v2 `.html` + `.svg` + `.png` |

All v1 files are always deleted at Step 11. SVG is the canonical deliverable (standalone, embeds CSS + Google Font @import, opens in any browser). HTML is the editable source for further tweaks. PNG is a raster export.

If the user wants the diagram permanently in the project (e.g., `assets/diagrams/`), `cp` from `./tmp_diagram/` to the chosen path.

## Anti-patterns (hard NOs)

Boundary rules not already enforced by a §Section above:

- **Diagonal arrows / cubic curves anywhere** — every edge (including callout) is orthogonal; the callout uses exactly ONE rounded corner (no Z-elbow, no cubic).
- **Edge crossing a node it doesn't connect to** — if an arrow segment passes through a non-source/dest node's bounding rect, reroute or reposition. Subagents have missed this; verify each arrow vs each node rect manually.
- **Sub-categorizing actions by sub-type** (decision / inventory / workflow → distinct colors) — all process steps are `action`. Topology and shape convey semantic, not extra colors.
- **Mixed node-label font sizes** — uniformly 18px. If text overflows, widen the box, never shrink the font.
- **Pure-black text or arrows** — use the palette's softened greys (`--text`, `--flow-line`); pure `#000` clashes with the cream / slate backgrounds.
- **`markerUnits="strokeWidth"`** (or omitting it) — markers will scale with stroke width.
- **Skipping the 3-subagent review** or accepting subagent claims without verifying against the rendered PNG yourself (subagent visual-claim false-positive rate ~50%).
- **More than 2 iterations** (v1 + v2). Hard cap.
- **Outputting `.html` or `.png` as the deliverable** — SVG is what the user gets; HTML is editable source; PNG is throwaway review raster.
- **Extracting SVG without injecting `text { font-family: var(--font); }`** — the body rule's font inheritance is gone in standalone SVG; without an explicit text rule, every `<text>` falls back to browser default (serif).
