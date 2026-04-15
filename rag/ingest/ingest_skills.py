# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Ingest .claude/skills/ SKILL.md files into the RAG store.

Crawls the hand-authored skills directory and indexes each SKILL.md as
a separate document with ``repo_ref="skills"``.  Chunks use heading-based
Markdown splitting (same as the main ingest pipeline).
"""

from __future__ import annotations

import logging
from pathlib import Path

from rag.ingest.embed import EmbeddingProvider
from rag.ingest.index import ingest
from rag.types import RepoFile
from rag.utils.hash import sha256

logger = logging.getLogger(__name__)

_DEFAULT_SKILLS_DIR = Path(__file__).resolve().parent.parent.parent / ".claude" / "skills"


def crawl_skills(skills_dir: Path | None = None) -> list[RepoFile]:
    """Walk the skills directory and return RepoFile entries for each SKILL.md.

    Args:
        skills_dir: Override the default ``.claude/skills/`` path.

    Returns:
        List of :class:`RepoFile` objects, one per SKILL.md found.
    """
    root = Path(skills_dir) if skills_dir else _DEFAULT_SKILLS_DIR
    if not root.is_dir():
        logger.warning("Skills directory not found: %s", root)
        return []

    files: list[RepoFile] = []
    for skill_md in sorted(root.rglob("SKILL.md")):
        try:
            text = skill_md.read_text(encoding="utf-8")
        except OSError as e:
            logger.warning("Cannot read %s: %s", skill_md, e)
            continue

        # Use relative path from skills dir for the document path
        rel = str(skill_md.relative_to(root)).replace("\\", "/")
        path = f".claude/skills/{rel}"

        files.append(RepoFile(
            path=path,
            kind="doc",
            language="markdown",
            text=text,
            hash=sha256(text),
        ))

    logger.info("Crawled %d skill files from %s", len(files), root)
    return files


def ingest_skills(
    skills_dir: Path | None = None,
    embedding_provider: EmbeddingProvider | None = None,
    db_path: str | Path | None = None,
) -> dict[str, int]:
    """Ingest all SKILL.md files into the RAG store.

    Delegates to :func:`rag.ingest.index.ingest` with
    ``repo_ref="skills"`` and pre-crawled skill files.

    Args:
        skills_dir: Override the default ``.claude/skills/`` path.
        embedding_provider: Optional embedding provider for vectors.
        db_path: Override the default RAG database path.

    Returns:
        Counts dict: ``{"processed": N, "skipped": N, "chunks": N}``.
    """
    files = crawl_skills(skills_dir)
    if not files:
        return {"processed": 0, "skipped": 0, "chunks": 0}

    kwargs: dict = {
        "repo_ref": "skills",
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
