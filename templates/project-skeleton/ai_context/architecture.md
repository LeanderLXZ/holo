<!--
MAINTENANCE — read before editing this file.
This file is an index for fast project follow-up, not a detailed manual.
1. Write "what / where to find"; link to authoritative sources (code paths, docs/*.md, schemas, logs).
2. Prefer deletion over addition; check if a new item merges into an existing one before adding.
3. Describe the current design only — no "legacy / deprecated / formerly / renamed from".
4. No real product / customer / private-content names — use structural placeholders.
Shorter is better than longer; push detail into the linked source rather than growing this file.
-->

# Architecture Snapshot

Compressed summary of the system architecture for fast follow-up.

**Authoritative sources**: detailed architecture docs live in
`docs/architecture/`. Each section here points to the corresponding
detail document.

This file exists so that session start does not need to load every
architecture document. Update both layers in lockstep when the
architecture changes — that pairing is one row of
`conventions.md` §Cross-File Alignment.

## Top-Level Structure

<bulleted list naming each top-level directory and what it holds in one
line. New top-level directories get a row here.>

## System Layers

<numbered list of the conceptual layers / stages of the system —
e.g. "1. Ingest — raw input normalization", "2. Processing — …".
Each layer should be one short line.>

## Key Boundaries

<bulleted list of hard boundaries the architecture enforces —
e.g. "Layer X never reads from Layer Y", "Schema-validated artifacts
do not leave directory Z without passing gate G". Each boundary should
trace to a paragraph in `docs/architecture/` for the full rationale.>

## Runtime / Entry Points

<short list of the primary entry points — CLI commands, services,
adapters — and one line on what each does. Detail lives in the linked
docs / READMEs.>
