"""
tests/test_skill_improver.py — Unit tests for src/skill_improver.py

Covers:
  - SkillImprover.identify_failure_patterns
  - SkillImprover.identify_promotion_candidates
  - SkillImprover.quality_score_for_session
"""

import tempfile
import time
from pathlib import Path

import pytest

from src.agent_memory import LongTermMemory, WorkingMemory
from src.skill import SkillRegistry
from src.skill_improver import SkillImprover
from src.telemetry import ToolTelemetry


@pytest.fixture
def improver_tmp():
    """
    SkillImprover with all three collaborators sharing a single temp DB.
    Yields (improver, tel, reg, ltm) for direct fixture manipulation.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    tel = ToolTelemetry(db_path=db_path)
    reg = SkillRegistry(db_path=db_path)
    ltm = LongTermMemory(db_path=db_path)
    imp = SkillImprover(telemetry=tel, registry=reg, ltm=ltm)

    yield imp, tel, reg, ltm

    tel.close()
    reg.close()
    ltm._conn.close()
    db_path.unlink(missing_ok=True)


def _record_error(tel: ToolTelemetry, tool_name: str, error_class: str = "RuntimeError"):
    tel.record_sync(
        tool_name=tool_name,
        inputs_json="{}",
        output_preview="error",
        error_class=error_class,
        latency_ms=10.0,
        risk_tier="SAFE_WRITE",
        operator="test",
        session_id="test-session",
    )


# ── identify_failure_patterns ────────────────────────────────────────────────


class TestIdentifyFailurePatterns:
    def test_empty_when_no_errors(self, improver_tmp):
        imp, tel, reg, ltm = improver_tmp
        result = imp.identify_failure_patterns(min_failures=1)
        assert result == []

    def test_returns_suggestion_for_failing_tool(self, improver_tmp):
        imp, tel, reg, ltm = improver_tmp
        for _ in range(4):
            _record_error(tel, "bad_tool", "ConnectionError")
        suggestions = imp.identify_failure_patterns(min_failures=3)
        assert len(suggestions) == 1
        assert suggestions[0].tool_name == "bad_tool"
        assert suggestions[0].failure_count == 4

    def test_suggestion_has_non_empty_hint(self, improver_tmp):
        imp, tel, reg, ltm = improver_tmp
        for _ in range(3):
            _record_error(tel, "flaky_tool", "RuntimeError")
        suggestions = imp.identify_failure_patterns(min_failures=3)
        assert suggestions[0].hint != ""

    def test_connection_error_hint_mentions_telnet(self, improver_tmp):
        imp, tel, reg, ltm = improver_tmp
        for _ in range(3):
            _record_error(tel, "navigate_console", "ConnectionError")
        suggestions = imp.identify_failure_patterns(min_failures=3)
        assert len(suggestions) == 1
        # The hint should mention Telnet (from _HINT_MAP)
        assert "Telnet" in suggestions[0].hint

    def test_excludes_tool_below_min_failures(self, improver_tmp):
        imp, tel, reg, ltm = improver_tmp
        for _ in range(2):
            _record_error(tel, "rarely_fails", "RuntimeError")
        result = imp.identify_failure_patterns(min_failures=3)
        assert result == []


# ── identify_promotion_candidates ────────────────────────────────────────────


class TestIdentifyPromotionCandidates:
    def test_empty_when_no_sessions(self, improver_tmp):
        imp, tel, reg, ltm = improver_tmp
        assert imp.identify_promotion_candidates() == []

    def test_returns_high_quality_session(self, improver_tmp):
        imp, tel, reg, ltm = improver_tmp
        wm = WorkingMemory(task_description="wash look blue")
        wm.charge_tokens(50)
        for i in range(9):
            wm.mark_done(f"step_{i}")
        wm.mark_failed("step_fail", "timeout")
        ltm.save_session(wm, outcome="success")

        candidates = imp.identify_promotion_candidates(min_quality=0.8)
        assert len(candidates) == 1
        assert candidates[0].task == "wash look blue"
        assert candidates[0].quality_score >= 0.8

    def test_excludes_already_promoted_session(self, improver_tmp):
        imp, tel, reg, ltm = improver_tmp
        wm = WorkingMemory(task_description="already promoted task")
        for i in range(9):
            wm.mark_done(f"s{i}")
        wm.mark_failed("f1", "err")
        ltm.save_session(wm, outcome="success")

        # Promote the session to a Skill
        reg.promote_from_session(
            session_id=wm.session_id,
            name="already_promoted",
            description="was promoted",
            body="body",
            safety_scope="SAFE_WRITE",
            applicable_context="test",
            quality_score=0.9,
        )

        candidates = imp.identify_promotion_candidates(min_quality=0.8)
        assert candidates == []

    def test_excludes_low_quality_session(self, improver_tmp):
        imp, tel, reg, ltm = improver_tmp
        wm = WorkingMemory(task_description="low quality task")
        wm.mark_done("s1")
        wm.mark_done("s2")
        for i in range(5):
            wm.mark_failed(f"f{i}", "err")
        ltm.save_session(wm, outcome="success")

        candidates = imp.identify_promotion_candidates(min_quality=0.8)
        assert candidates == []


# ── quality_score_for_session ─────────────────────────────────────────────────


class TestQualityScoreForSession:
    def test_unknown_session_returns_zero(self, improver_tmp):
        imp, tel, reg, ltm = improver_tmp
        assert imp.quality_score_for_session("phantom-id") == 0.0

    def test_correct_score_eight_done_two_failed(self, improver_tmp):
        imp, tel, reg, ltm = improver_tmp
        wm = WorkingMemory(task_description="scored task")
        for i in range(8):
            wm.mark_done(f"s{i}")
        wm.mark_failed("f1", "err")
        wm.mark_failed("f2", "err")
        ltm.save_session(wm, outcome="success")

        score = imp.quality_score_for_session(wm.session_id)
        assert abs(score - 0.8) < 0.01

    def test_all_steps_done_returns_one(self, improver_tmp):
        imp, tel, reg, ltm = improver_tmp
        wm = WorkingMemory(task_description="perfect task")
        for i in range(5):
            wm.mark_done(f"s{i}")
        ltm.save_session(wm, outcome="success")

        score = imp.quality_score_for_session(wm.session_id)
        assert score == 1.0
