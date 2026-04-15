# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
process_engine.py — Trace execution paths through the code graph.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..schema import EdgeType, NodeType
from ..store import GraphStore


@dataclass
class ProcessStep:
    """A single step in an execution trace."""

    node_id: str
    node_type: str
    label: str | None
    depth: int
    edge_type: str


@dataclass
class ProcessTrace:
    """An execution path through the code graph."""

    entry_point: str
    steps: list[ProcessStep] = field(default_factory=list)
    max_depth_reached: int = 0

    def to_dict(self) -> dict:
        return {
            "entry_point": self.entry_point,
            "steps": [
                {"node_id": s.node_id, "node_type": s.node_type,
                 "label": s.label, "depth": s.depth, "edge_type": s.edge_type}
                for s in self.steps
            ],
            "max_depth_reached": self.max_depth_reached,
            "step_count": len(self.steps),
        }


def trace_process(
    store: GraphStore,
    entry_point: str,
    max_depth: int = 10,
) -> ProcessTrace:
    """DFS from entry point following CALLS and IMPORTS edges outward."""
    trace = ProcessTrace(entry_point=entry_point)
    visited: set[str] = set()

    def _dfs(node_id: str, depth: int, via_edge: str) -> None:
        if node_id in visited or depth > max_depth:
            return
        visited.add(node_id)
        node = store.get_node(node_id)
        if node is None:
            return  # skip nodes not found in the store
        trace.steps.append(ProcessStep(
            node_id=node_id,
            node_type=node.node_type,
            label=node.label,
            depth=depth,
            edge_type=via_edge,
        ))
        if depth > trace.max_depth_reached:
            trace.max_depth_reached = depth

        for edge_type in (EdgeType.CALLS, EdgeType.IMPORTS):
            for edge in store.get_edges_from(node_id, edge_type):
                _dfs(edge.target_id, depth + 1, str(edge_type))

    _dfs(entry_point, 0, "entry")
    return trace


def find_entry_points(store: GraphStore) -> list[str]:
    """Find MODULE nodes with no incoming IMPORTS edges (root modules)."""
    entry_points: list[str] = []
    for node in store.get_nodes_by_type(NodeType.MODULE):
        incoming = store.get_edges_to(node.node_id, EdgeType.IMPORTS)
        if not incoming:
            entry_points.append(node.node_id)
    return sorted(entry_points)
