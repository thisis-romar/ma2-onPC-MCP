# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Abstract embedding interface, zero-vector stub, GitHub Models, OpenRouter, Gemini & Voyage providers."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod

import httpx

from rag.config import (
    DAILY_QUOTA_RETRY_AFTER,
    EMBED_INTER_REQUEST_DELAY,
    EMBED_TIMEOUT,
    GEMINI_EMBED_INTER_REQUEST_DELAY,
    MAX_RETRY_WAIT,
)

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers.

    Implementations must supply model_name, dimensions, embed_one, and embed_many.
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Identifier for the embedding model."""
        ...

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Dimensionality of the embedding vectors."""
        ...

    @abstractmethod
    def embed_one(self, text: str) -> list[float]:
        """Embed a single text string."""
        ...

    @abstractmethod
    def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple text strings."""
        ...


class ZeroVectorProvider(EmbeddingProvider):
    """Stub provider that returns zero vectors. For testing and development."""

    def __init__(self, dimensions: int = 1536) -> None:
        self._dimensions = dimensions

    @property
    def model_name(self) -> str:
        return "zero-vector-stub"

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed_one(self, text: str) -> list[float]:
        return [0.0] * self._dimensions

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * self._dimensions for _ in texts]


class GitHubModelsProvider(EmbeddingProvider):
    """Embedding provider using GitHub Models (OpenAI-compatible endpoint).

    Default model: openai/text-embedding-3-small (1536 dimensions)
    Endpoint: https://models.github.ai/inference
    Auth: GitHub PAT with models:read scope.

    Rate-limit strategy:
    - inter_request_delay: proactive pause between API calls (default 4s)
      keeps throughput at ~15 req/min, avoiding per-minute 429s entirely.
    - batch_size=32: halves API calls vs the old 16 with no quality loss.
    - Dedup: identical texts in a batch are embedded once and reused.
    - Daily quota detection: retry-after > 1h raises immediately with a
      clear "come back tomorrow" message instead of burning retries.
    """

    GITHUB_MODELS_BASE_URL = "https://models.github.ai/inference"

    def __init__(
        self,
        token: str,
        model: str = "openai/text-embedding-3-small",
        dimensions: int = 1536,
        batch_size: int = 32,
        timeout: float = EMBED_TIMEOUT,
        inter_request_delay: float = EMBED_INTER_REQUEST_DELAY,
    ) -> None:
        self._token = token
        self._model = model
        self._dimensions = dimensions
        self._batch_size = batch_size
        self._inter_request_delay = inter_request_delay
        self._client = httpx.Client(
            base_url=self.GITHUB_MODELS_BASE_URL,
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
        )

    def close(self) -> None:
        """Close the underlying HTTP client to release connections."""
        self._client.close()

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed_one(self, text: str) -> list[float]:
        return self.embed_many([text])[0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Embed texts with deduplication, pacing, and retry/backoff."""
        if not texts:
            return []

        # --- Change 4: chunk-level deduplication ---
        # Build ordered list of unique texts and a mapping back to original positions.
        unique_texts: list[str] = []
        unique_index: dict[str, int] = {}
        for text in texts:
            if text not in unique_index:
                unique_index[text] = len(unique_texts)
                unique_texts.append(text)

        dedup_savings = len(texts) - len(unique_texts)
        if dedup_savings:
            logger.info(
                "Dedup: skipped %d duplicate texts (%d unique of %d total)",
                dedup_savings, len(unique_texts), len(texts),
            )

        # Embed unique texts in batches
        unique_embeddings: list[list[float]] = []
        for i in range(0, len(unique_texts), self._batch_size):
            batch = unique_texts[i : i + self._batch_size]
            response = self._request_with_retry(batch)
            body = response.json()
            data = body.get("data")
            if not data:
                raise RuntimeError(
                    f"GitHub Models API returned no 'data' field: {body.get('error', body)}"
                )
            batch_embeddings = [
                item["embedding"]
                for item in sorted(data, key=lambda x: x["index"])
            ]
            unique_embeddings.extend(batch_embeddings)
            logger.debug(
                "Embedded batch %d-%d (%d texts)", i, i + len(batch), len(batch)
            )
            # --- Change 2: proactive inter-request pacing ---
            if self._inter_request_delay > 0 and i + self._batch_size < len(unique_texts):
                time.sleep(self._inter_request_delay)

        # Re-expand to original order (duplicates reuse the cached embedding)
        return [unique_embeddings[unique_index[text]] for text in texts]

    def _request_with_retry(
        self, batch: list[str], max_retries: int = 5
    ) -> httpx.Response:
        """POST embeddings request with pacing, exponential backoff on 429/5xx,
        and immediate failure on daily quota exhaustion."""
        delay = 2.0
        for attempt in range(max_retries + 1):
            try:
                response = self._client.post(
                    "/embeddings",
                    json={"input": batch, "model": self._model},
                )
            except (httpx.RemoteProtocolError, httpx.ReadError, httpx.ConnectError) as exc:
                if attempt == max_retries:
                    raise
                logger.warning(
                    "Network error: %s, retrying in %.1fs (attempt %d/%d)",
                    exc, delay, attempt + 1, max_retries,
                )
                time.sleep(delay)
                delay = min(delay * 2, MAX_RETRY_WAIT)
                continue

            # Log rate-limit headers for observability (run with -v to see)
            rl_headers = {
                k: v for k, v in response.headers.items()
                if k.lower().startswith(("x-ratelimit", "x-ms-", "ratelimit"))
            }
            if rl_headers:
                logger.debug("Rate-limit headers: %s", rl_headers)

            if response.status_code == 429 or response.status_code >= 500:
                retry_after = response.headers.get("retry-after")

                # --- Change 1: detect daily quota vs per-minute limit ---
                if retry_after and float(retry_after) > DAILY_QUOTA_RETRY_AFTER:
                    hours = float(retry_after) / DAILY_QUOTA_RETRY_AFTER
                    raise RuntimeError(
                        f"GitHub Models daily quota exhausted "
                        f"(retry-after={float(retry_after):.0f}s, ~{hours:.1f}h). "
                        f"Resume tomorrow or use --provider zero as fallback."
                    )

                if attempt == max_retries:
                    response.raise_for_status()

                wait = min(float(retry_after), MAX_RETRY_WAIT) if retry_after else delay
                logger.warning(
                    "Rate limited (%d), retrying in %.1fs (attempt %d/%d)",
                    response.status_code, wait, attempt + 1, max_retries,
                )
                time.sleep(wait)
                delay = min(delay * 2, MAX_RETRY_WAIT)
                continue

            response.raise_for_status()
            return response


class OpenRouterProvider(EmbeddingProvider):
    """Embedding provider using OpenRouter (OpenAI-compatible endpoint).

    Default model: nvidia/llama-nemotron-embed-vl-1b-v2:free (2048 dimensions)
    Endpoint: https://openrouter.ai/api/v1
    Auth: OpenRouter API key via Bearer token.

    Rate-limit strategy mirrors GitHubModelsProvider:
    - inter_request_delay: proactive pause between API calls (default 4s)
    - batch_size=32: texts per API call
    - Dedup: identical texts in a batch are embedded once and reused.
    - Daily quota detection: retry-after > 1h raises immediately.
    """

    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        token: str,
        model: str = "nvidia/llama-nemotron-embed-vl-1b-v2:free",
        dimensions: int = 2048,
        batch_size: int = 32,
        timeout: float = EMBED_TIMEOUT,
        inter_request_delay: float = EMBED_INTER_REQUEST_DELAY,
    ) -> None:
        self._token = token
        self._model = model
        self._dimensions = dimensions
        self._batch_size = batch_size
        self._inter_request_delay = inter_request_delay
        self._client = httpx.Client(
            base_url=self.OPENROUTER_BASE_URL,
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
        )

    def close(self) -> None:
        """Close the underlying HTTP client to release connections."""
        self._client.close()

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed_one(self, text: str) -> list[float]:
        return self.embed_many([text])[0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Embed texts with deduplication, pacing, and retry/backoff."""
        if not texts:
            return []

        # Chunk-level deduplication
        unique_texts: list[str] = []
        unique_index: dict[str, int] = {}
        for text in texts:
            if text not in unique_index:
                unique_index[text] = len(unique_texts)
                unique_texts.append(text)

        dedup_savings = len(texts) - len(unique_texts)
        if dedup_savings:
            logger.info(
                "Dedup: skipped %d duplicate texts (%d unique of %d total)",
                dedup_savings, len(unique_texts), len(texts),
            )

        # Embed unique texts in batches
        unique_embeddings: list[list[float]] = []
        for i in range(0, len(unique_texts), self._batch_size):
            batch = unique_texts[i : i + self._batch_size]
            response = self._request_with_retry(batch)
            body = response.json()
            data = body.get("data")
            if not data:
                raise RuntimeError(
                    f"OpenRouter API returned no 'data' field: {body.get('error', body)}"
                )
            batch_embeddings = [
                item["embedding"]
                for item in sorted(data, key=lambda x: x["index"])
            ]
            unique_embeddings.extend(batch_embeddings)
            logger.debug(
                "Embedded batch %d-%d (%d texts)", i, i + len(batch), len(batch)
            )
            if self._inter_request_delay > 0 and i + self._batch_size < len(unique_texts):
                time.sleep(self._inter_request_delay)

        return [unique_embeddings[unique_index[text]] for text in texts]

    def _request_with_retry(
        self, batch: list[str], max_retries: int = 5
    ) -> httpx.Response:
        """POST embeddings request with exponential backoff on 429/5xx."""
        delay = 2.0
        for attempt in range(max_retries + 1):
            try:
                response = self._client.post(
                    "/embeddings",
                    json={"input": batch, "model": self._model},
                )
            except (httpx.RemoteProtocolError, httpx.ReadError, httpx.ConnectError) as exc:
                if attempt == max_retries:
                    raise
                logger.warning(
                    "Network error: %s, retrying in %.1fs (attempt %d/%d)",
                    exc, delay, attempt + 1, max_retries,
                )
                time.sleep(delay)
                delay = min(delay * 2, MAX_RETRY_WAIT)
                continue

            rl_headers = {
                k: v for k, v in response.headers.items()
                if k.lower().startswith(("x-ratelimit", "ratelimit"))
            }
            if rl_headers:
                logger.debug("Rate-limit headers: %s", rl_headers)

            if response.status_code == 429 or response.status_code >= 500:
                retry_after = response.headers.get("retry-after")

                if retry_after and float(retry_after) > DAILY_QUOTA_RETRY_AFTER:
                    hours = float(retry_after) / DAILY_QUOTA_RETRY_AFTER
                    raise RuntimeError(
                        f"OpenRouter daily quota exhausted "
                        f"(retry-after={float(retry_after):.0f}s, ~{hours:.1f}h). "
                        f"Resume tomorrow or use --provider zero as fallback."
                    )

                if attempt == max_retries:
                    response.raise_for_status()

                wait = min(float(retry_after), MAX_RETRY_WAIT) if retry_after else delay
                logger.warning(
                    "Rate limited (%d), retrying in %.1fs (attempt %d/%d)",
                    response.status_code, wait, attempt + 1, max_retries,
                )
                time.sleep(wait)
                delay = min(delay * 2, MAX_RETRY_WAIT)
                continue

            response.raise_for_status()
            return response
        return response  # unreachable, keeps type checker happy


class GeminiProvider(EmbeddingProvider):
    """Embedding provider using Google Gemini gemini-embedding-001.

    Dimensions: 3072 (default)
    Endpoint: https://generativelanguage.googleapis.com/v1beta
    Auth: API key as query parameter.
    MTEB score: 68.32 (#1 on leaderboard as of 2026-04)

    Supports asymmetric search via task_type parameter:
    - RETRIEVAL_DOCUMENT: for indexing/storage (default)
    - RETRIEVAL_QUERY: for search queries

    Rate-limit strategy:
    - inter_request_delay: 1.0s (1,500 RPM free tier is generous)
    - batch_size=100: Gemini batchEmbedContents supports up to 100 items
    - Dedup: identical texts in a batch are embedded once and reused.
    - Daily quota detection: retry-after > 1h raises immediately.
    """

    GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-embedding-001",
        dimensions: int = 3072,
        batch_size: int = 100,
        timeout: float = EMBED_TIMEOUT,
        inter_request_delay: float = GEMINI_EMBED_INTER_REQUEST_DELAY,
        task_type: str = "RETRIEVAL_DOCUMENT",
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._dimensions = dimensions
        self._batch_size = batch_size
        self._inter_request_delay = inter_request_delay
        self._task_type = task_type
        self._client = httpx.Client(
            base_url=self.GEMINI_BASE_URL,
            timeout=timeout,
        )

    def close(self) -> None:
        """Close the underlying HTTP client to release connections."""
        self._client.close()

    def set_task_type(self, task_type: str) -> None:
        """Switch between RETRIEVAL_DOCUMENT and RETRIEVAL_QUERY for asymmetric search."""
        self._task_type = task_type

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed_one(self, text: str) -> list[float]:
        response = self._request_single_with_retry(text)
        body = response.json()
        embedding = body.get("embedding")
        if not embedding:
            raise RuntimeError(
                f"Gemini API returned no 'embedding' field: {body.get('error', body)}"
            )
        return embedding["values"]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Embed texts with deduplication, pacing, and retry/backoff."""
        if not texts:
            return []

        # Chunk-level deduplication
        unique_texts: list[str] = []
        unique_index: dict[str, int] = {}
        for text in texts:
            if text not in unique_index:
                unique_index[text] = len(unique_texts)
                unique_texts.append(text)

        dedup_savings = len(texts) - len(unique_texts)
        if dedup_savings:
            logger.info(
                "Dedup: skipped %d duplicate texts (%d unique of %d total)",
                dedup_savings, len(unique_texts), len(texts),
            )

        # Embed unique texts in batches
        unique_embeddings: list[list[float]] = []
        for i in range(0, len(unique_texts), self._batch_size):
            batch = unique_texts[i : i + self._batch_size]
            response = self._request_batch_with_retry(batch)
            body = response.json()
            embeddings = body.get("embeddings")
            if not embeddings:
                raise RuntimeError(
                    f"Gemini API returned no 'embeddings' field: {body.get('error', body)}"
                )
            # Gemini returns embeddings in request order (no index field)
            batch_embeddings = [item["values"] for item in embeddings]
            unique_embeddings.extend(batch_embeddings)
            logger.debug(
                "Embedded batch %d-%d (%d texts)", i, i + len(batch), len(batch)
            )
            if self._inter_request_delay > 0 and i + self._batch_size < len(unique_texts):
                time.sleep(self._inter_request_delay)

        return [unique_embeddings[unique_index[text]] for text in texts]

    def _build_single_payload(self, text: str) -> dict:
        """Build JSON payload for the single embedContent endpoint."""
        return {
            "model": f"models/{self._model}",
            "content": {"parts": [{"text": text}]},
            "taskType": self._task_type,
        }

    def _build_batch_payload(self, texts: list[str]) -> dict:
        """Build JSON payload for the batchEmbedContents endpoint."""
        return {
            "requests": [
                {
                    "model": f"models/{self._model}",
                    "content": {"parts": [{"text": text}]},
                    "taskType": self._task_type,
                }
                for text in texts
            ],
        }

    def _request_single_with_retry(
        self, text: str, max_retries: int = 5
    ) -> httpx.Response:
        """POST single embedContent request with retry/backoff."""
        url = f"/models/{self._model}:embedContent"
        payload = self._build_single_payload(text)
        return self._do_request(url, payload, max_retries)

    def _request_batch_with_retry(
        self, batch: list[str], max_retries: int = 5
    ) -> httpx.Response:
        """POST batchEmbedContents request with retry/backoff."""
        url = f"/models/{self._model}:batchEmbedContents"
        payload = self._build_batch_payload(batch)
        return self._do_request(url, payload, max_retries)

    def _do_request(
        self, url: str, payload: dict, max_retries: int
    ) -> httpx.Response:
        """Execute an HTTP request with exponential backoff on 429/5xx."""
        delay = 2.0
        for attempt in range(max_retries + 1):
            try:
                response = self._client.post(
                    url,
                    json=payload,
                    params={"key": self._api_key},
                )
            except (httpx.RemoteProtocolError, httpx.ReadError, httpx.ConnectError) as exc:
                if attempt == max_retries:
                    raise
                logger.warning(
                    "Network error: %s, retrying in %.1fs (attempt %d/%d)",
                    exc, delay, attempt + 1, max_retries,
                )
                time.sleep(delay)
                delay = min(delay * 2, MAX_RETRY_WAIT)
                continue

            if response.status_code == 429 or response.status_code >= 500:
                retry_after = response.headers.get("retry-after")

                if retry_after and float(retry_after) > DAILY_QUOTA_RETRY_AFTER:
                    hours = float(retry_after) / DAILY_QUOTA_RETRY_AFTER
                    raise RuntimeError(
                        f"Gemini daily quota exhausted "
                        f"(retry-after={float(retry_after):.0f}s, ~{hours:.1f}h). "
                        f"Resume tomorrow or use --provider zero as fallback."
                    )

                if attempt == max_retries:
                    response.raise_for_status()

                wait = min(float(retry_after), MAX_RETRY_WAIT) if retry_after else delay
                logger.warning(
                    "Rate limited (%d), retrying in %.1fs (attempt %d/%d)",
                    response.status_code, wait, attempt + 1, max_retries,
                )
                time.sleep(wait)
                delay = min(delay * 2, MAX_RETRY_WAIT)
                continue

            response.raise_for_status()
            return response
        return response  # unreachable, keeps type checker happy


class VoyageProvider(EmbeddingProvider):
    """Embedding provider using Voyage AI voyage-4.

    Dimensions: 1024 (default), supports 256/512/1024/2048
    MTEB: ~67
    Free tier: 200M tokens (one-time)
    Endpoint: https://api.voyageai.com/v1/embeddings
    Auth: Bearer token.

    Rate-limit strategy:
    - inter_request_delay: 1.0s (2,000 RPM free tier is generous)
    - batch_size=128: API supports up to 1,000 items, 320K tokens/request
    - Dedup: identical texts in a batch are embedded once and reused.
    - Daily quota detection: retry-after > 1h raises immediately.
    """

    VOYAGE_BASE_URL = "https://api.voyageai.com/v1"

    def __init__(
        self,
        token: str,
        model: str = "voyage-4",
        dimensions: int = 1024,
        batch_size: int = 128,
        timeout: float = EMBED_TIMEOUT,
        inter_request_delay: float = 1.0,
        input_type: str = "document",
    ) -> None:
        self._token = token
        self._model = model
        self._dimensions = dimensions
        self._batch_size = batch_size
        self._inter_request_delay = inter_request_delay
        self._input_type = input_type
        self._client = httpx.Client(
            base_url=self.VOYAGE_BASE_URL,
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
        )

    def close(self) -> None:
        """Close the underlying HTTP client to release connections."""
        self._client.close()

    def set_input_type(self, input_type: str) -> None:
        """Switch between 'document' (indexing) and 'query' (search) for asymmetric search."""
        self._input_type = input_type

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed_one(self, text: str) -> list[float]:
        return self.embed_many([text])[0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Embed texts with deduplication, pacing, and retry/backoff."""
        if not texts:
            return []

        # Chunk-level deduplication
        unique_texts: list[str] = []
        unique_index: dict[str, int] = {}
        for text in texts:
            if text not in unique_index:
                unique_index[text] = len(unique_texts)
                unique_texts.append(text)

        dedup_savings = len(texts) - len(unique_texts)
        if dedup_savings:
            logger.info(
                "Dedup: skipped %d duplicate texts (%d unique of %d total)",
                dedup_savings, len(unique_texts), len(texts),
            )

        # Embed unique texts in batches
        unique_embeddings: list[list[float]] = []
        for i in range(0, len(unique_texts), self._batch_size):
            batch = unique_texts[i : i + self._batch_size]
            response = self._request_with_retry(batch)
            body = response.json()
            data = body.get("data")
            if not data:
                raise RuntimeError(
                    f"Voyage API returned no 'data' field: {body.get('error', body)}"
                )
            batch_embeddings = [
                item["embedding"]
                for item in sorted(data, key=lambda x: x["index"])
            ]
            unique_embeddings.extend(batch_embeddings)
            logger.debug(
                "Embedded batch %d-%d (%d texts)", i, i + len(batch), len(batch)
            )
            if self._inter_request_delay > 0 and i + self._batch_size < len(unique_texts):
                time.sleep(self._inter_request_delay)

        return [unique_embeddings[unique_index[text]] for text in texts]

    def _request_with_retry(
        self, batch: list[str], max_retries: int = 5
    ) -> httpx.Response:
        """POST embeddings request with exponential backoff on 429/5xx."""
        delay = 2.0
        for attempt in range(max_retries + 1):
            try:
                response = self._client.post(
                    "/embeddings",
                    json={
                        "input": batch,
                        "model": self._model,
                        "input_type": self._input_type,
                        "output_dimension": self._dimensions,
                    },
                )
            except (httpx.RemoteProtocolError, httpx.ReadError, httpx.ConnectError) as exc:
                if attempt == max_retries:
                    raise
                logger.warning(
                    "Network error: %s, retrying in %.1fs (attempt %d/%d)",
                    exc, delay, attempt + 1, max_retries,
                )
                time.sleep(delay)
                delay = min(delay * 2, MAX_RETRY_WAIT)
                continue

            rl_headers = {
                k: v for k, v in response.headers.items()
                if k.lower().startswith(("x-ratelimit", "ratelimit"))
            }
            if rl_headers:
                logger.debug("Rate-limit headers: %s", rl_headers)

            if response.status_code == 429 or response.status_code >= 500:
                retry_after = response.headers.get("retry-after")

                if retry_after and float(retry_after) > DAILY_QUOTA_RETRY_AFTER:
                    hours = float(retry_after) / DAILY_QUOTA_RETRY_AFTER
                    raise RuntimeError(
                        f"Voyage daily quota exhausted "
                        f"(retry-after={float(retry_after):.0f}s, ~{hours:.1f}h). "
                        f"Resume tomorrow or use --provider zero as fallback."
                    )

                if attempt == max_retries:
                    response.raise_for_status()

                wait = min(float(retry_after), MAX_RETRY_WAIT) if retry_after else delay
                logger.warning(
                    "Rate limited (%d), retrying in %.1fs (attempt %d/%d)",
                    response.status_code, wait, attempt + 1, max_retries,
                )
                time.sleep(wait)
                delay = min(delay * 2, MAX_RETRY_WAIT)
                continue

            response.raise_for_status()
            return response
        return response  # unreachable, keeps type checker happy
