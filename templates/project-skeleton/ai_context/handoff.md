<!--
MAINTENANCE — read before editing this file.
This file is an index for fast project follow-up, not a detailed manual.
1. Write "what / where to find"; link to authoritative sources (code paths, docs/*.md, schemas, logs).
2. Prefer deletion over addition; check if a new item merges into an existing one before adding.
3. Describe the current design only — no "legacy / deprecated / formerly / renamed from".
4. No real product / customer / private-content names — use structural placeholders.
Shorter is better than longer; push detail into the linked source rather than growing this file.
-->

# Handoff

Last file in the session-start reading order. Hands the future AI
session a working mental model, a quick-start guide, and a list of
"things the user cares about" that aren't formal requirements but
shape every call.

## Mental Model

<2–4 short sentences describing where the project is conceptually
right now — design agreed, scaffold up, first feature done, etc. This
is the human-readable version of `current_status.md`.>

## Quick Start

<numbered list of 3–6 steps: read which files in which order, where
the entry-point doc lives, how to run / inspect the system. Each step
one line.>

## Operational Commands

<short list of the most common commands the project uses — CLI
invocations, build / test commands, deployment triggers. One line each.
If the project doesn't have any yet, write `(none yet)`.>

## What The User Cares About

<bulleted list of preferences, taste, and "soft" rules that aren't in
the formal requirements but reliably trigger user feedback if
violated. Examples:

- "Behavior consistency over surface tone"
- "No raw inputs pasted into logs / docs"
- "Incremental updates, never restart from scratch"
- "No real product / customer names in canonical docs"

Each bullet should be one line. Update these whenever the user gives
feedback that points to a durable preference, not just a one-off fix.>

## After Each Milestone

1. Write a `logs/change_logs/` entry per `conventions.md` §Logging.
2. Update `current_status.md`, `next_steps.md`, and this file only
   when the change is durable.
