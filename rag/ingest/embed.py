"""Abstract embedding interface, zero-vector stub, and GitHub Models provider."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import httpx

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

    def __init__(self, dimensions: int = 384) -> None:
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
    """

    GITHUB_MODELS_BASE_URL = "https://models.github.ai/inference"

    def __init__(
        self,
        token: str,
        model: str = "openai/text-embedding-3-small",
        dimensions: int = 1536,
        batch_size: int = 64,
        timeout: float = 60.0,
    ) -> None:
        self._token = token
        self._model = model
        self._dimensions = dimensions
        self._batch_size = batch_size
        self._client = httpx.Client(
            base_url=self.GITHUB_MODELS_BASE_URL,
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
        )

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed_one(self, text: str) -> list[float]:
        return self.embed_many([text])[0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]
            response = self._client.post(
                "/embeddings",
                json={"input": batch, "model": self._model},
            )
            response.raise_for_status()
            data = response.json()["data"]
            batch_embeddings = [
                item["embedding"]
                for item in sorted(data, key=lambda x: x["index"])
            ]
            all_embeddings.extend(batch_embeddings)
            logger.debug(
                "Embedded batch %d-%d (%d texts)", i, i + len(batch), len(batch)
            )
        return all_embeddings
