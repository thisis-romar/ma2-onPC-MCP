# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
skill_sync.py — Sync skills from SkillRegistry into the knowledge graph.

Creates SKILL nodes for each registered skill, and IMPROVES_UPON edges
for skills that have a parent (version lineage).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .schema import EdgeType, NodeType, node_id
from .store import GraphStore

if TYPE_CHECKING:
    from ..skill import SkillRegistry

logger = logging.getLogger(__name__)


def sync_skills(store: GraphStore, registry: SkillRegistry) -> dict[str, int]:
    """Sync all skills from a SkillRegistry into the graph.

    For each skill in ``registry.list_all()``, creates a node with
    ``node_id(NodeType.SKILL, skill.id)``.  Skills with ``parent_id``
    get an IMPROVES_UPON edge (child -> parent).

    Args:
        store: Initialized GraphStore.
        registry: SkillRegistry with skills to sync.

    Returns:
        Counts dict: ``{"nodes": N, "edges": N}``.
    """
    node_count = 0
    edge_count = 0

    skills = registry.list_all(limit=500)

    # First pass: create all nodes
    for skill in skills:
        nid = node_id(NodeType.SKILL, skill.id)
        props: dict = {
            "version": skill.version,
            "description": skill.description,
            "safety_scope": skill.safety_scope,
            "quality_score": skill.quality_score,
            "approved": skill.approved,
            "deprecated": skill.deprecated,
            "applicable_context": skill.applicable_context,
        }
        store.upsert_node(nid, NodeType.SKILL, label=skill.name, props=props)
        node_count += 1

    # Second pass: create lineage edges (all nodes already exist)
    for skill in skills:
        if skill.parent_id:
            child_nid = node_id(NodeType.SKILL, skill.id)
            parent_nid = node_id(NodeType.SKILL, skill.parent_id)
            # Only create edge if the parent node exists (it may not if
            # the parent was deprecated and excluded from list_all).
            parent_node = store.get_node(parent_nid)
            if parent_node is not None:
                store.upsert_edge(child_nid, parent_nid, EdgeType.IMPROVES_UPON)
                edge_count += 1
            else:
                logger.debug(
                    "Skipping IMPROVES_UPON edge: parent %s not in graph", skill.parent_id
                )

    logger.info("Synced %d skill nodes, %d lineage edges", node_count, edge_count)
    return {"nodes": node_count, "edges": edge_count}
