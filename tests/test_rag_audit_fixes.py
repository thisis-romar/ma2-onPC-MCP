# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for RAG + KG architecture audit fixes (round 2).

Covers: defensive guards, constant extraction, resource management,
error handling, and schema improvements.
"""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock, patch

import pytest

# ── KG: executor _mark_stale_nodes None guard ────────────────────────────


class TestMarkStaleNodesGuard:
    """_mark_stale_nodes must not crash when graph_store is None."""

    def test_mark_stale_nodes_with_none_graph_store(self):
        """Calling _mark_stale_nodes when graph_store is None should be a no-op."""
        from src.agent.executor import StepExecutor
        from src.agent.state import PlanStep
        from src.vocab import RiskTier

        executor = StepExecutor.__new__(StepExecutor)
        executor._graph_store = None

        step = PlanStep(
            id="s1",
            tool_name="delete_object",
            tool_args={},
            description="test",
            risk_tier=RiskTier.DESTRUCTIVE,
        )
        # Should not raise
        executor._mark_stale_nodes(step)

    def test_mark_stale_nodes_with_graph_store_calls_mark(self):
        """When graph_store is present, mark_type_stale should be called."""
        from src.agent.executor import StepExecutor
        from src.agent.state import PlanStep
        from src.vocab import RiskTier

        executor = StepExecutor.__new__(StepExecutor)
        mock_store = MagicMock()
        executor._graph_store = mock_store

        step = PlanStep(
            id="s1",
            tool_name="store_current_cue",
            tool_args={},
            description="test",
            risk_tier=RiskTier.DESTRUCTIVE,
        )
        executor._mark_stale_nodes(step)
        # store_current_cue → ["cue", "sequence"]
        assert mock_store.mark_type_stale.call_count == 2

    def test_mark_stale_unknown_tool_marks_all(self):
        """Unknown DESTRUCTIVE tool should mark all 6 node types stale."""
        from src.agent.executor import StepExecutor
        from src.agent.state import PlanStep
        from src.vocab import RiskTier

        executor = StepExecutor.__new__(StepExecutor)
        mock_store = MagicMock()
        executor._graph_store = mock_store

        step = PlanStep(
            id="s1",
            tool_name="some_unknown_destructive_tool",
            tool_args={},
            description="test",
            risk_tier=RiskTier.DESTRUCTIVE,
        )
        executor._mark_stale_nodes(step)
        assert mock_store.mark_type_stale.call_count == 6


# ── RAG: assert → ValueError in ingest index ────────────────────────────


class TestIngestEmbeddingMismatch:
    """ingest() must raise ValueError (not AssertionError) on dimension mismatch."""

    def test_raises_valueerror_not_assertion(self):
        from rag.ingest.index import ingest

        mock_provider = MagicMock()
        mock_provider.embed_many.return_value = [[0.1, 0.2]]  # 1 embedding for N chunks
        mock_provider.model_name = "test"

        # Create a temp file that will produce >1 chunk
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "test.py"
            # Write enough code to produce multiple chunks
            p.write_text("def a():\n    pass\n\ndef b():\n    pass\n" * 50)

            with pytest.raises(ValueError, match="Embedding count mismatch"):
                ingest(root_dir=td, embedding_provider=mock_provider, db_path=":memory:")


# ── RAG: rerank division-by-zero guard ───────────────────────────────────


class TestRerankDivisionGuard:
    """_keyword_overlap must handle empty query_terms gracefully."""

    def test_empty_query_terms_returns_zero(self):
        from rag.retrieve.rerank import _keyword_overlap

        assert _keyword_overlap([], "some text here") == 0.0

    def test_normal_overlap(self):
        from rag.retrieve.rerank import _keyword_overlap

        result = _keyword_overlap(["hello", "world"], "hello world")
        assert result == 1.0

    def test_partial_overlap(self):
        from rag.retrieve.rerank import _keyword_overlap

        result = _keyword_overlap(["hello", "missing"], "hello world")
        assert result == 0.5


# ── RAG: embedding provider close() ─────────────────────────────────────


class TestEmbeddingProviderClose:
    """Embedding providers must have close() methods."""

    def test_github_provider_has_close(self):
        from rag.ingest.embed import GitHubModelsProvider

        provider = GitHubModelsProvider(token="fake-token")
        assert hasattr(provider, "close")
        provider.close()  # Should not raise

    def test_openrouter_provider_has_close(self):
        from rag.ingest.embed import OpenRouterProvider

        provider = OpenRouterProvider(token="fake-token")
        assert hasattr(provider, "close")
        provider.close()  # Should not raise


# ── RAG: schema partial index ────────────────────────────────────────────


class TestSchemaPartialIndex:
    """schema.sql must include the partial index on embedding IS NOT NULL."""

    def test_partial_index_in_schema(self):
        from pathlib import Path

        schema_path = Path("rag/store/schema.sql")
        schema = schema_path.read_text()
        assert "idx_chunks_has_embedding" in schema
        assert "WHERE embedding IS NOT NULL" in schema

    def test_partial_index_created_in_db(self):
        """Verify the index is actually created when the schema is applied."""
        from pathlib import Path

        schema_path = Path("rag/store/schema.sql")
        schema_sql = schema_path.read_text()

        conn = sqlite3.connect(":memory:")
        conn.executescript(schema_sql)
        indices = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_chunks_has_embedding'"
        ).fetchall()
        conn.close()
        assert len(indices) == 1


# ── RAG: config constants are importable ─────────────────────────────────


class TestConfigConstants:
    """All extracted constants must be importable from rag.config."""

    def test_dedup_prefix_len(self):
        from rag.config import DEDUP_PREFIX_LEN

        assert isinstance(DEDUP_PREFIX_LEN, int)
        assert DEDUP_PREFIX_LEN > 0

    def test_min_page_text_length(self):
        from rag.config import MIN_PAGE_TEXT_LENGTH

        assert isinstance(MIN_PAGE_TEXT_LENGTH, int)
        assert MIN_PAGE_TEXT_LENGTH > 0

    def test_web_crawler_user_agent(self):
        from rag.config import WEB_CRAWLER_USER_AGENT

        assert isinstance(WEB_CRAWLER_USER_AGENT, str)
        assert "grandpa2-buddy" in WEB_CRAWLER_USER_AGENT

    def test_daily_quota_retry_after(self):
        from rag.config import DAILY_QUOTA_RETRY_AFTER

        assert isinstance(DAILY_QUOTA_RETRY_AFTER, float)
        assert DAILY_QUOTA_RETRY_AFTER == 3600.0

    def test_max_retry_wait(self):
        from rag.config import MAX_RETRY_WAIT

        assert isinstance(MAX_RETRY_WAIT, float)
        assert MAX_RETRY_WAIT == 300.0


# ── RAG: FTS5 rebuild warning ────────────────────────────────────────────


class TestFTS5RebuildWarning:
    """delete_by_repo_ref must log a warning when FTS5 rebuild fails."""

    def test_fts5_rebuild_failure_logs_warning(self):
        """When FTS5 rebuild fails, a warning should be logged (not silently suppressed)."""
        from rag.store.sqlite import RagStore

        store = RagStore(":memory:")
        store.init_db()

        # Drop FTS table triggers first, then the table, so DELETE won't fail
        store.conn.execute("DROP TRIGGER IF EXISTS chunks_fts_insert")
        store.conn.execute("DROP TRIGGER IF EXISTS chunks_fts_delete")
        store.conn.execute("DROP TRIGGER IF EXISTS chunks_fts_update")
        store.conn.execute("DROP TABLE IF EXISTS chunks_fts")

        with patch("rag.store.sqlite.logger") as mock_logger:
            store.delete_by_repo_ref("nonexistent")
            mock_logger.warning.assert_called_once()
            assert "FTS5 rebuild failed" in mock_logger.warning.call_args[0][0]

        store.close()


# ── RAG: embed.py JSON response validation ───────────────────────────────


class TestEmbedResponseValidation:
    """Embedding providers must raise RuntimeError on malformed API responses."""

    def test_github_missing_data_field(self):
        from rag.ingest.embed import GitHubModelsProvider

        provider = GitHubModelsProvider(token="fake-token")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "something went wrong"}

        with (
            patch.object(provider, "_request_with_retry", return_value=mock_response),
            pytest.raises(RuntimeError, match="no 'data' field"),
        ):
            provider.embed_many(["test text"])

        provider.close()

    def test_openrouter_missing_data_field(self):
        from rag.ingest.embed import OpenRouterProvider

        provider = OpenRouterProvider(token="fake-token")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "rate limited"}

        with (
            patch.object(provider, "_request_with_retry", return_value=mock_response),
            pytest.raises(RuntimeError, match="no 'data' field"),
        ):
            provider.embed_many(["test text"])

        provider.close()
