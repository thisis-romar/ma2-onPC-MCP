# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for src/agent/rollback.py — compensating transaction executor."""

import json
from unittest.mock import AsyncMock

import pytest

from src.agent.rollback import RollbackExecutor, RollbackResult
from src.agent.state import PlanStep, RollbackStrategy, RunContext
from src.vocab import RiskTier


def _step(tool_name="store_current_cue", **kwargs):
    return PlanStep(
        tool_name=tool_name,
        tool_args=kwargs,
        description=f"test {tool_name}",
        risk_tier=RiskTier.DESTRUCTIVE,
    )


def _context():
    return RunContext(goal="test", plan=[])


class TestRollbackExecutorOops:
    @pytest.mark.asyncio
    async def test_oops_success(self):
        dispatch = {"playback_action": AsyncMock(return_value='{"command": "oops"}')}
        executor = RollbackExecutor(dispatch)
        result = await executor.execute(
            RollbackStrategy.OOPS, _step(), _context(),
        )
        assert result.success is True
        assert result.strategy == RollbackStrategy.OOPS
        assert result.command_sent == "oops"
        dispatch["playback_action"].assert_awaited_once_with(action="oops")

    @pytest.mark.asyncio
    async def test_oops_error_in_response(self):
        dispatch = {"playback_action": AsyncMock(return_value='{"error": "unknown"}')}
        executor = RollbackExecutor(dispatch)
        result = await executor.execute(
            RollbackStrategy.OOPS, _step(), _context(),
        )
        assert result.success is False

    @pytest.mark.asyncio
    async def test_oops_tool_not_available(self):
        executor = RollbackExecutor({})
        result = await executor.execute(
            RollbackStrategy.OOPS, _step(), _context(),
        )
        assert result.success is False
        assert "not available" in result.response

    @pytest.mark.asyncio
    async def test_oops_exception(self):
        dispatch = {"playback_action": AsyncMock(side_effect=RuntimeError("conn lost"))}
        executor = RollbackExecutor(dispatch)
        result = await executor.execute(
            RollbackStrategy.OOPS, _step(), _context(),
        )
        assert result.success is False
        assert "conn lost" in result.response


class TestRollbackExecutorDelete:
    @pytest.mark.asyncio
    async def test_delete_success(self):
        resp = json.dumps({"command": "delete fixture 1", "response": "Ok"})
        dispatch = {"delete_object": AsyncMock(return_value=resp)}
        step = _step("patch_fixture", object_type="fixture", object_id="1")
        executor = RollbackExecutor(dispatch)
        result = await executor.execute(
            RollbackStrategy.DELETE, step, _context(),
        )
        assert result.success is True
        assert result.strategy == RollbackStrategy.DELETE
        assert "delete fixture 1" in (result.command_sent or "")

    @pytest.mark.asyncio
    async def test_delete_missing_object_info(self):
        dispatch = {"delete_object": AsyncMock()}
        step = _step("patch_fixture")  # no object_type/object_id
        executor = RollbackExecutor(dispatch)
        result = await executor.execute(
            RollbackStrategy.DELETE, step, _context(),
        )
        assert result.success is False
        assert "Cannot determine" in result.response

    @pytest.mark.asyncio
    async def test_delete_tool_not_available(self):
        executor = RollbackExecutor({})
        step = _step("patch_fixture", object_type="fixture", object_id="1")
        result = await executor.execute(
            RollbackStrategy.DELETE, step, _context(),
        )
        assert result.success is False


class TestRollbackExecutorNone:
    @pytest.mark.asyncio
    async def test_none_is_noop(self):
        executor = RollbackExecutor({})
        result = await executor.execute(
            RollbackStrategy.NONE, _step(), _context(),
        )
        assert result.success is True
        assert result.command_sent is None


class TestRollbackResult:
    def test_dataclass_fields(self):
        r = RollbackResult(
            success=True,
            strategy=RollbackStrategy.OOPS,
            command_sent="oops",
            response="Ok",
        )
        assert r.success is True
        assert r.strategy == RollbackStrategy.OOPS
