# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Ingest a GitHub repository's files into the RAG store.

Shallow-clones the repo, crawls its files using the standard
:func:`crawl_repo` walker, and indexes them via :func:`ingest`
with a configurable ``repo_ref`` label.

Usage::

    from rag.ingest.ingest_github_repo import ingest_github_repo

    result = ingest_github_repo(
        "https://github.com/MacTirney/GrandMA2-API-Documentation",
        repo_ref="ma2-lua-api",
    )
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from rag.ingest.crawl_repo import crawl_repo
from rag.ingest.embed import EmbeddingProvider
from rag.ingest.index import ingest
from rag.types import RepoFile

logger = logging.getLogger(__name__)


def _clone_shallow(repo_url: str, target_dir: Path) -> None:
    """Shallow-clone a git repository."""
    cmd = ["git", "clone", "--depth", "1", repo_url, str(target_dir)]
    logger.info("Cloning %s → %s", repo_url, target_dir)
    subprocess.run(cmd, check=True, capture_output=True, timeout=120)


def _repo_name_from_url(repo_url: str) -> str:
    """Extract repository name from a GitHub URL."""
    return repo_url.rstrip("/").split("/")[-1].removesuffix(".git")


def crawl_github_repo(
    repo_url: str,
    clone_dir: Path | None = None,
) -> list[RepoFile]:
    """Clone a GitHub repo and crawl its files.

    Args:
        repo_url: Full GitHub URL
            (e.g. ``https://github.com/MacTirney/GrandMA2-API-Documentation``).
        clone_dir: Optional directory for the clone.  When *None* a
            temporary directory is created and cleaned up automatically.

    Returns:
        List of :class:`RepoFile` objects with paths prefixed by the
        repository name (e.g. ``GrandMA2-API-Documentation/README.md``).
    """
    repo_name = _repo_name_from_url(repo_url)
    managed_dir = clone_dir is None

    if managed_dir:
        clone_dir = Path(tempfile.mkdtemp(prefix=f"rag-github-{repo_name}-"))

    try:
        _clone_shallow(repo_url, clone_dir)
        files = crawl_repo(clone_dir)

        # Prefix paths with repo name for clarity in the RAG store
        for f in files:
            f.path = f"{repo_name}/{f.path}"

        logger.info("Crawled %d files from %s", len(files), repo_url)
        return files
    finally:
        if managed_dir and clone_dir.exists():
            shutil.rmtree(clone_dir, ignore_errors=True)
            logger.debug("Cleaned up temp clone: %s", clone_dir)


def ingest_github_repo(
    repo_url: str,
    repo_ref: str = "ma2-lua-api",
    embedding_provider: EmbeddingProvider | None = None,
    db_path: str | Path | None = None,
    clone_dir: Path | None = None,
) -> dict[str, int]:
    """Clone and ingest a GitHub repo into the RAG store.

    Args:
        repo_url: Full GitHub URL.
        repo_ref: Label for this knowledge source in the database.
        embedding_provider: Optional embedding provider for vectors.
        db_path: Override the default RAG database path.
        clone_dir: Optional persistent clone directory.

    Returns:
        Counts dict: ``{"processed": N, "skipped": N, "chunks": N}``.
    """
    files = crawl_github_repo(repo_url, clone_dir=clone_dir)
    if not files:
        logger.warning("No files found in %s", repo_url)
        return {"processed": 0, "skipped": 0, "chunks": 0}

    kwargs: dict = {
        "repo_ref": repo_ref,
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
