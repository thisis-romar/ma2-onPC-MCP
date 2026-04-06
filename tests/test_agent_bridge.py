# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""tests/test_agent_bridge.py — Unit tests for src/agent_bridge.py."""

import json

import pytest

from src.agent.state import PlanStep, RunStatus, StepStatus
from src.agent_bridge import (
    execute_subtasks_via_agent,
    planstep_to_subtask,
    plansteps_from_subtasks,
    subtask_to_planstep,
    subtasks_from_plansteps,
)
from src.task_decomposer import SubTask
from src.vocab import RiskTier

# ── subtask_to_planstep ──────────────────────────────────────────────────────


class TestSubtaskToPlanstep:
    def _make_subtask(self, **kwargs) -> SubTask:
        defaults = dict(
            name="select_wash",
            agent_role="SelectionAgent",
            description="select wash fixtures",
            allowed_risk=RiskTier.SAFE_READ,
            mcp_tools=["discover_object_names"],
            inputs={"object_type": "Group"},
            depends_on=[],
        )
        defaults.update(kwargs)
        return SubTask(**defaults)

    def test_tool_name_from_first_mcp_tool(self):
        st = self._make_subtask(mcp_tools=["discover_object_names", "list_objects"])
        ps = subtask_to_planstep(st)
        assert ps.tool_name == "discover_object_names"

    def test_empty_mcp_tools_becomes_noop(self):
        st = self._make_subtask(mcp_tools=[])
        ps = subtask_to_planstep(st)
        assert ps.tool_name == "noop"

    def test_tool_args_from_inputs(self):
        st = self._make_subtask(inputs={"group": 5, "level": 100})
        ps = subtask_to_planstep(st)
        assert ps.tool_args == {"group": 5, "level": 100}

    def test_description_preserved(self):
        st = self._make_subtask(description="store preset 4.1")
        ps = subtask_to_planstep(st)
        assert ps.description == "store preset 4.1"

    def test_risk_tier_preserved(self):
        st = self._make_subtask(allowed_risk=RiskTier.DESTRUCTIVE)
        ps = subtask_to_planstep(st)
        assert ps.risk_tier == RiskTier.DESTRUCTIVE

    def test_depends_on_copied(self):
        st = self._make_subtask(depends_on=["step_a", "step_b"])
        ps = subtask_to_planstep(st)
        assert ps.depends_on == ["step_a", "step_b"]

    def test_depends_on_is_independent_copy(self):
        deps = ["step_a"]
        st = self._make_subtask(depends_on=deps)
        ps = subtask_to_planstep(st)
        deps.append("step_b")
        assert "step_b" not in ps.depends_on

    def test_status_defaults_to_pending(self):
        ps = subtask_to_planstep(self._make_subtask())
        assert ps.status == StepStatus.PENDING

    def test_returns_planstep_instance(self):
        ps = subtask_to_planstep(self._make_subtask())
        assert isinstance(ps, PlanStep)


# ── planstep_to_subtask ──────────────────────────────────────────────────────


class TestPlanstepToSubtask:
    def _make_planstep(self, **kwargs) -> PlanStep:
        defaults = dict(
            tool_name="group_at",
            tool_args={"group_id": 1, "level": 100},
            description="set wash to full",
            risk_tier=RiskTier.SAFE_WRITE,
            depends_on=[],
        )
        defaults.update(kwargs)
        return PlanStep(**defaults)

    def test_name_is_planstep_id(self):
        ps = self._make_planstep()
        st = planstep_to_subtask(ps)
        assert st.name == ps.id

    def test_agent_role_is_bridged_sentinel(self):
        st = planstep_to_subtask(self._make_planstep())
        assert st.agent_role == "BridgedAgent"

    def test_description_preserved(self):
        ps = self._make_planstep(description="go executor 1")
        st = planstep_to_subtask(ps)
        assert st.description == "go executor 1"

    def test_allowed_risk_from_risk_tier(self):
        ps = self._make_planstep(risk_tier=RiskTier.DESTRUCTIVE)
        st = planstep_to_subtask(ps)
        assert st.allowed_risk == RiskTier.DESTRUCTIVE

    def test_mcp_tools_contains_tool_name(self):
        ps = self._make_planstep(tool_name="store_preset")
        st = planstep_to_subtask(ps)
        assert st.mcp_tools == ["store_preset"]

    def test_inputs_from_tool_args(self):
        ps = self._make_planstep(tool_args={"a": 1, "b": 2})
        st = planstep_to_subtask(ps)
        assert st.inputs == {"a": 1, "b": 2}

    def test_confirmed_always_false(self):
        ps = self._make_planstep(risk_tier=RiskTier.DESTRUCTIVE)
        st = planstep_to_subtask(ps)
        assert st.confirmed is False

    def test_depends_on_copied(self):
        ps = self._make_planstep(depends_on=["x", "y"])
        st = planstep_to_subtask(ps)
        assert st.depends_on == ["x", "y"]

    def test_returns_subtask_instance(self):
        st = planstep_to_subtask(self._make_planstep())
        assert isinstance(st, SubTask)


# ── round-trip ───────────────────────────────────────────────────────────────


class TestRoundTrip:
    def test_subtask_planstep_subtask(self):
        original = SubTask(
            name="set_wash",
            agent_role="WriteAgent",
            description="set wash to 75%",
            allowed_risk=RiskTier.SAFE_WRITE,
            mcp_tools=["group_at"],
            inputs={"group_id": 3, "level": 75},
            depends_on=["discover_groups"],
        )
        planstep = subtask_to_planstep(original)
        recovered = planstep_to_subtask(planstep)

        assert recovered.description == original.description
        assert recovered.allowed_risk == original.allowed_risk
        assert recovered.mcp_tools == original.mcp_tools
        assert recovered.inputs == original.inputs
        assert recovered.depends_on == original.depends_on

    def test_planstep_subtask_planstep(self):
        original = PlanStep(
            tool_name="store_preset",
            tool_args={"preset_id": "4.1"},
            description="store position preset",
            risk_tier=RiskTier.DESTRUCTIVE,
            depends_on=["select_fixtures"],
        )
        subtask = planstep_to_subtask(original)
        recovered = subtask_to_planstep(subtask)

        assert recovered.tool_name == original.tool_name
        assert recovered.tool_args == original.tool_args
        assert recovered.description == original.description
        assert recovered.risk_tier == original.risk_tier
        assert recovered.depends_on == original.depends_on


# ── bulk helpers ─────────────────────────────────────────────────────────────


class TestBulkHelpers:
    def _subtasks(self) -> list[SubTask]:
        return [
            SubTask(
                name=f"step_{i}",
                agent_role="Agent",
                description=f"step {i}",
                allowed_risk=RiskTier.SAFE_READ,
                mcp_tools=["list_objects"],
                inputs={},
            )
            for i in range(3)
        ]

    def test_plansteps_from_subtasks_length(self):
        result = plansteps_from_subtasks(self._subtasks())
        assert len(result) == 3

    def test_plansteps_from_subtasks_types(self):
        result = plansteps_from_subtasks(self._subtasks())
        assert all(isinstance(ps, PlanStep) for ps in result)

    def test_subtasks_from_plansteps_length(self):
        plansteps = plansteps_from_subtasks(self._subtasks())
        result = subtasks_from_plansteps(plansteps)
        assert len(result) == 3

    def test_subtasks_from_plansteps_types(self):
        plansteps = plansteps_from_subtasks(self._subtasks())
        result = subtasks_from_plansteps(plansteps)
        assert all(isinstance(st, SubTask) for st in result)

    def test_empty_list_returns_empty(self):
        assert plansteps_from_subtasks([]) == []
        assert subtasks_from_plansteps([]) == []


# ── Dependency resolution tests ──────────────────────────────────────────


class TestDependencyResolution:
    """Tests that bulk converters resolve name↔UUID dependencies."""

    def test_plansteps_from_subtasks_resolves_dependencies(self):
        s1 = SubTask(
            name="step_a", agent_role="A", description="first",
            allowed_risk=RiskTier.SAFE_READ, mcp_tools=["tool_a"],
        )
        s2 = SubTask(
            name="step_b", agent_role="B", description="second",
            allowed_risk=RiskTier.SAFE_READ, mcp_tools=["tool_b"],
            depends_on=["step_a"],
        )
        plan_steps = plansteps_from_subtasks([s1, s2])
        # s2's depends_on should now contain s1's UUID, not "step_a"
        assert len(plan_steps[1].depends_on) == 1
        assert plan_steps[1].depends_on[0] == plan_steps[0].id
        # s1 has no dependencies
        assert plan_steps[0].depends_on == []

    def test_subtasks_from_plansteps_resolves_dependencies(self):
        ps1 = PlanStep(
            tool_name="tool_a", tool_args={}, description="first",
            risk_tier=RiskTier.SAFE_READ,
        )
        ps2 = PlanStep(
            tool_name="tool_b", tool_args={}, description="second",
            risk_tier=RiskTier.SAFE_READ,
            depends_on=[ps1.id],
        )
        subtasks = subtasks_from_plansteps([ps1, ps2])
        # s2's depends_on should be resolved to s1's name (which is ps1.id)
        assert len(subtasks[1].depends_on) == 1
        assert subtasks[1].depends_on[0] == subtasks[0].name

    def test_round_trip_preserves_dependency_order(self):
        """SubTask→PlanStep→SubTask preserves dependency graph structure."""
        s1 = SubTask(
            name="select", agent_role="A", description="select fixtures",
            allowed_risk=RiskTier.SAFE_READ, mcp_tools=["select_tool"],
        )
        s2 = SubTask(
            name="store", agent_role="B", description="store preset",
            allowed_risk=RiskTier.DESTRUCTIVE, mcp_tools=["store_tool"],
            depends_on=["select"],
        )
        s3 = SubTask(
            name="verify", agent_role="C", description="verify",
            allowed_risk=RiskTier.SAFE_READ, mcp_tools=["verify_tool"],
            depends_on=["store"],
        )
        plan_steps = plansteps_from_subtasks([s1, s2, s3])
        # Check chain: s3 depends on s2 depends on s1
        assert plan_steps[1].depends_on == [plan_steps[0].id]
        assert plan_steps[2].depends_on == [plan_steps[1].id]

    def test_unknown_dependency_is_dropped(self):
        """Dependencies referencing unknown step names are silently dropped."""
        s1 = SubTask(
            name="step_a", agent_role="A", description="first",
            allowed_risk=RiskTier.SAFE_READ, mcp_tools=["tool_a"],
            depends_on=["nonexistent_step"],
        )
        plan_steps = plansteps_from_subtasks([s1])
        assert plan_steps[0].depends_on == []


# ── execute_subtasks_via_agent tests ─────────────────────────────────────


async def _mock_success(**kwargs) -> str:
    return json.dumps({"ok": True})


@pytest.mark.asyncio
class TestExecuteSubtasksViaAgent:
    """Tests for the bridge execution function."""

    async def test_runs_subtasks_through_executor(self):
        from src.agent.executor import StepExecutor
        from src.agent.policy import PolicyEngine
        from src.agent.verification import Verifier

        executor = StepExecutor(
            tool_registry={"tool_a": _mock_success, "tool_b": _mock_success},
            policy=PolicyEngine(),
            verifier=Verifier(tool_dispatch={}),
        )
        s1 = SubTask(
            name="step_a", agent_role="A", description="first",
            allowed_risk=RiskTier.SAFE_READ, mcp_tools=["tool_a"],
        )
        s2 = SubTask(
            name="step_b", agent_role="B", description="second",
            allowed_risk=RiskTier.SAFE_READ, mcp_tools=["tool_b"],
            depends_on=["step_a"],
        )
        context = await execute_subtasks_via_agent(
            [s1, s2], executor, goal="bridge test"
        )
        assert context.status == RunStatus.COMPLETED
        assert len(context.completed_steps()) == 2
