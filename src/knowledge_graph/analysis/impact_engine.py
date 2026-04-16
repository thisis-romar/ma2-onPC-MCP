# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
impact_engine.py — Blast radius analysis for the code graph.

Given a symbol or module, find everything that depends on it via
reverse traversal of IMPORTS and CALLS edges.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from ..schema import EdgeType, NodeType
from ..store import GraphStore


@dataclass
class ImpactResult:
    """Result of a blast radius computation."""

    target_node_id: str
    direct_dependents: list[str] = field(default_factory=list)
    transitive_dependents: list[str] = field(default_factory=list)
    depth_map: dict[str, int] = field(default_factory=dict)
    blast_radius: int = 0

    def to_dict(self) -> dict:
        return {
            "target_node_id": self.target_node_id,
            "direct_dependents": self.direct_dependents,
            "transitive_dependents": self.transitive_dependents,
            "depth_map": self.depth_map,
            "blast_radius": self.blast_radius,
        }


def compute_blast_radius(
    store: GraphStore,
    target_id: str,
    max_depth: int = 5,
) -> ImpactResult:
    """BFS reverse traversal to find all dependents of a node."""
    result = ImpactResult(target_node_id=target_id)
    visited: set[str] = {target_id}
    queue: deque[tuple[str, int]] = deque()

    for edge_type in (EdgeType.IMPORTS, EdgeType.CALLS):
        for edge in store.get_edges_to(target_id, edge_type):
            if edge.source_id not in visited:
                visited.add(edge.source_id)
                queue.append((edge.source_id, 1))
                result.direct_dependents.append(edge.source_id)
                result.depth_map[edge.source_id] = 1

    while queue:
        node_id, depth = queue.popleft()
        if depth >= max_depth:
            continue
        for edge_type in (EdgeType.IMPORTS, EdgeType.CALLS):
            for edge in store.get_edges_to(node_id, edge_type):
                if edge.source_id not in visited:
                    visited.add(edge.source_id)
                    queue.append((edge.source_id, depth + 1))
                    result.depth_map[edge.source_id] = depth + 1

    result.transitive_dependents = sorted(
        [nid for nid in result.depth_map if nid not in result.direct_dependents]
    )
    result.blast_radius = len(result.depth_map)
    return result


def find_most_central(
    store: GraphStore,
    node_type: NodeType | str = NodeType.MODULE,
    limit: int = 10,
) -> list[tuple[str, int]]:
    """Find nodes with the most incoming edges (degree centrality)."""
    nodes = store.get_nodes_by_type(node_type)
    counts: list[tuple[str, int]] = []
    for node in nodes:
        incoming = len(store.get_edges_to(node.node_id))
        counts.append((node.node_id, incoming))
    counts.sort(key=lambda x: x[1], reverse=True)
    return counts[:limit]
