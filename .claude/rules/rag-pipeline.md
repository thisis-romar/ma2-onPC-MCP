---
title: RAG Pipeline Reference
description: How the RAG pipeline works, three indexed knowledge sources, pre-commit hook, and web doc batching
version: 1.0.0
created: 2026-03-30T00:00:00Z
last_updated: 2026-03-30T00:00:00Z
---

# RAG Pipeline Reference

## How It Works

```
crawl → chunk → embed → store (SQLite) → query → rerank
```

- Python files: AST-aware chunking. Markdown: heading-based. Everything else: line-based.
- Embeddings: `GitHubModelsProvider` (requires `GITHUB_MODELS_TOKEN`) or `ZeroVectorProvider` (CI/testing stub, 1536-dim zero vectors).
- The `search_codebase` MCP tool queries the store; auto-detects token and falls back to text search.
- Embedding API: 4s inter-request delay, batch_size=32 to stay within GitHub Models free tier.
- Dimension mismatch between old zero-vector chunks and new real embeddings is handled gracefully (mismatched chunks skipped, no error raised).

## Three Indexed Knowledge Sources

| `repo_ref` | Script | Content |
|------------|--------|---------|
| `worktree` | `rag_ingest.py` | This server's Python source, tests, docs, configs |
| `ma2-help-docs` | `rag_ingest_web.py` | ~1,043 grandMA2 help pages from help.malighting.com |
| `mcp-sdk` | `rag_ingest_mcp_sdk.py` | Installed MCP SDK source (~110 files) |

## Pre-commit Hook

`make install-hooks` installs `.githooks/pre-commit`, which runs zero-vector ingest on every commit (fast, no API calls). Real-vector rebuild must be run manually.

## Web Doc Batching

~1,043 grandMA2 help pages, embedded in nightly runs. The `--cache-crawl` flag saves the crawl to `rag/store/web_crawl_cache.json` — subsequent runs skip re-crawling.

**Web cache note:** cache schema version must match `_CACHE_SCHEMA_VERSION` in `scripts/rag_ingest_web.py` (currently v2). If the cache has an older version, it is invalidated automatically. Use `--recrawl` to force a fresh crawl.

## Commands

```bash
# Ingest repo (zero-vector, no token needed)
uv run python scripts/rag_ingest.py --root . --provider zero

# Ingest with real embeddings
source .env && export GITHUB_MODELS_TOKEN && \
  uv run python scripts/rag_ingest.py --provider github

# Ingest MA2 web docs (first run)
source .env && export GITHUB_MODELS_TOKEN && \
  PYTHONUNBUFFERED=1 uv run python scripts/rag_ingest_web.py \
  --provider github --cache-crawl

# Ingest MCP SDK source
uv run python scripts/rag_ingest_mcp_sdk.py --provider zero
```
