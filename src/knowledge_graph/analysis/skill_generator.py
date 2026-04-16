# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
skill_generator.py — Generate skill suggestions from graph cluster analysis.

Analyzes module clusters and their relationships to produce structured
skill body templates that can be promoted via the SkillRegistry.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..schema import EdgeType, NodeType
from ..store import GraphStore


@dataclass
class SkillSuggestion:
    """A generated skill suggestion from graph analysis."""

    name: str
    description: str
    body: str
    applicable_context: str
    safety_scope: str = "SAFE_READ"
    source_cluster: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "body": self.body,
            "applicable_context": self.applicable_context,
            "safety_scope": self.safety_scope,
            "source_cluster": self.source_cluster,
            "confidence": self.confidence,
        }


def generate_skill_for_cluster(
    store: GraphStore,
    cluster_node_id: str,
) -> SkillSuggestion | None:
    """Generate a skill suggestion for a single cluster.

    Analyzes the cluster's member modules, their symbols, and
    relationships to produce a structured skill body.
    """
    cluster = store.get_node(cluster_node_id)
    if cluster is None:
        return None

    # Get member modules
    members = [e.source_id for e in store.get_edges_to(cluster_node_id, EdgeType.PART_OF)]
    if not members:
        return None

    # Gather details for each member
    module_details: list[dict] = []
    for mid in members[:10]:  # cap at 10 for readability
        node = store.get_node(mid)
        if not node:
            continue
        symbols = [e.target_id for e in store.get_edges_from(mid, EdgeType.DEFINES)]
        symbol_names = []
        for sid in symbols[:5]:  # cap at 5 per module
            snode = store.get_node(sid)
            if snode and snode.label:
                symbol_names.append(snode.label)
        module_details.append({
            "name": node.label or mid,
            "symbols": symbol_names,
            "imports_out": len(store.get_edges_from(mid, EdgeType.IMPORTS)),
        })

    label = cluster.label or f"cluster-{cluster_node_id}"
    slug = label.replace(".", "-").replace(" ", "-").lower()

    # Build skill body
    lines = [
        f"# Working with {label}",
        "",
        f"This module group ({len(members)} modules) handles the `{label}` area of the codebase.",
        "",
        "## Key Modules",
        "",
    ]
    for md in module_details:
        sym_str = ", ".join(f"`{s}`" for s in md["symbols"]) if md["symbols"] else "(no exported symbols)"
        lines.append(f"- **{md['name']}** — {sym_str}")

    lines.extend([
        "",
        "## Common Operations",
        "",
        f"1. Import from `{label}` modules for {slug}-related functionality",
        f"2. Check `graph_impact(node_id=\"module:{label}\")` before modifying",
        f"3. Run `graph_trace_process(entry_point=\"module:{label}\")` to understand the call chain",
    ])

    confidence = min(1.0, len(members) / 5.0)  # more members = higher confidence

    return SkillSuggestion(
        name=f"understand-{slug}",
        description=f"Guide for working with the {label} module group ({len(members)} modules)",
        body="\n".join(lines),
        applicable_context=label,
        source_cluster=cluster_node_id,
        confidence=confidence,
    )


def generate_all_skills(
    store: GraphStore,
    min_cluster_size: int = 2,
) -> list[SkillSuggestion]:
    """Generate skill suggestions for all clusters above minimum size."""
    suggestions: list[SkillSuggestion] = []
    for cluster in store.get_nodes_by_type(NodeType.CLUSTER):
        size = cluster.props.get("size", 0)
        if size < min_cluster_size:
            continue
        suggestion = generate_skill_for_cluster(store, cluster.node_id)
        if suggestion:
            suggestions.append(suggestion)
    return suggestions
