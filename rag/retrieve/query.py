# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Top-K retrieval from the RAG store.

Supports optional graph-augmented retrieval (GraphRAG): when a GraphStore
is provided, entity mentions in the query are expanded with graph context
and attached to each hit's ``graph_context`` field.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from rag.config import DEDUP_PREFIX_LEN, DEFAULT_TOP_K, RAG_DB_PATH
from rag.ingest.embed import EmbeddingProvider
from rag.retrieve.rerank import rerank
from rag.store.sqlite import RagStore
from rag.types import RagHit

if TYPE_CHECKING:
    from src.knowledge_graph.store import GraphStore

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
        key = hit.text[:DEDUP_PREFIX_LEN]
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
    graph_store: GraphStore | None = None,
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
        graph_store: Optional initialized GraphStore for graph-augmented
            retrieval.  When provided, entity mentions in the query are
            expanded with graph context and attached to each hit.
    """
    store = RagStore(db_path)
    store.init_db()

    try:
        if embedding_provider is not None:
            try:
                # Switch to query mode for asymmetric search (Gemini)
                if hasattr(embedding_provider, "set_task_type"):
                    embedding_provider.set_task_type("RETRIEVAL_QUERY")
                query_embedding = embedding_provider.embed_one(query)
                hits = store.search_by_embedding(
                    query_embedding, top_k=top_k * 2,
                    repo_ref=repo_ref, kind=kind,
                )
            except ValueError:
                logger.warning(
                    "Embedding dimension mismatch — falling back to text search"
                )
                hits = store.search_by_text(query, top_k=top_k * 2)
        else:
            hits = store.search_by_text(query, top_k=top_k * 2)

        # Apply reranking
        hits = rerank(hits, query)

        # Deduplicate near-identical chunks (same text across different repo_refs)
        hits = _deduplicate(hits)

        hits = hits[:top_k]

        # Graph-augmented enrichment (optional)
        if graph_store is not None:
            _enrich_with_graph(hits, query, graph_store)

        return hits
    finally:
        store.close()


def _enrich_with_graph(
    hits: list[RagHit],
    query: str,
    graph_store: GraphStore,
) -> None:
    """Attach graph context to RAG hits.

    Extracts entity mentions from the query, expands them via graph
    traversal, and attaches the context to every hit.
    """
    from src.knowledge_graph.graph_rag import graph_rag_query

    contexts = graph_rag_query(query, graph_store, max_depth=2)
    if not contexts:
        return

    context_dicts = [ctx.to_dict() for ctx in contexts]
    for hit in hits:
        hit.graph_context = context_dicts
