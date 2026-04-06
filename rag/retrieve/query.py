# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Top-K retrieval from the RAG store."""

from __future__ import annotations

import logging
from pathlib import Path

from rag.config import DEFAULT_TOP_K, RAG_DB_PATH
from rag.ingest.embed import EmbeddingProvider
from rag.retrieve.rerank import rerank
from rag.store.sqlite import RagStore
from rag.types import RagHit

logger = logging.getLogger(__name__)


def _deduplicate(hits: list[RagHit]) -> list[RagHit]:
    """Remove near-duplicate hits by text content.

    Keeps the highest-scoring hit for each unique text prefix (first 200 chars).
    This handles the case where the same documentation appears in both
    ``worktree`` and ``ma2-help-docs`` repo_refs.
    """
    seen: dict[str, int] = {}  # text_prefix → index in result
    result: list[RagHit] = []
    for hit in hits:
        key = hit.text[:200]
        if key in seen:
            idx = seen[key]
            if hit.score > result[idx].score:
                result[idx] = hit
        else:
            seen[key] = len(result)
            result.append(hit)
    return result


def rag_query(
    query: str,
    *,
    embedding_provider: EmbeddingProvider | None = None,
    top_k: int = DEFAULT_TOP_K,
    db_path: str | Path = RAG_DB_PATH,
    repo_ref: str | None = None,
    kind: str | None = None,
) -> list[RagHit]:
    """Query the RAG index and return the top-K most relevant chunks.

    If an embedding_provider is given, uses vector similarity search.
    Falls back to text-based keyword search if no provider is given or
    if a dimension mismatch is detected.

    Args:
        repo_ref: Filter to a specific indexed source (e.g. "worktree",
            "ma2-help-docs", "mcp-sdk").  ``None`` searches all sources.
        kind: Filter to a specific chunk kind (e.g. "source", "test", "doc").
            ``None`` searches all kinds.
    """
    store = RagStore(db_path)
    store.init_db()

    try:
        if embedding_provider is not None:
            query_embedding = embedding_provider.embed_one(query)
            # Over-fetch 2x so the reranker has candidates to reorder before truncating.
            # Dimension-mismatched chunks (e.g. zero-vector-stub) are skipped transparently.
            hits = store.search_by_embedding(
                query_embedding, top_k=top_k * 2,
                repo_ref=repo_ref, kind=kind,
            )
        else:
            hits = store.search_by_text(query, top_k=top_k * 2)

        # Apply reranking
        hits = rerank(hits, query)

        # Deduplicate near-identical chunks (same text across different repo_refs)
        hits = _deduplicate(hits)

        return hits[:top_k]
    finally:
        store.close()
