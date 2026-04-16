# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for the cluster engine."""

from __future__ import annotations

import pytest

from src.knowledge_graph.analysis.cluster_engine import (
    assign_cluster_nodes,
    cluster_modules,
)
from src.knowledge_graph.schema import EdgeType, NodeType
from src.knowledge_graph.store import GraphStore


@pytest.fixture
def store():
    s = GraphStore(":memory:")
    s.initialize()
    yield s
    s.close()


def _build_two_groups(store):
    """Create two distinct module groups."""
    for n in ["src.a", "src.b", "src.c"]:
        store.upsert_node(f"module:{n}", NodeType.MODULE, label=n)
    for n in ["lib.x", "lib.y", "lib.z"]:
        store.upsert_node(f"module:{n}", NodeType.MODULE, label=n)
    # Intra-group imports
    store.upsert_edge("module:src.a", "module:src.b", EdgeType.IMPORTS)
    store.upsert_edge("module:src.b", "module:src.c", EdgeType.IMPORTS)
    store.upsert_edge("module:lib.x", "module:lib.y", EdgeType.IMPORTS)
    store.upsert_edge("module:lib.y", "module:lib.z", EdgeType.IMPORTS)
    # Add some DEFINES edges
    for n in ["src.a", "src.b", "src.c", "lib.x", "lib.y", "lib.z"]:
        store.upsert_node(f"symbol:{n}.func", NodeType.SYMBOL, label="func")
        store.upsert_edge(f"module:{n}", f"symbol:{n}.func", EdgeType.DEFINES)


class TestClusterModules:
    def test_basic(self, store):
        _build_two_groups(store)
        clusters = cluster_modules(store, n_clusters=2)
        assert len(clusters) == 2
        all_members = []
        for cl in clusters:
            all_members.extend(cl.members)
        assert len(all_members) == 6

    def test_auto_label(self, store):
        _build_two_groups(store)
        clusters = cluster_modules(store, n_clusters=2)
        labels = {cl.label for cl in clusters}
        # Should have meaningful labels from common prefixes
        assert all(len(lbl) > 0 for lbl in labels)

    def test_too_few_modules(self, store):
        store.upsert_node("module:only", NodeType.MODULE)
        clusters = cluster_modules(store)
        assert clusters == []

    def test_auto_detect_k(self, store):
        _build_two_groups(store)
        clusters = cluster_modules(store, n_clusters=0)
        assert len(clusters) >= 2


class TestAssignClusterNodes:
    def test_creates_nodes_and_edges(self, store):
        _build_two_groups(store)
        clusters = cluster_modules(store, n_clusters=2)
        count = assign_cluster_nodes(store, clusters)
        assert count > 0
        cluster_nodes = store.get_nodes_by_type(NodeType.CLUSTER)
        assert len(cluster_nodes) == 2
