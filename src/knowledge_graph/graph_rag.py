# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
graph_rag.py — Graph-augmented retrieval (GraphRAG).

Enriches standard RAG retrieval results with graph context by:
1. Extracting entity mentions from query text
2. Looking up those entities in the knowledge graph
3. Traversing neighbors to expand context
4. Attaching structured graph context to results
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .query import GraphQuery
from .schema import node_id
from .store import GraphStore

# Entity mention patterns — extract (node_type, identifier) pairs from text.
# These are intentionally conservative to avoid false positives: they require
# a type keyword followed by an ID or quoted name.
_ENTITY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("fixture", re.compile(r"\bfixture\s+(\d+)", re.IGNORECASE)),
    ("group", re.compile(r"\bgroup\s+(\d+)", re.IGNORECASE)),
    ("sequence", re.compile(r"\bsequence\s+(\d+)", re.IGNORECASE)),
    ("executor", re.compile(r"\bexecutor\s+(\d+)", re.IGNORECASE)),
    ("cue", re.compile(r"\bcue\s+([\d.]+)", re.IGNORECASE)),
    ("preset", re.compile(r"\bpreset\s+([\d.]+)", re.IGNORECASE)),
    ("world", re.compile(r"\bworld\s+(\d+)", re.IGNORECASE)),
    ("filter", re.compile(r"\bfilter\s+(\d+)", re.IGNORECASE)),
]

# Quoted name pattern: 'group "Front Wash"' → ("group", "Front Wash")
_QUOTED_ENTITY_PATTERN = re.compile(
    r"\b(fixture|group|sequence|executor|preset|world|filter)\s+\"([^\"]+)\"",
    re.IGNORECASE,
)


@dataclass
class EntityMention:
    """An entity detected in text."""

    node_type: str
    identifier: str  # numeric ID or name
    node_id: str  # resolved graph node_id (e.g. "group:3")


@dataclass
class GraphContext:
    """Graph-derived context attached to a retrieval result."""

    entity: EntityMention
    neighbors: list[dict[str, Any]] = field(default_factory=list)
    edges: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the graph context to a JSON-compatible dict."""
        return {
            "entity": {
                "type": self.entity.node_type,
                "id": self.entity.identifier,
                "node_id": self.entity.node_id,
            },
            "neighbors": self.neighbors,
            "edges": self.edges,
        }


def extract_entities(text: str, store: GraphStore) -> list[EntityMention]:
    """Extract entity mentions from text and verify they exist in the graph.

    Only returns entities that actually exist as nodes in the graph.
    """
    mentions: list[EntityMention] = []
    seen_node_ids: set[str] = set()

    # Pattern-based extraction (type + numeric ID)
    for entity_type, pattern in _ENTITY_PATTERNS:
        for match in pattern.finditer(text):
            identifier = match.group(1)
            nid = node_id(entity_type, identifier)
            if nid not in seen_node_ids and store.get_node(nid) is not None:
                mentions.append(EntityMention(
                    node_type=entity_type,
                    identifier=identifier,
                    node_id=nid,
                ))
                seen_node_ids.add(nid)

    # Quoted name extraction (type + "name")
    for match in _QUOTED_ENTITY_PATTERN.finditer(text):
        entity_type = match.group(1).lower()
        name = match.group(2)
        # Search for node by label
        for node in store.get_nodes_by_type(entity_type):
            if node.label and node.label.lower() == name.lower():
                if node.node_id not in seen_node_ids:
                    mentions.append(EntityMention(
                        node_type=entity_type,
                        identifier=name,
                        node_id=node.node_id,
                    ))
                    seen_node_ids.add(node.node_id)
                break

    return mentions


def expand_entities(
    entities: list[EntityMention],
    query_engine: GraphQuery,
    max_depth: int = 2,
) -> list[GraphContext]:
    """Expand each entity mention with graph context (neighbors + edges)."""
    contexts: list[GraphContext] = []

    for entity in entities:
        result = query_engine.expand_context(entity.node_id, max_depth=max_depth)
        neighbor_dicts = [
            {"node_id": n.node_id, "type": n.node_type, "label": n.label, "props": n.props}
            for n in result.nodes
            if n.node_id != entity.node_id  # exclude the entity itself
        ]
        edge_dicts = [
            {"source": e.source_id, "target": e.target_id, "type": e.edge_type, "props": e.props}
            for e in result.edges
        ]
        contexts.append(GraphContext(
            entity=entity,
            neighbors=neighbor_dicts,
            edges=edge_dicts,
        ))

    return contexts


def graph_rag_query(
    query: str,
    store: GraphStore,
    max_depth: int = 2,
) -> list[GraphContext]:
    """Extract entities from a query and expand them with graph context.

    This is the main entry point for GraphRAG. It does NOT perform RAG
    retrieval itself — it provides the graph context that enriches RAG results.

    Args:
        query: Natural language query text.
        store: Initialized GraphStore with populated nodes/edges.
        max_depth: Maximum traversal depth for context expansion.

    Returns:
        List of GraphContext objects, one per detected entity.
    """
    entities = extract_entities(query, store)
    if not entities:
        return []

    query_engine = GraphQuery(store)
    return expand_entities(entities, query_engine, max_depth=max_depth)
