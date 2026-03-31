"""
tests/test_telemetry.py — Unit tests for src/telemetry.py

Covers:
  - infer_risk_tier() module-level function
  - ToolTelemetry: record_sync, metrics, recent, top_failing_tools
"""

import tempfile
import time
from pathlib import Path

import pytest

from src.telemetry import ToolTelemetry, infer_risk_tier


# ── infer_risk_tier ──────────────────────────────────────────────────────────


class TestInferRiskTier:
    def test_confirm_destructive_param_returns_destructive(self):
        def delete_thing(confirm_destructive: bool = False):
            pass

        assert infer_risk_tier(delete_thing) == "DESTRUCTIVE"

    def test_list_prefix_returns_safe_read(self):
        def list_objects():
            pass

        assert infer_risk_tier(list_objects) == "SAFE_READ"

    def test_get_prefix_returns_safe_read(self):
        def get_variable():
            pass

        assert infer_risk_tier(get_variable) == "SAFE_READ"

    def test_discover_prefix_returns_safe_read(self):
        def discover_object_names():
            pass

        assert infer_risk_tier(discover_object_names) == "SAFE_READ"

    def test_suggest_prefix_returns_safe_read(self):
        def suggest_tool_for_task():
            pass

        assert infer_risk_tier(suggest_tool_for_task) == "SAFE_READ"

    def test_search_prefix_returns_safe_read(self):
        def search_codebase():
            pass

        assert infer_risk_tier(search_codebase) == "SAFE_READ"

    def test_non_read_non_destructive_returns_safe_write(self):
        def set_intensity(level: int):
            pass

        assert infer_risk_tier(set_intensity) == "SAFE_WRITE"

    def test_confirm_destructive_overrides_list_prefix(self):
        # A function starting with list_ BUT also having confirm_destructive → DESTRUCTIVE
        def list_and_delete(confirm_destructive: bool = False):
            pass

        assert infer_risk_tier(list_and_delete) == "DESTRUCTIVE"


# ── ToolTelemetry ────────────────────────────────────────────────────────────


@pytest.fixture
def tel_tmp():
    """ToolTelemetry backed by a temp DB, cleaned up after test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    tel = ToolTelemetry(db_path=db_path)
    yield tel
    tel.close()
    db_path.unlink(missing_ok=True)


def _record(tel: ToolTelemetry, tool_name: str, *, error_class=None, latency_ms=10.0):
    tel.record_sync(
        tool_name=tool_name,
        inputs_json="{}",
        output_preview="ok",
        error_class=error_class,
        latency_ms=latency_ms,
        risk_tier="SAFE_WRITE",
        operator="test",
        session_id="test-session",
    )


class TestToolTelemetryMetrics:
    def test_metrics_no_data_returns_zero_calls(self, tel_tmp):
        m = tel_tmp.metrics("unknown_tool")
        assert m["calls"] == 0

    def test_metrics_one_success(self, tel_tmp):
        _record(tel_tmp, "set_intensity")
        m = tel_tmp.metrics("set_intensity")
        assert m["calls"] == 1
        assert m["error_count"] == 0

    def test_metrics_one_error(self, tel_tmp):
        _record(tel_tmp, "set_intensity", error_class="RuntimeError")
        m = tel_tmp.metrics("set_intensity")
        assert m["error_count"] == 1
        assert "RuntimeError" in m["error_classes"]

    def test_metrics_error_rate(self, tel_tmp):
        _record(tel_tmp, "set_intensity")
        _record(tel_tmp, "set_intensity")
        _record(tel_tmp, "set_intensity", error_class="TimeoutError")
        m = tel_tmp.metrics("set_intensity")
        assert m["calls"] == 3
        assert m["error_count"] == 1
        assert abs(m["error_rate"] - 0.333) < 0.01

    def test_metrics_latency_stats_present(self, tel_tmp):
        _record(tel_tmp, "navigate_console", latency_ms=5.0)
        _record(tel_tmp, "navigate_console", latency_ms=15.0)
        m = tel_tmp.metrics("navigate_console")
        assert m["min_ms"] == 5.0
        assert m["max_ms"] == 15.0
        assert m["p50_ms"] is not None


class TestToolTelemetryRecent:
    def test_recent_empty_for_unknown_tool(self, tel_tmp):
        assert tel_tmp.recent("no_such_tool") == []

    def test_recent_returns_rows(self, tel_tmp):
        _record(tel_tmp, "play_back")
        rows = tel_tmp.recent("play_back")
        assert len(rows) == 1
        assert rows[0]["tool_name"] == "play_back"

    def test_recent_newest_first(self, tel_tmp):
        for i in range(3):
            _record(tel_tmp, "my_tool", latency_ms=float(i))
            time.sleep(0.01)
        rows = tel_tmp.recent("my_tool", limit=3)
        # rows are newest first: latencies should be 2, 1, 0
        assert rows[0]["latency_ms"] == 2.0
        assert rows[2]["latency_ms"] == 0.0

    def test_recent_limit_respected(self, tel_tmp):
        for _ in range(10):
            _record(tel_tmp, "flood_tool")
        rows = tel_tmp.recent("flood_tool", limit=3)
        assert len(rows) == 3


class TestToolTelemetryTopFailing:
    def test_top_failing_empty_when_no_errors(self, tel_tmp):
        _record(tel_tmp, "safe_tool")
        assert tel_tmp.top_failing_tools(min_failures=1) == []

    def test_top_failing_returns_tool_above_threshold(self, tel_tmp):
        for _ in range(4):
            _record(tel_tmp, "bad_tool", error_class="ConnectionError")
        result = tel_tmp.top_failing_tools(min_failures=3)
        assert len(result) == 1
        assert result[0]["tool_name"] == "bad_tool"
        assert result[0]["total"] == 4

    def test_top_failing_excludes_tool_below_threshold(self, tel_tmp):
        for _ in range(2):
            _record(tel_tmp, "slightly_bad", error_class="RuntimeError")
        result = tel_tmp.top_failing_tools(min_failures=3)
        assert result == []

    def test_top_failing_aggregates_multiple_error_classes(self, tel_tmp):
        _record(tel_tmp, "multi_err", error_class="ConnectionError")
        _record(tel_tmp, "multi_err", error_class="RuntimeError")
        _record(tel_tmp, "multi_err", error_class="TimeoutError")
        result = tel_tmp.top_failing_tools(min_failures=3)
        assert len(result) == 1
        assert len(result[0]["errors"]) == 3
        assert result[0]["total"] == 3
