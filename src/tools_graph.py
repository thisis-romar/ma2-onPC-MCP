# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
tools_graph.py — 9 ENTERPRISE MCP tools for the Graph Intelligence Layer.

All tools are SAFE_READ (no console I/O). They query the in-memory
knowledge graph populated at server startup.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import src.server_core as _sc
from src.auth import OAuthScope, require_scope
from src.knowledge_graph import get_graph_store
from src.knowledge_graph.parsers.repo_registry import RepoRegistry
from src.knowledge_graph.parsers.repo_scanner import scan_repository
from src.knowledge_graph.query import GraphQuery
from src.knowledge_graph.schema import NodeType

mcp = _sc.mcp
_handle_errors = _sc._handle_errors  # noqa: SLF001

logger = logging.getLogger(__name__)

_repo_registry = RepoRegistry()


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def graph_list_repos() -> str:
    """List all indexed repositories in the code graph."""
    repos = _repo_registry.list_repos()
    return json.dumps({
        "repos": [
            {"name": r.name, "root": r.root, "last_sha": r.last_sha,
             "last_indexed_iso": __import__("time").strftime(
                 "%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime(r.last_indexed)),
             "node_count": r.node_count, "edge_count": r.edge_count}
            for r in repos
        ],
        "count": len(repos),
    })


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def graph_analyze_repo(path: str = ".") -> str:
    """Analyze a repository and index its code structure into the graph.

    Args:
        path: Repository root path (default: current directory).
    """
    store = get_graph_store()
    if store is None:
        return json.dumps({"error": "Graph store not initialized"})

    root = Path(path).resolve()
    from src.knowledge_graph.parsers.repo_registry import get_git_head_sha
    sha = get_git_head_sha(root) or "unknown"

    counts = scan_repository(store, root)
    _repo_registry.register(root, sha, node_count=counts.get("nodes", 0),
                            edge_count=counts.get("edges", 0))
    return json.dumps({
        "path": str(root), "sha": sha[:12],
        "modules": counts.get("modules", 0), "symbols": counts.get("symbols", 0),
        "nodes_created": counts.get("nodes", 0), "edges_created": counts.get("edges", 0),
    })


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def graph_query(
    node_type: str = "module",
    pattern: str = "",
    limit: int = 20,
) -> str:
    """Query nodes in the code graph by type and optional name pattern.

    Args:
        node_type: Node type to query (module, symbol, package, cluster, skill, mcp_tool, etc.).
        pattern: Optional substring filter on node label.
        limit: Maximum results to return.
    """
    store = get_graph_store()
    if store is None:
        return json.dumps({"error": "Graph store not initialized"})

    valid_types = {t.value for t in NodeType}
    if node_type not in valid_types:
        return json.dumps({"error": f"Invalid node_type '{node_type}'. Valid: {sorted(valid_types)}"})

    nodes = store.get_nodes_by_type(node_type)
    if pattern:
        pat_lower = pattern.lower()
        nodes = [n for n in nodes if n.label and pat_lower in n.label.lower()]
    nodes = nodes[:limit]
    return json.dumps({
        "nodes": [{"node_id": n.node_id, "label": n.label, "props": n.props} for n in nodes],
        "count": len(nodes),
    })


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def graph_context(node_id: str, max_depth: int = 2) -> str:
    """Get the neighborhood context for a graph node.

    Args:
        node_id: The node ID to expand (e.g. "module:src.server").
        max_depth: Maximum traversal depth.
    """
    store = get_graph_store()
    if store is None:
        return json.dumps({"error": "Graph store not initialized"})

    query = GraphQuery(store)
    result = query.expand_context(node_id, max_depth=max_depth)
    return json.dumps(result.to_dict())


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def graph_impact(node_id: str, max_depth: int = 5) -> str:
    """Compute the blast radius of changes to a symbol or module.

    Args:
        node_id: Target node (e.g. "module:src.server" or "symbol:src.server.main").
        max_depth: Maximum dependency traversal depth.
    """
    store = get_graph_store()
    if store is None:
        return json.dumps({"error": "Graph store not initialized"})

    from src.knowledge_graph.analysis.impact_engine import compute_blast_radius
    result = compute_blast_radius(store, node_id, max_depth=max_depth)
    return json.dumps(result.to_dict())


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def graph_detect_changes(old_snapshot: str = "", new_snapshot: str = "") -> str:
    """Detect what symbols changed between two graph snapshots.

    Args:
        old_snapshot: JSON dict of {symbol_id: hash} from previous state.
        new_snapshot: JSON dict of {symbol_id: hash} from current state.
            If empty, uses the current graph state as new_snapshot.
    """
    store = get_graph_store()
    if store is None:
        return json.dumps({"error": "Graph store not initialized"})

    from src.knowledge_graph.analysis.change_detector import (
        detect_changes,
        symbols_to_hash_map,
    )
    old = json.loads(old_snapshot) if old_snapshot else {}
    new = json.loads(new_snapshot) if new_snapshot else symbols_to_hash_map(store)
    cs = detect_changes(old, new)
    return json.dumps(cs.to_dict())


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def graph_trace_process(entry_point: str, max_depth: int = 10) -> str:
    """Trace an execution path through the code graph from an entry point.

    Args:
        entry_point: Starting node ID (e.g. "module:src.server").
        max_depth: Maximum trace depth.
    """
    store = get_graph_store()
    if store is None:
        return json.dumps({"error": "Graph store not initialized"})

    from src.knowledge_graph.analysis.process_engine import trace_process
    trace = trace_process(store, entry_point, max_depth=max_depth)
    return json.dumps(trace.to_dict())


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def graph_list_clusters(min_size: int = 2) -> str:
    """List logical clusters of related modules in the code graph.

    Args:
        min_size: Minimum cluster size to include.
    """
    store = get_graph_store()
    if store is None:
        return json.dumps({"error": "Graph store not initialized"})

    clusters = store.get_nodes_by_type(NodeType.CLUSTER)
    result = []
    for cl in clusters:
        size = cl.props.get("size", 0)
        if size >= min_size:
            result.append({
                "node_id": cl.node_id, "label": cl.label,
                "size": size, "cohesion": cl.props.get("cohesion", 0.0),
            })
    return json.dumps({"clusters": result, "count": len(result)})


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def graph_generate_skills(cluster_id: str = "") -> str:
    """Generate skill suggestions from graph analysis of a cluster or the full codebase.

    Args:
        cluster_id: Optional cluster node ID. If empty, analyzes all clusters.
    """
    store = get_graph_store()
    if store is None:
        return json.dumps({"error": "Graph store not initialized"})

    clusters = store.get_nodes_by_type(NodeType.CLUSTER)
    if cluster_id:
        clusters = [c for c in clusters if c.node_id == cluster_id]

    suggestions: list[dict] = []
    for cl in clusters:
        members = [e.source_id for e in store.get_edges_to(cl.node_id)]
        if not members:
            continue
        member_labels = []
        for mid in members[:5]:
            node = store.get_node(mid)
            if node and node.label:
                member_labels.append(node.label)

        suggestions.append({
            "name": f"understand-{cl.label or 'cluster'}".replace(".", "-"),
            "description": f"Guide for working with the {cl.label} module group ({len(members)} modules)",
            "body_preview": f"## {cl.label}\n\nKey modules: {', '.join(member_labels)}",
            "applicable_context": cl.label or "",
        })

    return json.dumps({"suggestions": suggestions, "count": len(suggestions)})
