# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Step executor — calls MCP tool functions, handles retries and confirmations.

The executor imports tool functions from src/server.py and calls them directly
as async Python functions. No MCP protocol overhead — shared telnet client.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from enum import StrEnum

from src.agent.policy import PolicyEngine, StepDecision
from src.agent.rollback import RollbackExecutor, RollbackResult
from src.agent.state import (
    PlanStep,
    RollbackStrategy,
    RunContext,
    RunStatus,
    StepStatus,
)
from src.agent.verification import Verifier

logger = logging.getLogger(__name__)

# Type for the confirmation callback: receives a PlanStep, returns True to proceed
ConfirmCallback = Callable[[PlanStep], Awaitable[bool]]

DEFAULT_MAX_RETRIES = 2
RETRY_DELAYS = [1.0, 2.0, 4.0]  # seconds between retries


# ── Progress monitoring ──────────────────────────────────────────────────


class ProgressStatus(StrEnum):
    """Outcome of a progress check on a step."""

    PROGRESSING = "progressing"
    STALLED = "stalled"       # too many consecutive failures
    LOOPING = "looping"       # identical output repeated


class ProgressMonitor:
    """Detects stalled or looping execution by tracking outputs per step.

    Tracks two signals:
      1. **Consecutive failures** — if a step fails N times in a row, it's STALLED.
      2. **Identical outputs** — if the same output hash appears M times, it's LOOPING.
    """

    def __init__(
        self,
        max_consecutive_failures: int = 3,
        max_identical_outputs: int = 2,
    ):
        self.max_consecutive_failures = max_consecutive_failures
        self.max_identical_outputs = max_identical_outputs
        # Per-step tracking
        self._failures: dict[str, int] = {}          # step_id → consecutive failure count
        self._output_hashes: dict[str, dict[str, int]] = {}  # step_id → {hash → count}

    def track(self, step_id: str, output: str, *, success: bool) -> ProgressStatus:
        """Record an execution result and return the current progress status."""
        h = hashlib.sha256(output.encode()).hexdigest()[:16]

        if not success:
            self._failures[step_id] = self._failures.get(step_id, 0) + 1
            if self._failures[step_id] >= self.max_consecutive_failures:
                return ProgressStatus.STALLED
            return ProgressStatus.PROGRESSING

        # Success — reset failure counter
        self._failures[step_id] = 0

        # Track output hash
        hashes = self._output_hashes.setdefault(step_id, {})
        hashes[h] = hashes.get(h, 0) + 1
        if hashes[h] >= self.max_identical_outputs:
            return ProgressStatus.LOOPING

        return ProgressStatus.PROGRESSING

    def reset(self, step_id: str) -> None:
        """Clear all tracking data for a step."""
        self._failures.pop(step_id, None)
        self._output_hashes.pop(step_id, None)


class StepExecutor:
    """Executes PlanSteps by calling MCP tool functions."""

    # Type for a checkpoint callback: receives (run_id, step_index, step_dict)
    CheckpointFn = Callable[[str, int, dict], None]

    def __init__(
        self,
        tool_registry: dict[str, Callable[..., Awaitable[str]]],
        policy: PolicyEngine,
        verifier: Verifier,
        max_retries: int = DEFAULT_MAX_RETRIES,
        rollback: RollbackExecutor | None = None,
        checkpoint_fn: CheckpointFn | None = None,
    ):
        self._tools = tool_registry
        self._policy = policy
        self._verifier = verifier
        self._max_retries = max_retries
        self._rollback = rollback or RollbackExecutor(tool_registry)
        self._monitor = ProgressMonitor()
        self._checkpoint_fn = checkpoint_fn

    async def execute_plan(
        self,
        context: RunContext,
        on_confirm: ConfirmCallback | None = None,
    ) -> RunContext:
        """Execute all steps in order, respecting dependencies and policy."""
        context.status = RunStatus.EXECUTING
        context.updated_at = datetime.now(UTC)

        for i, step in enumerate(context.plan):
            context.current_step_index = i

            # Skip steps already completed/failed/skipped (resume scenario)
            if step.status in (
                StepStatus.COMPLETED, StepStatus.FAILED,
                StepStatus.SKIPPED, StepStatus.ROLLED_BACK,
            ):
                continue

            # Policy gate
            decision = self._policy.gate_step(step, context)

            if decision.action == StepDecision.BLOCK:
                logger.warning("Step blocked by policy: %s — %s", step.description, decision.reason)
                step.status = StepStatus.SKIPPED
                step.error = f"Blocked: {decision.reason}"
                self._save_checkpoint(context.run_id, i, step)
                self._skip_dependents(step, context)
                continue

            if decision.action == StepDecision.CONFIRM:
                if on_confirm:
                    step.status = StepStatus.AWAITING_CONFIRMATION
                    context.confirmations_pending.append(step.id)
                    confirmed = await on_confirm(step)
                    context.confirmations_pending = [
                        sid for sid in context.confirmations_pending if sid != step.id
                    ]
                    if not confirmed:
                        logger.info("Step not confirmed, aborting: %s", step.description)
                        step.status = StepStatus.SKIPPED
                        step.error = "User declined confirmation"
                        context.status = RunStatus.ABORTED
                        break
                    # Inject confirm_destructive=True for confirmed destructive steps
                    if "confirm_destructive" in step.tool_args:
                        step.tool_args["confirm_destructive"] = True
                else:
                    # No callback — auto-confirm
                    if "confirm_destructive" in step.tool_args:
                        step.tool_args["confirm_destructive"] = True

            if decision.action == StepDecision.DEFER_TO_DISCOVERY:
                logger.info("Deferring to discovery: %s", step.description)
                step.status = StepStatus.SKIPPED
                step.error = f"Deferred: {decision.reason}"
                continue

            # Execute with retries
            await self._execute_with_retries(step, context)

            # Persist step checkpoint for crash recovery
            self._save_checkpoint(context.run_id, i, step)

            # If step failed, decide whether to continue or abort
            if step.status == StepStatus.FAILED:
                # Skip dependents
                self._skip_dependents(step, context)
                # Check if any remaining non-skipped steps exist
                remaining = [
                    s for s in context.plan[i + 1:]
                    if s.status == StepStatus.PENDING
                ]
                if not remaining:
                    context.status = RunStatus.FAILED
                    break

        # Determine final status
        if context.status == RunStatus.EXECUTING:
            failed = context.failed_steps()
            if failed:
                context.status = RunStatus.FAILED
            else:
                context.status = RunStatus.COMPLETED

        context.updated_at = datetime.now(UTC)
        return context

    def _save_checkpoint(self, run_id: str, step_index: int, step: PlanStep) -> None:
        """Persist a step's state via the checkpoint callback (if configured)."""
        if self._checkpoint_fn is None:
            return
        try:
            self._checkpoint_fn(run_id, step_index, step.to_dict())
        except Exception as e:
            logger.warning("Checkpoint save failed for step %s: %s", step.id, e)

    async def _execute_with_retries(
        self, step: PlanStep, context: RunContext
    ) -> None:
        """Execute a single step with retry logic."""
        for attempt in range(self._max_retries + 1):
            step.status = StepStatus.RUNNING
            step.started_at = datetime.now(UTC)

            try:
                result = await self._call_tool(step)
                step.result = result
                step.completed_at = datetime.now(UTC)

                # Check for error in JSON response
                if self._is_error_result(result):
                    raise RuntimeError(f"Tool returned error: {result}")

                step.status = StepStatus.COMPLETED
                logger.info(
                    "Step completed: %s (attempt %d)", step.description, attempt + 1
                )

                # Progress monitoring — detect identical outputs (looping)
                progress = self._monitor.track(
                    step.id, result or "", success=True,
                )
                if progress == ProgressStatus.LOOPING:
                    logger.warning(
                        "Step '%s' is LOOPING — identical output repeated",
                        step.description,
                    )
                    step.error = "Stall detected: identical output repeated"
                    return  # stay COMPLETED but note the loop

                # Post-step verification
                if self._verifier.has_strategy(step.tool_name):
                    verification = await self._verifier.verify_step(step, context)
                    step.verification = verification
                    if not verification.passed:
                        logger.warning(
                            "Verification failed for %s: %s",
                            step.description,
                            verification.details,
                        )
                        # Attempt rollback if a strategy is available
                        rollback_strategy = self._verifier.suggest_rollback(step)
                        if rollback_strategy != RollbackStrategy.NONE:
                            rb_result = await self._rollback.execute(
                                rollback_strategy, step, context,
                            )
                            if rb_result.success:
                                step.status = StepStatus.ROLLED_BACK
                                step.error = (
                                    f"Verification failed, rolled back via "
                                    f"{rollback_strategy.value}: {rb_result.response}"
                                )
                                logger.info(
                                    "Rolled back step '%s' via %s",
                                    step.description,
                                    rollback_strategy.value,
                                )
                                return  # rolled back — don't retry

                return  # Success

            except Exception as e:
                step.retry_count = attempt + 1
                step.error = str(e)
                step.completed_at = datetime.now(UTC)
                logger.warning(
                    "Step failed: %s (attempt %d/%d) — %s",
                    step.description,
                    attempt + 1,
                    self._max_retries + 1,
                    e,
                )

                # Progress monitoring — detect consecutive failures (stalled)
                progress = self._monitor.track(
                    step.id, str(e), success=False,
                )
                if progress == ProgressStatus.STALLED:
                    logger.warning(
                        "Step '%s' is STALLED — %d consecutive failures",
                        step.description,
                        self._monitor._failures.get(step.id, 0),
                    )
                    step.status = StepStatus.FAILED
                    step.error = f"Stall detected: {e}"
                    return  # abort retries

                if attempt < self._max_retries:
                    delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                    await asyncio.sleep(delay)
                else:
                    step.status = StepStatus.FAILED
                    logger.error(
                        "Step permanently failed after %d attempts: %s",
                        self._max_retries + 1,
                        step.description,
                    )

    async def _call_tool(self, step: PlanStep) -> str:
        """Dispatch to the actual tool function."""
        tool_fn = self._tools.get(step.tool_name)
        if not tool_fn:
            raise ValueError(f"Unknown tool: {step.tool_name}")
        return await tool_fn(**step.tool_args)

    def _is_error_result(self, result: str) -> bool:
        """Check if a tool result JSON indicates an error."""
        try:
            data = json.loads(result)
            return data.get("blocked", False) or "error" in data
        except (json.JSONDecodeError, TypeError):
            return False

    def _skip_dependents(self, failed_step: PlanStep, context: RunContext) -> None:
        """Mark all steps that depend on a failed step as SKIPPED."""
        for step in context.plan:
            if step.status != StepStatus.PENDING:
                continue
            if failed_step.id in step.depends_on:
                step.status = StepStatus.SKIPPED
                step.error = f"Skipped: dependency '{failed_step.description}' failed"
                logger.info("Skipping dependent step: %s", step.description)
                # Recursively skip transitive dependents
                self._skip_dependents(step, context)
