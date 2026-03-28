"""
tests/test_server_orchestration_tools.py — Unit tests for src/server_orchestration_tools.py

Strategy: register_orchestration_tools() is called with a CaptureMcp shim that
intercepts @mcp.tool() registrations without scope-checking or error-handling,
giving direct access to the raw async tool functions. This avoids needing a live
FastMCP instance or the OAuth layer.

Tools covered:
  119 — get_console_state
  120 — get_park_ledger
  121 — get_filter_state
  122 — get_world_state
  123 — get_matricks_state
  124 — get_programmer_selection
  125 — hydrate_sequences
  126 — get_sequence_memory
  127 — assert_selection_count
  128 — assert_preset_exists
  129 — get_executor_detail
  (110-118 smoke tests via no-snapshot guard)
"""

import json
import dataclasses
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.server_orchestration_tools import register_orchestration_tools
from src.commands.constants import OAuthScope
from src.console_state import (
    ConsoleStateSnapshot,
    ExecutorState,
    SequenceEntry,
    CueRecord,
    MAtricksTracker,
)


# ── Test helpers ──────────────────────────────────────────────────────────────

def _make_snap(**kwargs) -> ConsoleStateSnapshot:
    return ConsoleStateSnapshot(**kwargs)


def _capture_tools(mock_orch) -> dict:
    """Register all orchestration tools with a capturing shim; return by name."""
    tools: dict = {}

    class CaptureMcp:
        def tool(self_inner):
            def decorator(fn):
                tools[fn.__name__] = fn
                return fn
            return decorator

    def noop_scope(scope):
        def dec(fn):
            return fn
        return dec

    def noop_errors(fn):
        return fn

    register_orchestration_tools(
        CaptureMcp(), mock_orch, noop_scope, noop_errors, OAuthScope
    )
    return tools


# ── No-snapshot guard (all Tools 119-129) ────────────────────────────────────

class TestNoSnapshotGuard:
    """Every snapshot-read tool returns an error dict when last_snapshot is None."""

    @pytest.mark.asyncio
    async def test_get_console_state_no_snapshot(self):
        mock_orch = MagicMock()
        mock_orch.last_snapshot = None
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_console_state"]())
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_park_ledger_no_snapshot(self):
        mock_orch = MagicMock()
        mock_orch.last_snapshot = None
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_park_ledger"]())
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_filter_state_no_snapshot(self):
        mock_orch = MagicMock()
        mock_orch.last_snapshot = None
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_filter_state"]())
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_world_state_no_snapshot(self):
        mock_orch = MagicMock()
        mock_orch.last_snapshot = None
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_world_state"]())
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_matricks_state_no_snapshot(self):
        mock_orch = MagicMock()
        mock_orch.last_snapshot = None
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_matricks_state"]())
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_programmer_selection_no_snapshot(self):
        mock_orch = MagicMock()
        mock_orch.last_snapshot = None
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_programmer_selection"]())
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_sequence_memory_no_snapshot(self):
        mock_orch = MagicMock()
        mock_orch.last_snapshot = None
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_sequence_memory"](sequence_id=1))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_assert_selection_count_no_snapshot(self):
        mock_orch = MagicMock()
        mock_orch.last_snapshot = None
        t = _capture_tools(mock_orch)
        result = json.loads(await t["assert_selection_count"](expected=5))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_assert_preset_exists_no_snapshot(self):
        mock_orch = MagicMock()
        mock_orch.last_snapshot = None
        t = _capture_tools(mock_orch)
        result = json.loads(await t["assert_preset_exists"](preset_type=2, preset_id=1))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_executor_detail_no_snapshot(self):
        mock_orch = MagicMock()
        mock_orch.last_snapshot = None
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_executor_detail"](executor_id=201))
        assert "error" in result


# ── Tool 119: get_console_state ───────────────────────────────────────────────

class TestGetConsoleState:

    @pytest.mark.asyncio
    async def test_returns_expected_keys(self):
        mock_orch = MagicMock()
        mock_orch.last_snapshot = _make_snap()
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_console_state"]())
        assert "hydrated" in result
        assert "staleness_warning" in result
        assert "age_seconds" in result
        assert "partial" in result
        assert "summary" in result

    @pytest.mark.asyncio
    async def test_age_seconds_is_numeric(self):
        mock_orch = MagicMock()
        mock_orch.last_snapshot = _make_snap()
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_console_state"]())
        assert isinstance(result["age_seconds"], float)

    @pytest.mark.asyncio
    async def test_partial_false_by_default(self):
        mock_orch = MagicMock()
        mock_orch.last_snapshot = _make_snap()
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_console_state"]())
        assert result["partial"] is False


# ── Tool 120: get_park_ledger ─────────────────────────────────────────────────

class TestGetParkLedger:

    @pytest.mark.asyncio
    async def test_empty_park_set(self):
        mock_orch = MagicMock()
        mock_orch.last_snapshot = _make_snap()
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_park_ledger"]())
        assert result["parked_fixtures"] == []
        assert result["count"] == 0
        assert result["warning"] is None

    @pytest.mark.asyncio
    async def test_with_parked_fixtures(self):
        snap = _make_snap()
        snap.parked_fixtures.add("fixture 20")
        snap.parked_fixtures.add("fixture 21")
        mock_orch = MagicMock()
        mock_orch.last_snapshot = snap
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_park_ledger"]())
        assert result["count"] == 2
        assert "fixture 20" in result["parked_fixtures"]
        assert result["warning"] is not None
        assert "2" in result["warning"]


# ── Tool 121: get_filter_state ────────────────────────────────────────────────

class TestGetFilterState:

    @pytest.mark.asyncio
    async def test_no_active_filter(self):
        snap = _make_snap()
        mock_orch = MagicMock()
        mock_orch.last_snapshot = snap
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_filter_state"]())
        assert result["active_filter"] is None
        assert result["warning"] is None

    @pytest.mark.asyncio
    async def test_with_active_filter(self):
        snap = _make_snap()
        snap.active_filter = 3
        mock_orch = MagicMock()
        mock_orch.last_snapshot = snap
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_filter_state"]())
        assert result["active_filter"] == 3
        assert result["warning"] is not None
        assert "3" in result["warning"]

    @pytest.mark.asyncio
    async def test_filter_vte_default(self):
        mock_orch = MagicMock()
        mock_orch.last_snapshot = _make_snap()
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_filter_state"]())
        assert result["filter_vte"] == {"value": True, "value_timing": True, "effect": True}


# ── Tool 122: get_world_state ─────────────────────────────────────────────────

class TestGetWorldState:

    @pytest.mark.asyncio
    async def test_no_active_world(self):
        mock_orch = MagicMock()
        mock_orch.last_snapshot = _make_snap()
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_world_state"]())
        assert result["active_world"] is None
        assert result["warning"] is None

    @pytest.mark.asyncio
    async def test_with_active_world(self):
        snap = _make_snap()
        snap.active_world = 2
        snap.world_labels = {2: "Stage Left"}
        mock_orch = MagicMock()
        mock_orch.last_snapshot = snap
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_world_state"]())
        assert result["active_world"] == 2
        assert result["warning"] is not None
        assert result["world_labels"]["2"] == "Stage Left"


# ── Tool 123: get_matricks_state ──────────────────────────────────────────────

class TestGetMatricksState:

    @pytest.mark.asyncio
    async def test_default_state(self):
        mock_orch = MagicMock()
        mock_orch.last_snapshot = _make_snap()
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_matricks_state"]())
        assert result["interleave"] is None
        assert result["wings"] is None
        assert result["active"] is False
        assert result["summary"] == "off"
        assert "note" in result

    @pytest.mark.asyncio
    async def test_with_active_matricks(self):
        snap = _make_snap()
        snap.matricks.interleave = 4
        snap.matricks.wings = 2
        mock_orch = MagicMock()
        mock_orch.last_snapshot = snap
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_matricks_state"]())
        assert result["interleave"] == 4
        assert result["wings"] == 2
        assert "interleave=4" in result["summary"]


# ── Tool 124: get_programmer_selection ───────────────────────────────────────

class TestGetProgrammerSelection:

    @pytest.mark.asyncio
    async def test_zero_selection(self):
        mock_orch = MagicMock()
        mock_orch.last_snapshot = _make_snap()
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_programmer_selection"]())
        assert result["selected_fixture_count"] == 0
        assert result["warning"] is not None

    @pytest.mark.asyncio
    async def test_with_selection(self):
        snap = _make_snap()
        snap.selected_fixture_count = 12
        snap.selected_exec = "1.1.201"
        snap.selected_exec_cue = "3"
        mock_orch = MagicMock()
        mock_orch.last_snapshot = snap
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_programmer_selection"]())
        assert result["selected_fixture_count"] == 12
        assert result["selected_exec"] == "1.1.201"
        assert result["selected_exec_cue"] == "3"
        assert result["warning"] is None


# ── Tool 125: hydrate_sequences ───────────────────────────────────────────────

class TestHydrateSequences:

    @pytest.mark.asyncio
    async def test_invalid_ids_returns_error(self):
        mock_orch = MagicMock()
        t = _capture_tools(mock_orch)
        result = json.loads(await t["hydrate_sequences"](sequence_ids="1,two,3"))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_empty_ids_returns_error(self):
        mock_orch = MagicMock()
        t = _capture_tools(mock_orch)
        result = json.loads(await t["hydrate_sequences"](sequence_ids="  "))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_valid_ids_calls_hydrate(self):
        snap = _make_snap()
        mock_orch = MagicMock()
        mock_orch.hydrate_snapshot = AsyncMock(return_value=snap)
        t = _capture_tools(mock_orch)
        result = json.loads(await t["hydrate_sequences"](sequence_ids="1,2,5"))
        assert result["hydrated"] is True
        assert result["sequence_ids"] == [1, 2, 5]
        mock_orch.hydrate_snapshot.assert_called_once_with(sequence_ids=[1, 2, 5])

    @pytest.mark.asyncio
    async def test_updates_last_snapshot(self):
        snap = _make_snap()
        mock_orch = MagicMock()
        mock_orch.hydrate_snapshot = AsyncMock(return_value=snap)
        t = _capture_tools(mock_orch)
        await t["hydrate_sequences"](sequence_ids="1")
        assert mock_orch.last_snapshot == snap


# ── Tool 126: get_sequence_memory ─────────────────────────────────────────────

class TestGetSequenceMemory:

    @pytest.mark.asyncio
    async def test_sequence_not_in_snapshot_returns_error(self):
        mock_orch = MagicMock()
        mock_orch.last_snapshot = _make_snap()
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_sequence_memory"](sequence_id=99))
        assert "error" in result
        assert "hint" in result

    @pytest.mark.asyncio
    async def test_sequence_found_returns_fields(self):
        snap = _make_snap()
        snap.sequences.append(SequenceEntry(id=5, label="Main", loop=True))
        snap.sequence_cues.append(CueRecord(sequence_id=5, cue_number=1.0, label="Go"))
        mock_orch = MagicMock()
        mock_orch.last_snapshot = snap
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_sequence_memory"](sequence_id=5))
        assert result["id"] == 5
        assert result["label"] == "Main"
        assert result["loop"] is True
        assert result["cue_count"] == 1
        assert result["cues"][0]["cue_number"] == 1.0

    @pytest.mark.asyncio
    async def test_known_ids_listed_in_error(self):
        snap = _make_snap()
        snap.sequences.append(SequenceEntry(id=3, label="Seq3"))
        mock_orch = MagicMock()
        mock_orch.last_snapshot = snap
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_sequence_memory"](sequence_id=99))
        assert 3 in result["known_ids"]


# ── Tool 127: assert_selection_count ─────────────────────────────────────────

class TestAssertSelectionCount:

    @pytest.mark.asyncio
    async def test_exact_match_passes(self):
        snap = _make_snap()
        snap.selected_fixture_count = 12
        mock_orch = MagicMock()
        mock_orch.last_snapshot = snap
        t = _capture_tools(mock_orch)
        result = json.loads(await t["assert_selection_count"](expected=12))
        assert result["passed"] is True
        assert result["message"] == "OK"

    @pytest.mark.asyncio
    async def test_mismatch_fails(self):
        snap = _make_snap()
        snap.selected_fixture_count = 10
        mock_orch = MagicMock()
        mock_orch.last_snapshot = snap
        t = _capture_tools(mock_orch)
        result = json.loads(await t["assert_selection_count"](expected=12))
        assert result["passed"] is False
        assert "10" in result["message"]

    @pytest.mark.asyncio
    async def test_within_tolerance_passes(self):
        snap = _make_snap()
        snap.selected_fixture_count = 11
        mock_orch = MagicMock()
        mock_orch.last_snapshot = snap
        t = _capture_tools(mock_orch)
        result = json.loads(await t["assert_selection_count"](expected=12, tolerance=2))
        assert result["passed"] is True

    @pytest.mark.asyncio
    async def test_outside_tolerance_fails(self):
        snap = _make_snap()
        snap.selected_fixture_count = 5
        mock_orch = MagicMock()
        mock_orch.last_snapshot = snap
        t = _capture_tools(mock_orch)
        result = json.loads(await t["assert_selection_count"](expected=12, tolerance=2))
        assert result["passed"] is False


# ── Tool 128: assert_preset_exists ───────────────────────────────────────────

class TestAssertPresetExists:

    @pytest.mark.asyncio
    async def test_preset_not_in_index(self):
        mock_orch = MagicMock()
        mock_orch.last_snapshot = _make_snap()
        t = _capture_tools(mock_orch)
        result = json.loads(await t["assert_preset_exists"](preset_type=2, preset_id=1))
        assert result["exists"] is False
        assert result["warning"] is not None

    @pytest.mark.asyncio
    async def test_preset_in_index(self):
        snap = _make_snap()
        snap.name_index.add_entry("preset", "Position 1", 1, preset_type=2)
        mock_orch = MagicMock()
        mock_orch.last_snapshot = snap
        t = _capture_tools(mock_orch)
        result = json.loads(await t["assert_preset_exists"](preset_type=2, preset_id=1))
        assert result["exists"] is True
        assert result["warning"] is None


# ── Tool 129: get_executor_detail ─────────────────────────────────────────────

class TestGetExecutorDetail:

    @pytest.mark.asyncio
    async def test_executor_not_in_snapshot(self):
        mock_orch = MagicMock()
        mock_orch.last_snapshot = _make_snap()
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_executor_detail"](executor_id=201))
        assert "error" in result
        assert "known_ids" in result

    @pytest.mark.asyncio
    async def test_executor_found_returns_all_fields(self):
        snap = _make_snap()
        snap.executor_state[201] = ExecutorState(id=201, page=1, priority="high", kill_protect=True)
        mock_orch = MagicMock()
        mock_orch.last_snapshot = snap
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_executor_detail"](executor_id=201))
        assert result["id"] == 201
        assert result["priority"] == "high"
        assert result["kill_protect"] is True

    @pytest.mark.asyncio
    async def test_known_ids_listed_in_error(self):
        snap = _make_snap()
        snap.executor_state[5] = ExecutorState(id=5)
        mock_orch = MagicMock()
        mock_orch.last_snapshot = snap
        t = _capture_tools(mock_orch)
        result = json.loads(await t["get_executor_detail"](executor_id=99))
        assert 5 in result["known_ids"]
