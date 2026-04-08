# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for knowledge graph traversal queries."""

import pytest

from src.knowledge_graph.schema import EdgeType, NodeType, node_id
from src.knowledge_graph.store import GraphStore
from src.knowledge_graph.query import GraphQuery


@pytest.fixture
def store():
    """Create an in-memory GraphStore for testing."""
    s = GraphStore(":memory:")
    s.initialize()
    yield s
    s.close()


@pytest.fixture
def query(store):
    return GraphQuery(store)


def _build_playback_chain(store: GraphStore) -> None:
    """Build a typical playback chain: fixtures → group → sequence → cues → executor."""
    # Fixtures
    store.upsert_node("fixture:1", NodeType.FIXTURE, label="Mac700 #1")
    store.upsert_node("fixture:2", NodeType.FIXTURE, label="Mac700 #2")
    store.upsert_node("fixture:3", NodeType.FIXTURE, label="Mac700 #3")

    # Group
    store.upsert_node("group:1", NodeType.GROUP, label="Front Wash")

    # Fixture → Group (member_of)
    store.upsert_edge("fixture:1", "group:1", EdgeType.MEMBER_OF)
    store.upsert_edge("fixture:2", "group:1", EdgeType.MEMBER_OF)

    # Sequence
    store.upsert_node("sequence:1", NodeType.SEQUENCE, label="Main Show")

    # Cues
    store.upsert_node("cue:1.1", NodeType.CUE, label="Blackout", props={"cue_number": 1.0})
    store.upsert_node("cue:1.2", NodeType.CUE, label="Warm Open", props={"cue_number": 2.0})

    # Sequence → Cue (has_cue)
    store.upsert_edge("sequence:1", "cue:1.1", EdgeType.HAS_CUE, props={"cue_number": 1.0})
    store.upsert_edge("sequence:1", "cue:1.2", EdgeType.HAS_CUE, props={"cue_number": 2.0})

    # Executor
    store.upsert_node("executor:1.1", NodeType.EXECUTOR, label="Exec 1", props={"page": 1})

    # Sequence → Executor (assigned_to)
    store.upsert_edge("sequence:1", "executor:1.1", EdgeType.ASSIGNED_TO, props={"page": 1, "priority": "normal"})

    # Executor → Sequence (controls)
    store.upsert_edge("executor:1.1", "sequence:1", EdgeType.CONTROLS)

    # Preset
    store.upsert_node("preset:4.1", NodeType.PRESET, label="Red", props={"preset_type": 4})

    # Cue → Preset (uses_preset)
    store.upsert_edge("cue:1.2", "preset:4.1", EdgeType.USES_PRESET, props={"preset_type": 4})


class TestNeighbors:
    def test_neighbors_out(self, store, query):
        store.upsert_node("fixture:1", NodeType.FIXTURE)
        store.upsert_node("group:1", NodeType.GROUP)
        store.upsert_node("group:2", NodeType.GROUP)
        store.upsert_edge("fixture:1", "group:1", EdgeType.MEMBER_OF)
        store.upsert_edge("fixture:1", "group:2", EdgeType.MEMBER_OF)

        neighbors = query.neighbors_out("fixture:1")
        assert len(neighbors) == 2
        assert {n.node_id for n in neighbors} == {"group:1", "group:2"}

    def test_neighbors_out_filtered(self, store, query):
        store.upsert_node("fixture:1", NodeType.FIXTURE)
        store.upsert_node("group:1", NodeType.GROUP)
        store.upsert_node("fixture_type:1", NodeType.FIXTURE_TYPE)
        store.upsert_edge("fixture:1", "group:1", EdgeType.MEMBER_OF)
        store.upsert_edge("fixture:1", "fixture_type:1", EdgeType.INSTANCE_OF)

        members = query.neighbors_out("fixture:1", EdgeType.MEMBER_OF)
        assert len(members) == 1
        assert members[0].node_id == "group:1"

    def test_neighbors_in(self, store, query):
        store.upsert_node("fixture:1", NodeType.FIXTURE)
        store.upsert_node("fixture:2", NodeType.FIXTURE)
        store.upsert_node("group:1", NodeType.GROUP)
        store.upsert_edge("fixture:1", "group:1", EdgeType.MEMBER_OF)
        store.upsert_edge("fixture:2", "group:1", EdgeType.MEMBER_OF)

        members = query.neighbors_in("group:1", EdgeType.MEMBER_OF)
        assert len(members) == 2
        assert {n.node_id for n in members} == {"fixture:1", "fixture:2"}

    def test_neighbors_missing_node(self, store, query):
        assert query.neighbors_out("fixture:999") == []
        assert query.neighbors_in("fixture:999") == []


class TestBfs:
    def test_single_hop(self, store, query):
        _build_playback_chain(store)
        result = query.bfs("sequence:1", max_depth=1)
        # sequence → cue:1.1, cue:1.2, executor:1.1
        target_ids = {n.node_id for n in result.nodes}
        assert "sequence:1" in target_ids
        assert "cue:1.1" in target_ids
        assert "cue:1.2" in target_ids
        assert "executor:1.1" in target_ids

    def test_depth_limit(self, store, query):
        _build_playback_chain(store)
        result = query.bfs("sequence:1", max_depth=0)
        assert len(result.nodes) == 1
        assert result.nodes[0].node_id == "sequence:1"

    def test_multi_hop(self, store, query):
        _build_playback_chain(store)
        result = query.bfs("sequence:1", max_depth=2)
        target_ids = {n.node_id for n in result.nodes}
        # Depth 2: sequence → cue:1.2 → preset:4.1
        assert "preset:4.1" in target_ids

    def test_bfs_with_edge_filter(self, store, query):
        _build_playback_chain(store)
        result = query.bfs("sequence:1", max_depth=2, edge_types={EdgeType.HAS_CUE})
        target_ids = {n.node_id for n in result.nodes}
        assert "cue:1.1" in target_ids
        assert "executor:1.1" not in target_ids  # assigned_to edge filtered

    def test_bfs_bidirectional(self, store, query):
        _build_playback_chain(store)
        result = query.bfs("group:1", max_depth=1, direction="both")
        target_ids = {n.node_id for n in result.nodes}
        # incoming: fixture:1, fixture:2 (member_of edges point TO group)
        assert "fixture:1" in target_ids
        assert "fixture:2" in target_ids

    def test_bfs_missing_start(self, store, query):
        result = query.bfs("nonexistent:0")
        assert len(result.nodes) == 0


class TestFindPath:
    def test_direct_path(self, store, query):
        _build_playback_chain(store)
        path = query.find_path("sequence:1", "cue:1.1")
        assert path == ["sequence:1", "cue:1.1"]

    def test_two_hop_path(self, store, query):
        _build_playback_chain(store)
        path = query.find_path("sequence:1", "preset:4.1")
        assert path is not None
        assert path[0] == "sequence:1"
        assert path[-1] == "preset:4.1"
        assert len(path) == 3  # sequence → cue:1.2 → preset

    def test_no_path(self, store, query):
        _build_playback_chain(store)
        path = query.find_path("fixture:3", "preset:4.1")
        # fixture:3 has no edges
        assert path is None

    def test_self_path(self, store, query):
        store.upsert_node("fixture:1", NodeType.FIXTURE)
        path = query.find_path("fixture:1", "fixture:1")
        assert path == ["fixture:1"]

    def test_depth_limit_prevents_find(self, store, query):
        _build_playback_chain(store)
        path = query.find_path("sequence:1", "preset:4.1", max_depth=1)
        assert path is None  # 2 hops needed, max_depth=1


class TestDomainQueries:
    def test_fixtures_in_group(self, store, query):
        _build_playback_chain(store)
        fixtures = query.fixtures_in_group(1)
        assert len(fixtures) == 2
        assert {f.node_id for f in fixtures} == {"fixture:1", "fixture:2"}

    def test_fixtures_in_empty_group(self, store, query):
        store.upsert_node("group:99", NodeType.GROUP, label="Empty")
        assert query.fixtures_in_group(99) == []

    def test_groups_for_fixture(self, store, query):
        _build_playback_chain(store)
        groups = query.groups_for_fixture(1)
        assert len(groups) == 1
        assert groups[0].node_id == "group:1"

    def test_cues_in_sequence(self, store, query):
        _build_playback_chain(store)
        cues = query.cues_in_sequence(1)
        assert len(cues) == 2
        labels = {c.label for c in cues}
        assert "Blackout" in labels
        assert "Warm Open" in labels

    def test_executor_for_sequence(self, store, query):
        _build_playback_chain(store)
        executors = query.executor_for_sequence(1)
        assert len(executors) == 1
        assert executors[0].node_id == "executor:1.1"

    def test_sequence_on_executor(self, store, query):
        _build_playback_chain(store)
        seq = query.sequence_on_executor(1, page=1)
        assert seq is not None
        assert seq.node_id == "sequence:1"

    def test_sequence_on_empty_executor(self, store, query):
        store.upsert_node("executor:1.99", NodeType.EXECUTOR)
        assert query.sequence_on_executor(99, page=1) is None


class TestExpandContext:
    def test_expand_from_sequence(self, store, query):
        _build_playback_chain(store)
        result = query.expand_context("sequence:1", max_depth=2)
        node_ids = {n.node_id for n in result.nodes}
        # Should include sequence itself, cues, executor, and presets (2 hops)
        assert "sequence:1" in node_ids
        assert "cue:1.1" in node_ids
        assert "executor:1.1" in node_ids
        assert "preset:4.1" in node_ids

    def test_to_dict(self, store, query):
        _build_playback_chain(store)
        result = query.expand_context("sequence:1", max_depth=1)
        d = result.to_dict()
        assert "nodes" in d
        assert "edges" in d
        assert len(d["nodes"]) > 0
