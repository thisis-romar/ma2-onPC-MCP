# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for knowledge graph planning integration."""

import pytest

from src.agent.planner import DomainPlanner
from src.agent.policy import PolicyEngine
from src.agent.state import GoalIntent, PlanStep
from src.knowledge_graph.planning import PlanningQueries
from src.knowledge_graph.schema import EdgeType, NodeType
from src.knowledge_graph.store import GraphStore
from src.vocab import RiskTier


@pytest.fixture
def store():
    s = GraphStore(":memory:")
    s.initialize()
    yield s
    s.close()


def _populate_console_state(store: GraphStore) -> None:
    """Populate a graph resembling a typical console state."""
    # Fixtures
    store.upsert_node("fixture:1", NodeType.FIXTURE, label="Mac700 #1")
    store.upsert_node("fixture:2", NodeType.FIXTURE, label="Mac700 #2")

    # Groups
    store.upsert_node("group:1", NodeType.GROUP, label="Front Wash")
    store.upsert_edge("fixture:1", "group:1", EdgeType.MEMBER_OF)
    store.upsert_edge("fixture:2", "group:1", EdgeType.MEMBER_OF)

    store.upsert_node("group:2", NodeType.GROUP, label="Empty Group")
    # group:2 has no members

    # Sequences
    store.upsert_node("sequence:1", NodeType.SEQUENCE, label="Main Show")
    store.upsert_node("cue:1.1.0", NodeType.CUE, label="Blackout")
    store.upsert_edge("sequence:1", "cue:1.1.0", EdgeType.HAS_CUE)

    store.upsert_node("sequence:2", NodeType.SEQUENCE, label="Empty Seq")
    # sequence:2 has no cues

    # Executors
    store.upsert_node("executor:1.1", NodeType.EXECUTOR, label="Exec 1")
    store.upsert_edge("sequence:1", "executor:1.1", EdgeType.ASSIGNED_TO)


# -- PlanningQueries tests --------------------------------------------------


class TestResolveEntity:
    def test_resolve_existing_by_id(self, store):
        _populate_console_state(store)
        pq = PlanningQueries(store)
        ctx = pq.resolve_entity("group", object_id=1)
        assert ctx.exists is True
        assert ctx.label == "Front Wash"
        assert ctx.related_count == 2  # 2 member_of edges

    def test_resolve_existing_by_name(self, store):
        _populate_console_state(store)
        pq = PlanningQueries(store)
        ctx = pq.resolve_entity("group", name="Front Wash")
        assert ctx.exists is True
        assert ctx.node_id == "group:1"

    def test_resolve_missing(self, store):
        _populate_console_state(store)
        pq = PlanningQueries(store)
        ctx = pq.resolve_entity("group", object_id=99)
        assert ctx.exists is False

    def test_resolve_with_related_types(self, store):
        _populate_console_state(store)
        pq = PlanningQueries(store)
        ctx = pq.resolve_entity("sequence", object_id=1)
        assert ctx.exists is True
        assert "has_cue" in ctx.related_types or "assigned_to" in ctx.related_types


class TestEnrichGoal:
    def test_enrich_existing_group(self, store):
        _populate_console_state(store)
        pq = PlanningQueries(store)
        enrichment = pq.enrich_goal("group", object_id=1)
        assert len(enrichment.entity_contexts) == 1
        assert enrichment.entity_contexts[0].exists is True
        assert len(enrichment.warnings) == 0

    def test_enrich_missing_entity_warns(self, store):
        _populate_console_state(store)
        pq = PlanningQueries(store)
        enrichment = pq.enrich_goal("group", object_id=99)
        assert len(enrichment.warnings) == 1
        assert "not found" in enrichment.warnings[0]

    def test_enrich_empty_group_suggests(self, store):
        _populate_console_state(store)
        pq = PlanningQueries(store)
        enrichment = pq.enrich_goal("group", object_id=2)
        assert len(enrichment.suggestions) == 1
        assert "no member fixtures" in enrichment.suggestions[0]

    def test_enrich_empty_sequence_suggests(self, store):
        _populate_console_state(store)
        pq = PlanningQueries(store)
        enrichment = pq.enrich_goal("sequence", object_id=2)
        assert len(enrichment.suggestions) == 1
        assert "no cues" in enrichment.suggestions[0]

    def test_enrich_none_type_returns_empty(self, store):
        pq = PlanningQueries(store)
        enrichment = pq.enrich_goal(None)
        assert len(enrichment.entity_contexts) == 0

    def test_to_dict(self, store):
        _populate_console_state(store)
        pq = PlanningQueries(store)
        enrichment = pq.enrich_goal("group", object_id=1)
        d = enrichment.to_dict()
        assert "entity_contexts" in d
        assert "warnings" in d
        assert "suggestions" in d


class TestExecutorAvailability:
    def test_occupied_executor(self, store):
        _populate_console_state(store)
        pq = PlanningQueries(store)
        available, msg = pq.check_executor_available(1, page=1)
        assert available is False
        assert msg is not None
        assert "occupied" in msg

    def test_free_executor(self, store):
        _populate_console_state(store)
        pq = PlanningQueries(store)
        available, msg = pq.check_executor_available(99, page=1)
        assert available is True
        assert msg is None


class TestValidatePlanDependencies:
    def test_valid_references(self, store):
        _populate_console_state(store)
        pq = PlanningQueries(store)
        steps = [
            {"tool_name": "query_object_list", "tool_args": {"object_type": "group", "object_id": 1}},
        ]
        warnings = pq.validate_plan_dependencies(steps)
        assert len(warnings) == 0

    def test_invalid_reference_warns(self, store):
        _populate_console_state(store)
        pq = PlanningQueries(store)
        steps = [
            {"tool_name": "store_cue", "tool_args": {"object_type": "sequence", "object_id": 99}},
        ]
        warnings = pq.validate_plan_dependencies(steps)
        assert len(warnings) == 1
        assert "sequence 99" in warnings[0]


class TestCheckEntityExists:
    def test_existing_entity_returns_true(self, store):
        _populate_console_state(store)
        pq = PlanningQueries(store)
        assert pq.check_entity_exists("fixture", 1) is True

    def test_missing_entity_returns_false(self, store):
        _populate_console_state(store)
        pq = PlanningQueries(store)
        assert pq.check_entity_exists("fixture", 999) is False

    def test_group_exists(self, store):
        _populate_console_state(store)
        pq = PlanningQueries(store)
        assert pq.check_entity_exists("group", 1) is True


class TestCountByType:
    def test_fixture_count(self, store):
        _populate_console_state(store)
        pq = PlanningQueries(store)
        assert pq.count_by_type("fixture") == 2

    def test_group_count(self, store):
        _populate_console_state(store)
        pq = PlanningQueries(store)
        assert pq.count_by_type("group") == 2

    def test_empty_type_returns_zero(self, store):
        _populate_console_state(store)
        pq = PlanningQueries(store)
        assert pq.count_by_type("world") == 0


# -- DomainPlanner with graph tests -----------------------------------------


class TestPlannerWithGraph:
    def test_planner_without_graph_unchanged(self):
        """Existing behavior: planner works without a graph store."""
        planner = DomainPlanner()
        goal = planner.classify_goal("list all groups")
        assert goal.intent == GoalIntent.DISCOVER
        assert "graph_enrichment" not in goal.options

    def test_planner_with_graph_enriches(self, store):
        _populate_console_state(store)
        planner = DomainPlanner(graph_store=store)
        goal = planner.classify_goal("store preset for group 1")
        assert "graph_enrichment" in goal.options
        enrichment = goal.options["graph_enrichment"]
        assert len(enrichment["entity_contexts"]) >= 1

    def test_planner_with_graph_warns_on_missing(self, store):
        _populate_console_state(store)
        planner = DomainPlanner(graph_store=store)
        goal = planner.classify_goal("label group 99")
        enrichment = goal.options.get("graph_enrichment", {})
        warnings = enrichment.get("warnings", [])
        assert any("not found" in w for w in warnings)

    def test_plan_still_works_with_graph(self, store):
        """Plans should generate the same steps regardless of graph."""
        _populate_console_state(store)
        planner = DomainPlanner(graph_store=store)
        goal, steps = planner.plan_from_text("list all groups")
        assert len(steps) >= 1
        assert steps[0].risk_tier == RiskTier.SAFE_READ


# -- PolicyEngine with graph tests ------------------------------------------


class TestPolicyWithGraph:
    def test_policy_without_graph_unchanged(self):
        """Existing behavior: policy works without a graph store."""
        engine = PolicyEngine()
        plan = [
            PlanStep(
                tool_name="query_object_list",
                tool_args={"object_type": "group"},
                description="List groups",
                risk_tier=RiskTier.SAFE_READ,
            ),
        ]
        result = engine.validate_plan(plan)
        assert result.approved is True

    def test_policy_warns_on_missing_entity(self, store):
        _populate_console_state(store)
        engine = PolicyEngine(graph_store=store)
        plan = [
            PlanStep(
                tool_name="query_object_list",
                tool_args={"object_type": "group"},
                description="List groups",
                risk_tier=RiskTier.SAFE_READ,
            ),
            PlanStep(
                tool_name="store_cue",
                tool_args={"object_type": "sequence", "object_id": 99},
                description="Store cue in sequence 99",
                risk_tier=RiskTier.DESTRUCTIVE,
            ),
        ]
        result = engine.validate_plan(plan)
        # Should have a warning about sequence 99 not existing
        assert any("sequence 99" in w for w in result.warnings)

    def test_policy_warns_on_occupied_executor(self, store):
        _populate_console_state(store)
        engine = PolicyEngine(graph_store=store)
        plan = [
            PlanStep(
                tool_name="query_object_list",
                tool_args={"object_type": "executor"},
                description="List executors",
                risk_tier=RiskTier.SAFE_READ,
            ),
            PlanStep(
                tool_name="assign_executor",
                tool_args={"executor_id": 1, "page": 1},
                description="Assign to executor 1",
                risk_tier=RiskTier.DESTRUCTIVE,
            ),
        ]
        result = engine.validate_plan(plan)
        assert any("occupied" in w for w in result.warnings)

    def test_graph_warnings_dont_block(self, store):
        """Graph-based rules are advisory — they should never block plans."""
        _populate_console_state(store)
        engine = PolicyEngine(graph_store=store)
        plan = [
            PlanStep(
                tool_name="query_object_list",
                tool_args={"object_type": "group"},
                description="List groups",
                risk_tier=RiskTier.SAFE_READ,
            ),
            PlanStep(
                tool_name="store_cue",
                tool_args={"object_type": "sequence", "object_id": 99},
                description="Store cue in nonexistent sequence",
                risk_tier=RiskTier.DESTRUCTIVE,
            ),
            PlanStep(
                tool_name="get_object_info",
                tool_args={"object_type": "sequence"},
                description="Verify cue stored",
                risk_tier=RiskTier.SAFE_READ,
            ),
        ]
        result = engine.validate_plan(plan)
        # Warnings present but plan still approved
        assert len(result.warnings) > 0
        assert result.approved is True
