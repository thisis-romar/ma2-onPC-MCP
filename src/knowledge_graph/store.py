# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
store.py — SQLite-backed graph store for the MA2 knowledge graph.

CRUD operations for nodes and edges. The graph lives in-memory by default
(`:memory:`) for session-scoped use, or on disk for persistence across
sessions.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Any

from .schema import SCHEMA_SQL, EdgeType, NodeType

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass
class Node:
    """A node in the knowledge graph."""

    node_id: str
    node_type: str
    label: str | None = None
    props: dict[str, Any] = field(default_factory=dict)
    updated_at: str = ""


@dataclass
class Edge:
    """An edge (relationship) in the knowledge graph."""

    edge_id: int | None
    source_id: str
    target_id: str
    edge_type: str
    props: dict[str, Any] = field(default_factory=dict)
    updated_at: str = ""


class GraphStore:
    """SQLite-backed graph store.

    By default creates an in-memory database (session-scoped, no disk I/O).
    Pass a file path to ``db_path`` for persistent storage.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    # -- lifecycle -----------------------------------------------------------

    def initialize(self) -> None:
        """Create tables and indexes if they don't exist."""
        self._conn = sqlite3.connect(self._db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(SCHEMA_SQL)
        self._conn.commit()

    def close(self) -> None:
        """Close the SQLite connection and release resources."""
        if self._conn:
            self._conn.close()
            self._conn = None

    @property
    def conn(self) -> sqlite3.Connection:
        """Return the active SQLite connection, raising if not initialized."""
        if self._conn is None:
            raise RuntimeError("GraphStore not initialized — call initialize() first")
        return self._conn

    # -- node CRUD -----------------------------------------------------------

    def upsert_node(
        self,
        node_id: str,
        node_type: NodeType | str,
        label: str | None = None,
        props: dict[str, Any] | None = None,
    ) -> Node:
        """Insert or update a node. Returns the upserted Node."""
        now = _now_iso()
        props_json = json.dumps(props or {})
        self.conn.execute(
            """
            INSERT INTO kg_nodes (node_id, node_type, label, props, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(node_id) DO UPDATE SET
                node_type  = excluded.node_type,
                label      = excluded.label,
                props      = excluded.props,
                updated_at = excluded.updated_at
            """,
            (node_id, str(node_type), label, props_json, now),
        )
        self.conn.commit()
        return Node(
            node_id=node_id,
            node_type=str(node_type),
            label=label,
            props=props or {},
            updated_at=now,
        )

    def get_node(self, node_id: str) -> Node | None:
        """Fetch a single node by ID, or None if not found."""
        row = self.conn.execute(
            "SELECT node_id, node_type, label, props, updated_at FROM kg_nodes WHERE node_id = ?",
            (node_id,),
        ).fetchone()
        if row is None:
            return None
        return Node(
            node_id=row[0],
            node_type=row[1],
            label=row[2],
            props=json.loads(row[3]),
            updated_at=row[4],
        )

    def get_nodes_by_type(self, node_type: NodeType | str) -> list[Node]:
        """Fetch all nodes of a given type."""
        rows = self.conn.execute(
            "SELECT node_id, node_type, label, props, updated_at FROM kg_nodes WHERE node_type = ?",
            (str(node_type),),
        ).fetchall()
        return [
            Node(node_id=r[0], node_type=r[1], label=r[2], props=json.loads(r[3]), updated_at=r[4])
            for r in rows
        ]

    def delete_node(self, node_id: str) -> bool:
        """Delete a node and all its edges. Returns True if the node existed."""
        cur = self.conn.execute("DELETE FROM kg_nodes WHERE node_id = ?", (node_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def delete_nodes_by_type(self, node_type: NodeType | str) -> int:
        """Delete all nodes of a given type. Returns count of deleted nodes."""
        cur = self.conn.execute("DELETE FROM kg_nodes WHERE node_type = ?", (str(node_type),))
        self.conn.commit()
        return cur.rowcount

    def node_count(self, node_type: NodeType | str | None = None) -> int:
        """Count nodes, optionally filtered by type."""
        if node_type is None:
            return self.conn.execute("SELECT COUNT(*) FROM kg_nodes").fetchone()[0]
        return self.conn.execute(
            "SELECT COUNT(*) FROM kg_nodes WHERE node_type = ?", (str(node_type),)
        ).fetchone()[0]

    # -- edge CRUD -----------------------------------------------------------

    def upsert_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType | str,
        props: dict[str, Any] | None = None,
    ) -> Edge:
        """Insert or update an edge. Returns the upserted Edge."""
        now = _now_iso()
        props_json = json.dumps(props or {})
        self.conn.execute(
            """
            INSERT INTO kg_edges (source_id, target_id, edge_type, props, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(source_id, target_id, edge_type) DO UPDATE SET
                props      = excluded.props,
                updated_at = excluded.updated_at
            """,
            (source_id, target_id, str(edge_type), props_json, now),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT edge_id FROM kg_edges WHERE source_id = ? AND target_id = ? AND edge_type = ?",
            (source_id, target_id, str(edge_type)),
        ).fetchone()
        return Edge(
            edge_id=row[0] if row else None,
            source_id=source_id,
            target_id=target_id,
            edge_type=str(edge_type),
            props=props or {},
            updated_at=now,
        )

    def get_edges_from(
        self,
        source_id: str,
        edge_type: EdgeType | str | None = None,
    ) -> list[Edge]:
        """Fetch all outgoing edges from a node, optionally filtered by type."""
        if edge_type is None:
            rows = self.conn.execute(
                "SELECT edge_id, source_id, target_id, edge_type, props, updated_at "
                "FROM kg_edges WHERE source_id = ?",
                (source_id,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT edge_id, source_id, target_id, edge_type, props, updated_at "
                "FROM kg_edges WHERE source_id = ? AND edge_type = ?",
                (source_id, str(edge_type)),
            ).fetchall()
        return [
            Edge(edge_id=r[0], source_id=r[1], target_id=r[2], edge_type=r[3],
                 props=json.loads(r[4]), updated_at=r[5])
            for r in rows
        ]

    def get_edges_to(
        self,
        target_id: str,
        edge_type: EdgeType | str | None = None,
    ) -> list[Edge]:
        """Fetch all incoming edges to a node, optionally filtered by type."""
        if edge_type is None:
            rows = self.conn.execute(
                "SELECT edge_id, source_id, target_id, edge_type, props, updated_at "
                "FROM kg_edges WHERE target_id = ?",
                (target_id,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT edge_id, source_id, target_id, edge_type, props, updated_at "
                "FROM kg_edges WHERE target_id = ? AND edge_type = ?",
                (target_id, str(edge_type)),
            ).fetchall()
        return [
            Edge(edge_id=r[0], source_id=r[1], target_id=r[2], edge_type=r[3],
                 props=json.loads(r[4]), updated_at=r[5])
            for r in rows
        ]

    def delete_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType | str,
    ) -> bool:
        """Delete a specific edge. Returns True if it existed."""
        cur = self.conn.execute(
            "DELETE FROM kg_edges WHERE source_id = ? AND target_id = ? AND edge_type = ?",
            (source_id, target_id, str(edge_type)),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def delete_edges_by_type(self, edge_type: EdgeType | str) -> int:
        """Delete all edges of a given type. Returns count of deleted edges."""
        cur = self.conn.execute("DELETE FROM kg_edges WHERE edge_type = ?", (str(edge_type),))
        self.conn.commit()
        return cur.rowcount

    def edge_count(self, edge_type: EdgeType | str | None = None) -> int:
        """Count edges, optionally filtered by type."""
        if edge_type is None:
            return self.conn.execute("SELECT COUNT(*) FROM kg_edges").fetchone()[0]
        return self.conn.execute(
            "SELECT COUNT(*) FROM kg_edges WHERE edge_type = ?", (str(edge_type),)
        ).fetchone()[0]

    # -- freshness tracking --------------------------------------------------

    def mark_stale(self, node_id: str) -> bool:
        """Mark a node as stale by setting updated_at to epoch.

        Returns True if the node existed.
        """
        cur = self.conn.execute(
            "UPDATE kg_nodes SET updated_at = '1970-01-01T00:00:00Z' WHERE node_id = ?",
            (node_id,),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def mark_type_stale(self, node_type: NodeType | str) -> int:
        """Mark all nodes of a type as stale. Returns count."""
        cur = self.conn.execute(
            "UPDATE kg_nodes SET updated_at = '1970-01-01T00:00:00Z' WHERE node_type = ?",
            (str(node_type),),
        )
        self.conn.commit()
        return cur.rowcount

    def stale_nodes(self, max_age_iso: str) -> list[Node]:
        """Get all nodes older than max_age_iso timestamp."""
        rows = self.conn.execute(
            "SELECT node_id, node_type, label, props, updated_at "
            "FROM kg_nodes WHERE updated_at < ?",
            (max_age_iso,),
        ).fetchall()
        return [
            Node(node_id=r[0], node_type=r[1], label=r[2], props=json.loads(r[3]), updated_at=r[4])
            for r in rows
        ]

    def is_fresh(self, node_id: str, max_age_iso: str) -> bool:
        """Check if a node's updated_at is >= max_age_iso."""
        row = self.conn.execute(
            "SELECT updated_at FROM kg_nodes WHERE node_id = ?",
            (node_id,),
        ).fetchone()
        if row is None:
            return False
        return row[0] >= max_age_iso

    # -- bulk operations -----------------------------------------------------

    def clear(self) -> None:
        """Delete all nodes and edges."""
        self.conn.execute("DELETE FROM kg_edges")
        self.conn.execute("DELETE FROM kg_nodes")
        self.conn.commit()

    def stats(self) -> dict[str, int]:
        """Return node and edge counts by type."""
        result: dict[str, int] = {}
        for row in self.conn.execute(
            "SELECT node_type, COUNT(*) FROM kg_nodes GROUP BY node_type"
        ).fetchall():
            result[f"nodes:{row[0]}"] = row[1]
        for row in self.conn.execute(
            "SELECT edge_type, COUNT(*) FROM kg_edges GROUP BY edge_type"
        ).fetchall():
            result[f"edges:{row[0]}"] = row[1]
        result["total_nodes"] = self.node_count()
        result["total_edges"] = self.edge_count()
        return result
