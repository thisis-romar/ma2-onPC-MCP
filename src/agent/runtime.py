# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Agent runtime — top-level orchestrator wiring planner, executor, policy, and memory.

This is the entry point for the agent harness. It accepts a high-level goal,
generates a plan, validates it, executes steps, and produces a trace.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from src.agent.executor import ConfirmCallback, StepExecutor
from src.agent.memory import WorkflowMemory
from src.agent.planner import DomainPlanner
from src.agent.policy import PolicyEngine
from src.agent.state import ParsedGoal, PlanStep, RunContext, RunStatus, StepStatus
from src.agent.trace import ExecutionTrace, build_trace
from src.agent.verification import Verifier

logger = logging.getLogger(__name__)


class AgentRuntime:
    """Top-level agent harness that turns goals into executed plans."""

    def __init__(
        self,
        tool_registry: dict[str, Callable[..., Awaitable[str]]],
        *,
        memory_db_path: str | None = None,
        batch_limit: int = 10,
        max_retries: int = 2,
    ):
        self.planner = DomainPlanner()
        self.policy = PolicyEngine(batch_limit=batch_limit)
        self.verifier = Verifier(tool_dispatch=tool_registry)
        if memory_db_path:
            self.memory = WorkflowMemory(db_path=memory_db_path)
        else:
            self.memory = WorkflowMemory()
        self.executor = StepExecutor(
            tool_registry=tool_registry,
            policy=self.policy,
            verifier=self.verifier,
            max_retries=max_retries,
            checkpoint_fn=self._checkpoint,
        )

    def _checkpoint(self, run_id: str, step_index: int, step_dict: dict) -> None:
        """Persist a step's state for crash recovery."""
        try:
            self.memory.save_step_checkpoint(run_id, step_index, step_dict)
        except Exception as e:
            logger.warning("Failed to persist step checkpoint: %s", e)

    async def run(
        self,
        goal: str,
        on_confirm: ConfirmCallback | None = None,
    ) -> ExecutionTrace:
        """Full agent loop: goal -> plan -> validate -> execute -> trace.

        Args:
            goal: High-level natural language goal.
            on_confirm: Async callback for destructive step confirmation.
                Receives a PlanStep, returns True to proceed or False to abort.

        Returns:
            ExecutionTrace with the complete run record.
        """
        started_at = datetime.now(UTC)

        # 1. Parse goal
        parsed_goal = self.planner.classify_goal(goal)
        logger.info(
            "Goal classified: intent=%s, object_type=%s, confidence=%.2f",
            parsed_goal.intent.value,
            parsed_goal.object_type,
            parsed_goal.confidence,
        )

        # 2. Check memory for matching recipes
        recipe = self._find_matching_recipe(parsed_goal)
        if recipe:
            logger.info("Found matching recipe: %s", recipe["name"])

        # 3. Generate plan
        plan = self.planner.plan(parsed_goal)
        logger.info("Plan generated: %d steps", len(plan))

        # 4. Validate plan via policy engine
        policy_result = self.policy.validate_plan(plan, confidence=parsed_goal.confidence)
        policy_warnings = policy_result.warnings

        if not policy_result.approved:
            # Plan rejected by policy
            context = RunContext(goal=goal, plan=plan, status=RunStatus.ABORTED)
            violation_msgs = [v.message for v in policy_result.violations]
            logger.warning("Plan rejected by policy: %s", violation_msgs)
            trace = build_trace(context, started_at, policy_warnings=violation_msgs)
            return trace

        # Inject any policy-added steps (verification, discovery)
        if policy_result.injected_steps:
            plan = policy_result.injected_steps + plan

        # 5. Create run context
        context = RunContext(goal=goal, plan=plan)
        logger.info("Run %s started: %s", context.run_id, goal)

        # 5b. Persist plan so resume_run can reconstruct the DAG on crash
        try:
            self.memory.record_run_summary(
                run_id=context.run_id,
                goal=goal,
                result="in_progress",
                trace_json=json.dumps({"plan": [s.to_dict() for s in plan]}),
            )
        except Exception as e:
            logger.warning("Failed to persist plan before execution: %s", e)

        # 6. Execute
        context = await self.executor.execute_plan(context, on_confirm=on_confirm)

        # 7. Build trace
        trace = build_trace(context, started_at, policy_warnings=policy_warnings)

        # 8. Store in memory (overwrites the "in_progress" record)
        try:
            self.memory.record_run_summary(
                run_id=trace.run_id,
                goal=trace.goal,
                result=trace.result,
                trace_json=trace.to_json(),
            )
            # Clean up step checkpoints — run completed successfully
            self.memory.delete_run_checkpoints(trace.run_id)
        except Exception as e:
            logger.warning("Failed to store run in memory: %s", e)

        # 9. Save trace to file
        try:
            trace.to_file()
        except Exception as e:
            logger.warning("Failed to write trace file: %s", e)

        logger.info(
            "Run %s completed: result=%s, steps=%d, duration=%dms",
            trace.run_id,
            trace.result,
            len(trace.steps),
            trace.total_duration_ms,
        )

        return trace

    async def plan_only(self, goal: str) -> tuple[ParsedGoal, list[PlanStep], list[str]]:
        """Generate and validate a plan without executing it.

        Returns:
            (parsed_goal, plan_steps, policy_warnings)
        """
        parsed_goal = self.planner.classify_goal(goal)
        plan = self.planner.plan(parsed_goal)
        policy_result = self.policy.validate_plan(plan, confidence=parsed_goal.confidence)
        return parsed_goal, plan, policy_result.warnings

    async def resume_run(
        self,
        run_id: str,
        on_confirm: ConfirmCallback | None = None,
    ) -> ExecutionTrace | None:
        """Resume a previously interrupted run from its last checkpoint.

        Returns None if the run_id is not found or has no saved plan.
        """
        # Load the original plan from run_history
        runs = self.memory.recall_runs(limit=200)
        run_record = next((r for r in runs if r["run_id"] == run_id), None)
        if not run_record:
            logger.warning("Cannot resume run %s — not found in history", run_id)
            return None

        trace_data = run_record.get("trace", {})
        plan_dicts = trace_data.get("plan", [])
        if not plan_dicts:
            logger.warning("Cannot resume run %s — no plan data stored", run_id)
            return None

        # Reconstruct PlanStep list from stored plan
        plan: list[PlanStep] = []
        for d in plan_dicts:
            step = PlanStep(
                tool_name=d["tool_name"],
                tool_args=d.get("tool_args", {}),
                description=d.get("description", ""),
                risk_tier=d.get("risk_tier", "SAFE_READ"),
            )
            step.id = d.get("id", step.id)
            step.depends_on = d.get("depends_on", [])
            plan.append(step)

        # Load checkpoints and mark completed steps
        checkpoints = self.memory.load_run_checkpoints(run_id)
        checkpoint_map = {cp["step_id"]: cp for cp in checkpoints}

        for step in plan:
            cp = checkpoint_map.get(step.id)
            if cp and cp["status"] in ("completed", "COMPLETED"):
                step.status = StepStatus.COMPLETED
                step.result = cp.get("result")
            elif cp and cp["status"] in ("failed", "FAILED"):
                step.status = StepStatus.FAILED
                step.error = cp.get("error")
            elif cp and cp["status"] in ("skipped", "SKIPPED"):
                step.status = StepStatus.SKIPPED
                step.error = cp.get("error")
            # else: remains PENDING — will be re-executed

        # Build context and execute remaining steps
        context = RunContext(goal=run_record["goal"], plan=plan)
        context.run_id = run_id
        logger.info(
            "Resuming run %s — %d steps total, %d already completed",
            run_id,
            len(plan),
            sum(1 for s in plan if s.status == StepStatus.COMPLETED),
        )

        started_at = datetime.now(UTC)
        context = await self.executor.execute_plan(context, on_confirm=on_confirm)
        trace = build_trace(context, started_at)

        # Store final result
        try:
            self.memory.record_run_summary(
                run_id=run_id,
                goal=trace.goal,
                result=trace.result,
                trace_json=trace.to_json(),
            )
            self.memory.delete_run_checkpoints(run_id)
        except Exception as e:
            logger.warning("Failed to store resumed run: %s", e)

        return trace

    def _find_matching_recipe(self, goal: ParsedGoal) -> dict[str, Any] | None:
        """Check workflow memory for a matching recipe."""
        try:
            # Search by intent tag
            recipes = self.memory.recall_recipe(tags=[goal.intent.value])
            if recipes:
                return recipes[0]

            # Search by object type tag
            if goal.object_type:
                recipes = self.memory.recall_recipe(tags=[goal.object_type])
                if recipes:
                    return recipes[0]
        except Exception as e:
            logger.debug("Recipe search failed: %s", e)

        return None
