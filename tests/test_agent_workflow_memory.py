# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for src/agent/memory.py — SQLite workflow memory."""

import os
import tempfile

import pytest

from src.agent.memory import WorkflowMemory


@pytest.fixture
def memory():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_memory.db")
        mem = WorkflowMemory(db_path=db_path)
        yield mem
        mem.close()


class TestConventions:
    def test_store_and_recall(self, memory):
        memory.store_convention("naming", "fixtures", {"prefix": "Mac700"})
        result = memory.recall_convention("naming", "fixtures")
        assert len(result) == 1
        assert result[0]["value"]["prefix"] == "Mac700"

    def test_recall_by_category(self, memory):
        memory.store_convention("naming", "fixtures", {"prefix": "Mac"})
        memory.store_convention("naming", "groups", {"prefix": "GRP"})
        memory.store_convention("layout", "page1", {"rows": 4})
        result = memory.recall_convention("naming")
        assert len(result) == 2

    def test_upsert_convention(self, memory):
        memory.store_convention("naming", "fixtures", {"prefix": "Mac"})
        memory.store_convention("naming", "fixtures", {"prefix": "Martin"})
        result = memory.recall_convention("naming", "fixtures")
        assert len(result) == 1
        assert result[0]["value"]["prefix"] == "Martin"

    def test_recall_nonexistent(self, memory):
        result = memory.recall_convention("nonexistent")
        assert result == []


class TestRecipes:
    def test_store_and_recall(self, memory):
        steps = [{"tool": "patch_fixture", "args": {"fixture_id": 1}}]
        memory.store_recipe("basic_patch", steps, ["patch", "mac700"])
        result = memory.recall_recipe(name="basic_patch")
        assert len(result) == 1
        assert result[0]["name"] == "basic_patch"
        assert result[0]["steps"] == steps
        assert result[0]["tags"] == ["patch", "mac700"]

    def test_recall_by_tags(self, memory):
        memory.store_recipe("r1", [{"tool": "a"}], ["patch", "mac700"])
        memory.store_recipe("r2", [{"tool": "b"}], ["preset", "color"])
        result = memory.recall_recipe(tags=["patch"])
        assert len(result) == 1
        assert result[0]["name"] == "r1"

    def test_recall_all(self, memory):
        memory.store_recipe("r1", [], ["a"])
        memory.store_recipe("r2", [], ["b"])
        result = memory.recall_recipe()
        assert len(result) == 2

    def test_increment_usage(self, memory):
        memory.store_recipe("r1", [], ["a"])
        memory.increment_recipe_usage("r1")
        memory.increment_recipe_usage("r1")
        result = memory.recall_recipe(name="r1")
        assert result[0]["use_count"] == 2
        assert result[0]["last_used_at"] is not None


class TestRunHistory:
    def test_record_and_recall(self, memory):
        memory.record_run_summary(
            run_id="run_abc",
            goal="List groups",
            result="success",
            trace_json='{"steps": []}',
        )
        result = memory.recall_runs()
        assert len(result) == 1
        assert result[0]["run_id"] == "run_abc"
        assert result[0]["result"] == "success"

    def test_recall_filtered(self, memory):
        memory.record_run_summary("r1", "g1", "success", "{}")
        memory.record_run_summary("r2", "g2", "failure", "{}")
        success = memory.recall_runs(result_filter="success")
        assert len(success) == 1
        failures = memory.recall_runs(result_filter="failure")
        assert len(failures) == 1

    def test_search_by_goal(self, memory):
        memory.record_run_summary("r1", "Patch 8 Mac 700 fixtures", "success", "{}")
        memory.record_run_summary("r2", "List all groups", "success", "{}")
        result = memory.search_runs_by_goal("Mac 700")
        assert len(result) == 1
        assert result[0]["run_id"] == "r1"

    def test_recall_limit(self, memory):
        for i in range(25):
            memory.record_run_summary(f"r{i}", f"goal {i}", "success", "{}")
        result = memory.recall_runs(limit=10)
        assert len(result) == 10

    def test_upsert_run(self, memory):
        memory.record_run_summary("r1", "goal", "failure", "{}")
        memory.record_run_summary("r1", "goal", "success", '{"retry": true}')
        result = memory.recall_runs()
        assert len(result) == 1


# ── Step checkpoint tests ────────────────────────────────────────────────


class TestStepCheckpoints:
    """Tests for the step_checkpoints table and methods."""

    def test_step_checkpoints_table_created(self, memory):
        """The step_checkpoints table exists after initialization."""
        row = memory._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='step_checkpoints'"
        ).fetchone()
        assert row is not None

    def test_save_step_checkpoint_creates_record(self, memory):
        step_dict = {
            "id": "step-001",
            "tool_name": "list_groups",
            "status": "COMPLETED",
            "result": "ok",
            "error": None,
            "started_at": "2026-04-06T12:00:00Z",
            "completed_at": "2026-04-06T12:00:01Z",
            "retry_count": 0,
        }
        memory.save_step_checkpoint("run-1", 0, step_dict)
        rows = memory.load_run_checkpoints("run-1")
        assert len(rows) == 1
        assert rows[0]["step_id"] == "step-001"
        assert rows[0]["status"] == "COMPLETED"
        assert rows[0]["result"] == "ok"

    def test_load_run_checkpoints_returns_ordered(self, memory):
        for i in range(3):
            memory.save_step_checkpoint("run-2", i, {
                "id": f"step-{i}", "tool_name": f"tool_{i}", "status": "COMPLETED",
            })
        rows = memory.load_run_checkpoints("run-2")
        assert len(rows) == 3
        assert [r["step_index"] for r in rows] == [0, 1, 2]

    def test_delete_run_checkpoints_clears_all(self, memory):
        for i in range(3):
            memory.save_step_checkpoint("run-3", i, {
                "id": f"s{i}", "tool_name": "t", "status": "COMPLETED",
            })
        deleted = memory.delete_run_checkpoints("run-3")
        assert deleted == 3
        assert memory.load_run_checkpoints("run-3") == []

    def test_checkpoint_upsert_on_retry(self, memory):
        """Saving a checkpoint twice for the same step_id upserts."""
        step = {"id": "s1", "tool_name": "t", "status": "FAILED", "error": "err1"}
        memory.save_step_checkpoint("run-4", 0, step)
        step["status"] = "COMPLETED"
        step["error"] = None
        step["result"] = "ok"
        memory.save_step_checkpoint("run-4", 0, step)
        rows = memory.load_run_checkpoints("run-4")
        assert len(rows) == 1
        assert rows[0]["status"] == "COMPLETED"
        assert rows[0]["result"] == "ok"

    def test_load_empty_run_returns_empty(self, memory):
        assert memory.load_run_checkpoints("nonexistent") == []

    def test_delete_empty_run_returns_zero(self, memory):
        assert memory.delete_run_checkpoints("nonexistent") == 0
