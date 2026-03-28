"""
tests/test_task_decomposer.py — Unit tests for src/task_decomposer.py

Covers:
  - SubTask dataclass
  - TaskPlan ordering (topological sort)
  - TaskDecomposer built-in rules (wash, blackout, library)
  - TaskDecomposer fallback plan
  - register_rule() custom rules
"""

import pytest
from src.task_decomposer import SubTask, TaskPlan, TaskDecomposer
from src.vocab import RiskTier


# ── SubTask ──────────────────────────────────────────────────────────────────

class TestSubTask:
    def test_defaults(self):
        st = SubTask(
            name="test",
            agent_role="TestAgent",
            description="desc",
            allowed_risk=RiskTier.SAFE_READ,
            mcp_tools=["navigate_console"],
        )
        assert st.retryable is True
        assert st.confirmed is False
        assert st.depends_on == []
        assert st.inputs == {}
        assert st.outputs == {}

    def test_destructive_default_unconfirmed(self):
        st = SubTask(
            name="risky",
            agent_role="Agent",
            description="",
            allowed_risk=RiskTier.DESTRUCTIVE,
            mcp_tools=["store_current_cue"],
        )
        assert st.confirmed is False


# ── TaskPlan.ordered_steps() ─────────────────────────────────────────────────

class TestTaskPlanOrdering:
    def _make_step(self, name, depends_on=None):
        return SubTask(
            name=name,
            agent_role="A",
            description="",
            allowed_risk=RiskTier.SAFE_READ,
            mcp_tools=[],
            depends_on=depends_on or [],
        )

    def test_no_deps_returns_all(self):
        plan = TaskPlan(goal="g", steps=[
            self._make_step("a"),
            self._make_step("b"),
        ])
        names = [s.name for s in plan.ordered_steps()]
        assert set(names) == {"a", "b"}

    def test_deps_respected(self):
        plan = TaskPlan(goal="g", steps=[
            self._make_step("b", depends_on=["a"]),
            self._make_step("a"),
        ])
        ordered = [s.name for s in plan.ordered_steps()]
        assert ordered.index("a") < ordered.index("b")

    def test_chain_deps(self):
        plan = TaskPlan(goal="g", steps=[
            self._make_step("c", depends_on=["b"]),
            self._make_step("b", depends_on=["a"]),
            self._make_step("a"),
        ])
        ordered = [s.name for s in plan.ordered_steps()]
        assert ordered == ["a", "b", "c"]

    def test_summary_contains_goal(self):
        plan = TaskPlan(goal="blue wash test", steps=[self._make_step("s1")])
        assert "blue wash test" in plan.summary()


# ── TaskDecomposer — built-in rules ──────────────────────────────────────────

class TestDecomposeWashRule:
    def setup_method(self):
        self.d = TaskDecomposer()

    def test_wash_matches(self):
        plan = self.d.decompose("blue wash on movers")
        assert plan.goal == "blue wash on movers"
        assert len(plan.steps) >= 3

    def test_color_look_matches(self):
        plan = self.d.decompose("color look for stage")
        assert len(plan.steps) >= 3

    def test_wash_has_selection_step(self):
        plan = self.d.decompose("wash on wash fixtures")
        names = [s.name for s in plan.steps]
        assert any("select" in n for n in names)

    def test_wash_has_destructive_store_step(self):
        plan = self.d.decompose("blue wash")
        tiers = [s.allowed_risk for s in plan.steps]
        assert RiskTier.DESTRUCTIVE in tiers

    def test_wash_params_passed(self):
        plan = self.d.decompose("wash", params={"color": "red", "group": "spots"})
        desc_text = " ".join(s.description for s in plan.steps)
        assert "spots" in desc_text or "red" in desc_text

    def test_ordered_steps_dependencies(self):
        plan = self.d.decompose("blue wash")
        ordered = plan.ordered_steps()
        # store step should come after color step
        names = [s.name for s in ordered]
        if "apply_wash_color" in names and "store_wash_cue" in names:
            assert names.index("apply_wash_color") < names.index("store_wash_cue")


class TestDecomposeBlackoutRule:
    def setup_method(self):
        self.d = TaskDecomposer()

    def test_blackout_matches(self):
        plan = self.d.decompose("add a blackout at end of sequence 1")
        assert len(plan.steps) >= 2

    def test_blk_matches(self):
        plan = self.d.decompose("store BLK cue")
        assert len(plan.steps) >= 1

    def test_fade_to_black_matches(self):
        plan = self.d.decompose("fade to black")
        assert len(plan.steps) >= 1

    def test_blackout_has_read_first(self):
        plan = self.d.decompose("blackout")
        first = plan.ordered_steps()[0]
        assert first.allowed_risk in (RiskTier.SAFE_READ, RiskTier.SAFE_WRITE)


class TestDecomposeLibraryRule:
    def setup_method(self):
        self.d = TaskDecomposer()

    def test_library_matches(self):
        plan = self.d.decompose("build group and preset library")
        assert len(plan.steps) >= 3

    def test_rig_setup_matches(self):
        plan = self.d.decompose("rig setup from scratch")
        assert len(plan.steps) >= 3

    def test_patch_matches(self):
        plan = self.d.decompose("patch new fixtures and build groups")
        assert len(plan.steps) >= 3

    def test_library_has_discover_first(self):
        plan = self.d.decompose("library")
        first = plan.ordered_steps()[0]
        assert first.allowed_risk == RiskTier.SAFE_READ


# ── TaskDecomposer — fallback ────────────────────────────────────────────────

class TestDecomposeFallback:
    def test_unmatched_goal_returns_inspection_plan(self):
        d = TaskDecomposer()
        plan = d.decompose("do something completely unknown xyz")
        assert len(plan.steps) == 1
        assert plan.steps[0].name == "inspect_console"
        assert plan.steps[0].allowed_risk == RiskTier.SAFE_READ

    def test_fallback_uses_read_only_tools(self):
        d = TaskDecomposer()
        plan = d.decompose("xyz123")
        for tool in plan.steps[0].mcp_tools:
            assert tool in (
                "navigate_console", "list_console_destination",
                "get_object_info", "query_object_list",
            )


# ── TaskDecomposer — register_rule() ────────────────────────────────────────

class TestCustomRule:
    def test_custom_rule_takes_priority(self):
        from src.task_decomposer import TaskPlan, SubTask, RiskTier as RT
        d = TaskDecomposer()

        def custom_builder(goal, params):
            return TaskPlan(goal=goal, steps=[
                SubTask(
                    name="custom_step",
                    agent_role="CustomAgent",
                    description="custom",
                    allowed_risk=RT.SAFE_READ,
                    mcp_tools=["navigate_console"],
                )
            ])

        d.register_rule(r"custom_keyword", custom_builder)
        plan = d.decompose("trigger custom_keyword here")
        assert plan.steps[0].name == "custom_step"

    def test_custom_rule_does_not_affect_other_patterns(self):
        d = TaskDecomposer()
        d.register_rule(r"only_this", lambda g, p: TaskPlan(goal=g, steps=[]))
        plan = d.decompose("blue wash")
        assert len(plan.steps) > 0  # wash rule still fires
