"""Optional reranking hook for RAG retrieval results.

This is a stub — returns hits unchanged. Implement MMR, cross-encoder,
or other reranking strategies here when needed.
"""

from __future__ import annotations

from rag.types import RagHit


def rerank(hits: list[RagHit], query: str) -> list[RagHit]:
    """Rerank retrieval results. Currently a passthrough stub."""
    return hits
