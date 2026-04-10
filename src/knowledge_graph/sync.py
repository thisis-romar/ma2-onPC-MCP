# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
sync.py — Sync ConsoleStateSnapshot data into the knowledge graph.

Populates nodes and edges from the hydrated snapshot. Called once after
ConsoleStateHydrator completes — no additional telnet traffic needed.

Uses incremental delta sync: upserts nodes/edges from the snapshot, then
prunes any nodes that are no longer present (stale leftovers from a
previous sync cycle).
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

    Uses incremental delta sync: upserts all nodes and edges derived from
    the snapshot, then prunes stale nodes that were not touched during this
    cycle.  This avoids the full clear+rebuild cost and keeps the graph
    readable during sync.

    Returns a stats dict with counts of synced/pruned nodes and edges.
    """
    seen_node_ids: set[str] = set()
    seen_edge_keys: set[tuple[str, str, str]] = set()
    counts = {"nodes": 0, "edges": 0, "pruned_nodes": 0, "pruned_edges": 0}

    _sync_users(store, snapshot, counts, seen_node_ids)
    _sync_fixture_types(store, snapshot, counts, seen_node_ids)
    _sync_pool_entries(store, snapshot, counts, seen_node_ids)
    _sync_sequences(store, snapshot, counts, seen_node_ids)
    _sync_cues(store, snapshot, counts, seen_node_ids, seen_edge_keys)
    _sync_executors(store, snapshot, counts, seen_node_ids, seen_edge_keys)
    _sync_worlds(store, snapshot, counts, seen_node_ids)
    _sync_filters(store, snapshot, counts, seen_node_ids)
    _sync_instance_of_edges(store, snapshot, counts, seen_node_ids, seen_edge_keys)

    # Prune stale nodes and edges not seen during this sync cycle
    pruned = _prune_stale(store, seen_node_ids, seen_edge_keys)
    counts["pruned_nodes"] = pruned["pruned_nodes"]
    counts["pruned_edges"] = pruned["pruned_edges"]

    logger.info(
        "KG sync complete: %d nodes, %d edges upserted, "
        "%d nodes, %d edges pruned (snapshot age %.1fs)",
        counts["nodes"], counts["edges"],
        counts["pruned_nodes"], counts["pruned_edges"],
        snapshot.age_seconds(),
    )
    return counts


def _sync_users(
    store: GraphStore,
    snapshot: ConsoleStateSnapshot,
    counts: dict[str, int],
    seen: set[str],
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
    seen.add(uid)
    counts["nodes"] += 1


def _sync_fixture_types(
    store: GraphStore,
    snapshot: ConsoleStateSnapshot,
    counts: dict[str, int],
    seen: set[str],
) -> None:
    """Sync fixture type inventory."""
    for i, ft_name in enumerate(snapshot.fixture_types, start=1):
        ftid = node_id(NodeType.FIXTURE_TYPE, i)
        store.upsert_node(ftid, NodeType.FIXTURE_TYPE, label=ft_name)
        seen.add(ftid)
        counts["nodes"] += 1


def _sync_pool_entries(
    store: GraphStore,
    snapshot: ConsoleStateSnapshot,
    counts: dict[str, int],
    seen: set[str],
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
            seen.add(nid)
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
            seen.add(pid)
            counts["nodes"] += 1


def _sync_sequences(
    store: GraphStore,
    snapshot: ConsoleStateSnapshot,
    counts: dict[str, int],
    seen: set[str],
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
        seen.add(sid)
        counts["nodes"] += 1


def _sync_cues(
    store: GraphStore,
    snapshot: ConsoleStateSnapshot,
    counts: dict[str, int],
    seen: set[str],
    seen_edges: set[tuple[str, str, str]],
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
        seen.add(cid)
        counts["nodes"] += 1

        # Edge: sequence → cue
        sid = node_id(NodeType.SEQUENCE, cue.sequence_id)
        if store.get_node(sid) is not None:
            store.upsert_edge(
                sid, cid, EdgeType.HAS_CUE,
                props={"cue_number": cue.cue_number},
            )
            seen_edges.add((sid, cid, str(EdgeType.HAS_CUE)))
            counts["edges"] += 1


def _sync_executors(
    store: GraphStore,
    snapshot: ConsoleStateSnapshot,
    counts: dict[str, int],
    seen: set[str],
    seen_edges: set[tuple[str, str, str]],
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
        seen.add(eid)
        counts["nodes"] += 1

        # Edge: sequence ↔ executor (only if the sequence node exists)
        if ex.sequence_id is not None:
            sid = node_id(NodeType.SEQUENCE, ex.sequence_id)
            if store.get_node(sid) is not None:
                store.upsert_edge(
                    sid, eid, EdgeType.ASSIGNED_TO,
                    props={"page": ex.page, "priority": ex.priority},
                )
                seen_edges.add((sid, eid, str(EdgeType.ASSIGNED_TO)))
                counts["edges"] += 1

                # Edge: executor → sequence (controls)
                store.upsert_edge(eid, sid, EdgeType.CONTROLS)
                seen_edges.add((eid, sid, str(EdgeType.CONTROLS)))
                counts["edges"] += 1


def _sync_worlds(
    store: GraphStore,
    snapshot: ConsoleStateSnapshot,
    counts: dict[str, int],
    seen: set[str],
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
        seen.add(wid)
        counts["nodes"] += 1


def _sync_filters(
    store: GraphStore,
    snapshot: ConsoleStateSnapshot,
    counts: dict[str, int],
    seen: set[str],
) -> None:
    """Sync filter state."""
    if snapshot.active_filter is not None:
        fid = node_id(NodeType.FILTER, snapshot.active_filter)
        # Upsert — if already created by pool index, just update props
        existing = store.get_node(fid)
        if existing is None:
            store.upsert_node(
                fid,
                NodeType.FILTER,
                label=f"Filter {snapshot.active_filter}",
                props={"active": True, "vte": snapshot.filter_vte},
            )
            counts["nodes"] += 1
        else:
            # Update the existing node with active flag
            props = {**existing.props, "active": True, "vte": snapshot.filter_vte}
            store.upsert_node(fid, NodeType.FILTER, label=existing.label, props=props)
        seen.add(fid)


def _sync_instance_of_edges(
    store: GraphStore,
    snapshot: ConsoleStateSnapshot,
    counts: dict[str, int],
    seen: set[str],
    seen_edges: set[tuple[str, str, str]],
) -> None:
    """Create INSTANCE_OF edges linking fixtures to their fixture types.

    Uses fixture name prefix matching against known fixture type names.
    E.g. fixture "Mac700 #1" matches fixture_type "Mac700" or "Mac 700".

    This is a best-effort heuristic — exact mapping requires FixtureType.Mode
    data not available in the basic pool list.
    """
    if not snapshot.fixture_types:
        return

    # Build a lookup: lowercase fixture type name → fixture_type node_id
    ft_index: list[tuple[str, str]] = []
    for i, ft_name in enumerate(snapshot.fixture_types, start=1):
        ftid = node_id(NodeType.FIXTURE_TYPE, i)
        ft_index.append((ft_name.lower(), ftid))

    # Sort by name length descending so longer (more specific) names match first
    ft_index.sort(key=lambda t: len(t[0]), reverse=True)

    idx = snapshot.name_index
    for entry in idx.all_entries("fixture"):
        fix_name_lower = entry["name"].lower()
        fix_nid = node_id(NodeType.FIXTURE, entry["id"])
        if fix_nid not in seen:
            continue  # fixture node wasn't synced

        for ft_name_lower, ftid in ft_index:
            if fix_name_lower.startswith(ft_name_lower):
                store.upsert_edge(fix_nid, ftid, EdgeType.INSTANCE_OF)
                seen_edges.add((fix_nid, ftid, str(EdgeType.INSTANCE_OF)))
                counts["edges"] += 1
                break


def _prune_stale(
    store: GraphStore,
    seen_node_ids: set[str],
    seen_edge_keys: set[tuple[str, str, str]],
) -> dict[str, int]:
    """Remove nodes and edges that were not touched during this sync cycle.

    Returns counts of pruned nodes and edges.
    """
    pruned = {"pruned_nodes": 0, "pruned_edges": 0}

    # Prune stale edges first (before deleting nodes, which cascades)
    all_edges = store.conn.execute(
        "SELECT source_id, target_id, edge_type FROM kg_edges"
    ).fetchall()
    for src, tgt, etype in all_edges:
        if (src, tgt, etype) not in seen_edge_keys:
            store.delete_edge(src, tgt, etype)
            pruned["pruned_edges"] += 1

    # Prune stale nodes
    all_node_ids = [
        row[0] for row in store.conn.execute("SELECT node_id FROM kg_nodes").fetchall()
    ]
    for nid in all_node_ids:
        if nid not in seen_node_ids:
            store.delete_node(nid)
            pruned["pruned_nodes"] += 1

    return pruned
