# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Ingest MCP resource outputs into the RAG store.

Extracts resource metadata via :func:`extract_mcp_metadata` and creates
pseudo-documents from resource docstrings, indexed with
``repo_ref="mcp-resources"``.

Resources are not files on disk — they're runtime-generated content.
This module creates synthetic :class:`RepoFile` entries from the metadata
so the standard ingest pipeline can chunk and embed them.
"""

from __future__ import annotations

import logging
from pathlib import Path

from rag.ingest.embed import EmbeddingProvider
from rag.ingest.index import ingest
from rag.types import RepoFile
from rag.utils.hash import sha256

logger = logging.getLogger(__name__)


def crawl_resources(server_path: Path | None = None) -> list[RepoFile]:
    """Extract MCP resource/prompt metadata and convert to RepoFile entries.

    Each resource URI becomes a synthetic document with its docstring as content.

    Args:
        server_path: Override the server.py path for metadata extraction.

    Returns:
        List of :class:`RepoFile` objects, one per resource and prompt.
    """
    try:
        from src.knowledge_graph.mcp_metadata import extract_mcp_metadata
    except ImportError:
        logger.warning("mcp_metadata not available — skipping resource crawl")
        return []

    metadata = extract_mcp_metadata(server_path)
    files: list[RepoFile] = []

    # Resources
    for uri, resource in metadata.resources.items():
        doc = resource.docstring or ""
        if not doc.strip():
            continue
        text = f"# MCP Resource: {uri}\n\n{doc}"
        files.append(RepoFile(
            path=f"mcp-resource://{uri}",
            kind="doc",
            language="markdown",
            text=text,
            hash=sha256(text),
        ))

    # Prompts
    for name, prompt in metadata.prompts.items():
        doc = prompt.docstring or ""
        if not doc.strip():
            continue
        args_str = ", ".join(prompt.args) if prompt.args else "(no args)"
        text = f"# MCP Prompt: {name}\n\nArgs: {args_str}\n\n{doc}"
        files.append(RepoFile(
            path=f"mcp-prompt://{name}",
            kind="doc",
            language="markdown",
            text=text,
            hash=sha256(text),
        ))

    logger.info("Crawled %d MCP resource/prompt entries", len(files))
    return files


def ingest_resources(
    server_path: Path | None = None,
    embedding_provider: EmbeddingProvider | None = None,
    db_path: str | Path | None = None,
) -> dict[str, int]:
    """Ingest MCP resource/prompt docstrings into the RAG store.

    Delegates to :func:`rag.ingest.index.ingest` with
    ``repo_ref="mcp-resources"`` and synthetic resource files.

    Args:
        server_path: Override the server.py path for metadata extraction.
        embedding_provider: Optional embedding provider for vectors.
        db_path: Override the default RAG database path.

    Returns:
        Counts dict: ``{"processed": N, "skipped": N, "chunks": N}``.
    """
    files = crawl_resources(server_path)
    if not files:
        return {"processed": 0, "skipped": 0, "chunks": 0}

    kwargs: dict = {
        "repo_ref": "mcp-resources",
        "embedding_provider": embedding_provider,
        "files": files,
    }
    if db_path is not None:
        kwargs["db_path"] = db_path

    result = ingest(**kwargs)
    return {
        "processed": result.files_processed,
        "skipped": result.files_skipped,
        "chunks": result.chunks_created,
    }
