# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Rollback executor — compensating transactions for failed agent steps.

Maps ``RollbackStrategy`` (from ``src/agent/verification.py``) to concrete
grandMA2 commands that undo or reverse the effect of a failed mutation.

Strategies:
  OOPS   → send the ``oops`` console command (undoes last operator action)
  DELETE → send ``delete {object_type} {object_id}`` (removes created object)
  NONE   → no-op
"""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from src.agent.state import PlanStep, RollbackStrategy, RunContext

logger = logging.getLogger(__name__)


@dataclass
class RollbackResult:
    """Outcome of a rollback attempt."""

    success: bool
    strategy: RollbackStrategy
    command_sent: str | None
    response: str


class RollbackExecutor:
    """Executes compensating transactions for failed or unverified steps."""

    def __init__(
        self,
        tool_dispatch: dict[str, Callable[..., Awaitable[str]]] | None = None,
    ):
        self._dispatch = tool_dispatch or {}

    async def execute(
        self,
        strategy: RollbackStrategy,
        step: PlanStep,
        context: RunContext,
    ) -> RollbackResult:
        """Execute the rollback strategy for a given step."""
        if strategy == RollbackStrategy.NONE:
            return RollbackResult(
                success=True, strategy=strategy, command_sent=None, response="",
            )

        if strategy == RollbackStrategy.OOPS:
            return await self._execute_oops(step)

        if strategy == RollbackStrategy.DELETE:
            return await self._execute_delete(step)

        return RollbackResult(
            success=False, strategy=strategy, command_sent=None,
            response=f"Unknown strategy: {strategy}",
        )

    async def _execute_oops(self, step: PlanStep) -> RollbackResult:
        """Send the grandMA2 ``oops`` command to undo the last action."""
        dispatch_fn = self._dispatch.get("playback_action")
        if dispatch_fn is None:
            logger.warning("playback_action tool not available for oops rollback")
            return RollbackResult(
                success=False, strategy=RollbackStrategy.OOPS,
                command_sent=None, response="playback_action tool not available",
            )

        try:
            resp = await dispatch_fn(action="oops")
            is_error = "error" in resp.lower() if resp else True
            logger.info("Oops rollback for step '%s': %s", step.description, resp)
            return RollbackResult(
                success=not is_error,
                strategy=RollbackStrategy.OOPS,
                command_sent="oops",
                response=resp,
            )
        except Exception as e:
            logger.error("Oops rollback failed: %s", e)
            return RollbackResult(
                success=False, strategy=RollbackStrategy.OOPS,
                command_sent="oops", response=str(e),
            )

    async def _execute_delete(self, step: PlanStep) -> RollbackResult:
        """Send a delete command to remove the object created by the step."""
        dispatch_fn = self._dispatch.get("delete_object")
        if dispatch_fn is None:
            logger.warning("delete_object tool not available for delete rollback")
            return RollbackResult(
                success=False, strategy=RollbackStrategy.DELETE,
                command_sent=None, response="delete_object tool not available",
            )

        # Extract object type and ID from step args
        object_type = step.tool_args.get("object_type", "")
        object_id = step.tool_args.get("object_id", step.tool_args.get("id", ""))

        if not object_type or not object_id:
            logger.warning(
                "Cannot determine object_type/id for delete rollback on step '%s'",
                step.description,
            )
            return RollbackResult(
                success=False, strategy=RollbackStrategy.DELETE,
                command_sent=None,
                response="Cannot determine object_type/id from step args",
            )

        try:
            resp = await dispatch_fn(
                object_type=object_type, object_id=object_id,
                confirm_destructive=True,
            )
            data = json.loads(resp) if resp else {}
            is_error = data.get("blocked", False) or "error" in resp.lower()
            cmd = f"delete {object_type} {object_id}"
            logger.info("Delete rollback for step '%s': %s", step.description, resp)
            return RollbackResult(
                success=not is_error,
                strategy=RollbackStrategy.DELETE,
                command_sent=cmd,
                response=resp,
            )
        except Exception as e:
            logger.error("Delete rollback failed: %s", e)
            return RollbackResult(
                success=False, strategy=RollbackStrategy.DELETE,
                command_sent=None, response=str(e),
            )
