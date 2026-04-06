# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
agent_bridge.py — Adapters between the orchestrator's SubTask model and the
agent harness's PlanStep model.

The two subsystems use different vocabulary for the same concept (one atomic
unit of console work), so these pure converters let them interoperate without
coupling their internals.

Conversion rules
----------------
SubTask → PlanStep
  tool_name   = subtask.mcp_tools[0] if mcp_tools else "noop"
  tool_args   = subtask.inputs
  description = subtask.description
  risk_tier   = subtask.allowed_risk
  depends_on  = subtask.depends_on

PlanStep → SubTask
  name        = planstep.id (UUID string)
  agent_role  = "BridgedAgent"
  description = planstep.description
  allowed_risk = planstep.risk_tier
  mcp_tools   = [planstep.tool_name]
  inputs      = planstep.tool_args
  confirmed   = False  (DESTRUCTIVE steps must be re-confirmed on the SubTask side)
  depends_on  = planstep.depends_on
"""

from __future__ import annotations

from src.agent.state import PlanStep
from src.task_decomposer import SubTask


def subtask_to_planstep(subtask: SubTask) -> PlanStep:
    """Convert an orchestrator SubTask to an agent-harness PlanStep.

    If ``mcp_tools`` is empty the step is mapped to tool name ``"noop"`` so the
    agent executor can handle it gracefully without crashing.
    """
    tool_name = subtask.mcp_tools[0] if subtask.mcp_tools else "noop"
    return PlanStep(
        tool_name=tool_name,
        tool_args=dict(subtask.inputs),
        description=subtask.description,
        risk_tier=subtask.allowed_risk,
        depends_on=list(subtask.depends_on),
    )


def planstep_to_subtask(planstep: PlanStep) -> SubTask:
    """Convert an agent-harness PlanStep to an orchestrator SubTask.

    Notes
    -----
    - ``confirmed`` is always ``False``: DESTRUCTIVE steps must be explicitly
      re-confirmed by the orchestrator before execution.
    - ``agent_role`` is set to ``"BridgedAgent"`` as a sentinel so callers can
      detect bridged steps if needed.
    - ``status``, ``result``, ``error``, and timing fields on the PlanStep are
      intentionally dropped; they are execution-state that the SubTask model
      does not carry.
    """
    return SubTask(
        name=planstep.id,
        agent_role="BridgedAgent",
        description=planstep.description,
        allowed_risk=planstep.risk_tier,
        mcp_tools=[planstep.tool_name],
        inputs=dict(planstep.tool_args),
        depends_on=list(planstep.depends_on),
        confirmed=False,
    )


def plansteps_from_subtasks(subtasks: list[SubTask]) -> list[PlanStep]:
    """Bulk convert an ordered SubTask list to PlanSteps.

    Resolves name-based dependencies (SubTask.depends_on) to UUID-based
    (PlanStep.depends_on) using a mapping table built from the conversion.
    """
    steps = [subtask_to_planstep(st) for st in subtasks]
    # Build name → UUID mapping
    name_to_id: dict[str, str] = {}
    for st, ps in zip(subtasks, steps, strict=True):
        name_to_id[st.name] = ps.id
    # Resolve depends_on from names to UUIDs
    for ps, st in zip(steps, subtasks, strict=True):
        ps.depends_on = [
            name_to_id[dep] for dep in st.depends_on if dep in name_to_id
        ]
    return steps


def subtasks_from_plansteps(plansteps: list[PlanStep]) -> list[SubTask]:
    """Bulk convert a PlanStep list to SubTasks.

    Resolves UUID-based dependencies (PlanStep.depends_on) to name-based
    (SubTask.depends_on) using each PlanStep's UUID as the SubTask name.
    """
    subtasks = [planstep_to_subtask(ps) for ps in plansteps]
    # Build UUID → name mapping
    id_to_name: dict[str, str] = {}
    for ps, st in zip(plansteps, subtasks, strict=True):
        id_to_name[ps.id] = st.name
    # Resolve depends_on from UUIDs to names
    for st, ps in zip(subtasks, plansteps, strict=True):
        st.depends_on = [
            id_to_name[dep] for dep in ps.depends_on if dep in id_to_name
        ]
    return subtasks


async def execute_subtasks_via_agent(
    subtasks: list[SubTask],
    executor: "StepExecutor",
    goal: str = "",
    on_confirm: "ConfirmCallback | None" = None,
) -> "RunContext":
    """Convert SubTasks to PlanSteps and execute via StepExecutor.

    This bridges System A plans (TaskDecomposer output) into System B
    execution (with verification, rollback, and progress monitoring).

    Returns:
        RunContext with fully populated plan steps (status, result, error).
    """
    plan_steps = plansteps_from_subtasks(subtasks)
    from src.agent.state import RunContext  # deferred to avoid circular import

    context = RunContext(goal=goal, plan=plan_steps)
    return await executor.execute_plan(context, on_confirm=on_confirm)
