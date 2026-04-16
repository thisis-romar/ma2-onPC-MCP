# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
change_detector.py — Detect symbol-level changes between two graph snapshots.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..schema import EdgeType, NodeType
from ..store import GraphStore
from .impact_engine import compute_blast_radius


@dataclass
class ChangeSet:
    """Symbols that changed between two snapshots."""

    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    modified: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not self.added and not self.removed and not self.modified

    def to_dict(self) -> dict:
        return {
            "added": self.added,
            "removed": self.removed,
            "modified": self.modified,
            "total_changes": len(self.added) + len(self.removed) + len(self.modified),
        }


def detect_changes(
    old_symbols: dict[str, str],
    new_symbols: dict[str, str],
) -> ChangeSet:
    """Compare two symbol hash maps to find what changed."""
    old_keys = set(old_symbols)
    new_keys = set(new_symbols)
    return ChangeSet(
        added=sorted(new_keys - old_keys),
        removed=sorted(old_keys - new_keys),
        modified=sorted(k for k in old_keys & new_keys if old_symbols[k] != new_symbols[k]),
    )


def symbols_to_hash_map(store: GraphStore) -> dict[str, str]:
    """Walk all SYMBOL nodes and return {node_id: docstring hash}."""
    result: dict[str, str] = {}
    for node in store.get_nodes_by_type(NodeType.SYMBOL):
        doc = node.props.get("docstring", "")
        result[node.node_id] = str(hash(doc))
    return result


def impacted_by_changes(
    store: GraphStore,
    change_set: ChangeSet,
    max_depth: int = 3,
) -> list[str]:
    """Find all nodes impacted by a set of symbol changes."""
    impacted: set[str] = set()
    for symbol_id in change_set.modified + change_set.removed:
        defining_edges = store.get_edges_to(symbol_id, EdgeType.DEFINES)
        for edge in defining_edges:
            r = compute_blast_radius(store, edge.source_id, max_depth=max_depth)
            impacted.update(r.depth_map.keys())
        r = compute_blast_radius(store, symbol_id, max_depth=max_depth)
        impacted.update(r.depth_map.keys())
    return sorted(impacted)
