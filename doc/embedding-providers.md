---
title: Embedding Provider Comparison
description: Evaluation of embedding providers for the RAG pipeline — dimensions, cost, rate limits, and migration strategy
version: 1.0.0
created: 2026-04-08T03:04:49Z
last_updated: 2026-04-08T03:04:49Z
---

# Embedding Provider Comparison

## Overview

The RAG pipeline supports three embedding providers via `rag/ingest/embed.py`. All share a common `EmbeddingProvider` interface with identical batch handling, deduplication, and retry logic.

## Provider Comparison

| Property | GitHubModelsProvider | OpenRouterProvider | ZeroVectorProvider |
|----------|---------------------|--------------------|--------------------|
| **Model** | `openai/text-embedding-3-small` | `nvidia/llama-nemotron-embed-vl-1b-v2:free` | stub (all zeros) |
| **Dimensions** | 1536 | 2048 | configurable (default 1536) |
| **Cost** | Free (GitHub Models) | Free (OpenRouter free tier) | N/A |
| **Endpoint** | `https://models.github.ai/inference` | `https://openrouter.ai/api/v1` | local |
| **Auth env var** | `GITHUB_MODELS_TOKEN` or `GITHUB_TOKEN` | `OPENROUTER_API_KEY` | none |
| **Batch size** | 32 | 32 | instant |
| **Inter-request delay** | 4.0s | 4.0s | 0s |
| **Max retries** | 5 (exponential backoff) | 5 (exponential backoff) | N/A |
| **Daily quota detection** | Yes (retry-after > 3600s) | Yes (retry-after > 3600s) | N/A |
| **Deduplication** | Yes (identical texts in batch) | Yes (identical texts in batch) | N/A |

## Dimension Asymmetry

GitHub Models uses **1536-dim** vectors; OpenRouter uses **2048-dim** vectors. These **cannot be mixed in the same SQLite store** — cosine similarity requires matching dimensions.

### Consequences

- Switching from one provider to another requires re-embedding all chunks
- Zero-vector stubs (1536-dim) are compatible with GitHub Models but not OpenRouter
- The `search_by_embedding` method in `rag/store/sqlite.py` raises `ValueError` on dimension mismatch

### Migration Strategy

Use the existing upgrade script to switch providers:

```bash
# Re-embed all chunks with a new provider (e.g., switching from GitHub to OpenRouter)
uv run python scripts/rag_upgrade_embeddings.py --provider openrouter --re-embed-all

# Or switch back to GitHub Models
uv run python scripts/rag_upgrade_embeddings.py --provider github --re-embed-all
```

The `--re-embed-all` flag deletes existing embeddings and re-embeds every chunk. Use `--batch-size N` for free-tier quota management.

## Environment Variables

| Variable | Purpose | Used by |
|----------|---------|---------|
| `GITHUB_MODELS_TOKEN` | GitHub Models API token | GitHubModelsProvider |
| `GITHUB_TOKEN` | Fallback for GitHub Models | GitHubModelsProvider |
| `OPENROUTER_API_KEY` | OpenRouter API key | OpenRouterProvider |
| `RAG_EMBED_MODEL` | Override default model name | both providers |
| `RAG_EMBED_DIMENSIONS` | Override default dimensions | both providers |

## CLI Support

| Script | Providers available |
|--------|-------------------|
| `scripts/rag_ingest.py` | `--provider {github, openrouter, zero}` + auto-detect |
| `scripts/rag_ingest_web.py` | `--provider {github, openrouter, zero}` + auto-detect |
| `scripts/rag_ingest_mcp_sdk.py` | `--provider {github, zero}` + auto-detect |
| `scripts/rag_upgrade_embeddings.py` | `--provider {github, openrouter}` |

Auto-detect order: GitHub Models > OpenRouter > zero-vector fallback.

## Evaluation Methodology

To compare retrieval quality between providers:

1. Build a test query set (~20 representative queries covering command builders, help docs, and SDK)
2. Ingest the same corpus with both providers (requires separate DB files or `--re-embed-all`)
3. For each query, compare retrieval@8 results: precision, recall, and rank ordering
4. Measure latency per query (vector search vs text-search fallback)

Key metrics:
- **Recall@8**: How many of the expected top results appear in the top 8?
- **MRR** (Mean Reciprocal Rank): How high is the first relevant result ranked?
- **Embedding latency**: Time to embed the full corpus (affects ingest time, not query time)
