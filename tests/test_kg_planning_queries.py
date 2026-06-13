# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for src/knowledge_graph/planning.py — PlanningQueries (BR=48)."""

import pytest

from src.knowledge_graph.planning import EntityContext, PlanningQueries
from src.knowledge_graph.schema import EdgeType, NodeType, node_id
from src.knowledge_graph.store import GraphStore


@pytest.fixture()
def store():
    """Create an in-memory GraphStore with test data."""
    s = GraphStore(":memory:")
    s.initialize()

    # Fixtures
    s.upsert_node(node_id(NodeType.FIXTURE, 1), NodeType.FIXTURE, label="Mac 700 #1")
    s.upsert_node(node_id(NodeType.FIXTURE, 2), NodeType.FIXTURE, label="Mac 700 #2")

    # Group with members
    s.upsert_node(node_id(NodeType.GROUP, 1), NodeType.GROUP, label="All Mac 700")
    s.upsert_edge(node_id(NodeType.FIXTURE, 1), node_id(NodeType.GROUP, 1), EdgeType.MEMBER_OF)
    s.upsert_edge(node_id(NodeType.FIXTURE, 2), node_id(NodeType.GROUP, 1), EdgeType.MEMBER_OF)

    # Empty group (no members)
    s.upsert_node(node_id(NodeType.GROUP, 2), NodeType.GROUP, label="Empty Group")

    # Sequence with cue
    s.upsert_node(node_id(NodeType.SEQUENCE, 1), NodeType.SEQUENCE, label="Main Show")
    s.upsert_node(node_id(NodeType.CUE, "1.1"), NodeType.CUE, label="Cue 1")
    s.upsert_edge(node_id(NodeType.SEQUENCE, 1), node_id(NodeType.CUE, "1.1"), EdgeType.HAS_CUE)

    # Executor with assigned sequence
    s.upsert_node(node_id(NodeType.EXECUTOR, "1.201"), NodeType.EXECUTOR, label="Exec 201")
    s.upsert_edge(
        node_id(NodeType.SEQUENCE, 1),
        node_id(NodeType.EXECUTOR, "1.201"),
        EdgeType.ASSIGNED_TO,
        props={"page": 1},
    )

    # Free executor (nothing assigned)
    s.upsert_node(node_id(NodeType.EXECUTOR, "1.202"), NodeType.EXECUTOR, label="Exec 202")

    return s


@pytest.fixture()
def pq(store):
    """PlanningQueries instance backed by test store."""
    return PlanningQueries(store)


# -- resolve_entity -----------------------------------------------------------


class TestResolveEntity:

    def test_existing_by_id(self, pq):
        ctx = pq.resolve_entity("fixture", object_id=1)
        assert ctx.exists is True
        assert ctx.node_id == "fixture:1"
        assert ctx.label == "Mac 700 #1"

    def test_existing_by_name(self, pq):
        ctx = pq.resolve_entity("group", name="All Mac 700")
        assert ctx.exists is True
        assert ctx.label == "All Mac 700"

    def test_existing_by_name_case_insensitive(self, pq):
        ctx = pq.resolve_entity("group", name="all mac 700")
        assert ctx.exists is True

    def test_not_found(self, pq):
        ctx = pq.resolve_entity("fixture", object_id=999)
        assert ctx.exists is False
        assert ctx.node_id == "fixture:999"

    def test_not_found_by_name(self, pq):
        ctx = pq.resolve_entity("group", name="Nonexistent")
        assert ctx.exists is False

    def test_related_count(self, pq):
        ctx = pq.resolve_entity("group", object_id=1)
        assert ctx.exists is True
        # Group 1 has 2 MEMBER_OF edges pointing to it
        assert ctx.related_count >= 2

    def test_entity_context_dataclass(self, pq):
        ctx = pq.resolve_entity("fixture", object_id=1)
        assert isinstance(ctx, EntityContext)
        assert isinstance(ctx.props, dict)
        assert isinstance(ctx.related_types, list)


# -- check_executor_available -------------------------------------------------


class TestCheckExecutorAvailable:

    def test_occupied_executor(self, pq):
        available, msg = pq.check_executor_available(201, page=1)
        assert available is False
        assert msg is not None
        assert "201" in msg

    def test_empty_executor(self, pq):
        available, msg = pq.check_executor_available(202, page=1)
        assert available is True
        assert msg is None

    def test_nonexistent_executor(self, pq):
        """An executor not in the graph is considered available."""
        available, msg = pq.check_executor_available(999, page=1)
        assert available is True
        assert msg is None


# -- check_entity_exists ------------------------------------------------------


class TestCheckEntityExists:

    def test_existing_entity(self, pq):
        assert pq.check_entity_exists("fixture", 1) is True

    def test_nonexistent_entity(self, pq):
        assert pq.check_entity_exists("fixture", 999) is False

    def test_existing_group(self, pq):
        assert pq.check_entity_exists("group", 1) is True


# -- count_by_type ------------------------------------------------------------


class TestCountByType:

    def test_fixture_count(self, pq):
        assert pq.count_by_type("fixture") == 2

    def test_group_count(self, pq):
        assert pq.count_by_type("group") == 2

    def test_empty_type(self, pq):
        assert pq.count_by_type("user") == 0


# -- validate_plan_dependencies -----------------------------------------------


class TestValidatePlanDependencies:

    def test_all_exist(self, pq):
        steps = [
            {"tool_name": "go", "tool_args": {"object_type": "fixture", "object_id": 1}},
            {"tool_name": "info", "tool_args": {"object_type": "group", "object_id": 1}},
        ]
        warnings = pq.validate_plan_dependencies(steps)
        assert warnings == []

    def test_missing_entity(self, pq):
        steps = [
            {"tool_name": "delete", "tool_args": {"object_type": "fixture", "object_id": 999}},
        ]
        warnings = pq.validate_plan_dependencies(steps)
        assert len(warnings) == 1
        assert "999" in warnings[0]
        assert "delete" in warnings[0]

    def test_step_without_object_id(self, pq):
        """Steps missing object_id should not produce warnings."""
        steps = [
            {"tool_name": "clear", "tool_args": {"object_type": "fixture"}},
        ]
        warnings = pq.validate_plan_dependencies(steps)
        assert warnings == []

    def test_step_without_tool_args(self, pq):
        """Steps missing tool_args entirely should not crash."""
        steps = [{"tool_name": "blackout"}]
        warnings = pq.validate_plan_dependencies(steps)
        assert warnings == []


# -- enrich_goal ---------------------------------------------------------------


class TestEnrichGoal:

    def test_no_object_type(self, pq):
        enrichment = pq.enrich_goal(None)
        assert enrichment.entity_contexts == []
        assert enrichment.warnings == []

    def test_existing_entity(self, pq):
        enrichment = pq.enrich_goal("group", object_id=1)
        assert len(enrichment.entity_contexts) == 1
        assert enrichment.entity_contexts[0].exists is True

    def test_missing_entity_produces_warning(self, pq):
        enrichment = pq.enrich_goal("fixture", object_id=999)
        assert len(enrichment.warnings) == 1
        assert "999" in enrichment.warnings[0]

    def test_goal_enrichment_to_dict(self, pq):
        enrichment = pq.enrich_goal("group", object_id=1)
        d = enrichment.to_dict()
        assert "entity_contexts" in d
        assert "warnings" in d
        assert "suggestions" in d
