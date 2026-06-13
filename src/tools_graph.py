# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
tools_graph.py — 12 ENTERPRISE MCP tools for the Graph Intelligence Layer.

SAFE_READ tools query the in-memory knowledge graph populated at server startup.
SYSTEM_ADMIN tools (graph_upsert_node, graph_add_edge) write to the graph.
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
from src.knowledge_graph.schema import EdgeType, NodeType

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


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def graph_rag_query_tool(query: str, max_depth: int = 2) -> str:
    """Query the knowledge graph using RAG over node neighborhood contexts.

    Resolves entity mentions in the query to graph nodes, then expands each
    match to depth max_depth. Use alongside graph_query() for hybrid search.

    Args:
        query: Natural language query (e.g. "tools that use telnet", "skill for gobo presets").
        max_depth: Neighborhood depth to expand around each matched entity.
    """
    store = get_graph_store()
    if store is None:
        return json.dumps({"error": "Graph store not initialized"})

    from src.knowledge_graph import graph_rag_query  # local import to avoid circular at load time
    contexts = graph_rag_query(query, store, max_depth=max_depth)
    return json.dumps({
        "query": query,
        "entities_found": len(contexts),
        "contexts": [c.to_dict() for c in contexts],
    })


@mcp.tool()
@require_scope(OAuthScope.SYSTEM_ADMIN)
@_handle_errors
async def graph_upsert_node(
    node_id: str,
    node_type: str,
    label: str = "",
    props: str = "{}",
) -> str:
    """Insert or update a node in the knowledge graph.

    Idempotent — calling twice with the same node_id updates the existing node.
    Use to push external entities (e.g. graphify clusters, skill centroids) into the repo KG.

    Args:
        node_id: Unique ID, conventionally "type:name" (e.g. "cluster:auth", "skill:ft-pools").
        node_type: One of the NodeType values: fixture, group, sequence, cue, executor, preset,
            user, world, filter, module, symbol, package, cluster, skill, mcp_tool,
            mcp_resource, mcp_prompt, fixture_type.
        label: Human-readable name shown in graph visualizations.
        props: JSON object of additional properties (arbitrary key-value pairs).
    """
    store = get_graph_store()
    if store is None:
        return json.dumps({"error": "Graph store not initialized"})

    valid_types = {t.value for t in NodeType}
    if node_type not in valid_types:
        return json.dumps({"error": f"Invalid node_type '{node_type}'. Valid: {sorted(valid_types)}"})

    try:
        props_dict = json.loads(props)
    except json.JSONDecodeError as exc:
        return json.dumps({"error": f"Invalid props JSON: {exc}"})

    node = store.upsert_node(node_id, node_type, label=label or None, props=props_dict)
    return json.dumps({
        "upserted": True,
        "node_id": node.node_id,
        "node_type": node.node_type,
        "label": node.label,
    })


@mcp.tool()
@require_scope(OAuthScope.SYSTEM_ADMIN)
@_handle_errors
async def graph_add_edge(
    source_id: str,
    target_id: str,
    edge_type: str,
    props: str = "{}",
) -> str:
    """Add or update a directed edge between two nodes in the knowledge graph.

    Idempotent — (source_id, target_id, edge_type) is a unique constraint; calling
    twice updates the edge props. Both nodes must already exist (use graph_upsert_node first).

    Args:
        source_id: Source node ID (must exist in the graph).
        target_id: Target node ID (must exist in the graph).
        edge_type: One of the EdgeType values: member_of, instance_of, patched_to,
            assigned_to, has_cue, controls, uses_preset, has_role, scoped_by,
            filtered_by, part_of, imports, calls, defines, contains, implements,
            documents, orchestrates, improves_upon, categorized_as.
        props: JSON object of additional edge properties.
    """
    store = get_graph_store()
    if store is None:
        return json.dumps({"error": "Graph store not initialized"})

    valid_edge_types = {t.value for t in EdgeType}
    if edge_type not in valid_edge_types:
        return json.dumps({"error": f"Invalid edge_type '{edge_type}'. Valid: {sorted(valid_edge_types)}"})

    try:
        props_dict = json.loads(props)
    except json.JSONDecodeError as exc:
        return json.dumps({"error": f"Invalid props JSON: {exc}"})

    edge = store.upsert_edge(source_id, target_id, edge_type, props=props_dict)
    return json.dumps({
        "upserted": True,
        "edge_id": edge.edge_id,
        "source_id": edge.source_id,
        "target_id": edge.target_id,
        "edge_type": edge.edge_type,
    })
