# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
sync.py — Sync ConsoleStateSnapshot data into the knowledge graph.

Populates nodes and edges from the hydrated snapshot. Called once after
ConsoleStateHydrator completes — no additional telnet traffic needed.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .schema import EdgeType, NodeType, node_id
from .store import GraphStore

if TYPE_CHECKING:
    from ..console_state import ConsoleStateSnapshot

logger = logging.getLogger(__name__)


def sync_snapshot(store: GraphStore, snapshot: ConsoleStateSnapshot) -> dict[str, int]:
    """Populate the knowledge graph from a ConsoleStateSnapshot.

    Clears existing graph data and rebuilds from the snapshot.
    Returns a stats dict with counts of synced nodes and edges.

    This is a full-replace sync: the graph is the snapshot's structured view.
    Incremental sync (Phase 4) will be added later.
    """
    store.clear()

    counts = {"nodes": 0, "edges": 0}

    _sync_users(store, snapshot, counts)
    _sync_fixture_types(store, snapshot, counts)
    _sync_pool_entries(store, snapshot, counts)
    _sync_sequences(store, snapshot, counts)
    _sync_cues(store, snapshot, counts)
    _sync_executors(store, snapshot, counts)
    _sync_worlds(store, snapshot, counts)
    _sync_filters(store, snapshot, counts)

    logger.info(
        "KG sync complete: %d nodes, %d edges from snapshot (age %.1fs)",
        counts["nodes"], counts["edges"], snapshot.age_seconds(),
    )
    return counts


def _sync_users(
    store: GraphStore,
    snapshot: ConsoleStateSnapshot,
    counts: dict[str, int],
) -> None:
    """Sync the active user as a node with role edge."""
    if not snapshot.active_user:
        return

    uid = node_id(NodeType.USER, snapshot.active_user)
    store.upsert_node(
        uid,
        NodeType.USER,
        label=snapshot.active_user,
        props={
            "rights": snapshot.user_rights_str,
            "ma2_right": str(snapshot.user_right),
            "profile": snapshot.active_user_profile,
        },
    )
    counts["nodes"] += 1


def _sync_fixture_types(
    store: GraphStore,
    snapshot: ConsoleStateSnapshot,
    counts: dict[str, int],
) -> None:
    """Sync fixture type inventory."""
    for i, ft_name in enumerate(snapshot.fixture_types, start=1):
        ftid = node_id(NodeType.FIXTURE_TYPE, i)
        store.upsert_node(ftid, NodeType.FIXTURE_TYPE, label=ft_name)
        counts["nodes"] += 1


def _sync_pool_entries(
    store: GraphStore,
    snapshot: ConsoleStateSnapshot,
    counts: dict[str, int],
) -> None:
    """Sync pool name index entries as nodes.

    Maps pool object types to KG node types where applicable.
    """
    pool_type_map: dict[str, NodeType] = {
        "fixture": NodeType.FIXTURE,
        "group": NodeType.GROUP,
        "sequence": NodeType.SEQUENCE,
        "executor": NodeType.EXECUTOR,
        "world": NodeType.WORLD,
        "filter": NodeType.FILTER,
    }

    idx = snapshot.name_index

    for pool_type in idx.indexed_types():
        kg_type = pool_type_map.get(pool_type.lower())
        if kg_type is None:
            # Preset pools and others not directly mapped to top-level node types
            # are handled via preset-specific logic below.
            continue

        for entry in idx.all_entries(pool_type):
            nid = node_id(kg_type, entry["id"])
            store.upsert_node(nid, kg_type, label=entry["name"])
            counts["nodes"] += 1

    # Sync preset pool entries (keyed by preset_type 1-7)
    for preset_type_id in range(1, 8):
        for entry in idx.all_entries("preset", preset_type=preset_type_id):
            pid = node_id(NodeType.PRESET, f"{preset_type_id}.{entry['id']}")
            store.upsert_node(
                pid,
                NodeType.PRESET,
                label=entry["name"],
                props={"preset_type": preset_type_id},
            )
            counts["nodes"] += 1


def _sync_sequences(
    store: GraphStore,
    snapshot: ConsoleStateSnapshot,
    counts: dict[str, int],
) -> None:
    """Sync sequence entries with their properties."""
    for seq in snapshot.sequences:
        sid = node_id(NodeType.SEQUENCE, seq.id)
        store.upsert_node(
            sid,
            NodeType.SEQUENCE,
            label=seq.label,
            props={
                "loop": seq.loop,
                "chaser": seq.chaser,
                "autoprepare": seq.autoprepare,
                "speed_master": seq.speed_master,
            },
        )
        counts["nodes"] += 1


def _sync_cues(
    store: GraphStore,
    snapshot: ConsoleStateSnapshot,
    counts: dict[str, int],
) -> None:
    """Sync cue records and link them to their sequences."""
    for cue in snapshot.sequence_cues:
        cid = node_id(NodeType.CUE, f"{cue.sequence_id}.{cue.cue_number}")
        store.upsert_node(
            cid,
            NodeType.CUE,
            label=cue.label,
            props={
                "cue_number": cue.cue_number,
                "sequence_id": cue.sequence_id,
                "parts": len(cue.parts),
            },
        )
        counts["nodes"] += 1

        # Edge: sequence → cue
        sid = node_id(NodeType.SEQUENCE, cue.sequence_id)
        if store.get_node(sid) is not None:
            store.upsert_edge(
                sid, cid, EdgeType.HAS_CUE,
                props={"cue_number": cue.cue_number},
            )
            counts["edges"] += 1


def _sync_executors(
    store: GraphStore,
    snapshot: ConsoleStateSnapshot,
    counts: dict[str, int],
) -> None:
    """Sync executor state and link executors to sequences."""
    for exec_id, ex in snapshot.executor_state.items():
        eid = node_id(NodeType.EXECUTOR, f"{ex.page}.{exec_id}")
        store.upsert_node(
            eid,
            NodeType.EXECUTOR,
            label=ex.label,
            props={
                "page": ex.page,
                "priority": ex.priority,
                "button_function": ex.button_function,
                "fader_function": ex.fader_function,
                "ooo": ex.ooo,
                "kill_protect": ex.kill_protect,
                "auto_start": ex.auto_start,
            },
        )
        counts["nodes"] += 1

        # Edge: sequence → executor (assigned_to)
        if ex.sequence_id is not None:
            sid = node_id(NodeType.SEQUENCE, ex.sequence_id)
            store.upsert_edge(
                sid, eid, EdgeType.ASSIGNED_TO,
                props={"page": ex.page, "priority": ex.priority},
            )
            counts["edges"] += 1

            # Edge: executor → sequence (controls)
            store.upsert_edge(eid, sid, EdgeType.CONTROLS)
            counts["edges"] += 1


def _sync_worlds(
    store: GraphStore,
    snapshot: ConsoleStateSnapshot,
    counts: dict[str, int],
) -> None:
    """Sync world labels."""
    for world_id, label in snapshot.world_labels.items():
        wid = node_id(NodeType.WORLD, world_id)
        store.upsert_node(
            wid,
            NodeType.WORLD,
            label=label,
            props={"active": world_id == snapshot.active_world},
        )
        counts["nodes"] += 1


def _sync_filters(
    store: GraphStore,
    snapshot: ConsoleStateSnapshot,
    counts: dict[str, int],
) -> None:
    """Sync filter state."""
    if snapshot.active_filter is not None:
        fid = node_id(NodeType.FILTER, snapshot.active_filter)
        # Only create if not already in pool index
        if store.get_node(fid) is None:
            store.upsert_node(
                fid,
                NodeType.FILTER,
                label=f"Filter {snapshot.active_filter}",
                props={"active": True, "vte": snapshot.filter_vte},
            )
            counts["nodes"] += 1
