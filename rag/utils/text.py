"""Text processing utilities for the RAG pipeline."""

from __future__ import annotations

import re

from rag.config import CHARS_PER_TOKEN


def estimate_tokens(text: str) -> int:
    """Rough token count based on character length (~4 chars/token)."""
    return max(1, len(text) // CHARS_PER_TOKEN)


def normalize_whitespace(text: str) -> str:
    """Collapse runs of whitespace into single spaces and strip."""
    return re.sub(r"\s+", " ", text).strip()
