# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
Knowledge Graph layer for GrandPA2-Buddy.

SQLite-backed in-process graph modeling MA2 domain entities (fixtures, groups,
sequences, executors, presets, users) and their relationships. Populated from
ConsoleStateSnapshot hydration — no additional telnet traffic.

Public API::

    from src.knowledge_graph import GraphStore, GraphQuery, NodeType, EdgeType
    from src.knowledge_graph import sync_snapshot, graph_rag_query
    from src.knowledge_graph import get_graph_store, set_graph_store
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .graph_rag import extract_entities, graph_rag_query
from .mcp_metadata import MCPMetadata, extract_mcp_metadata
from .parsers.extractor import ImportInfo, ModuleInfo, SymbolInfo, extract_module_info
from .parsers.normalizer import normalize_to_graph
from .parsers.repo_scanner import scan_repository
from .planning import PlanningQueries
from .query import GraphQuery, TraversalResult
from .resource_sync import sync_resources
from .schema import EdgeType, NodeType, node_id
from .skill_sync import sync_skills
from .store import Edge, GraphStore, Node
from .sync import sync_snapshot

if TYPE_CHECKING:
    pass

__all__ = [
    # Store
    "GraphStore",
    "Node",
    "Edge",
    # Schema
    "NodeType",
    "EdgeType",
    "node_id",
    # Query
    "GraphQuery",
    "TraversalResult",
    # Sync
    "sync_snapshot",
    # Skill sync
    "sync_skills",
    # Resource sync
    "sync_resources",
    # MCP metadata
    "extract_mcp_metadata",
    "MCPMetadata",
    # GraphRAG
    "graph_rag_query",
    "extract_entities",
    # Planning
    "PlanningQueries",
    # Code graph parsers
    "extract_module_info",
    "ModuleInfo",
    "SymbolInfo",
    "ImportInfo",
    "normalize_to_graph",
    "scan_repository",
    # Global accessor
    "get_graph_store",
    "set_graph_store",
]

__version__ = "0.1.0"

_graph_store: GraphStore | None = None


def get_graph_store() -> GraphStore | None:
    """Return the global GraphStore instance, or None if not initialized."""
    return _graph_store


def set_graph_store(store: GraphStore) -> None:
    """Set the global GraphStore instance (called during server startup or orchestrator init)."""
    global _graph_store
    _graph_store = store
