# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for src/knowledge_graph/schema.py — NodeType, EdgeType, node_id (BR=62)."""

from src.knowledge_graph.schema import SCHEMA_SQL, EdgeType, NodeType, node_id


class TestNodeType:
    """NodeType enum validation."""

    def test_count(self):
        """NodeType should have exactly 18 members."""
        assert len(NodeType) == 18

    def test_all_values_lowercase(self):
        for member in NodeType:
            assert member.value == member.value.lower(), f"{member.name} has non-lowercase value"

    def test_domain_entities_present(self):
        expected = {
            "fixture", "fixture_type", "group", "sequence", "cue",
            "executor", "preset", "user", "world", "filter",
        }
        actual = {m.value for m in NodeType}
        assert expected.issubset(actual)

    def test_code_structure_entities_present(self):
        expected = {"module", "symbol", "package", "cluster"}
        actual = {m.value for m in NodeType}
        assert expected.issubset(actual)

    def test_mcp_metadata_entities_present(self):
        expected = {"skill", "mcp_tool", "mcp_resource", "mcp_prompt"}
        actual = {m.value for m in NodeType}
        assert expected.issubset(actual)


class TestEdgeType:
    """EdgeType enum validation."""

    def test_count(self):
        """EdgeType should have exactly 20 members."""
        assert len(EdgeType) == 20

    def test_all_values_lowercase_with_underscores(self):
        for member in EdgeType:
            assert member.value == member.value.lower(), f"{member.name} has non-lowercase value"
            assert " " not in member.value, f"{member.name} contains spaces"

    def test_domain_edges_present(self):
        expected = {
            "member_of", "instance_of", "patched_to", "assigned_to",
            "has_cue", "controls", "uses_preset", "has_role",
            "scoped_by", "filtered_by", "part_of",
        }
        actual = {m.value for m in EdgeType}
        assert expected.issubset(actual)

    def test_code_structure_edges_present(self):
        expected = {"imports", "calls", "defines", "contains"}
        actual = {m.value for m in EdgeType}
        assert expected.issubset(actual)

    def test_mcp_metadata_edges_present(self):
        expected = {
            "implements", "documents", "orchestrates",
            "improves_upon", "categorized_as",
        }
        actual = {m.value for m in EdgeType}
        assert expected.issubset(actual)


class TestNodeId:
    """node_id() function tests."""

    def test_with_enum_and_int(self):
        assert node_id(NodeType.FIXTURE, 1) == "fixture:1"

    def test_with_string_and_dotted_id(self):
        assert node_id("preset", "4.2") == "preset:4.2"

    def test_with_enum_and_string_id(self):
        assert node_id(NodeType.MCP_TOOL, "go_executor") == "mcp_tool:go_executor"

    def test_with_zero_id(self):
        assert node_id(NodeType.GROUP, 0) == "group:0"


class TestSchemaSql:
    """SCHEMA_SQL DDL string validation."""

    def test_contains_nodes_table(self):
        assert "kg_nodes" in SCHEMA_SQL

    def test_contains_edges_table(self):
        assert "kg_edges" in SCHEMA_SQL

    def test_contains_node_type_index(self):
        assert "idx_kg_nodes_type" in SCHEMA_SQL

    def test_contains_edge_source_index(self):
        assert "idx_kg_edges_source" in SCHEMA_SQL

    def test_contains_edge_target_index(self):
        assert "idx_kg_edges_target" in SCHEMA_SQL

    def test_contains_edge_type_index(self):
        assert "idx_kg_edges_type" in SCHEMA_SQL
