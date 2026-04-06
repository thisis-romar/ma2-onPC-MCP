# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for src/agent/policy.py — plan-level governance rules."""

from src.agent.policy import PolicyEngine, PolicyStrictness, StepDecision
from src.agent.state import PlanStep, RunContext, StepStatus
from src.vocab import RiskTier


def _step(tool_name="test", risk=RiskTier.SAFE_READ, description="test"):
    return PlanStep(
        tool_name=tool_name,
        tool_args={},
        description=description,
        risk_tier=risk,
    )


class TestPolicyEngine:
    def test_approve_safe_plan(self):
        engine = PolicyEngine()
        plan = [_step(risk=RiskTier.SAFE_READ, description="list groups")]
        result = engine.validate_plan(plan)
        assert result.approved is True
        assert len(result.violations) == 0

    def test_staging_warning_read_after_destructive(self):
        engine = PolicyEngine()
        plan = [
            _step(risk=RiskTier.DESTRUCTIVE, description="store cue"),
            _step(risk=RiskTier.SAFE_READ, description="list fixtures"),
        ]
        result = engine.validate_plan(plan)
        assert result.approved is True  # warning, not error
        assert any("Staging" in w for w in result.warnings)

    def test_staging_no_warning_for_verify_after_destructive(self):
        engine = PolicyEngine()
        plan = [
            _step(risk=RiskTier.DESTRUCTIVE, description="store cue"),
            _step(risk=RiskTier.SAFE_READ, description="Verify: cue stored"),
        ]
        result = engine.validate_plan(plan)
        staging_warnings = [w for w in result.warnings if "Staging" in w]
        assert len(staging_warnings) == 0

    def test_verification_warning_no_verify_after_destructive(self):
        engine = PolicyEngine()
        plan = [
            _step(risk=RiskTier.DESTRUCTIVE, description="store preset"),
            _step(risk=RiskTier.DESTRUCTIVE, description="assign executor"),
        ]
        result = engine.validate_plan(plan)
        assert any("verification" in w.lower() for w in result.warnings)

    def test_discovery_first_warning(self):
        engine = PolicyEngine()
        plan = [
            _step(risk=RiskTier.SAFE_WRITE, description="set intensity"),
        ]
        result = engine.validate_plan(plan)
        assert any("mutation" in w.lower() for w in result.warnings)

    def test_confidence_gate_blocks_low_confidence(self):
        engine = PolicyEngine()
        plan = [_step()]
        result = engine.validate_plan(plan, confidence=0.3)
        assert result.approved is False
        assert any(v.rule == "confidence_gate" for v in result.violations)

    def test_confidence_gate_passes_high_confidence(self):
        engine = PolicyEngine()
        plan = [_step()]
        result = engine.validate_plan(plan, confidence=0.9)
        assert result.approved is True

    def test_connection_safety_blocks_unsafe_new_show(self):
        engine = PolicyEngine()
        plan = [
            PlanStep(
                tool_name="create_new_show",
                tool_args={"preserve_connectivity": False},
                description="New show (unsafe)",
                risk_tier=RiskTier.DESTRUCTIVE,
            )
        ]
        result = engine.validate_plan(plan)
        assert result.approved is False
        assert any(v.rule == "connection_safety" for v in result.violations)

    def test_connection_safety_allows_safe_new_show(self):
        engine = PolicyEngine()
        plan = [
            PlanStep(
                tool_name="create_new_show",
                tool_args={"preserve_connectivity": True},
                description="New show (safe)",
                risk_tier=RiskTier.DESTRUCTIVE,
            )
        ]
        result = engine.validate_plan(plan)
        # No connection_safety violation
        assert not any(v.rule == "connection_safety" for v in result.violations)

    def test_batch_limit_warning(self):
        engine = PolicyEngine(batch_limit=3)
        plan = [
            _step(risk=RiskTier.DESTRUCTIVE, description=f"store {i}")
            for i in range(5)
        ]
        result = engine.validate_plan(plan)
        assert any("batch" in w.lower() or "limit" in w.lower() for w in result.warnings)

    def test_batch_limit_no_warning_under_limit(self):
        engine = PolicyEngine(batch_limit=10)
        plan = [
            _step(risk=RiskTier.DESTRUCTIVE, description=f"store {i}")
            for i in range(3)
        ]
        result = engine.validate_plan(plan)
        batch_warnings = [w for w in result.warnings if "batch" in w.lower() or "limit" in w.lower()]
        assert len(batch_warnings) == 0


class TestGateStep:
    def test_execute_safe_step(self):
        engine = PolicyEngine()
        step = _step(risk=RiskTier.SAFE_READ)
        ctx = RunContext(goal="test", plan=[step])
        decision = engine.gate_step(step, ctx)
        assert decision.action == StepDecision.EXECUTE

    def test_confirm_destructive_step(self):
        engine = PolicyEngine()
        step = _step(risk=RiskTier.DESTRUCTIVE)
        ctx = RunContext(goal="test", plan=[step])
        decision = engine.gate_step(step, ctx)
        assert decision.action == StepDecision.CONFIRM

    def test_block_unmet_dependency(self):
        engine = PolicyEngine()
        s1 = _step(description="step 1")
        s2 = PlanStep(
            tool_name="test",
            tool_args={},
            description="step 2",
            risk_tier=RiskTier.SAFE_READ,
            depends_on=[s1.id],
        )
        ctx = RunContext(goal="test", plan=[s1, s2])
        decision = engine.gate_step(s2, ctx)
        assert decision.action == StepDecision.BLOCK

    def test_allow_met_dependency(self):
        engine = PolicyEngine()
        s1 = _step(description="step 1")
        s1.status = StepStatus.COMPLETED
        s2 = PlanStep(
            tool_name="test",
            tool_args={},
            description="step 2",
            risk_tier=RiskTier.SAFE_READ,
            depends_on=[s1.id],
        )
        ctx = RunContext(goal="test", plan=[s1, s2])
        decision = engine.gate_step(s2, ctx)
        assert decision.action == StepDecision.EXECUTE


class TestPolicyStrictness:
    """Tests for BLOCK mode — rules 1-3 become blocking errors."""

    def test_strictness_enum_values(self):
        assert PolicyStrictness.WARN == "warn"
        assert PolicyStrictness.BLOCK == "block"

    def test_default_strictness_is_warn(self):
        engine = PolicyEngine()
        assert engine.strictness == PolicyStrictness.WARN

    def test_explicit_block_strictness(self):
        engine = PolicyEngine(strictness=PolicyStrictness.BLOCK)
        assert engine.strictness == PolicyStrictness.BLOCK

    def test_env_var_sets_block(self, monkeypatch):
        monkeypatch.setenv("GMA_POLICY_STRICTNESS", "block")
        engine = PolicyEngine()
        assert engine.strictness == PolicyStrictness.BLOCK

    def test_env_var_case_insensitive(self, monkeypatch):
        monkeypatch.setenv("GMA_POLICY_STRICTNESS", "BLOCK")
        engine = PolicyEngine()
        assert engine.strictness == PolicyStrictness.BLOCK

    def test_block_staging_rejects_read_after_destructive(self):
        engine = PolicyEngine(strictness=PolicyStrictness.BLOCK)
        plan = [
            _step(risk=RiskTier.DESTRUCTIVE, description="store cue"),
            _step(risk=RiskTier.SAFE_READ, description="list fixtures"),
        ]
        result = engine.validate_plan(plan)
        assert result.approved is False
        assert any(v.rule == "staging" and v.severity == "error" for v in result.violations)

    def test_warn_staging_approves_read_after_destructive(self):
        engine = PolicyEngine(strictness=PolicyStrictness.WARN)
        plan = [
            _step(risk=RiskTier.DESTRUCTIVE, description="store cue"),
            _step(risk=RiskTier.SAFE_READ, description="list fixtures"),
        ]
        result = engine.validate_plan(plan)
        assert result.approved is True  # warning only

    def test_block_verification_rejects_unverified_destructive(self):
        engine = PolicyEngine(strictness=PolicyStrictness.BLOCK)
        plan = [
            _step(risk=RiskTier.DESTRUCTIVE, description="store preset"),
            _step(risk=RiskTier.DESTRUCTIVE, description="assign executor"),
        ]
        result = engine.validate_plan(plan)
        assert result.approved is False
        assert any(v.rule == "verification" and v.severity == "error" for v in result.violations)

    def test_block_discovery_first_rejects_mutation_start(self):
        engine = PolicyEngine(strictness=PolicyStrictness.BLOCK)
        plan = [
            _step(risk=RiskTier.SAFE_WRITE, description="set intensity"),
        ]
        result = engine.validate_plan(plan)
        assert result.approved is False
        assert any(v.rule == "discovery_first" and v.severity == "error" for v in result.violations)

    def test_block_still_allows_clean_plan(self):
        engine = PolicyEngine(strictness=PolicyStrictness.BLOCK)
        plan = [
            _step(risk=RiskTier.SAFE_READ, description="list groups"),
            _step(risk=RiskTier.DESTRUCTIVE, description="store cue"),
            _step(risk=RiskTier.SAFE_READ, description="Verify: cue stored"),
        ]
        result = engine.validate_plan(plan)
        assert result.approved is True
