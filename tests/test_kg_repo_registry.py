# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for the repo registry (multi-repo tracking)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from src.knowledge_graph.parsers.repo_registry import RepoRegistry, get_git_head_sha


class TestRepoRegistry:
    def test_register_and_get(self, tmp_path: Path):
        reg = RepoRegistry()
        entry = reg.register(tmp_path, "abc123", node_count=10, edge_count=5)
        assert entry.name == tmp_path.name
        assert entry.last_sha == "abc123"
        assert entry.node_count == 10

        fetched = reg.get(tmp_path)
        assert fetched is not None
        assert fetched.last_sha == "abc123"

    def test_get_missing_returns_none(self, tmp_path: Path):
        reg = RepoRegistry()
        assert reg.get(tmp_path) is None

    def test_needs_reindex_when_never_indexed(self, tmp_path: Path):
        reg = RepoRegistry()
        assert reg.needs_reindex(tmp_path) is True

    def test_needs_reindex_when_sha_changed(self, tmp_path: Path):
        reg = RepoRegistry()
        reg.register(tmp_path, "old_sha")
        with patch(
            "src.knowledge_graph.parsers.repo_registry.get_git_head_sha",
            return_value="new_sha",
        ):
            assert reg.needs_reindex(tmp_path) is True

    def test_no_reindex_when_sha_same(self, tmp_path: Path):
        reg = RepoRegistry()
        reg.register(tmp_path, "same_sha")
        with patch(
            "src.knowledge_graph.parsers.repo_registry.get_git_head_sha",
            return_value="same_sha",
        ):
            assert reg.needs_reindex(tmp_path) is False

    def test_list_repos(self, tmp_path: Path):
        reg = RepoRegistry()
        dir_a = tmp_path / "alpha"
        dir_b = tmp_path / "beta"
        dir_a.mkdir()
        dir_b.mkdir()
        reg.register(dir_b, "sha_b")
        reg.register(dir_a, "sha_a")
        repos = reg.list_repos()
        assert [r.name for r in repos] == ["alpha", "beta"]

    def test_remove(self, tmp_path: Path):
        reg = RepoRegistry()
        reg.register(tmp_path, "sha")
        assert reg.count() == 1
        assert reg.remove(tmp_path) is True
        assert reg.count() == 0
        assert reg.remove(tmp_path) is False

    def test_count(self, tmp_path: Path):
        reg = RepoRegistry()
        assert reg.count() == 0
        reg.register(tmp_path, "sha")
        assert reg.count() == 1


class TestGetGitHeadSha:
    def test_returns_sha_for_real_repo(self):
        # This test runs in the actual repo
        sha = get_git_head_sha(Path("."))
        assert sha is not None
        assert len(sha) == 40  # full SHA

    def test_returns_none_for_non_repo(self, tmp_path: Path):
        sha = get_git_head_sha(tmp_path)
        assert sha is None
