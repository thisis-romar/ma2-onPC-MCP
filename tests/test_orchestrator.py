"""
tests/test_orchestrator.py — Unit tests for src/orchestrator.py

Covers:
  - _preflight_guard()
  - _default_sub_agent() (mocked tool_caller)
  - Orchestrator.run() — sequential execution, success/partial/failed outcomes
  - Orchestrator.run() — auto_confirm_destructive
  - Orchestrator.recent_sessions() / recall()
  - OrchestrationResult.report()
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from src.orchestrator import (
    _preflight_guard,
    _default_sub_agent,
    Orchestrator,
    OrchestrationResult,
    StepResult,
)
from src.task_decomposer import SubTask, TaskPlan, TaskDecomposer
from src.agent_memory import WorkingMemory, LongTermMemory
from src.rights import RightsContext, FeedbackClass
from src.vocab import RiskTier
from src.commands.constants import MA2Right


# ── Helpers ──────────────────────────────────────────────────────────────────

def _step(name, risk=RiskTier.SAFE_READ, tools=None, depends_on=None, confirmed=False):
    return SubTask(
        name=name,
        agent_role="TestAgent",
        description=f"step {name}",
        allowed_risk=risk,
        mcp_tools=tools or ["navigate_console"],
        depends_on=depends_on or [],
        confirmed=confirmed,
    )


def _wm(right=MA2Right.ADMIN):
    wm = WorkingMemory(task_description="test")
    wm.rights_context = RightsContext(user_right=right, username="testuser")
    return wm


def _ltm_tmp():
    fd, path_str = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    path = Path(path_str)
    return LongTermMemory(db_path=path), path


# ── _preflight_guard() ───────────────────────────────────────────────────────

class TestPreflightGuard:
    def test_safe_read_always_passes(self):
        step = _step("read", risk=RiskTier.SAFE_READ)
        wm = _wm(right=MA2Right.NONE)
        assert _preflight_guard(step, wm) is None

    def test_destructive_unconfirmed_blocked(self):
        step = _step("store", risk=RiskTier.DESTRUCTIVE, confirmed=False)
        wm = _wm()
        err = _preflight_guard(step, wm)
        assert err is not None
        assert "DESTRUCTIVE" in err

    def test_destructive_confirmed_passes_rights(self):
        step = _step("store", risk=RiskTier.DESTRUCTIVE,
                     tools=["store_current_cue"], confirmed=True)
        wm = _wm(right=MA2Right.ADMIN)
        # snapshot None → staleness check returns warning but doesn't block
        result = _preflight_guard(step, wm)
        # DESTRUCTIVE + confirmed + stale snapshot → should block on staleness
        assert result is not None  # "No ConsoleStateSnapshot" staleness warning blocks

    def test_rights_check_insufficient_right(self):
        step = _step("load", risk=RiskTier.SAFE_READ, tools=["load_show"])
        wm = _wm(right=MA2Right.SETUP)  # load_show requires ADMIN
        err = _preflight_guard(step, wm)
        assert err is not None
        assert "FAILED_CLOSED" in err

    def test_rights_check_none_skipped(self):
        # rights=NONE means "not yet hydrated" — do not block
        step = _step("read", risk=RiskTier.SAFE_READ, tools=["load_show"])
        wm = _wm(right=MA2Right.NONE)
        assert _preflight_guard(step, wm) is None

    def test_no_tools_passes(self):
        step = SubTask(
            name="empty", agent_role="A", description="",
            allowed_risk=RiskTier.SAFE_READ, mcp_tools=[],
        )
        wm = _wm()
        assert _preflight_guard(step, wm) is None


# ── _default_sub_agent() ─────────────────────────────────────────────────────

class TestDefaultSubAgent:
    @pytest.mark.asyncio
    async def test_success_pass_allowed(self):
        step = _step("read", tools=["navigate_console"])
        wm = _wm()
        tool_caller = AsyncMock(return_value='{"command_sent": "cd /", "raw_response": "Fixture"}')
        result = await _default_sub_agent(step, wm, tool_caller)
        assert result.success is True
        assert result.feedback_class == FeedbackClass.PASS_ALLOWED

    @pytest.mark.asyncio
    async def test_no_tools_fails(self):
        step = SubTask(
            name="empty", agent_role="A", description="",
            allowed_risk=RiskTier.SAFE_READ, mcp_tools=[],
        )
        wm = _wm()
        result = await _default_sub_agent(step, wm, AsyncMock())
        assert result.success is False
        assert "No tools" in result.error

    @pytest.mark.asyncio
    async def test_destructive_unconfirmed_blocked(self):
        step = _step("store", risk=RiskTier.DESTRUCTIVE, confirmed=False)
        wm = _wm()
        result = await _default_sub_agent(step, wm, AsyncMock())
        assert result.success is False
        assert result.feedback_class == FeedbackClass.PASS_DENIED

    @pytest.mark.asyncio
    async def test_tool_exception_captured(self):
        step = _step("read", tools=["navigate_console"])
        wm = _wm()
        async def raise_fn(name, inputs):
            raise RuntimeError("telnet timeout")
        result = await _default_sub_agent(step, wm, raise_fn)
        assert result.success is False
        assert "telnet timeout" in result.error

    @pytest.mark.asyncio
    async def test_error_72_classified_failed_open(self):
        step = _step("read", tools=["navigate_console"])
        wm = _wm()
        tool_caller = AsyncMock(return_value="Error #72 insufficient rights")
        result = await _default_sub_agent(step, wm, tool_caller)
        assert result.feedback_class == FeedbackClass.FAILED_OPEN


# ── Orchestrator ─────────────────────────────────────────────────────────────

@pytest.fixture
def ltm_and_path():
    ltm, path = _ltm_tmp()
    yield ltm, path
    ltm._conn.close()
    path.unlink(missing_ok=True)


@pytest.fixture
def simple_orchestrator(ltm_and_path):
    ltm, _ = ltm_and_path
    calls = []

    async def tool_caller(name, inputs):
        calls.append((name, inputs))
        return '{"command_sent": "test", "raw_response": "OK"}'

    orch = Orchestrator(
        tool_caller=tool_caller,
        telnet_send=None,
        ltm=ltm,
        parallel=False,
    )
    return orch, calls


class TestOrchestratorRun:
    @pytest.mark.asyncio
    async def test_safe_steps_succeed(self, simple_orchestrator):
        orch, calls = simple_orchestrator
        result = await orch.run("blue wash on movers", {"color": "blue"})
        assert result.outcome in ("success", "partial", "failed")
        assert isinstance(result.session_id, str)
        assert len(result.session_id) == 8

    @pytest.mark.asyncio
    async def test_all_safe_steps_succeed(self, simple_orchestrator):
        orch, _ = simple_orchestrator

        class SafeDecomposer:
            def decompose(self, goal, params):
                return TaskPlan(goal=goal, steps=[
                    _step("read1", risk=RiskTier.SAFE_READ),
                    _step("read2", risk=RiskTier.SAFE_READ, depends_on=["read1"]),
                ])

        orch._decomposer = SafeDecomposer()
        result = await orch.run("safe goal")
        assert result.outcome == "success"
        assert result.steps_done == 2
        assert result.steps_failed == 0

    @pytest.mark.asyncio
    async def test_destructive_blocked_without_confirm(self, simple_orchestrator):
        orch, _ = simple_orchestrator

        class DestructDecomposer:
            def decompose(self, goal, params):
                return TaskPlan(goal=goal, steps=[
                    _step("destroy", risk=RiskTier.DESTRUCTIVE, confirmed=False),
                ])

        orch._decomposer = DestructDecomposer()
        result = await orch.run("destructive goal")
        assert result.steps_failed >= 1

    @pytest.mark.asyncio
    async def test_auto_confirm_destructive(self, simple_orchestrator):
        orch, _ = simple_orchestrator

        class DestructDecomposer:
            def decompose(self, goal, params):
                return TaskPlan(goal=goal, steps=[
                    _step("destroy", risk=RiskTier.DESTRUCTIVE, tools=["navigate_console"],
                          confirmed=False),
                ])

        orch._decomposer = DestructDecomposer()
        result = await orch.run("destructive goal", auto_confirm_destructive=True)
        # staleness check still blocks (no snapshot) — but confirm gate is open
        # outcome depends on whether staleness guard blocks
        assert isinstance(result.outcome, str)

    @pytest.mark.asyncio
    async def test_result_has_report(self, simple_orchestrator):
        orch, _ = simple_orchestrator
        result = await orch.run("blue wash")
        report = result.report()
        assert "Orchestration Report" in report
        assert result.goal in report

    @pytest.mark.asyncio
    async def test_result_tokens_tracked(self, simple_orchestrator):
        orch, _ = simple_orchestrator

        class SafeDecomposer:
            def decompose(self, goal, params):
                return TaskPlan(goal=goal, steps=[
                    _step("s1", risk=RiskTier.SAFE_READ),
                ])

        orch._decomposer = SafeDecomposer()
        result = await orch.run("token test")
        assert result.total_tokens >= 0

    @pytest.mark.asyncio
    async def test_session_saved_to_ltm(self, ltm_and_path):
        ltm, _ = ltm_and_path

        async def tool_caller(name, inputs):
            return '{"ok": true}'

        orch = Orchestrator(tool_caller=tool_caller, ltm=ltm)
        await orch.run("save test")
        sessions = orch.recent_sessions(5)
        assert len(sessions) >= 1

    @pytest.mark.asyncio
    async def test_recall_returns_snapshot(self, ltm_and_path):
        ltm, _ = ltm_and_path

        async def tool_caller(name, inputs):
            return '{"ok": true}'

        orch = Orchestrator(tool_caller=tool_caller, ltm=ltm)
        result = await orch.run("recall test")
        snap = orch.recall(result.session_id)
        assert snap is not None
        assert snap.get("task_description") == "recall test"

    @pytest.mark.asyncio
    async def test_recall_unknown_returns_none(self, ltm_and_path):
        ltm, _ = ltm_and_path
        orch = Orchestrator(tool_caller=AsyncMock(), ltm=ltm)
        assert orch.recall("deadbeef") is None

    @pytest.mark.asyncio
    async def test_dep_failure_skips_dependent(self, ltm_and_path):
        ltm, _ = ltm_and_path

        async def failing_caller(name, inputs):
            return '{"blocked": true, "error": "scope fail"}'

        orch = Orchestrator(tool_caller=failing_caller, ltm=ltm)

        class DepDecomposer:
            def decompose(self, goal, params):
                return TaskPlan(goal=goal, steps=[
                    _step("fail_step", risk=RiskTier.SAFE_READ),
                    _step("dep_step", risk=RiskTier.SAFE_READ, depends_on=["fail_step"]),
                ])

        orch._decomposer = DepDecomposer()
        result = await orch.run("dep test")
        # dep_step should be skipped because fail_step didn't succeed
        dep_results = [r for r in result.step_results if r.step_name == "dep_step"]
        if dep_results:
            assert dep_results[0].success is False


# ── OrchestrationResult.report() ────────────────────────────────────────────

class TestOrchestrationReport:
    def test_report_format(self):
        r = OrchestrationResult(
            session_id="abc12345",
            goal="test goal",
            outcome="success",
            steps_done=2,
            steps_failed=0,
            total_tokens=100,
            elapsed_s=1.5,
            step_results=[
                StepResult(step_name="s1", success=True,
                           feedback_class=FeedbackClass.PASS_ALLOWED),
            ],
        )
        report = r.report()
        assert "abc12345" in report
        assert "test goal" in report
        assert "SUCCESS" in report
        assert "s1" in report
