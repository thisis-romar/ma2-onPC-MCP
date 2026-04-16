# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for the RAG embedding interface."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from rag.ingest.embed import (
    EmbeddingProvider,
    GeminiProvider,
    GitHubModelsProvider,
    OpenRouterProvider,
    ZeroVectorProvider,
)


class TestZeroVectorProvider:
    def test_model_name(self):
        p = ZeroVectorProvider()
        assert p.model_name == "zero-vector-stub"

    def test_default_dimensions(self):
        p = ZeroVectorProvider()
        assert p.dimensions == 1536  # matches GitHubModelsProvider default

    def test_custom_dimensions(self):
        p = ZeroVectorProvider(dimensions=128)
        assert p.dimensions == 128

    def test_embed_one_returns_zeros(self):
        p = ZeroVectorProvider(dimensions=3)
        result = p.embed_one("hello world")
        assert result == [0.0, 0.0, 0.0]

    def test_embed_one_correct_length(self):
        p = ZeroVectorProvider(dimensions=256)
        result = p.embed_one("test")
        assert len(result) == 256

    def test_embed_many(self):
        p = ZeroVectorProvider(dimensions=3)
        results = p.embed_many(["a", "b", "c"])
        assert len(results) == 3
        for r in results:
            assert r == [0.0, 0.0, 0.0]

    def test_embed_many_empty(self):
        p = ZeroVectorProvider(dimensions=3)
        results = p.embed_many([])
        assert results == []


class TestEmbeddingProviderABC:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            EmbeddingProvider()  # type: ignore[abstract]

    def test_subclass_must_implement_all(self):
        class PartialProvider(EmbeddingProvider):
            @property
            def model_name(self) -> str:
                return "partial"

            @property
            def dimensions(self) -> int:
                return 10

            # Missing embed_one and embed_many

        with pytest.raises(TypeError):
            PartialProvider()  # type: ignore[abstract]


def _mock_embedding_response(embeddings: list[list[float]]) -> httpx.Response:
    """Build a mock httpx.Response with OpenAI-compatible embedding data."""
    data = [{"index": i, "embedding": emb} for i, emb in enumerate(embeddings)]
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 200
    resp.headers = {}
    resp.json.return_value = {"data": data, "model": "openai/text-embedding-3-small"}
    resp.raise_for_status = MagicMock()
    return resp


class TestGitHubModelsProvider:
    def test_properties(self):
        p = GitHubModelsProvider(token="ghp_test123")
        assert p.model_name == "openai/text-embedding-3-small"
        assert p.dimensions == 1536

    def test_custom_properties(self):
        p = GitHubModelsProvider(
            token="ghp_test123",
            model="openai/text-embedding-3-large",
            dimensions=3072,
        )
        assert p.model_name == "openai/text-embedding-3-large"
        assert p.dimensions == 3072

    @patch.object(httpx.Client, "post")
    def test_embed_one(self, mock_post: MagicMock):
        mock_post.return_value = _mock_embedding_response([[0.1, 0.2, 0.3]])

        p = GitHubModelsProvider(token="ghp_test123", dimensions=3)
        result = p.embed_one("hello world")

        assert result == [0.1, 0.2, 0.3]
        mock_post.assert_called_once_with(
            "/embeddings",
            json={"input": ["hello world"], "model": "openai/text-embedding-3-small"},
        )

    @patch.object(httpx.Client, "post")
    def test_embed_many(self, mock_post: MagicMock):
        mock_post.return_value = _mock_embedding_response(
            [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]
        )

        p = GitHubModelsProvider(token="ghp_test123", dimensions=2)
        result = p.embed_many(["a", "b", "c"])

        assert len(result) == 3
        assert result[0] == [0.1, 0.2]
        assert result[2] == [0.5, 0.6]

    @patch.object(httpx.Client, "post")
    def test_embed_many_empty(self, mock_post: MagicMock):
        p = GitHubModelsProvider(token="ghp_test123")
        result = p.embed_many([])

        assert result == []
        mock_post.assert_not_called()

    @patch.object(httpx.Client, "post")
    def test_embed_many_batching(self, mock_post: MagicMock):
        """150 texts with batch_size=64 should produce 3 API calls."""

        def _response_for_batch(*args, **kwargs):
            batch = kwargs["json"]["input"]
            return _mock_embedding_response([[0.1] * 3 for _ in range(len(batch))])

        mock_post.side_effect = _response_for_batch

        p = GitHubModelsProvider(token="ghp_test123", dimensions=3, batch_size=64, inter_request_delay=0.0)
        texts = [f"text_{i}" for i in range(150)]
        result = p.embed_many(texts)

        assert mock_post.call_count == 3
        # First batch: 64 texts, second: 64, third: 22
        calls = mock_post.call_args_list
        assert len(calls[0].kwargs["json"]["input"]) == 64
        assert len(calls[1].kwargs["json"]["input"]) == 64
        assert len(calls[2].kwargs["json"]["input"]) == 22
        assert len(result) == 150

    @patch.object(httpx.Client, "post")
    def test_result_ordering(self, mock_post: MagicMock):
        """API may return embeddings out of order — provider must sort by index."""
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 200
        resp.headers = {}
        resp.json.return_value = {
            "data": [
                {"index": 2, "embedding": [0.5, 0.6]},
                {"index": 0, "embedding": [0.1, 0.2]},
                {"index": 1, "embedding": [0.3, 0.4]},
            ],
            "model": "openai/text-embedding-3-small",
        }
        resp.raise_for_status = MagicMock()
        mock_post.return_value = resp

        p = GitHubModelsProvider(token="ghp_test123", dimensions=2)
        result = p.embed_many(["a", "b", "c"])

        assert result == [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]

    @patch.object(httpx.Client, "post")
    def test_http_error_raises(self, mock_post: MagicMock):
        """HTTP errors should propagate as httpx.HTTPStatusError."""
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 401
        resp.headers = {}
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=resp
        )
        mock_post.return_value = resp

        p = GitHubModelsProvider(token="bad_token")
        with pytest.raises(httpx.HTTPStatusError):
            p.embed_one("hello")


def _mock_openrouter_response(embeddings: list[list[float]]) -> httpx.Response:
    """Build a mock httpx.Response with OpenRouter-compatible embedding data."""
    data = [{"index": i, "embedding": emb} for i, emb in enumerate(embeddings)]
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 200
    resp.headers = {}
    resp.json.return_value = {"data": data, "model": "nvidia/llama-nemotron-embed-vl-1b-v2:free"}
    resp.raise_for_status = MagicMock()
    return resp


class TestOpenRouterProvider:
    def test_properties(self):
        p = OpenRouterProvider(token="or-test123")
        assert p.model_name == "nvidia/llama-nemotron-embed-vl-1b-v2:free"
        assert p.dimensions == 2048

    def test_custom_properties(self):
        p = OpenRouterProvider(
            token="or-test123",
            model="openai/text-embedding-3-small",
            dimensions=1536,
        )
        assert p.model_name == "openai/text-embedding-3-small"
        assert p.dimensions == 1536

    @patch.object(httpx.Client, "post")
    def test_embed_one(self, mock_post: MagicMock):
        mock_post.return_value = _mock_openrouter_response([[0.1, 0.2, 0.3]])

        p = OpenRouterProvider(token="or-test123", dimensions=3)
        result = p.embed_one("hello world")

        assert result == [0.1, 0.2, 0.3]
        mock_post.assert_called_once_with(
            "/embeddings",
            json={"input": ["hello world"], "model": "nvidia/llama-nemotron-embed-vl-1b-v2:free"},
        )

    @patch.object(httpx.Client, "post")
    def test_embed_many(self, mock_post: MagicMock):
        mock_post.return_value = _mock_openrouter_response(
            [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]
        )

        p = OpenRouterProvider(token="or-test123", dimensions=2)
        result = p.embed_many(["a", "b", "c"])

        assert len(result) == 3
        assert result[0] == [0.1, 0.2]
        assert result[2] == [0.5, 0.6]

    @patch.object(httpx.Client, "post")
    def test_embed_many_empty(self, mock_post: MagicMock):
        p = OpenRouterProvider(token="or-test123")
        result = p.embed_many([])

        assert result == []
        mock_post.assert_not_called()

    @patch.object(httpx.Client, "post")
    def test_embed_many_batching(self, mock_post: MagicMock):
        """70 texts with batch_size=32 should produce 3 API calls."""

        def _response_for_batch(*args, **kwargs):
            batch = kwargs["json"]["input"]
            return _mock_openrouter_response([[0.1] * 3 for _ in range(len(batch))])

        mock_post.side_effect = _response_for_batch

        p = OpenRouterProvider(token="or-test123", dimensions=3, batch_size=32, inter_request_delay=0.0)
        texts = [f"text_{i}" for i in range(70)]
        result = p.embed_many(texts)

        assert mock_post.call_count == 3
        calls = mock_post.call_args_list
        assert len(calls[0].kwargs["json"]["input"]) == 32
        assert len(calls[1].kwargs["json"]["input"]) == 32
        assert len(calls[2].kwargs["json"]["input"]) == 6
        assert len(result) == 70

    @patch.object(httpx.Client, "post")
    def test_deduplication(self, mock_post: MagicMock):
        """Identical texts are embedded once and reused."""
        mock_post.return_value = _mock_openrouter_response([[0.1, 0.2]])

        p = OpenRouterProvider(token="or-test123", dimensions=2, inter_request_delay=0.0)
        result = p.embed_many(["hello", "hello", "hello"])

        # Only 1 unique text → 1 API call with 1-item batch
        mock_post.assert_called_once()
        assert len(mock_post.call_args.kwargs["json"]["input"]) == 1
        assert len(result) == 3
        assert result[0] == result[1] == result[2] == [0.1, 0.2]

    @patch.object(httpx.Client, "post")
    def test_result_ordering(self, mock_post: MagicMock):
        """Out-of-order API response is sorted by index before returning."""
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 200
        resp.headers = {}
        resp.json.return_value = {
            "data": [
                {"index": 2, "embedding": [0.5, 0.6]},
                {"index": 0, "embedding": [0.1, 0.2]},
                {"index": 1, "embedding": [0.3, 0.4]},
            ],
            "model": "nvidia/llama-nemotron-embed-vl-1b-v2:free",
        }
        resp.raise_for_status = MagicMock()
        mock_post.return_value = resp

        p = OpenRouterProvider(token="or-test123", dimensions=2)
        result = p.embed_many(["a", "b", "c"])

        assert result == [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]

    @patch.object(httpx.Client, "post")
    def test_http_error_raises(self, mock_post: MagicMock):
        """Non-retryable HTTP errors propagate after max retries."""
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 401
        resp.headers = {}
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=resp
        )
        mock_post.return_value = resp

        p = OpenRouterProvider(token="bad_token")
        with pytest.raises(httpx.HTTPStatusError):
            p.embed_one("hello")

    @patch.object(httpx.Client, "post")
    def test_daily_quota_raises_runtime_error(self, mock_post: MagicMock):
        """retry-after > 3600 signals daily quota exhausted — raise immediately."""
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 429
        resp.headers = {"retry-after": "86400"}  # 24 hours
        resp.raise_for_status = MagicMock()
        mock_post.return_value = resp

        p = OpenRouterProvider(token="or-test123", inter_request_delay=0.0)
        with pytest.raises(RuntimeError, match="daily quota exhausted"):
            p.embed_one("hello")


# ── Retry/backoff tests ─────────────────────────────────────────────────


class TestRetryBackoff:
    """_request_with_retry must retry on 429/5xx and give up after max_retries."""

    @patch("time.sleep")
    @patch.object(httpx.Client, "post")
    def test_429_then_success(self, mock_post: MagicMock, mock_sleep: MagicMock):
        """429 on first attempt, success on second."""
        resp_429 = MagicMock(spec=httpx.Response)
        resp_429.status_code = 429
        resp_429.headers = {"retry-after": "1"}
        resp_429.raise_for_status = MagicMock()

        resp_ok = _mock_embedding_response([[0.1, 0.2]])

        mock_post.side_effect = [resp_429, resp_ok]

        p = GitHubModelsProvider(token="ghp_test", dimensions=2, inter_request_delay=0.0)
        result = p.embed_one("hello")

        assert result == [0.1, 0.2]
        assert mock_post.call_count == 2
        mock_sleep.assert_called_once()  # slept between retries

    @patch("time.sleep")
    @patch.object(httpx.Client, "post")
    def test_max_retries_exhausted_raises(self, mock_post: MagicMock, mock_sleep: MagicMock):
        """Repeated 429s beyond max_retries should raise."""
        resp_429 = MagicMock(spec=httpx.Response)
        resp_429.status_code = 429
        resp_429.headers = {}
        resp_429.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Too Many Requests", request=MagicMock(), response=resp_429
        )
        mock_post.return_value = resp_429

        p = GitHubModelsProvider(token="ghp_test", dimensions=2, inter_request_delay=0.0)
        with pytest.raises(httpx.HTTPStatusError):
            p.embed_one("hello")

        # Should have tried max_retries + 1 times (default max_retries=5 → 6 attempts)
        assert mock_post.call_count == 6


# ── Gemini provider tests ─────────────────────────────────────────────


def _mock_gemini_single_response(values: list[float]) -> httpx.Response:
    """Build a mock httpx.Response for Gemini embedContent endpoint."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 200
    resp.headers = {}
    resp.json.return_value = {"embedding": {"values": values}}
    resp.raise_for_status = MagicMock()
    return resp


def _mock_gemini_batch_response(embeddings: list[list[float]]) -> httpx.Response:
    """Build a mock httpx.Response for Gemini batchEmbedContents endpoint."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 200
    resp.headers = {}
    resp.json.return_value = {
        "embeddings": [{"values": emb} for emb in embeddings]
    }
    resp.raise_for_status = MagicMock()
    return resp


class TestGeminiProvider:
    def test_properties(self):
        p = GeminiProvider(api_key="test-key")
        assert p.model_name == "text-embedding-004"
        assert p.dimensions == 768

    def test_custom_properties(self):
        p = GeminiProvider(
            api_key="test-key",
            model="text-embedding-005",
            dimensions=1024,
        )
        assert p.model_name == "text-embedding-005"
        assert p.dimensions == 1024

    @patch.object(httpx.Client, "post")
    def test_embed_one(self, mock_post: MagicMock):
        mock_post.return_value = _mock_gemini_single_response([0.1, 0.2, 0.3])

        p = GeminiProvider(api_key="test-key", dimensions=3)
        result = p.embed_one("hello world")

        assert result == [0.1, 0.2, 0.3]
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs["json"]
        assert payload["content"]["parts"][0]["text"] == "hello world"
        assert payload["taskType"] == "RETRIEVAL_DOCUMENT"
        assert call_kwargs.kwargs["params"] == {"key": "test-key"}

    @patch.object(httpx.Client, "post")
    def test_embed_many(self, mock_post: MagicMock):
        mock_post.return_value = _mock_gemini_batch_response(
            [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]
        )

        p = GeminiProvider(api_key="test-key", dimensions=2)
        result = p.embed_many(["a", "b", "c"])

        assert len(result) == 3
        assert result[0] == [0.1, 0.2]
        assert result[2] == [0.5, 0.6]

    @patch.object(httpx.Client, "post")
    def test_embed_many_empty(self, mock_post: MagicMock):
        p = GeminiProvider(api_key="test-key")
        result = p.embed_many([])

        assert result == []
        mock_post.assert_not_called()

    @patch.object(httpx.Client, "post")
    def test_embed_many_batching(self, mock_post: MagicMock):
        """250 texts with batch_size=100 should produce 3 API calls."""

        def _response_for_batch(*args, **kwargs):
            batch = kwargs["json"]["requests"]
            return _mock_gemini_batch_response([[0.1] * 3 for _ in range(len(batch))])

        mock_post.side_effect = _response_for_batch

        p = GeminiProvider(api_key="test-key", dimensions=3, batch_size=100, inter_request_delay=0.0)
        texts = [f"text_{i}" for i in range(250)]
        result = p.embed_many(texts)

        assert mock_post.call_count == 3
        calls = mock_post.call_args_list
        assert len(calls[0].kwargs["json"]["requests"]) == 100
        assert len(calls[1].kwargs["json"]["requests"]) == 100
        assert len(calls[2].kwargs["json"]["requests"]) == 50
        assert len(result) == 250

    @patch.object(httpx.Client, "post")
    def test_deduplication(self, mock_post: MagicMock):
        """Identical texts are embedded once and reused."""
        mock_post.return_value = _mock_gemini_batch_response([[0.1, 0.2]])

        p = GeminiProvider(api_key="test-key", dimensions=2, inter_request_delay=0.0)
        result = p.embed_many(["hello", "hello", "hello"])

        mock_post.assert_called_once()
        assert len(mock_post.call_args.kwargs["json"]["requests"]) == 1
        assert len(result) == 3
        assert result[0] == result[1] == result[2] == [0.1, 0.2]

    @patch.object(httpx.Client, "post")
    def test_task_type_in_request(self, mock_post: MagicMock):
        """taskType field is included in the request payload."""
        mock_post.return_value = _mock_gemini_single_response([0.1])

        p = GeminiProvider(api_key="test-key", dimensions=1)
        p.embed_one("test")

        payload = mock_post.call_args.kwargs["json"]
        assert payload["taskType"] == "RETRIEVAL_DOCUMENT"

    @patch.object(httpx.Client, "post")
    def test_set_task_type(self, mock_post: MagicMock):
        """set_task_type switches the taskType for subsequent requests."""
        mock_post.return_value = _mock_gemini_single_response([0.1])

        p = GeminiProvider(api_key="test-key", dimensions=1)
        p.set_task_type("RETRIEVAL_QUERY")
        p.embed_one("search query")

        payload = mock_post.call_args.kwargs["json"]
        assert payload["taskType"] == "RETRIEVAL_QUERY"

    @patch.object(httpx.Client, "post")
    def test_http_error_raises(self, mock_post: MagicMock):
        """Non-retryable HTTP errors propagate."""
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 401
        resp.headers = {}
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=resp
        )
        mock_post.return_value = resp

        p = GeminiProvider(api_key="bad-key")
        with pytest.raises(httpx.HTTPStatusError):
            p.embed_one("hello")

    @patch.object(httpx.Client, "post")
    def test_daily_quota_raises_runtime_error(self, mock_post: MagicMock):
        """retry-after > 3600 signals daily quota exhausted — raise immediately."""
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 429
        resp.headers = {"retry-after": "86400"}
        resp.raise_for_status = MagicMock()
        mock_post.return_value = resp

        p = GeminiProvider(api_key="test-key", inter_request_delay=0.0)
        with pytest.raises(RuntimeError, match="daily quota exhausted"):
            p.embed_one("hello")
