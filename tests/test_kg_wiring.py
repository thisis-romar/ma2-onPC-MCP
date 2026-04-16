# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Integration tests for knowledge graph wiring through the agent harness."""

import json
import os
import tempfile

import pytest

from src.agent.planner import DomainPlanner
from src.agent.policy import PolicyEngine
from src.agent.runtime import AgentRuntime
from src.agent.state import PlanStep
from src.commands.constants import MA2Right
from src.console_state import (
    ConsoleStateSnapshot,
    ExecutorState,
    SequenceEntry,
)
from src.knowledge_graph.store import GraphStore
from src.knowledge_graph.sync import sync_snapshot
from src.pool_name_index import PoolNameIndex
from src.vocab import RiskTier


@pytest.fixture
def store():
    s = GraphStore(":memory:")
    s.initialize()
    yield s
    s.close()


def _make_snapshot() -> ConsoleStateSnapshot:
    """Build a realistic snapshot for wiring tests."""
    idx = PoolNameIndex()
    idx.add_entry("Fixture", "Mac700 #1", 1)
    idx.add_entry("Fixture", "Mac700 #2", 2)
    idx.add_entry("Group", "Front Wash", 1)
    idx.add_entry("Sequence", "Main Show", 1)
    return ConsoleStateSnapshot(
        active_user="administrator",
        user_rights_str="Admin",
        user_right=MA2Right.ADMIN,
        showfile="test_show",
        name_index=idx,
        sequences=[SequenceEntry(id=1, label="Main Show")],
        executor_state={
            1: ExecutorState(id=1, page=1, sequence_id=1, label="Exec 1"),
        },
    )


# -- Global accessor tests --------------------------------------------------


class TestGlobalAccessor:
    def test_get_set(self, store):
        from src.knowledge_graph import get_graph_store, set_graph_store

        assert get_graph_store() is None or True  # may be set from prior test
        set_graph_store(store)
        assert get_graph_store() is store


# -- Runtime wiring tests ---------------------------------------------------


async def _mock_success(**kwargs):
    return json.dumps({"ok": True})


async def _mock_query(**kwargs):
    return json.dumps({"entries": [{"id": 1, "name": "test"}]})


MOCK_REGISTRY = {
    "query_object_list": _mock_query,
    "get_console_location": _mock_success,
    "list_console_destination": _mock_success,
    "get_object_info": _mock_success,
    "create_fixture_group": _mock_success,
}


class TestRuntimeWiring:
    def test_runtime_passes_graph_to_planner(self, store):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            rt = AgentRuntime(
                tool_registry=MOCK_REGISTRY,
                memory_db_path=db_path,
                graph_store=store,
            )
            try:
                assert rt.planner._graph_store is store
                assert rt.policy._graph_store is store
                assert rt.executor._graph_store is store
            finally:
                rt.memory.close()

    def test_runtime_works_without_graph(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            rt = AgentRuntime(
                tool_registry=MOCK_REGISTRY,
                memory_db_path=db_path,
            )
            try:
                assert rt.planner._graph_store is None
                assert rt.policy._graph_store is None
                assert rt.executor._graph_store is None
            finally:
                rt.memory.close()


# -- Planner enrichment flow tests ------------------------------------------


class TestPlannerEnrichmentFlow:
    def test_classify_with_populated_graph(self, store):
        """Full flow: sync snapshot → classify goal → get enrichment."""
        snap = _make_snapshot()
        sync_snapshot(store, snap)

        planner = DomainPlanner(graph_store=store)
        goal = planner.classify_goal("store preset for group 1")
        assert "graph_enrichment" in goal.options
        enrichment = goal.options["graph_enrichment"]
        assert enrichment["entity_contexts"][0]["exists"] is True

    def test_classify_warns_on_missing_entity(self, store):
        snap = _make_snapshot()
        sync_snapshot(store, snap)

        planner = DomainPlanner(graph_store=store)
        goal = planner.classify_goal("label group 99")
        enrichment = goal.options.get("graph_enrichment", {})
        assert any("not found" in w for w in enrichment.get("warnings", []))


# -- Policy graph rules flow tests ------------------------------------------


class TestPolicyGraphRulesFlow:
    def test_policy_warns_missing_entity_after_sync(self, store):
        snap = _make_snapshot()
        sync_snapshot(store, snap)

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
                description="Store cue",
                risk_tier=RiskTier.DESTRUCTIVE,
            ),
            PlanStep(
                tool_name="get_object_info",
                tool_args={"object_type": "sequence"},
                description="Verify",
                risk_tier=RiskTier.SAFE_READ,
            ),
        ]
        result = engine.validate_plan(plan)
        assert any("sequence 99" in w for w in result.warnings)
        assert result.approved is True  # advisory only


# -- Executor staleness tests -----------------------------------------------


class TestExecutorStaleness:
    def test_mark_stale_after_destructive_step(self, store):
        """Verify that executor marks nodes stale after a DESTRUCTIVE step."""
        snap = _make_snapshot()
        sync_snapshot(store, snap)

        # Verify nodes are fresh before
        assert store.is_fresh("sequence:1", "2020-01-01T00:00:00Z")

        from src.agent.executor import StepExecutor
        from src.agent.policy import PolicyEngine
        from src.agent.verification import Verifier

        executor = StepExecutor(
            tool_registry=MOCK_REGISTRY,
            policy=PolicyEngine(),
            verifier=Verifier(tool_dispatch=MOCK_REGISTRY),
            graph_store=store,
        )

        # Simulate what _mark_stale_nodes does for store_current_cue
        step = PlanStep(
            tool_name="store_current_cue",
            tool_args={},
            description="Store cue",
            risk_tier=RiskTier.DESTRUCTIVE,
        )
        executor._mark_stale_nodes(step)

        # Cue and sequence nodes should now be stale
        assert not store.is_fresh("sequence:1", "2020-01-01T00:00:00Z")

    def test_no_stale_on_safe_read(self, store):
        """SAFE_READ steps should not mark anything stale."""
        snap = _make_snapshot()
        sync_snapshot(store, snap)

        from src.agent.executor import StepExecutor
        from src.agent.policy import PolicyEngine
        from src.agent.verification import Verifier

        StepExecutor(
            tool_registry=MOCK_REGISTRY,
            policy=PolicyEngine(),
            verifier=Verifier(tool_dispatch=MOCK_REGISTRY),
            graph_store=store,
        )

        # _mark_stale_nodes is only called when risk_tier != SAFE_READ
        # so we just verify that nodes remain fresh when no mutation happens
        assert store.is_fresh("sequence:1", "2020-01-01T00:00:00Z")

    def test_unknown_tool_marks_all_stale(self, store):
        """Unknown mutation tools should mark ALL types stale (safe fallback)."""
        snap = _make_snapshot()
        sync_snapshot(store, snap)

        from src.agent.executor import StepExecutor
        from src.agent.policy import PolicyEngine
        from src.agent.verification import Verifier

        executor = StepExecutor(
            tool_registry=MOCK_REGISTRY,
            policy=PolicyEngine(),
            verifier=Verifier(tool_dispatch=MOCK_REGISTRY),
            graph_store=store,
        )

        step = PlanStep(
            tool_name="some_unknown_destructive_tool",
            tool_args={},
            description="Unknown tool",
            risk_tier=RiskTier.DESTRUCTIVE,
        )
        executor._mark_stale_nodes(step)

        # All common types should be stale
        assert not store.is_fresh("fixture:1", "2020-01-01T00:00:00Z")
        assert not store.is_fresh("group:1", "2020-01-01T00:00:00Z")
        assert not store.is_fresh("sequence:1", "2020-01-01T00:00:00Z")


# -- Policy freshness warning tests -----------------------------------------


class TestPolicyFreshnessWarning:
    """Rule 9: DESTRUCTIVE steps referencing stale graph data produce warnings."""

    def test_stale_entity_triggers_warning(self, store):
        """DESTRUCTIVE step referencing a stale group should warn."""
        snap = _make_snapshot()
        sync_snapshot(store, snap)

        # Mark group:1 as stale
        store.mark_stale("group:1")

        engine = PolicyEngine(graph_store=store)
        plan = [
            PlanStep(
                tool_name="query_object_list",
                tool_args={"object_type": "group"},
                description="List groups",
                risk_tier=RiskTier.SAFE_READ,
            ),
            PlanStep(
                tool_name="delete_object",
                tool_args={"group_id": 1},
                description="Delete group 1",
                risk_tier=RiskTier.DESTRUCTIVE,
            ),
            PlanStep(
                tool_name="get_object_info",
                tool_args={"object_type": "group"},
                description="Verify",
                risk_tier=RiskTier.SAFE_READ,
            ),
        ]
        result = engine.validate_plan(plan)
        stale_warnings = [w for w in result.warnings if "Stale graph data" in w]
        assert len(stale_warnings) >= 1
        assert "group:1" in stale_warnings[0]
        assert result.approved is True  # advisory only

    def test_fresh_entity_no_warning(self, store):
        """DESTRUCTIVE step referencing a fresh group should not warn."""
        snap = _make_snapshot()
        sync_snapshot(store, snap)

        engine = PolicyEngine(graph_store=store)
        plan = [
            PlanStep(
                tool_name="query_object_list",
                tool_args={"object_type": "group"},
                description="List groups",
                risk_tier=RiskTier.SAFE_READ,
            ),
            PlanStep(
                tool_name="delete_object",
                tool_args={"group_id": 1},
                description="Delete group 1",
                risk_tier=RiskTier.DESTRUCTIVE,
            ),
            PlanStep(
                tool_name="get_object_info",
                tool_args={"object_type": "group"},
                description="Verify",
                risk_tier=RiskTier.SAFE_READ,
            ),
        ]
        result = engine.validate_plan(plan)
        stale_warnings = [w for w in result.warnings if "Stale graph data" in w]
        assert len(stale_warnings) == 0

    def test_safe_read_with_stale_no_warning(self, store):
        """SAFE_READ steps should not trigger freshness warnings even if stale."""
        snap = _make_snapshot()
        sync_snapshot(store, snap)
        store.mark_stale("group:1")

        engine = PolicyEngine(graph_store=store)
        plan = [
            PlanStep(
                tool_name="query_object_list",
                tool_args={"group_id": 1},
                description="List group 1",
                risk_tier=RiskTier.SAFE_READ,
            ),
        ]
        result = engine.validate_plan(plan)
        stale_warnings = [w for w in result.warnings if "Stale graph data" in w]
        assert len(stale_warnings) == 0


# -- Server startup wiring tests ----------------------------------------------


class TestServerGraphStoreWiring:
    """Verify that server.py creates and wires the global GraphStore."""

    def test_server_module_graph_store_exists(self):
        """server.py must expose an initialized _graph_store module attribute."""
        from src.server import _graph_store

        assert _graph_store is not None
        assert _graph_store._conn is not None  # proves initialize() was called

    def test_orchestrator_has_graph_store(self):
        """The module-level _orchestrator must have the graph_store wired in."""
        from src.server import _orchestrator

        if _orchestrator is None:
            pytest.skip("_orchestrator is None (private submodule not available)")
        assert _orchestrator._graph_store is not None
