# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for knowledge graph sync from ConsoleStateSnapshot."""

import pytest

from src.commands.constants import MA2Right
from src.console_state import (
    ConsoleStateSnapshot,
    CuePart,
    CueRecord,
    ExecutorState,
    SequenceEntry,
)
from src.knowledge_graph.schema import EdgeType, NodeType
from src.knowledge_graph.store import GraphStore
from src.knowledge_graph.sync import sync_snapshot
from src.pool_name_index import PoolNameIndex


@pytest.fixture
def store():
    s = GraphStore(":memory:")
    s.initialize()
    yield s
    s.close()


def _make_snapshot(**overrides) -> ConsoleStateSnapshot:
    """Build a ConsoleStateSnapshot with sensible defaults, accepting overrides."""
    defaults = {
        "active_user": "administrator",
        "user_rights_str": "Admin",
        "user_right": MA2Right.ADMIN,
        "active_user_profile": "Default",
        "showfile": "test_show",
        "version": "3.9.60.65",
    }
    defaults.update(overrides)
    return ConsoleStateSnapshot(**defaults)


def _make_index_with_fixtures() -> PoolNameIndex:
    """Build a PoolNameIndex with sample fixtures and groups."""
    idx = PoolNameIndex()
    idx.add_entry("Fixture", "Mac700 #1", 1)
    idx.add_entry("Fixture", "Mac700 #2", 2)
    idx.add_entry("Fixture", "Mac700 #3", 3)
    idx.add_entry("Group", "Front Wash", 1)
    idx.add_entry("Group", "Back Fill", 2)
    idx.add_entry("Sequence", "Main Show", 1)
    return idx


def _make_index_with_presets() -> PoolNameIndex:
    """Build a PoolNameIndex with preset entries."""
    idx = _make_index_with_fixtures()
    # Color presets (preset_type=4)
    idx.add_entry("Preset", "Red", 1, preset_type=4)
    idx.add_entry("Preset", "Blue", 2, preset_type=4)
    # Position presets (preset_type=2)
    idx.add_entry("Preset", "Center", 1, preset_type=2)
    return idx


class TestSyncUser:
    def test_syncs_active_user(self, store):
        snap = _make_snapshot()
        counts = sync_snapshot(store, snap)
        assert counts["nodes"] >= 1

        user_node = store.get_node("user:administrator")
        assert user_node is not None
        assert user_node.label == "administrator"
        assert user_node.props["rights"] == "Admin"
        assert user_node.props["ma2_right"] == str(MA2Right.ADMIN)

    def test_no_user_when_empty(self, store):
        snap = _make_snapshot(active_user="")
        sync_snapshot(store, snap)
        assert store.node_count(NodeType.USER) == 0


class TestSyncFixtureTypes:
    def test_syncs_fixture_types(self, store):
        snap = _make_snapshot(fixture_types=["Mac 700", "VL3000", "Generic Dimmer"])
        sync_snapshot(store, snap)
        ft_nodes = store.get_nodes_by_type(NodeType.FIXTURE_TYPE)
        assert len(ft_nodes) == 3
        labels = {n.label for n in ft_nodes}
        assert "Mac 700" in labels
        assert "VL3000" in labels


class TestSyncPoolEntries:
    def test_syncs_fixtures_and_groups(self, store):
        idx = _make_index_with_fixtures()
        snap = _make_snapshot(name_index=idx)
        sync_snapshot(store, snap)

        fixtures = store.get_nodes_by_type(NodeType.FIXTURE)
        assert len(fixtures) == 3
        groups = store.get_nodes_by_type(NodeType.GROUP)
        assert len(groups) == 2
        sequences = store.get_nodes_by_type(NodeType.SEQUENCE)
        assert len(sequences) == 1

    def test_syncs_presets(self, store):
        idx = _make_index_with_presets()
        snap = _make_snapshot(name_index=idx)
        sync_snapshot(store, snap)

        presets = store.get_nodes_by_type(NodeType.PRESET)
        assert len(presets) == 3  # 2 color + 1 position

        red = store.get_node("preset:4.1")
        assert red is not None
        assert red.label == "Red"
        assert red.props["preset_type"] == 4

        center = store.get_node("preset:2.1")
        assert center is not None
        assert center.label == "Center"


class TestSyncSequences:
    def test_syncs_sequence_properties(self, store):
        snap = _make_snapshot(
            sequences=[
                SequenceEntry(id=1, label="Main Show", loop=False, chaser=False),
                SequenceEntry(id=2, label="Chase 1", loop=True, chaser=True, speed_master=1),
            ],
        )
        sync_snapshot(store, snap)

        seq_nodes = store.get_nodes_by_type(NodeType.SEQUENCE)
        assert len(seq_nodes) == 2

        seq2 = store.get_node("sequence:2")
        assert seq2 is not None
        assert seq2.label == "Chase 1"
        assert seq2.props["chaser"] is True
        assert seq2.props["speed_master"] == 1


class TestSyncCues:
    def test_syncs_cues_with_edges(self, store):
        snap = _make_snapshot(
            sequences=[SequenceEntry(id=1, label="Main Show")],
            sequence_cues=[
                CueRecord(sequence_id=1, cue_number=1.0, label="Blackout"),
                CueRecord(sequence_id=1, cue_number=2.0, label="Warm Open"),
            ],
        )
        sync_snapshot(store, snap)

        cue_nodes = store.get_nodes_by_type(NodeType.CUE)
        assert len(cue_nodes) == 2

        # Verify sequence → cue edges
        edges = store.get_edges_from("sequence:1", EdgeType.HAS_CUE)
        assert len(edges) == 2
        target_ids = {e.target_id for e in edges}
        assert "cue:1.1.0" in target_ids
        assert "cue:1.2.0" in target_ids

    def test_cue_with_parts(self, store):
        snap = _make_snapshot(
            sequences=[SequenceEntry(id=1, label="Show")],
            sequence_cues=[
                CueRecord(
                    sequence_id=1, cue_number=3.0, label="Multi-part",
                    parts=[CuePart(part=0, label="Base"), CuePart(part=1, label="Color")],
                ),
            ],
        )
        sync_snapshot(store, snap)

        cue = store.get_node("cue:1.3.0")
        assert cue is not None
        assert cue.props["parts"] == 2


class TestSyncExecutors:
    def test_syncs_executors_with_edges(self, store):
        snap = _make_snapshot(
            sequences=[SequenceEntry(id=5, label="Seq 5")],
            executor_state={
                1: ExecutorState(id=1, page=1, sequence_id=5, label="Main", priority="normal"),
                2: ExecutorState(id=2, page=1, sequence_id=None, label="Empty"),
            },
        )
        sync_snapshot(store, snap)

        exec_nodes = store.get_nodes_by_type(NodeType.EXECUTOR)
        assert len(exec_nodes) == 2

        # Executor with sequence → has assigned_to and controls edges
        assigned = store.get_edges_from("sequence:5", EdgeType.ASSIGNED_TO)
        assert len(assigned) == 1
        assert assigned[0].target_id == "executor:1.1"

        controls = store.get_edges_from("executor:1.1", EdgeType.CONTROLS)
        assert len(controls) == 1
        assert controls[0].target_id == "sequence:5"

        # Empty executor → no edges
        assert store.get_edges_from("executor:1.2", EdgeType.CONTROLS) == []

    def test_executor_with_missing_sequence_skips_edges(self, store):
        """When executor references a sequence that doesn't exist in the graph,
        no edges should be created (FK safety)."""
        snap = _make_snapshot(
            sequences=[],  # sequence 99 NOT in pool
            executor_state={
                1: ExecutorState(id=1, page=1, sequence_id=99, label="Orphan"),
            },
        )
        sync_snapshot(store, snap)

        # Executor node should exist
        exec_nodes = store.get_nodes_by_type(NodeType.EXECUTOR)
        assert len(exec_nodes) == 1

        # But no edges should be created since sequence:99 doesn't exist
        assert store.get_edges_from("executor:1.1", EdgeType.CONTROLS) == []
        assert store.get_edges_to("executor:1.1", EdgeType.ASSIGNED_TO) == []


class TestSyncWorlds:
    def test_syncs_worlds(self, store):
        snap = _make_snapshot(
            world_labels={1: "Full", 2: "Stage Left", 3: "Stage Right"},
            active_world=1,
        )
        sync_snapshot(store, snap)

        worlds = store.get_nodes_by_type(NodeType.WORLD)
        assert len(worlds) == 3

        full = store.get_node("world:1")
        assert full is not None
        assert full.props["active"] is True

        left = store.get_node("world:2")
        assert left is not None
        assert left.props["active"] is False


class TestSyncFilters:
    def test_syncs_active_filter(self, store):
        snap = _make_snapshot(active_filter=3)
        sync_snapshot(store, snap)

        f = store.get_node("filter:3")
        assert f is not None
        assert f.props["active"] is True

    def test_no_filter_when_none(self, store):
        snap = _make_snapshot(active_filter=None)
        sync_snapshot(store, snap)
        assert store.node_count(NodeType.FILTER) == 0


class TestFullSync:
    def test_full_sync_counts(self, store):
        idx = _make_index_with_presets()
        snap = _make_snapshot(
            name_index=idx,
            fixture_types=["Mac 700"],
            sequences=[SequenceEntry(id=1, label="Main")],
            sequence_cues=[
                CueRecord(sequence_id=1, cue_number=1.0, label="Cue 1"),
            ],
            executor_state={
                1: ExecutorState(id=1, page=1, sequence_id=1, label="Exec 1"),
            },
            world_labels={1: "Full"},
            active_world=1,
        )
        counts = sync_snapshot(store, snap)
        assert counts["nodes"] > 0
        assert counts["edges"] > 0

        stats = store.stats()
        assert stats["total_nodes"] > 10
        assert stats["total_edges"] >= 3  # has_cue + assigned_to + controls

    def test_double_sync_replaces(self, store):
        snap = _make_snapshot(fixture_types=["Mac 700", "VL3000"])
        sync_snapshot(store, snap)
        first_count = store.node_count()

        # Second sync with different data
        snap2 = _make_snapshot(fixture_types=["Generic Dimmer"])
        sync_snapshot(store, snap2)
        ft_nodes = store.get_nodes_by_type(NodeType.FIXTURE_TYPE)
        assert len(ft_nodes) == 1
        assert ft_nodes[0].label == "Generic Dimmer"
        # Total count should be different
        assert store.node_count() != first_count


class TestIncrementalSync:
    """Tests for incremental delta sync (pruning stale nodes/edges)."""

    def test_prunes_removed_fixture_types(self, store):
        """When fixture types are removed between syncs, stale nodes are pruned."""
        snap1 = _make_snapshot(fixture_types=["Mac 700", "VL3000", "Generic Dimmer"])
        sync_snapshot(store, snap1)
        assert store.node_count(NodeType.FIXTURE_TYPE) == 3

        # Second sync drops VL3000 and Generic Dimmer
        snap2 = _make_snapshot(fixture_types=["Mac 700"])
        counts = sync_snapshot(store, snap2)
        assert store.node_count(NodeType.FIXTURE_TYPE) == 1
        assert counts["pruned_nodes"] >= 2  # VL3000 + Generic Dimmer pruned

    def test_prunes_removed_sequences_and_edges(self, store):
        """When a sequence is removed, its node and edges are pruned."""
        snap1 = _make_snapshot(
            sequences=[
                SequenceEntry(id=1, label="Show A"),
                SequenceEntry(id=2, label="Show B"),
            ],
            sequence_cues=[
                CueRecord(sequence_id=1, cue_number=1.0, label="Cue 1"),
                CueRecord(sequence_id=2, cue_number=1.0, label="Cue 1"),
            ],
        )
        sync_snapshot(store, snap1)
        assert store.node_count(NodeType.SEQUENCE) == 2
        assert store.node_count(NodeType.CUE) == 2

        # Remove sequence 2 and its cues
        snap2 = _make_snapshot(
            sequences=[SequenceEntry(id=1, label="Show A")],
            sequence_cues=[
                CueRecord(sequence_id=1, cue_number=1.0, label="Cue 1"),
            ],
        )
        counts = sync_snapshot(store, snap2)
        assert store.node_count(NodeType.SEQUENCE) == 1
        assert store.node_count(NodeType.CUE) == 1
        assert counts["pruned_nodes"] >= 2  # sequence:2 + cue:2.1.0

    def test_upsert_updates_existing_nodes(self, store):
        """Incremental sync updates existing nodes rather than duplicating."""
        snap1 = _make_snapshot(
            sequences=[SequenceEntry(id=1, label="Old Name", chaser=False)],
        )
        sync_snapshot(store, snap1)
        seq = store.get_node("sequence:1")
        assert seq.label == "Old Name"
        assert seq.props["chaser"] is False

        # Sync again with updated label and property
        snap2 = _make_snapshot(
            sequences=[SequenceEntry(id=1, label="New Name", chaser=True)],
        )
        sync_snapshot(store, snap2)
        seq = store.get_node("sequence:1")
        assert seq.label == "New Name"
        assert seq.props["chaser"] is True
        assert store.node_count(NodeType.SEQUENCE) == 1  # no duplicates

    def test_prunes_stale_executor_edges(self, store):
        """When an executor's sequence changes, old edges are pruned."""
        snap1 = _make_snapshot(
            sequences=[
                SequenceEntry(id=1, label="Seq A"),
                SequenceEntry(id=2, label="Seq B"),
            ],
            executor_state={
                1: ExecutorState(id=1, page=1, sequence_id=1, label="Exec"),
            },
        )
        sync_snapshot(store, snap1)
        # Executor 1 → Seq 1
        edges = store.get_edges_from("executor:1.1", EdgeType.CONTROLS)
        assert len(edges) == 1
        assert edges[0].target_id == "sequence:1"

        # Reassign executor to Seq 2
        snap2 = _make_snapshot(
            sequences=[
                SequenceEntry(id=1, label="Seq A"),
                SequenceEntry(id=2, label="Seq B"),
            ],
            executor_state={
                1: ExecutorState(id=1, page=1, sequence_id=2, label="Exec"),
            },
        )
        counts = sync_snapshot(store, snap2)
        # Now executor 1 → Seq 2
        edges = store.get_edges_from("executor:1.1", EdgeType.CONTROLS)
        assert len(edges) == 1
        assert edges[0].target_id == "sequence:2"
        # Old edge should have been pruned
        assert counts["pruned_edges"] >= 2  # old assigned_to + old controls

    def test_counts_include_pruned(self, store):
        """Returned counts include pruned_nodes and pruned_edges keys."""
        snap = _make_snapshot()
        counts = sync_snapshot(store, snap)
        assert "pruned_nodes" in counts
        assert "pruned_edges" in counts
        assert counts["pruned_nodes"] >= 0
        assert counts["pruned_edges"] >= 0


class TestInstanceOfEdges:
    """Tests for INSTANCE_OF edges linking fixtures to fixture types."""

    def test_creates_instance_of_edges(self, store):
        """Fixtures whose names match fixture type names get INSTANCE_OF edges."""
        idx = PoolNameIndex()
        idx.add_entry("Fixture", "Mac 700 #1", 1)
        idx.add_entry("Fixture", "Mac 700 #2", 2)
        idx.add_entry("Fixture", "VL3000 Front", 3)
        snap = _make_snapshot(
            name_index=idx,
            fixture_types=["Mac 700", "VL3000"],
        )
        sync_snapshot(store, snap)

        # Mac 700 fixtures → fixture_type:1
        e1 = store.get_edges_from("fixture:1", EdgeType.INSTANCE_OF)
        assert len(e1) == 1
        assert e1[0].target_id == "fixture_type:1"

        e2 = store.get_edges_from("fixture:2", EdgeType.INSTANCE_OF)
        assert len(e2) == 1
        assert e2[0].target_id == "fixture_type:1"

        # VL3000 fixture → fixture_type:2
        e3 = store.get_edges_from("fixture:3", EdgeType.INSTANCE_OF)
        assert len(e3) == 1
        assert e3[0].target_id == "fixture_type:2"

    def test_no_instance_of_without_fixture_types(self, store):
        """No INSTANCE_OF edges created when fixture_types list is empty."""
        idx = PoolNameIndex()
        idx.add_entry("Fixture", "Mac 700 #1", 1)
        snap = _make_snapshot(name_index=idx, fixture_types=[])
        sync_snapshot(store, snap)

        edges = store.get_edges_from("fixture:1", EdgeType.INSTANCE_OF)
        assert len(edges) == 0

    def test_no_match_no_edge(self, store):
        """Fixture names that don't match any type name get no INSTANCE_OF edge."""
        idx = PoolNameIndex()
        idx.add_entry("Fixture", "Unknown Fixture", 1)
        snap = _make_snapshot(
            name_index=idx,
            fixture_types=["Mac 700", "VL3000"],
        )
        sync_snapshot(store, snap)

        edges = store.get_edges_from("fixture:1", EdgeType.INSTANCE_OF)
        assert len(edges) == 0

    def test_longest_match_wins(self, store):
        """When multiple type names could match, the longest prefix wins."""
        idx = PoolNameIndex()
        idx.add_entry("Fixture", "Mac 700 Wash #1", 1)
        snap = _make_snapshot(
            name_index=idx,
            fixture_types=["Mac", "Mac 700", "Mac 700 Wash"],
        )
        sync_snapshot(store, snap)

        edges = store.get_edges_from("fixture:1", EdgeType.INSTANCE_OF)
        assert len(edges) == 1
        # "Mac 700 Wash" is fixture_type:3 (3rd in list) — longest match
        assert edges[0].target_id == "fixture_type:3"
