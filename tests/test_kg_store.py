# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for the knowledge graph SQLite store."""

import pytest

from src.knowledge_graph.schema import EdgeType, NodeType, node_id
from src.knowledge_graph.store import GraphStore


@pytest.fixture
def store():
    """Create an in-memory GraphStore for testing."""
    s = GraphStore(":memory:")
    s.initialize()
    yield s
    s.close()


class TestNodeId:
    def test_basic(self):
        assert node_id(NodeType.FIXTURE, 1) == "fixture:1"

    def test_string_type(self):
        assert node_id("preset", "4.2") == "preset:4.2"

    def test_executor(self):
        assert node_id(NodeType.EXECUTOR, "1.5") == "executor:1.5"


class TestStoreInit:
    def test_creates_tables(self, store):
        assert store.node_count() == 0
        assert store.edge_count() == 0

    def test_double_init_is_safe(self, store):
        store.initialize()
        assert store.node_count() == 0

    def test_stats_empty(self, store):
        stats = store.stats()
        assert stats["total_nodes"] == 0
        assert stats["total_edges"] == 0


class TestNodeCrud:
    def test_upsert_and_get(self, store):
        node = store.upsert_node("fixture:1", NodeType.FIXTURE, label="Mac700 #1")
        assert node.node_id == "fixture:1"
        assert node.label == "Mac700 #1"

        fetched = store.get_node("fixture:1")
        assert fetched is not None
        assert fetched.node_type == "fixture"
        assert fetched.label == "Mac700 #1"

    def test_get_missing_returns_none(self, store):
        assert store.get_node("fixture:999") is None

    def test_upsert_updates_existing(self, store):
        store.upsert_node("fixture:1", NodeType.FIXTURE, label="Old")
        store.upsert_node("fixture:1", NodeType.FIXTURE, label="New")
        node = store.get_node("fixture:1")
        assert node is not None
        assert node.label == "New"

    def test_props_roundtrip(self, store):
        store.upsert_node("fixture:1", NodeType.FIXTURE, props={"universe": 1, "address": 101})
        node = store.get_node("fixture:1")
        assert node is not None
        assert node.props == {"universe": 1, "address": 101}

    def test_get_nodes_by_type(self, store):
        store.upsert_node("fixture:1", NodeType.FIXTURE, label="F1")
        store.upsert_node("fixture:2", NodeType.FIXTURE, label="F2")
        store.upsert_node("group:1", NodeType.GROUP, label="G1")

        fixtures = store.get_nodes_by_type(NodeType.FIXTURE)
        assert len(fixtures) == 2
        groups = store.get_nodes_by_type(NodeType.GROUP)
        assert len(groups) == 1

    def test_delete_node(self, store):
        store.upsert_node("fixture:1", NodeType.FIXTURE)
        assert store.delete_node("fixture:1") is True
        assert store.get_node("fixture:1") is None
        assert store.delete_node("fixture:1") is False

    def test_delete_node_cascades_edges(self, store):
        store.upsert_node("fixture:1", NodeType.FIXTURE)
        store.upsert_node("group:1", NodeType.GROUP)
        store.upsert_edge("fixture:1", "group:1", EdgeType.MEMBER_OF)
        assert store.edge_count() == 1

        store.delete_node("fixture:1")
        assert store.edge_count() == 0

    def test_delete_nodes_by_type(self, store):
        store.upsert_node("fixture:1", NodeType.FIXTURE)
        store.upsert_node("fixture:2", NodeType.FIXTURE)
        store.upsert_node("group:1", NodeType.GROUP)
        count = store.delete_nodes_by_type(NodeType.FIXTURE)
        assert count == 2
        assert store.node_count() == 1

    def test_node_count_filtered(self, store):
        store.upsert_node("fixture:1", NodeType.FIXTURE)
        store.upsert_node("group:1", NodeType.GROUP)
        assert store.node_count(NodeType.FIXTURE) == 1
        assert store.node_count(NodeType.GROUP) == 1
        assert store.node_count() == 2


class TestEdgeCrud:
    def test_upsert_and_get(self, store):
        store.upsert_node("fixture:1", NodeType.FIXTURE)
        store.upsert_node("group:1", NodeType.GROUP)
        edge = store.upsert_edge("fixture:1", "group:1", EdgeType.MEMBER_OF)
        assert edge.source_id == "fixture:1"
        assert edge.target_id == "group:1"
        assert edge.edge_type == "member_of"

    def test_edge_props(self, store):
        store.upsert_node("sequence:1", NodeType.SEQUENCE)
        store.upsert_node("executor:1.1", NodeType.EXECUTOR)
        edge = store.upsert_edge(
            "sequence:1", "executor:1.1", EdgeType.ASSIGNED_TO,
            props={"page": 1, "priority": "normal"},
        )
        assert edge.props == {"page": 1, "priority": "normal"}

    def test_upsert_updates_edge(self, store):
        store.upsert_node("fixture:1", NodeType.FIXTURE)
        store.upsert_node("group:1", NodeType.GROUP)
        store.upsert_edge("fixture:1", "group:1", EdgeType.MEMBER_OF, props={"old": True})
        store.upsert_edge("fixture:1", "group:1", EdgeType.MEMBER_OF, props={"new": True})
        edges = store.get_edges_from("fixture:1", EdgeType.MEMBER_OF)
        assert len(edges) == 1
        assert edges[0].props == {"new": True}

    def test_get_edges_from(self, store):
        store.upsert_node("fixture:1", NodeType.FIXTURE)
        store.upsert_node("group:1", NodeType.GROUP)
        store.upsert_node("group:2", NodeType.GROUP)
        store.upsert_edge("fixture:1", "group:1", EdgeType.MEMBER_OF)
        store.upsert_edge("fixture:1", "group:2", EdgeType.MEMBER_OF)

        all_edges = store.get_edges_from("fixture:1")
        assert len(all_edges) == 2
        typed_edges = store.get_edges_from("fixture:1", EdgeType.MEMBER_OF)
        assert len(typed_edges) == 2

    def test_get_edges_to(self, store):
        store.upsert_node("fixture:1", NodeType.FIXTURE)
        store.upsert_node("fixture:2", NodeType.FIXTURE)
        store.upsert_node("group:1", NodeType.GROUP)
        store.upsert_edge("fixture:1", "group:1", EdgeType.MEMBER_OF)
        store.upsert_edge("fixture:2", "group:1", EdgeType.MEMBER_OF)

        incoming = store.get_edges_to("group:1", EdgeType.MEMBER_OF)
        assert len(incoming) == 2

    def test_delete_edge(self, store):
        store.upsert_node("fixture:1", NodeType.FIXTURE)
        store.upsert_node("group:1", NodeType.GROUP)
        store.upsert_edge("fixture:1", "group:1", EdgeType.MEMBER_OF)
        assert store.delete_edge("fixture:1", "group:1", EdgeType.MEMBER_OF) is True
        assert store.edge_count() == 0
        assert store.delete_edge("fixture:1", "group:1", EdgeType.MEMBER_OF) is False

    def test_delete_edges_by_type(self, store):
        store.upsert_node("fixture:1", NodeType.FIXTURE)
        store.upsert_node("group:1", NodeType.GROUP)
        store.upsert_node("group:2", NodeType.GROUP)
        store.upsert_edge("fixture:1", "group:1", EdgeType.MEMBER_OF)
        store.upsert_edge("fixture:1", "group:2", EdgeType.MEMBER_OF)
        count = store.delete_edges_by_type(EdgeType.MEMBER_OF)
        assert count == 2
        assert store.edge_count() == 0

    def test_edge_count_filtered(self, store):
        store.upsert_node("fixture:1", NodeType.FIXTURE)
        store.upsert_node("group:1", NodeType.GROUP)
        store.upsert_node("sequence:1", NodeType.SEQUENCE)
        store.upsert_edge("fixture:1", "group:1", EdgeType.MEMBER_OF)
        store.upsert_edge("sequence:1", "fixture:1", EdgeType.HAS_CUE)
        assert store.edge_count(EdgeType.MEMBER_OF) == 1
        assert store.edge_count(EdgeType.HAS_CUE) == 1
        assert store.edge_count() == 2


class TestBulkOps:
    def test_clear(self, store):
        store.upsert_node("fixture:1", NodeType.FIXTURE)
        store.upsert_node("group:1", NodeType.GROUP)
        store.upsert_edge("fixture:1", "group:1", EdgeType.MEMBER_OF)
        store.clear()
        assert store.node_count() == 0
        assert store.edge_count() == 0

    def test_stats(self, store):
        store.upsert_node("fixture:1", NodeType.FIXTURE)
        store.upsert_node("fixture:2", NodeType.FIXTURE)
        store.upsert_node("group:1", NodeType.GROUP)
        store.upsert_edge("fixture:1", "group:1", EdgeType.MEMBER_OF)

        stats = store.stats()
        assert stats["nodes:fixture"] == 2
        assert stats["nodes:group"] == 1
        assert stats["edges:member_of"] == 1
        assert stats["total_nodes"] == 3
        assert stats["total_edges"] == 1
