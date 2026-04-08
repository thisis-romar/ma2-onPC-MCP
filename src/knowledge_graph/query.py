# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
query.py — Graph traversal queries for the MA2 knowledge graph.

Provides BFS/DFS traversal, neighbor lookup, path finding, and
domain-specific convenience queries (e.g., "which fixtures are in group 3?").
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

from .schema import EdgeType, NodeType, node_id
from .store import Edge, GraphStore, Node


@dataclass
class TraversalResult:
    """Result of a graph traversal."""

    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    paths: list[list[str]] = field(default_factory=list)

    def node_ids(self) -> list[str]:
        return [n.node_id for n in self.nodes]

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [
                {"node_id": n.node_id, "node_type": n.node_type, "label": n.label, "props": n.props}
                for n in self.nodes
            ],
            "edges": [
                {"source": e.source_id, "target": e.target_id, "type": e.edge_type, "props": e.props}
                for e in self.edges
            ],
            "paths": self.paths,
        }


class GraphQuery:
    """Query interface for the MA2 knowledge graph."""

    def __init__(self, store: GraphStore) -> None:
        self._store = store

    # -- neighbor lookups ----------------------------------------------------

    def neighbors_out(
        self,
        node_id: str,
        edge_type: EdgeType | str | None = None,
    ) -> list[Node]:
        """Get all nodes reachable via outgoing edges from node_id."""
        edges = self._store.get_edges_from(node_id, edge_type)
        nodes = []
        for edge in edges:
            n = self._store.get_node(edge.target_id)
            if n is not None:
                nodes.append(n)
        return nodes

    def neighbors_in(
        self,
        node_id: str,
        edge_type: EdgeType | str | None = None,
    ) -> list[Node]:
        """Get all nodes that have edges pointing TO node_id."""
        edges = self._store.get_edges_to(node_id, edge_type)
        nodes = []
        for edge in edges:
            n = self._store.get_node(edge.source_id)
            if n is not None:
                nodes.append(n)
        return nodes

    # -- BFS traversal -------------------------------------------------------

    def bfs(
        self,
        start_id: str,
        max_depth: int = 3,
        edge_types: set[EdgeType | str] | None = None,
        direction: str = "out",
    ) -> TraversalResult:
        """Breadth-first traversal from a starting node.

        Args:
            start_id: Node to start from.
            max_depth: Maximum hop count.
            edge_types: If given, only follow these edge types.
            direction: "out" (follow outgoing), "in" (follow incoming), or "both".

        Returns:
            TraversalResult with all discovered nodes and edges.
        """
        result = TraversalResult()
        visited: set[str] = set()
        queue: deque[tuple[str, int]] = deque()

        start_node = self._store.get_node(start_id)
        if start_node is None:
            return result

        visited.add(start_id)
        result.nodes.append(start_node)
        queue.append((start_id, 0))

        while queue:
            current_id, depth = queue.popleft()
            if depth >= max_depth:
                continue

            edges: list[Edge] = []
            if direction in ("out", "both"):
                edges.extend(self._store.get_edges_from(current_id))
            if direction in ("in", "both"):
                edges.extend(self._store.get_edges_to(current_id))

            for edge in edges:
                if edge_types and edge.edge_type not in edge_types:
                    continue

                result.edges.append(edge)
                neighbor_id = (
                    edge.target_id if edge.source_id == current_id else edge.source_id
                )

                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    neighbor_node = self._store.get_node(neighbor_id)
                    if neighbor_node is not None:
                        result.nodes.append(neighbor_node)
                        queue.append((neighbor_id, depth + 1))

        return result

    # -- path finding --------------------------------------------------------

    def find_path(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 5,
        direction: str = "out",
    ) -> list[str] | None:
        """Find a shortest path from start to end using BFS.

        Returns a list of node IDs forming the path, or None if no path exists.
        """
        if start_id == end_id:
            return [start_id]

        visited: set[str] = {start_id}
        queue: deque[list[str]] = deque([[start_id]])

        while queue:
            path = queue.popleft()
            if len(path) - 1 >= max_depth:
                continue

            current = path[-1]
            edges: list[Edge] = []
            if direction in ("out", "both"):
                edges.extend(self._store.get_edges_from(current))
            if direction in ("in", "both"):
                edges.extend(self._store.get_edges_to(current))

            for edge in edges:
                neighbor_id = (
                    edge.target_id if edge.source_id == current else edge.source_id
                )
                if neighbor_id == end_id:
                    return path + [neighbor_id]
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append(path + [neighbor_id])

        return None

    # -- domain-specific queries ---------------------------------------------

    def fixtures_in_group(self, group_id: int) -> list[Node]:
        """Which fixtures are members of a given group?"""
        gid = node_id(NodeType.GROUP, group_id)
        return self.neighbors_in(gid, EdgeType.MEMBER_OF)

    def groups_for_fixture(self, fixture_id: int) -> list[Node]:
        """Which groups does a fixture belong to?"""
        fid = node_id(NodeType.FIXTURE, fixture_id)
        return self.neighbors_out(fid, EdgeType.MEMBER_OF)

    def cues_in_sequence(self, sequence_id: int) -> list[Node]:
        """Which cues belong to a sequence?"""
        sid = node_id(NodeType.SEQUENCE, sequence_id)
        return self.neighbors_out(sid, EdgeType.HAS_CUE)

    def executor_for_sequence(self, sequence_id: int) -> list[Node]:
        """Which executors is a sequence assigned to?"""
        sid = node_id(NodeType.SEQUENCE, sequence_id)
        return self.neighbors_out(sid, EdgeType.ASSIGNED_TO)

    def sequence_on_executor(self, executor_id: int, page: int = 1) -> Node | None:
        """Which sequence is assigned to an executor?"""
        eid = node_id(NodeType.EXECUTOR, f"{page}.{executor_id}")
        controllers = self.neighbors_in(eid, EdgeType.ASSIGNED_TO)
        return controllers[0] if controllers else None

    def fixtures_affected_by_executor(self, executor_id: int, page: int = 1) -> list[Node]:
        """Multi-hop: executor → sequence → cues → presets, plus sequence → group → fixtures."""
        result_nodes: list[Node] = []
        seq = self.sequence_on_executor(executor_id, page)
        if seq is None:
            return result_nodes

        # Traverse: sequence → cues
        cues = self.cues_in_sequence(int(seq.node_id.split(":")[1]))

        # Traverse: sequence → assigned groups → fixtures
        # (via BFS from sequence node, following member_of edges back)
        traversal = self.bfs(
            seq.node_id,
            max_depth=3,
            edge_types={EdgeType.HAS_CUE, EdgeType.MEMBER_OF, EdgeType.USES_PRESET},
            direction="both",
        )
        result_nodes = [n for n in traversal.nodes if n.node_type == NodeType.FIXTURE]
        return result_nodes

    def expand_context(self, start_id: str, max_depth: int = 2) -> TraversalResult:
        """General-purpose context expansion from any node.

        Used by GraphRAG to enrich retrieval results with relationship context.
        """
        return self.bfs(start_id, max_depth=max_depth, direction="both")
