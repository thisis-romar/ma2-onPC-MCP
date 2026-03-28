"""
task_decomposer.py — Break high-level show intent into ordered sub-agent steps.

Jensen: "In the future, we're going to write ideas, architectures, specifications.
We're going to organize teams... define how to evaluate the definition of good vs bad."

A TaskDecomposer takes a natural-language lighting goal and produces an ordered
plan of SubTask objects, each scoped to one agent and one risk tier — so no single
agent ever holds all three capabilities (read + write + destructive) at once.

Jensen: "we have policies that give these agents two of the three things
but not all three things at the same time."
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable

from .vocab import RiskTier  # single source of truth — do not redefine


# ---------------------------------------------------------------------------
# Sub-task definition
# ---------------------------------------------------------------------------

@dataclass
class SubTask:
    """
    One atomic unit of work assigned to a specialized sub-agent.

    Jensen's agent model: each agent has a clear scope, memory access,
    allowed tools, and a definition of success.
    """

    name: str                           # e.g. "select_wash_fixtures"
    agent_role: str                     # e.g. "SelectionAgent"
    description: str                    # natural-language intent
    allowed_risk: RiskTier              # max risk level this agent may exercise
    mcp_tools: list[str]                # which of the 90 tools it may call
    inputs: dict = field(default_factory=dict)   # params passed in
    outputs: dict = field(default_factory=dict)  # results written back
    depends_on: list[str] = field(default_factory=list)  # step names
    eval_criteria: str = ""             # Jensen: "definition of good vs bad"
    retryable: bool = True
    confirmed: bool = False             # must be True for DESTRUCTIVE steps


@dataclass
class TaskPlan:
    """Ordered sequence of SubTasks for one high-level goal."""

    goal: str
    steps: list[SubTask] = field(default_factory=list)
    session_id: str = ""

    def ordered_steps(self) -> list[SubTask]:
        """Topological sort respecting depends_on."""
        completed: set[str] = set()
        ordered: list[SubTask] = []
        remaining = list(self.steps)
        max_passes = len(remaining) + 1
        passes = 0
        while remaining and passes < max_passes:
            passes += 1
            for step in list(remaining):
                if all(d in completed for d in step.depends_on):
                    ordered.append(step)
                    completed.add(step.name)
                    remaining.remove(step)
        ordered.extend(remaining)  # append any cycles unresolved
        return ordered

    def summary(self) -> str:
        lines = [f"Goal: {self.goal}", f"Steps ({len(self.steps)}):"]
        for i, s in enumerate(self.ordered_steps(), 1):
            deps = f" [after: {', '.join(s.depends_on)}]" if s.depends_on else ""
            lines.append(f"  {i}. [{s.agent_role}] {s.name}{deps}")
            lines.append(f"     risk={s.allowed_risk.value} tools={s.mcp_tools}")
            lines.append(f"     eval: {s.eval_criteria}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Built-in decomposition rules
# ---------------------------------------------------------------------------

# Each rule: (pattern, plan_builder_fn)
# pattern matches against the lowercased goal string.

Rule = tuple[str, Callable[[str, dict], TaskPlan]]

def _build_wash_look(goal: str, params: dict) -> TaskPlan:
    """Decompose a 'wash look' lighting goal."""
    color   = params.get("color", "")
    group   = params.get("group", "wash")
    preset  = params.get("preset", "")
    seq     = params.get("sequence", 1)
    cue     = params.get("cue", 1.0)

    return TaskPlan(goal=goal, steps=[
        SubTask(
            name="select_wash_group",
            agent_role="SelectionAgent",
            description=f"Select all fixtures in group '{group}'",
            allowed_risk=RiskTier.SAFE_WRITE,
            mcp_tools=["select_fixtures_by_group", "modify_selection"],
            inputs={"group": group},
            eval_criteria="Programmer selection is non-empty and matches group",
        ),
        SubTask(
            name="apply_wash_color",
            agent_role="ColorAgent",
            description=f"Apply {color} color preset to selection",
            allowed_risk=RiskTier.SAFE_WRITE,
            mcp_tools=["apply_preset", "set_attribute"],
            inputs={"color": color, "preset": preset},
            depends_on=["select_wash_group"],
            eval_criteria="Color attribute matches target in programmer",
        ),
        SubTask(
            name="set_wash_intensity",
            agent_role="IntensityAgent",
            description="Set wash intensity to full",
            allowed_risk=RiskTier.SAFE_WRITE,
            mcp_tools=["set_intensity"],
            inputs={"level": 100},
            depends_on=["select_wash_group"],
            eval_criteria="Intensity channel is at 100% in programmer",
        ),
        SubTask(
            name="store_wash_cue",
            agent_role="CueAgent",
            description=f"Store programmer state into sequence {seq} cue {cue}",
            allowed_risk=RiskTier.DESTRUCTIVE,
            mcp_tools=["store_current_cue", "store_cue_with_timing"],
            inputs={"sequence": seq, "cue": cue, "label": f"{color} wash"},
            depends_on=["apply_wash_color", "set_wash_intensity"],
            eval_criteria="Cue exists in sequence with correct label",
            confirmed=False,  # orchestrator must set True after human approval
        ),
        SubTask(
            name="verify_wash_cue",
            agent_role="ValidationAgent",
            description="Confirm cue is stored and playback-ready",
            allowed_risk=RiskTier.SAFE_READ,
            mcp_tools=["list_sequence_cues", "get_executor_status"],
            inputs={"sequence": seq, "cue": cue},
            depends_on=["store_wash_cue"],
            eval_criteria="Cue appears in sequence list with matching label",
        ),
    ])


def _build_blackout_sequence(goal: str, params: dict) -> TaskPlan:
    seq = params.get("sequence", 1)
    return TaskPlan(goal=goal, steps=[
        SubTask(
            name="read_current_cues",
            agent_role="InspectionAgent",
            description="List existing cues so we don't overwrite",
            allowed_risk=RiskTier.SAFE_READ,
            mcp_tools=["list_sequence_cues", "navigate_console"],
            inputs={"sequence": seq},
            eval_criteria="Cue list returned without error",
        ),
        SubTask(
            name="store_blackout_cue",
            agent_role="CueAgent",
            description="Store a blackout cue at end of sequence",
            allowed_risk=RiskTier.DESTRUCTIVE,
            mcp_tools=["store_current_cue"],
            inputs={"sequence": seq, "label": "BLK"},
            depends_on=["read_current_cues"],
            eval_criteria="Blackout cue appended to sequence",
            confirmed=False,
        ),
    ])


def _build_group_preset_library(goal: str, params: dict) -> TaskPlan:
    """Decompose building a fixture group + preset library."""
    return TaskPlan(goal=goal, steps=[
        SubTask(
            name="discover_fixtures",
            agent_role="InspectionAgent",
            description="List all patched fixtures to understand the rig",
            allowed_risk=RiskTier.SAFE_READ,
            mcp_tools=["list_fixtures", "list_fixture_types", "list_universes"],
            eval_criteria="Fixture list non-empty",
        ),
        SubTask(
            name="create_groups",
            agent_role="GroupAgent",
            description="Create fixture groups from discovered rig layout",
            allowed_risk=RiskTier.DESTRUCTIVE,
            mcp_tools=["create_fixture_group"],
            depends_on=["discover_fixtures"],
            eval_criteria="Groups created for each zone",
            confirmed=False,
        ),
        SubTask(
            name="build_color_presets",
            agent_role="PresetAgent",
            description="Store color presets for common looks",
            allowed_risk=RiskTier.DESTRUCTIVE,
            mcp_tools=["store_new_preset"],
            depends_on=["create_groups"],
            eval_criteria="Preset pool contains target colors",
            confirmed=False,
        ),
        SubTask(
            name="verify_library",
            agent_role="ValidationAgent",
            description="Confirm all groups and presets are accessible",
            allowed_risk=RiskTier.SAFE_READ,
            mcp_tools=["list_preset_pool", "query_object_list"],
            depends_on=["build_color_presets"],
            eval_criteria="Groups and presets queryable from pool",
        ),
    ])


_RULES: list[Rule] = [
    (r"wash|color look|stage wash",            _build_wash_look),
    (r"blackout|blk|fade to black",            _build_blackout_sequence),
    (r"group.*preset|library|rig setup|patch", _build_group_preset_library),
]


# ---------------------------------------------------------------------------
# Decomposer
# ---------------------------------------------------------------------------

class TaskDecomposer:
    """
    Converts a natural-language lighting goal into a TaskPlan.

    Jensen: "You're going to write ideas, architectures, specifications...
    help them define how to evaluate the definition of good versus bad."
    """

    def __init__(self, custom_rules: list[Rule] | None = None) -> None:
        self._rules: list[Rule] = list(_RULES)
        if custom_rules:
            self._rules = custom_rules + self._rules

    def decompose(self, goal: str, params: dict | None = None) -> TaskPlan:
        """
        Match goal against rules and return a TaskPlan.
        Falls back to a safe read-only inspection plan if no rule matches.
        """
        params = params or {}
        lower = goal.lower()

        for pattern, builder in self._rules:
            if re.search(pattern, lower):
                plan = builder(goal, params)
                return plan

        # Fallback: read-only discovery plan
        return TaskPlan(
            goal=goal,
            steps=[
                SubTask(
                    name="inspect_console",
                    agent_role="InspectionAgent",
                    description=f"No template matched '{goal}'. Gather console state to plan next steps.",
                    allowed_risk=RiskTier.SAFE_READ,
                    mcp_tools=[
                        "navigate_console", "list_console_destination",
                        "get_object_info", "query_object_list",
                    ],
                    eval_criteria="Console state returned without error",
                )
            ],
        )

    def register_rule(self, pattern: str, builder: Callable[[str, dict], TaskPlan]) -> None:
        """Add a domain-specific decomposition rule at the front of the chain."""
        self._rules.insert(0, (pattern, builder))
