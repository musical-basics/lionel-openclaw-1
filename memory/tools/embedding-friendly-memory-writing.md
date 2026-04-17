# Embedding-Friendly Memory Writing

> Explains how to write atomic memory notes so vector retrieval embeddings stay sharp instead of smeared.

## Retrieval Model

Atomic memory notes should be written for OpenClaw's vector retrieval layer. OpenClaw `memory_search` chunks, embeds, and indexes `MEMORY.md` and files under `memory/`, so each chunk should represent one concept cleanly enough to retrieve on differently worded queries.

The current embedding model is OpenAI `text-embedding-3-large`. It already handles synonymy, paraphrase, and cross-lingual similarity well enough that source files should stay clean. BM25 covers exact proper nouns, filenames, IDs, and other exact-match terms.

## Writing Rules

Each atomic file should stay focused on one topic, and each section should stay focused on one subtopic. Each section should lead with the concept it is about. Proper nouns should be written exactly and consistently. Do not add keyword lists, synonym padding, or reformulated-concept sections. Use prose for conceptual material and save bullet lists for genuinely list-shaped content. When a file changes, update it in place and keep a `### Updated` line current.

## Query Strategy

When retrieval feels uncertain, expand the query at search time instead of editing source files to include extra keywords.

## Verification Test

After a significant memory restructure or new atomic file, run a retrieval test with deliberately different wording from the stored text.

### Related

- `memory/projects/memory-system-v2.md` — the main memory-system design decision

### Updated

2026-04-17 — Created during V2 migration
