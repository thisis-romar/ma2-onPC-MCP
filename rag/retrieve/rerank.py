# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Keyword-overlap reranker for RAG retrieval results.

Reranks hits by combining their original score with a keyword-overlap
bonus — the fraction of query terms appearing in the chunk text.
No external dependencies required.

Also provides ``rerank_tools()`` for second-stage reranking of tool
suggestions against their full docstrings/bodies.
"""

from __future__ import annotations

import re

from rag.config import RERANK_BODY_OVERLAP_WEIGHT
from rag.types import RagHit

# Minimum word length to consider as a keyword (skip "a", "is", etc.)
_MIN_TERM_LENGTH = 2


def rerank(hits: list[RagHit], query: str) -> list[RagHit]:
    """Rerank retrieval results using keyword overlap scoring.

    For each hit, computes the fraction of query terms found in the
    chunk text (case-insensitive) and adds it as a bonus to the
    original score. Hits are re-sorted by the combined score.
    """
    if not hits or not query.strip():
        return hits

    query_terms = _extract_terms(query)
    if not query_terms:
        return hits

    reranked: list[RagHit] = []
    for hit in hits:
        overlap = _keyword_overlap(query_terms, hit.text)
        reranked.append(RagHit(
            chunk_id=hit.chunk_id,
            path=hit.path,
            kind=hit.kind,
            start_line=hit.start_line,
            end_line=hit.end_line,
            score=hit.score + overlap,
            text=hit.text,
        ))

    reranked.sort(key=lambda h: h.score, reverse=True)
    return reranked


def _extract_terms(text: str) -> list[str]:
    """Extract lowercase terms from text, filtering short words."""
    return [
        w.lower()
        for w in re.findall(r"[a-zA-Z0-9_]+", text)
        if len(w) >= _MIN_TERM_LENGTH
    ]


def _keyword_overlap(query_terms: list[str], chunk_text: str) -> float:
    """Return fraction of query terms found in chunk text (0.0 to 1.0)."""
    if not query_terms:
        return 0.0
    chunk_lower = chunk_text.lower()
    matches = sum(1 for term in query_terms if term in chunk_lower)
    return matches / len(query_terms)


# ── Tool-body reranker ────────────────────────────────────────────────────


def rerank_tools(
    candidates: list[tuple[str, float]],
    query: str,
    tool_bodies: dict[str, str],
) -> list[tuple[str, float]]:
    """Rerank tool suggestions by keyword overlap against full tool bodies.

    This is the second stage in a retrieve-then-rerank pipeline:
    first-pass retrieval produces ``candidates`` (name, score); this function
    re-scores each candidate by computing keyword overlap between the query
    and the tool's full docstring/body text, then combines with the original
    score.

    Args:
        candidates: First-pass results as ``(tool_name, score)`` tuples.
        query: The original task description.
        tool_bodies: Mapping of ``tool_name → full_docstring_text``.

    Returns:
        Re-sorted ``(tool_name, combined_score)`` list, descending.
    """
    if not candidates or not query.strip():
        return candidates

    query_terms = _extract_terms(query)
    if not query_terms:
        return candidates

    reranked: list[tuple[str, float]] = []
    for name, score in candidates:
        body = tool_bodies.get(name, "")
        if body:
            overlap = _keyword_overlap(query_terms, body)
            combined = score + overlap * RERANK_BODY_OVERLAP_WEIGHT
        else:
            combined = score
        reranked.append((name, combined))

    reranked.sort(key=lambda x: -x[1])
    return reranked
