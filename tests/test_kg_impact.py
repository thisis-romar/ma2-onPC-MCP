# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for the impact engine."""

from __future__ import annotations

import pytest

from src.knowledge_graph.analysis.impact_engine import compute_blast_radius, find_most_central
from src.knowledge_graph.schema import EdgeType, NodeType
from src.knowledge_graph.store import GraphStore


@pytest.fixture
def store():
    s = GraphStore(":memory:")
    s.initialize()
    yield s
    s.close()


def _build_chain(store, names):
    """Build A -> B -> C chain via IMPORTS edges."""
    for n in names:
        store.upsert_node(f"module:{n}", NodeType.MODULE, label=n)
    for i in range(len(names) - 1):
        store.upsert_edge(f"module:{names[i]}", f"module:{names[i+1]}", EdgeType.IMPORTS)


class TestBlastRadius:
    def test_direct(self, store):
        _build_chain(store, ["a", "b"])
        result = compute_blast_radius(store, "module:b")
        assert result.direct_dependents == ["module:a"]
        assert result.blast_radius == 1

    def test_transitive(self, store):
        _build_chain(store, ["a", "b", "c"])
        result = compute_blast_radius(store, "module:c")
        assert "module:b" in result.direct_dependents
        assert "module:a" in result.transitive_dependents
        assert result.blast_radius == 2

    def test_no_dependents(self, store):
        store.upsert_node("module:lonely", NodeType.MODULE)
        result = compute_blast_radius(store, "module:lonely")
        assert result.blast_radius == 0
        assert result.direct_dependents == []

    def test_with_cycles(self, store):
        for n in ["a", "b", "c"]:
            store.upsert_node(f"module:{n}", NodeType.MODULE, label=n)
        store.upsert_edge("module:a", "module:b", EdgeType.IMPORTS)
        store.upsert_edge("module:b", "module:c", EdgeType.IMPORTS)
        store.upsert_edge("module:c", "module:a", EdgeType.IMPORTS)
        result = compute_blast_radius(store, "module:a")
        assert result.blast_radius == 2  # b and c depend on a (via cycle)

    def test_max_depth(self, store):
        _build_chain(store, ["a", "b", "c", "d", "e"])
        result = compute_blast_radius(store, "module:e", max_depth=2)
        assert "module:d" in result.depth_map
        assert "module:c" in result.depth_map
        assert "module:b" not in result.depth_map


class TestMostCentral:
    def test_basic(self, store):
        for n in ["a", "b", "c"]:
            store.upsert_node(f"module:{n}", NodeType.MODULE, label=n)
        store.upsert_edge("module:a", "module:c", EdgeType.IMPORTS)
        store.upsert_edge("module:b", "module:c", EdgeType.IMPORTS)
        result = find_most_central(store, "module")
        assert result[0] == ("module:c", 2)
