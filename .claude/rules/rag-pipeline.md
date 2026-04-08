---
title: RAG Pipeline Developer Conventions
description: How the crawl-chunk-embed-store-retrieve pipeline works and how to maintain it
version: 1.1.0
created: 2026-03-29T21:44:45Z
last_updated: 2026-04-08T03:19:39Z
---

# RAG Pipeline Developer Conventions

> Loaded when working on rag/, scripts/rag_ingest*.py, or the search_codebase tool.

---

## How it works

```
crawl → chunk → embed → store (SQLite) → query → rerank
```

- Python files: AST-aware chunking. Markdown: heading-based. Everything else: line-based.
- Embeddings: `GitHubModelsProvider` (requires `GITHUB_MODELS_TOKEN`, 1536-dim) or `OpenRouterProvider` (requires `OPENROUTER_API_KEY`, 2048-dim) or `ZeroVectorProvider` (CI/testing stub, 1536-dim zero vectors).
- The `search_codebase` MCP tool queries the store; auto-detects token and falls back to text search when absent.
- Embedding API is rate-limited — 4s inter-request delay, batch_size=32 to stay within free tier limits.
- Dimension mismatch between old zero-vector chunks and new real embeddings is handled gracefully.
- **Dimension asymmetry**: GitHub Models uses 1536-dim, OpenRouter uses 2048-dim. Cannot mix in the same store — use `rag_upgrade_embeddings.py --re-embed-all` when switching providers.

---

## Three indexed knowledge sources

| `repo_ref` | Script | Content |
|------------|--------|---------|
| `worktree` | `rag_ingest.py` | This server's Python source, tests, docs, configs |
| `ma2-help-docs` | `rag_ingest_web.py` | ~1,043 grandMA2 help pages from help.malighting.com |
| `mcp-sdk` | `rag_ingest_mcp_sdk.py` | Installed MCP SDK source (~110 files) |

---

## Pre-commit hook

`make install-hooks` installs `.githooks/pre-commit`, which runs zero-vector ingest on every commit (fast, no API calls). Real-vector rebuild must be run manually.

---

## Web doc batching

~1,043 grandMA2 help pages, embedded in nightly runs. The `--cache-crawl` flag saves the crawl to `rag/store/web_crawl_cache.json` — subsequent runs skip re-crawling.

**Web cache note:** cache schema version must match `_CACHE_SCHEMA_VERSION` in `scripts/rag_ingest_web.py` (currently v2). If the cache file has an older version (v1), it is invalidated automatically. Re-run with `--recrawl` to force a fresh crawl.

---

## Markdown chunk merging

`_merge_small_ranges()` in `rag/ingest/chunk.py` merges consecutive tiny Markdown heading sections into larger chunks for better retrieval context.

- **Merge threshold**: chunks smaller than `MERGE_MIN_CHARS` (200 chars) are candidates
- **Target size**: merging stops when combined size would exceed `MERGE_TARGET_CHARS` (2000 chars)
- **Boundary protection**: never merges across H1 or H2 headings (major section breaks)
- **Symbol preservation**: heading texts from all merged ranges are combined
- Config constants in `rag/config.py`

---

## HTML boilerplate stripping

`rag/ingest/crawl_web.py` strips noise from within the content area of grandMA2 help pages before chunking:

- `_strip_boilerplate()`: removes breadcrumbs (`.breadcrumb`, `.topic-breadcrumb`), "Related Topics" / "See Also" sections, copyright notices, feedback blocks, and pagination elements — via CSS selectors and text pattern matching
- `_normalize_code_blocks()`: wraps `<pre>` content with fenced code markers for better chunking
- `_strip_img_noise()`: removes `<img>` elements that produce noisy alt text (e.g. `[Graphic]`)
