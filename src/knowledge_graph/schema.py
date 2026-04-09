# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
schema.py — Node and edge type definitions for the MA2 knowledge graph.

Defines the domain vocabulary: what kinds of entities (nodes) exist in a
grandMA2 show file, and how they relate to each other (edges).
"""

from __future__ import annotations

from enum import StrEnum


class NodeType(StrEnum):
    """Entity types in the grandMA2 domain."""

    FIXTURE = "fixture"
    FIXTURE_TYPE = "fixture_type"
    GROUP = "group"
    SEQUENCE = "sequence"
    CUE = "cue"
    EXECUTOR = "executor"
    PRESET = "preset"
    USER = "user"
    WORLD = "world"
    FILTER = "filter"


class EdgeType(StrEnum):
    """Relationship types between MA2 domain entities."""

    # Fixture relationships
    MEMBER_OF = "member_of"          # fixture → group
    INSTANCE_OF = "instance_of"      # fixture → fixture_type
    PATCHED_TO = "patched_to"        # fixture → universe/address (props)

    # Playback chain
    ASSIGNED_TO = "assigned_to"      # sequence → executor (props: page, priority)
    HAS_CUE = "has_cue"             # sequence → cue (props: cue_number)
    CONTROLS = "controls"            # executor → sequence

    # Preset references
    USES_PRESET = "uses_preset"      # cue → preset (props: preset_type)

    # User / permissions
    HAS_ROLE = "has_role"            # user → rights level (props: ma2_right, scope_tier)

    # Scoping
    SCOPED_BY = "scoped_by"          # executor → world
    FILTERED_BY = "filtered_by"      # executor → filter

    # Structural
    PART_OF = "part_of"              # cue_part → cue


def node_id(node_type: NodeType | str, obj_id: int | str) -> str:
    """Build a canonical node ID string.

    >>> node_id(NodeType.FIXTURE, 1)
    'fixture:1'
    >>> node_id("preset", "4.2")
    'preset:4.2'
    """
    return f"{node_type}:{obj_id}"


# SQL DDL for the graph tables — executed by GraphStore.initialize().
SCHEMA_SQL = """\
CREATE TABLE IF NOT EXISTS kg_nodes (
    node_id    TEXT PRIMARY KEY,
    node_type  TEXT NOT NULL,
    label      TEXT,
    props      TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_kg_nodes_type ON kg_nodes(node_type);

CREATE TABLE IF NOT EXISTS kg_edges (
    edge_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id  TEXT NOT NULL REFERENCES kg_nodes(node_id) ON DELETE CASCADE,
    target_id  TEXT NOT NULL REFERENCES kg_nodes(node_id) ON DELETE CASCADE,
    edge_type  TEXT NOT NULL,
    props      TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL,
    UNIQUE(source_id, target_id, edge_type)
);

CREATE INDEX IF NOT EXISTS idx_kg_edges_source ON kg_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_kg_edges_target ON kg_edges(target_id);
CREATE INDEX IF NOT EXISTS idx_kg_edges_type   ON kg_edges(edge_type);
"""
