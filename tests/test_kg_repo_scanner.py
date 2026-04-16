# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for the knowledge graph repository scanner."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.knowledge_graph.parsers.repo_scanner import scan_repository
from src.knowledge_graph.schema import EdgeType, NodeType, node_id
from src.knowledge_graph.store import GraphStore


@pytest.fixture
def store():
    """Create an in-memory GraphStore for testing."""
    s = GraphStore(":memory:")
    s.initialize()
    yield s
    s.close()


def _write_file(path: Path, content: str) -> None:
    """Helper to create a file with parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestScanRepository:
    def test_basic_scan(self, store, tmp_path):
        _write_file(tmp_path / "hello.py", "def greet():\n    pass\n")
        _write_file(tmp_path / "utils.py", "def helper():\n    pass\n\ndef other():\n    pass\n")

        counts = scan_repository(store, tmp_path)
        assert counts["modules"] == 2
        assert counts["symbols"] >= 3  # greet, helper, other

    def test_nested_modules(self, store, tmp_path):
        _write_file(tmp_path / "pkg" / "__init__.py", "")
        _write_file(tmp_path / "pkg" / "core.py", "class Engine:\n    pass\n")

        counts = scan_repository(store, tmp_path)
        assert counts["modules"] == 2  # __init__.py + core.py

        # Check the module nodes exist
        mod_nid = node_id(NodeType.MODULE, "pkg.core")
        mod = store.get_node(mod_nid)
        assert mod is not None

    def test_exclude_patterns(self, store, tmp_path):
        _write_file(tmp_path / "good.py", "x = 1\n")
        _write_file(tmp_path / "__pycache__" / "cached.py", "y = 2\n")
        _write_file(tmp_path / ".venv" / "lib.py", "z = 3\n")

        counts = scan_repository(store, tmp_path)
        assert counts["modules"] == 1  # Only good.py

    def test_custom_exclude_patterns(self, store, tmp_path):
        _write_file(tmp_path / "keep.py", "a = 1\n")
        _write_file(tmp_path / "skip_me" / "hidden.py", "b = 2\n")

        counts = scan_repository(store, tmp_path, exclude_patterns=["skip_me"])
        assert counts["modules"] == 1

    def test_package_detection(self, store, tmp_path):
        _write_file(tmp_path / "mypkg" / "__init__.py", "")
        _write_file(tmp_path / "mypkg" / "sub" / "__init__.py", "")
        _write_file(tmp_path / "mypkg" / "sub" / "mod.py", "def f():\n    pass\n")

        counts = scan_repository(store, tmp_path)
        assert counts["packages"] >= 2  # mypkg, mypkg.sub

        # Check package nodes
        pkg1 = store.get_node(node_id(NodeType.PACKAGE, "mypkg"))
        assert pkg1 is not None
        pkg2 = store.get_node(node_id(NodeType.PACKAGE, "mypkg.sub"))
        assert pkg2 is not None

    def test_aggregate_counts(self, store, tmp_path):
        _write_file(tmp_path / "a.py", "def fa():\n    pass\n")
        _write_file(tmp_path / "b.py", "def fb():\n    pass\ndef fc():\n    pass\n")

        counts = scan_repository(store, tmp_path)
        assert counts["modules"] == 2
        assert counts["symbols"] == 3  # fa, fb, fc
        assert counts["nodes"] > 0
        assert counts["edges"] > 0

    def test_empty_directory(self, store, tmp_path):
        counts = scan_repository(store, tmp_path)
        assert counts["modules"] == 0
        assert counts["symbols"] == 0
        assert counts["nodes"] == 0
        assert counts["edges"] == 0

    def test_syntax_error_file_still_indexed(self, store, tmp_path):
        _write_file(tmp_path / "broken.py", "def bad(:\n    pass\n")
        _write_file(tmp_path / "good.py", "def ok():\n    pass\n")

        counts = scan_repository(store, tmp_path)
        assert counts["modules"] == 2  # Both get indexed

        # Broken module should have parse_error in props
        mod_nid = node_id(NodeType.MODULE, "broken")
        mod = store.get_node(mod_nid)
        assert mod is not None
        assert "parse_error" in mod.props

    def test_imports_across_files(self, store, tmp_path):
        _write_file(tmp_path / "pkg" / "__init__.py", "")
        _write_file(tmp_path / "pkg" / "a.py", "def func_a():\n    pass\n")
        _write_file(
            tmp_path / "pkg" / "b.py",
            "from pkg.a import func_a\n\ndef func_b():\n    return func_a()\n",
        )

        scan_repository(store, tmp_path)

        # b imports a
        mod_b_nid = node_id(NodeType.MODULE, "pkg.b")
        import_edges = store.get_edges_from(mod_b_nid, EdgeType.IMPORTS)
        assert len(import_edges) == 1
        assert import_edges[0].target_id == node_id(NodeType.MODULE, "pkg.a")

    def test_non_python_files_ignored(self, store, tmp_path):
        _write_file(tmp_path / "readme.md", "# Hello\n")
        _write_file(tmp_path / "config.json", '{"key": "value"}\n')
        _write_file(tmp_path / "code.py", "x = 1\n")

        counts = scan_repository(store, tmp_path)
        assert counts["modules"] == 1  # Only code.py
