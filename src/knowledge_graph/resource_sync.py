# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
resource_sync.py — Sync MCP tools, resources, and prompts into the knowledge graph.

Creates MCP_TOOL, MCP_RESOURCE, and MCP_PROMPT nodes, and establishes
DOCUMENTS / ORCHESTRATES edges when docstrings mention known tool names.
"""

from __future__ import annotations

import logging
import re

from .mcp_metadata import MCPMetadata
from .schema import EdgeType, NodeType, node_id
from .store import GraphStore

logger = logging.getLogger(__name__)


def _parse_category_from_uri(uri: str) -> str:
    """Extract a category token from a resource URI.

    >>> _parse_category_from_uri("ma2://docs/rights-matrix")
    'docs'
    >>> _parse_category_from_uri("ma2://busking/patterns")
    'busking'
    >>> _parse_category_from_uri("ma2://skills/{skill_id}")
    'skills'
    """
    # Strip scheme
    path = uri.split("://", 1)[-1] if "://" in uri else uri
    parts = path.strip("/").split("/")
    return parts[0] if parts else "unknown"


def _find_tool_mentions(text: str, known_tools: set[str]) -> set[str]:
    """Find known tool names mentioned in a block of text.

    Uses word-boundary matching so that ``execute_sequence`` is found in
    a sentence but ``exec`` doesn't false-positive on ``execute``.
    """
    mentions: set[str] = set()
    for tool_name in known_tools:
        # Use word boundaries to avoid substring matches
        if re.search(r"\b" + re.escape(tool_name) + r"\b", text):
            mentions.add(tool_name)
    return mentions


def sync_resources(store: GraphStore, metadata: MCPMetadata) -> dict[str, int]:
    """Sync MCP tool/resource/prompt metadata into the graph.

    Creates nodes for every tool, resource, and prompt, and detects
    cross-references (tool mentions in docstrings) to create DOCUMENTS
    and ORCHESTRATES edges.

    Args:
        store: Initialized GraphStore.
        metadata: :class:`MCPMetadata` from :func:`extract_mcp_metadata`.

    Returns:
        Counts dict: ``{"nodes": N, "edges": N}``.
    """
    node_count = 0
    edge_count = 0

    known_tools: set[str] = set(metadata.tools.keys())

    # -- MCP_TOOL nodes --------------------------------------------------------

    for name, tool in metadata.tools.items():
        nid = node_id(NodeType.MCP_TOOL, name)
        props = {
            "docstring": (tool.docstring[:200] if tool.docstring else ""),
            "args": tool.args,
            "module": tool.module,
        }
        store.upsert_node(nid, NodeType.MCP_TOOL, label=name, props=props)
        node_count += 1

    # -- MCP_RESOURCE nodes ----------------------------------------------------

    for uri, resource in metadata.resources.items():
        nid = node_id(NodeType.MCP_RESOURCE, uri)
        category = _parse_category_from_uri(uri)
        props = {
            "function_name": resource.function_name,
            "docstring": (resource.docstring[:200] if resource.docstring else ""),
            "category": category,
        }
        store.upsert_node(nid, NodeType.MCP_RESOURCE, label=uri, props=props)
        node_count += 1

        # DOCUMENTS edges: resource -> tool (when docstring mentions tool)
        if resource.docstring:
            for tool_name in _find_tool_mentions(resource.docstring, known_tools):
                tool_nid = node_id(NodeType.MCP_TOOL, tool_name)
                store.upsert_edge(nid, tool_nid, EdgeType.DOCUMENTS)
                edge_count += 1

    # -- MCP_PROMPT nodes ------------------------------------------------------

    for name, prompt in metadata.prompts.items():
        nid = node_id(NodeType.MCP_PROMPT, name)
        props = {
            "docstring": (prompt.docstring[:200] if prompt.docstring else ""),
            "args": prompt.args,
        }
        store.upsert_node(nid, NodeType.MCP_PROMPT, label=name, props=props)
        node_count += 1

        # ORCHESTRATES edges: prompt -> tool (when docstring mentions tool)
        if prompt.docstring:
            for tool_name in _find_tool_mentions(prompt.docstring, known_tools):
                tool_nid = node_id(NodeType.MCP_TOOL, tool_name)
                store.upsert_edge(nid, tool_nid, EdgeType.ORCHESTRATES)
                edge_count += 1

    logger.info("Synced %d MCP nodes, %d edges", node_count, edge_count)
    return {"nodes": node_count, "edges": edge_count}
