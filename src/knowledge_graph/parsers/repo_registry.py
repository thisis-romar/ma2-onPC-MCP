# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
repo_registry.py — Multi-repo tracking with git SHA for the code graph.

Tracks which repositories have been indexed, their last-indexed commit SHA,
and when they were last scanned. Enables incremental re-indexing by detecting
when a repo's HEAD has changed since the last scan.
"""

from __future__ import annotations

import logging
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class RepoEntry:
    """A tracked repository in the registry."""

    root: str            # Absolute path to repo root
    name: str            # Short name (directory basename)
    last_sha: str        # Git HEAD SHA at last index time
    last_indexed: float  # Unix timestamp of last scan
    node_count: int      # Number of graph nodes created
    edge_count: int      # Number of graph edges created


def get_git_head_sha(repo_root: Path) -> str | None:
    """Return the current HEAD SHA for a git repository, or None if not a repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        pass
    return None


class RepoRegistry:
    """In-memory registry of indexed repositories.

    Tracks which repos have been scanned and their git SHA at scan time.
    Used by the code graph layer to decide whether a re-index is needed.

    Not persisted to disk — rebuilt on each server start. For persistent
    tracking, store entries in the GraphStore as nodes (future work).
    """

    def __init__(self) -> None:
        self._repos: dict[str, RepoEntry] = {}

    def register(
        self,
        root: Path,
        sha: str,
        node_count: int = 0,
        edge_count: int = 0,
    ) -> RepoEntry:
        """Register a repository as indexed at the given SHA."""
        key = str(root.resolve())
        entry = RepoEntry(
            root=key,
            name=root.name,
            last_sha=sha,
            last_indexed=time.time(),
            node_count=node_count,
            edge_count=edge_count,
        )
        self._repos[key] = entry
        logger.info("Registered repo %s at SHA %s (%d nodes)", entry.name, sha[:8], node_count)
        return entry

    def get(self, root: Path) -> RepoEntry | None:
        """Lookup a repo by root path."""
        return self._repos.get(str(root.resolve()))

    def needs_reindex(self, root: Path) -> bool:
        """Check if a repo needs re-indexing (HEAD SHA changed or never indexed)."""
        entry = self.get(root)
        if entry is None:
            return True
        current_sha = get_git_head_sha(root)
        if current_sha is None:
            return True  # Can't determine SHA, re-index to be safe
        return current_sha != entry.last_sha

    def list_repos(self) -> list[RepoEntry]:
        """Return all registered repos, sorted by name."""
        return sorted(self._repos.values(), key=lambda e: e.name)

    def remove(self, root: Path) -> bool:
        """Remove a repo from the registry. Returns True if it existed."""
        key = str(root.resolve())
        if key in self._repos:
            del self._repos[key]
            return True
        return False

    def count(self) -> int:
        """Return the number of tracked repos."""
        return len(self._repos)
