# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
planning.py — Planning-specific graph queries for the agent harness.

Provides functions that the DomainPlanner and PolicyEngine use to enrich
goal classification and validate plans against the current console state
as represented in the knowledge graph.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .query import GraphQuery
from .schema import EdgeType, node_id
from .store import GraphStore, Node


@dataclass
class EntityContext:
    """Context about a referenced entity, resolved from the graph."""

    exists: bool
    node_id: str
    node_type: str
    label: str | None = None
    props: dict[str, Any] = field(default_factory=dict)
    related_count: int = 0
    related_types: list[str] = field(default_factory=list)


@dataclass
class GoalEnrichment:
    """Graph-derived enrichment for a parsed goal."""

    entity_contexts: list[EntityContext] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the goal enrichment to a JSON-compatible dict."""
        return {
            "entity_contexts": [
                {
                    "exists": ec.exists,
                    "node_id": ec.node_id,
                    "node_type": ec.node_type,
                    "label": ec.label,
                    "props": ec.props,
                    "related_count": ec.related_count,
                    "related_types": ec.related_types,
                }
                for ec in self.entity_contexts
            ],
            "warnings": self.warnings,
            "suggestions": self.suggestions,
        }


class PlanningQueries:
    """Graph queries for the planning layer."""

    def __init__(self, store: GraphStore) -> None:
        self._store = store
        self._query = GraphQuery(store)

    def resolve_entity(
        self,
        object_type: str,
        object_id: int | str | None = None,
        name: str | None = None,
    ) -> EntityContext:
        """Resolve an entity reference to its graph context.

        Looks up by ID first, then by name. Returns an EntityContext
        with exists=False if not found.
        """
        nid: str | None = None
        node: Node | None = None

        # Try by ID
        if object_id is not None:
            nid = node_id(object_type, object_id)
            node = self._store.get_node(nid)

        # Try by name if ID didn't match
        if node is None and name is not None:
            for n in self._store.get_nodes_by_type(object_type):
                if n.label and n.label.lower() == name.lower():
                    node = n
                    nid = n.node_id
                    break

        if node is None:
            return EntityContext(
                exists=False,
                node_id=nid or node_id(object_type, object_id or "?"),
                node_type=object_type,
            )

        # Count related entities
        edges_out = self._store.get_edges_from(node.node_id)
        edges_in = self._store.get_edges_to(node.node_id)
        related_types = list({
            e.edge_type for e in edges_out + edges_in
        })

        return EntityContext(
            exists=True,
            node_id=node.node_id,
            node_type=node.node_type,
            label=node.label,
            props=node.props,
            related_count=len(edges_out) + len(edges_in),
            related_types=related_types,
        )

    def enrich_goal(
        self,
        object_type: str | None,
        object_id: int | str | None = None,
        name: str | None = None,
    ) -> GoalEnrichment:
        """Enrich a parsed goal with graph context.

        Resolves referenced entities and generates warnings/suggestions.
        """
        enrichment = GoalEnrichment()

        if object_type is None:
            return enrichment

        ctx = self.resolve_entity(object_type, object_id, name)
        enrichment.entity_contexts.append(ctx)

        if not ctx.exists and object_id is not None:
            enrichment.warnings.append(
                f"{object_type} {object_id} not found in current console state"
            )

        # Add type-specific suggestions
        if ctx.exists:
            if object_type == "group" and ctx.related_count == 0:
                enrichment.suggestions.append(
                    f"Group '{ctx.label}' exists but has no member fixtures"
                )
            elif object_type == "sequence":
                # Use the resolved node_id (handles name-based lookups
                # where object_id may be None).
                cues = self._query.neighbors_out(ctx.node_id, EdgeType.HAS_CUE)
                if not cues:
                    enrichment.suggestions.append(
                        f"Sequence '{ctx.label}' has no cues — store cues first"
                    )

        return enrichment

    def check_executor_available(
        self,
        executor_id: int,
        page: int = 1,
    ) -> tuple[bool, str | None]:
        """Check if an executor slot is available.

        Returns (available, message). If occupied, message describes
        what's currently there.
        """
        seq = self._query.sequence_on_executor(executor_id, page)
        if seq is not None:
            return False, (
                f"Executor {page}.{executor_id} is occupied by "
                f"sequence '{seq.label}' ({seq.node_id})"
            )
        return True, None

    def check_entity_exists(
        self,
        object_type: str,
        object_id: int | str,
    ) -> bool:
        """Quick existence check for an entity."""
        nid = node_id(object_type, object_id)
        return self._store.get_node(nid) is not None

    def count_by_type(self, object_type: str) -> int:
        """Count entities of a given type in the graph."""
        return self._store.node_count(object_type)

    def validate_plan_dependencies(
        self,
        steps: list[dict[str, Any]],
    ) -> list[str]:
        """Validate that plan step references exist in the graph.

        Returns a list of warning messages for references that don't resolve.
        Each step dict should have 'tool_args' with 'object_type' and
        optionally 'object_id'.
        """
        warnings: list[str] = []
        for step in steps:
            args = step.get("tool_args", {})
            obj_type = args.get("object_type")
            obj_id = args.get("object_id")

            if obj_type and obj_id and not self.check_entity_exists(obj_type, obj_id):
                tool = step.get("tool_name", "unknown")
                warnings.append(
                    f"Step '{tool}' references {obj_type} {obj_id} "
                    f"which does not exist in the current console state"
                )

        return warnings
