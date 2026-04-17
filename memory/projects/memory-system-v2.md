# Workspace Memory System V2

> Records the decision to use a pointer-index long-term memory plus atomic files and structured distillation.

## Decision

On 2026-04-17, the workspace was migrated from a flat MEMORY.md to a structured V2 model. `MEMORY.md` now serves as a small pointer index and durable recall lives in atomic files under `memory/`.

## Structure

- Behavior and always-loaded preferences live in `SOUL.md`, `AGENTS.md`, `TOOLS.md`, and `USER.md`.
- Lookup-oriented memory lives in atomic files under `memory/projects/`, `memory/tools/`, `memory/people/`, `memory/ideas/`, and `memory/summaries/`.
- Daily capture lives in `memory/YYYY-MM-DD.md` with typed entry prefixes.
- Corrections, failures, and feature gaps live in `.learnings/`.

## Retrieval Rules

This structure assumes embedding-first retrieval. Do not add keyword-stuffing sections, synonym padding, or repeated reformulations inside source documents. If recall feels uncertain, expand the query at search time instead of diluting the source files.

### Updated

2026-04-17 — Migrated from flat MEMORY.md
