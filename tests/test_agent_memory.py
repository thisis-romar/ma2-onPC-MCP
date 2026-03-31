"""
tests/test_agent_memory.py — Unit tests for src/agent_memory.py

Covers:
  - FixtureSnapshot
  - WorkingMemory: fixture tracking, park ledger, mode overrides, step tracking
  - WorkingMemory: DecisionCheckpoint add/lookup/freshness
  - LongTermMemory: save/load, recent_sessions, recall
"""

import os
import time
import pytest
import tempfile
from pathlib import Path
from src.agent_memory import DecisionCheckpoint, FixtureSnapshot, WorkingMemory, LongTermMemory
from src.rights import RightsContext
from src.commands.constants import MA2Right


# ── FixtureSnapshot ──────────────────────────────────────────────────────────

class TestFixtureSnapshot:
    def test_basic_fields(self):
        fs = FixtureSnapshot(fixture_id=1, group="wash", intensity=75.0)
        assert fs.fixture_id == 1
        assert fs.group == "wash"
        assert fs.intensity == 75.0
        assert fs.preset_applied is None
        assert fs.attribute == {}


# ── WorkingMemory ────────────────────────────────────────────────────────────

class TestWorkingMemory:
    def test_session_id_auto_generated(self):
        wm = WorkingMemory()
        assert len(wm.session_id) == 8

    def test_session_id_unique(self):
        wm1, wm2 = WorkingMemory(), WorkingMemory()
        assert wm1.session_id != wm2.session_id

    def test_record_fixture_creates_entry(self):
        wm = WorkingMemory()
        wm.record_fixture(1, group="wash", intensity=100.0)
        assert "1" in wm.fixtures
        assert wm.fixtures["1"].intensity == 100.0

    def test_record_fixture_updates_existing(self):
        wm = WorkingMemory()
        wm.record_fixture(1, intensity=50.0)
        wm.record_fixture(1, intensity=100.0)
        assert wm.fixtures["1"].intensity == 100.0

    def test_record_fixture_attributes(self):
        wm = WorkingMemory()
        wm.record_fixture(1, attributes={"color": "blue"})
        assert wm.fixtures["1"].attribute["color"] == "blue"

    def test_fixtures_in_group(self):
        wm = WorkingMemory()
        wm.record_fixture(1, group="wash")
        wm.record_fixture(2, group="wash")
        wm.record_fixture(3, group="spots")
        result = wm.fixtures_in_group("wash")
        assert len(result) == 2

    # Park ledger

    def test_park_adds_to_ledger(self):
        wm = WorkingMemory()
        wm.park(5)
        assert wm.is_parked(5) is True

    def test_unpark_removes_from_ledger(self):
        wm = WorkingMemory()
        wm.park(5)
        wm.unpark(5)
        assert wm.is_parked(5) is False

    def test_park_uses_string_key(self):
        wm = WorkingMemory()
        wm.park("7")
        assert wm.is_parked(7) is True  # int lookup works

    # Mode overrides

    def test_is_blind_default_false(self):
        wm = WorkingMemory()
        assert wm.is_blind() is False

    def test_set_blind_mode(self):
        wm = WorkingMemory()
        wm.set_mode("blind", True)
        assert wm.is_blind() is True

    def test_set_mode_no_console_state(self):
        wm = WorkingMemory()
        wm.set_mode("freeze", True)
        assert wm.mode_overrides["freeze"] is True

    # Step tracking

    def test_mark_done(self):
        wm = WorkingMemory()
        wm.mark_done("step_a")
        assert "step_a" in wm.completed_steps

    def test_mark_failed(self):
        wm = WorkingMemory()
        wm.mark_failed("step_b", "timeout")
        assert any("step_b" in s for s in wm.failed_steps)

    # Rights context

    def test_can_execute_with_admin_rights(self):
        wm = WorkingMemory()
        wm.rights_context = RightsContext(user_right=MA2Right.ADMIN)
        assert wm.can_execute("load_show") is True

    def test_can_execute_denied_at_low_right(self):
        wm = WorkingMemory()
        wm.rights_context = RightsContext(user_right=MA2Right.PLAYBACK)
        assert wm.can_execute("store_current_cue") is False

    def test_upr_flag(self):
        wm = WorkingMemory()
        wm.rights_context = RightsContext(user_right=MA2Right.PROGRAM)
        assert wm.upr_flag() == "/UPR=3"

    # Staleness with no snapshot

    def test_staleness_warning_no_snapshot(self):
        wm = WorkingMemory()
        warn = wm.staleness_warning()
        assert warn is not None
        assert "hydrate" in warn.lower() or "snapshot" in warn.lower()

    # Console summary with no snapshot

    def test_console_summary_no_snapshot(self):
        wm = WorkingMemory()
        summary = wm.console_summary()
        assert "not hydrated" in summary.lower()


# ── LongTermMemory ───────────────────────────────────────────────────────────

@pytest.fixture
def ltm_tmp():
    """LTM instance backed by a temp file, cleaned up after test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    ltm = LongTermMemory(db_path=db_path)
    yield ltm
    ltm._conn.close()
    db_path.unlink(missing_ok=True)


class TestLongTermMemory:
    def test_save_and_recent_sessions(self, ltm_tmp):
        wm = WorkingMemory(task_description="test wash look")
        wm.charge_tokens(120)
        ltm_tmp.save_session(wm, outcome="success")
        sessions = ltm_tmp.recent_sessions(5)
        assert len(sessions) == 1
        assert sessions[0]["task"] == "test wash look"
        assert sessions[0]["outcome"] == "success"
        assert sessions[0]["tokens"] == 120

    def test_recent_sessions_limit(self, ltm_tmp):
        for i in range(5):
            wm = WorkingMemory(task_description=f"task {i}")
            ltm_tmp.save_session(wm, outcome="success")
        assert len(ltm_tmp.recent_sessions(3)) == 3

    def test_recall_existing_session(self, ltm_tmp):
        wm = WorkingMemory(task_description="recall test")
        ltm_tmp.save_session(wm, outcome="success")
        snap = ltm_tmp.recall_session(wm.session_id)
        assert snap is not None
        assert snap.get("task_description") == "recall test"

    def test_recall_nonexistent_returns_none(self, ltm_tmp):
        result = ltm_tmp.recall_session("deadbeef")
        assert result is None

    def test_recent_sessions_empty(self, ltm_tmp):
        assert ltm_tmp.recent_sessions(10) == []

    def test_session_id_stored(self, ltm_tmp):
        wm = WorkingMemory(task_description="id check")
        ltm_tmp.save_session(wm, outcome="success")
        sessions = ltm_tmp.recent_sessions(1)
        assert sessions[0]["id"] == wm.session_id

    def test_fixture_history(self, ltm_tmp):
        wm = WorkingMemory(task_description="fx history test")
        wm.record_fixture(3, group="wash", intensity=80.0, preset="blue")
        ltm_tmp.save_session(wm, outcome="success")
        hist = ltm_tmp.fixture_history("3", limit=5)
        assert len(hist) == 1
        assert hist[0]["group_name"] == "wash"

    def test_park_history(self, ltm_tmp):
        wm = WorkingMemory(task_description="park test")
        wm.park(7)
        ltm_tmp.save_session(wm, outcome="success")
        hist = ltm_tmp.park_history("7")
        assert len(hist) == 1
        assert hist[0]["action"] == "parked"


# ── DecisionCheckpoint ────────────────────────────────────────────────────────


class TestDecisionCheckpoint:
    def _make(self, fault="test_fault", fresh_for=60.0, age=0.0) -> DecisionCheckpoint:
        return DecisionCheckpoint(
            fault=fault,
            query="Was position preset applied?",
            observed_at=time.time() - age,
            fresh_for_seconds=fresh_for,
            replay="browse_preset_type(2, depth=1)",
            confidence=0.9,
        )

    def test_is_fresh_within_window(self):
        cp = self._make(fresh_for=60.0, age=5.0)
        assert cp.is_fresh() is True

    def test_is_stale_past_window(self):
        cp = self._make(fresh_for=10.0, age=30.0)
        assert cp.is_fresh() is False

    def test_is_fresh_exactly_at_boundary(self):
        # age == fresh_for → stale (strict less-than)
        cp = self._make(fresh_for=10.0, age=10.0)
        assert cp.is_fresh() is False

    def test_default_confidence(self):
        cp = self._make()
        assert cp.confidence == 0.9


class TestWorkingMemoryCheckpoints:
    def test_add_checkpoint(self):
        wm = WorkingMemory()
        cp = DecisionCheckpoint(
            fault="no_position_preset",
            query="check position presets",
            observed_at=time.time(),
            fresh_for_seconds=60.0,
            replay="browse_preset_type(2)",
        )
        wm.add_checkpoint(cp)
        assert len(wm.checkpoints) == 1

    def test_add_checkpoint_replaces_same_fault(self):
        wm = WorkingMemory()
        cp1 = DecisionCheckpoint(
            fault="no_position_preset", query="v1",
            observed_at=time.time(), fresh_for_seconds=60.0, replay="v1",
        )
        cp2 = DecisionCheckpoint(
            fault="no_position_preset", query="v2",
            observed_at=time.time(), fresh_for_seconds=60.0, replay="v2",
        )
        wm.add_checkpoint(cp1)
        wm.add_checkpoint(cp2)
        assert len(wm.checkpoints) == 1
        assert wm.checkpoints[0].query == "v2"

    def test_add_different_faults_accumulate(self):
        wm = WorkingMemory()
        for fault in ("fault_a", "fault_b", "fault_c"):
            wm.add_checkpoint(DecisionCheckpoint(
                fault=fault, query="q",
                observed_at=time.time(), fresh_for_seconds=60.0, replay="r",
            ))
        assert len(wm.checkpoints) == 3

    def test_fresh_checkpoint_returns_fresh(self):
        wm = WorkingMemory()
        cp = DecisionCheckpoint(
            fault="my_fault", query="q",
            observed_at=time.time(), fresh_for_seconds=60.0, replay="r",
        )
        wm.add_checkpoint(cp)
        result = wm.fresh_checkpoint("my_fault")
        assert result is not None
        assert result.fault == "my_fault"

    def test_fresh_checkpoint_returns_none_when_stale(self):
        wm = WorkingMemory()
        cp = DecisionCheckpoint(
            fault="stale_fault", query="q",
            observed_at=time.time() - 120,   # 120s ago
            fresh_for_seconds=60.0,
            replay="r",
        )
        wm.add_checkpoint(cp)
        assert wm.fresh_checkpoint("stale_fault") is None

    def test_fresh_checkpoint_returns_none_when_absent(self):
        wm = WorkingMemory()
        assert wm.fresh_checkpoint("nonexistent") is None

    def test_to_dict_includes_checkpoints(self):
        wm = WorkingMemory()
        wm.add_checkpoint(DecisionCheckpoint(
            fault="dict_test", query="q",
            observed_at=time.time(), fresh_for_seconds=60.0, replay="r",
        ))
        d = wm.to_dict()
        assert "checkpoints" in d
        assert len(d["checkpoints"]) == 1
        assert d["checkpoints"][0]["fault"] == "dict_test"
