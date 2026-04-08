# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for knowledge graph freshness tracking."""


import pytest

from src.knowledge_graph.schema import EdgeType, NodeType
from src.knowledge_graph.store import GraphStore


@pytest.fixture
def store():
    s = GraphStore(":memory:")
    s.initialize()
    yield s
    s.close()


class TestMarkStale:
    def test_mark_node_stale(self, store):
        store.upsert_node("fixture:1", NodeType.FIXTURE, label="F1")
        assert store.mark_stale("fixture:1") is True

        node = store.get_node("fixture:1")
        assert node is not None
        assert node.updated_at == "1970-01-01T00:00:00Z"

    def test_mark_missing_node_returns_false(self, store):
        assert store.mark_stale("fixture:999") is False

    def test_mark_type_stale(self, store):
        store.upsert_node("fixture:1", NodeType.FIXTURE, label="F1")
        store.upsert_node("fixture:2", NodeType.FIXTURE, label="F2")
        store.upsert_node("group:1", NodeType.GROUP, label="G1")

        count = store.mark_type_stale(NodeType.FIXTURE)
        assert count == 2

        f1 = store.get_node("fixture:1")
        assert f1 is not None
        assert f1.updated_at == "1970-01-01T00:00:00Z"

        # Group should not be stale
        g1 = store.get_node("group:1")
        assert g1 is not None
        assert g1.updated_at != "1970-01-01T00:00:00Z"


class TestStaleNodes:
    def test_find_stale_nodes(self, store):
        store.upsert_node("fixture:1", NodeType.FIXTURE, label="F1")
        store.upsert_node("fixture:2", NodeType.FIXTURE, label="F2")

        # Mark one as stale
        store.mark_stale("fixture:1")

        # Query for nodes older than "now"
        stale = store.stale_nodes("2000-01-01T00:00:00Z")
        assert len(stale) == 1
        assert stale[0].node_id == "fixture:1"

    def test_no_stale_nodes(self, store):
        store.upsert_node("fixture:1", NodeType.FIXTURE, label="F1")
        stale = store.stale_nodes("1970-01-01T00:00:00Z")
        assert len(stale) == 0


class TestIsFresh:
    def test_fresh_node(self, store):
        store.upsert_node("fixture:1", NodeType.FIXTURE, label="F1")
        # Node was just created, should be fresh relative to 2020
        assert store.is_fresh("fixture:1", "2020-01-01T00:00:00Z") is True

    def test_stale_node(self, store):
        store.upsert_node("fixture:1", NodeType.FIXTURE, label="F1")
        store.mark_stale("fixture:1")
        # Node is epoch, should not be fresh relative to 2020
        assert store.is_fresh("fixture:1", "2020-01-01T00:00:00Z") is False

    def test_missing_node_not_fresh(self, store):
        assert store.is_fresh("fixture:999", "2020-01-01T00:00:00Z") is False

    def test_refresh_after_stale(self, store):
        store.upsert_node("fixture:1", NodeType.FIXTURE, label="F1")
        store.mark_stale("fixture:1")
        assert store.is_fresh("fixture:1", "2020-01-01T00:00:00Z") is False

        # Re-upsert refreshes the timestamp
        store.upsert_node("fixture:1", NodeType.FIXTURE, label="F1 updated")
        assert store.is_fresh("fixture:1", "2020-01-01T00:00:00Z") is True


class TestFreshnessWorkflow:
    def test_stale_and_refresh_cycle(self, store):
        """Simulate: sync → mark stale → re-sync."""
        # Initial sync
        store.upsert_node("fixture:1", NodeType.FIXTURE, label="Mac700 #1")
        store.upsert_node("fixture:2", NodeType.FIXTURE, label="Mac700 #2")
        store.upsert_node("group:1", NodeType.GROUP, label="Front Wash")
        store.upsert_edge("fixture:1", "group:1", EdgeType.MEMBER_OF)

        assert store.node_count() == 3
        assert store.is_fresh("fixture:1", "2020-01-01T00:00:00Z")

        # After a DESTRUCTIVE step, mark fixtures stale
        store.mark_type_stale(NodeType.FIXTURE)
        assert not store.is_fresh("fixture:1", "2020-01-01T00:00:00Z")
        assert store.is_fresh("group:1", "2020-01-01T00:00:00Z")  # group still fresh

        # Re-sync (simulated by re-upsert)
        store.upsert_node("fixture:1", NodeType.FIXTURE, label="Mac700 #1")
        store.upsert_node("fixture:2", NodeType.FIXTURE, label="Mac700 #2")
        assert store.is_fresh("fixture:1", "2020-01-01T00:00:00Z")
        assert store.is_fresh("fixture:2", "2020-01-01T00:00:00Z")
