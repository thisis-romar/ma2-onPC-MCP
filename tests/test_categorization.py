"""Tests for the ML-based tool categorization system.

Covers feature extraction, K-Means clustering, silhouette scoring,
label generation, taxonomy I/O, and MCP tool wrappers.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest

from src.categorization.clustering import (
    combine_features,
    cosine_similarity,
    euclidean_distance,
    find_optimal_k,
    kmeans,
    kmeans_plus_plus,
    normalize_minmax,
    silhouette_samples,
    silhouette_score,
)
from src.categorization.features import (
    ToolFeatures,
    extract_tool_features,
)
from src.categorization.labeling import generate_labels
from src.categorization.taxonomy import (
    get_feature_matrix,
    get_tools_by_category,
    load_taxonomy,
    save_taxonomy,
)

# Path to the real server.py
SERVER_PATH = Path(__file__).resolve().parent.parent / "src" / "server.py"


# ===========================================================================
# Feature Extraction Tests
# ===========================================================================


class TestFeatureExtraction:
    """Tests for AST-based feature extraction from server.py."""

    def test_extract_features_finds_tools(self):
        """AST extraction should find MCP tools from server.py."""
        tools = extract_tool_features(str(SERVER_PATH))
        # The project has 78+ tools; we just verify we get a substantial count
        assert len(tools) >= 70, f"Expected ≥70 tools, got {len(tools)}"

    def test_extract_features_names_unique(self):
        tools = extract_tool_features(str(SERVER_PATH))
        names = [t.name for t in tools]
        assert len(names) == len(set(names)), "Tool names must be unique"

    def test_extract_features_detects_destructive(self):
        """Tools with confirm_destructive param should be flagged."""
        tools = extract_tool_features(str(SERVER_PATH))
        destructive_tools = [t for t in tools if t.has_confirm_destructive]
        assert len(destructive_tools) >= 5, (
            f"Expected ≥5 destructive tools, got {len(destructive_tools)}"
        )
        # All destructive-param tools should have DESTRUCTIVE risk tier
        for t in destructive_tools:
            assert t.risk_tier == "DESTRUCTIVE", (
                f"{t.name} has confirm_destructive but risk_tier={t.risk_tier}"
            )

    def test_extract_features_docstrings_not_empty(self):
        tools = extract_tool_features(str(SERVER_PATH))
        for t in tools:
            assert t.docstring, f"Tool {t.name} has empty docstring"

    def test_extract_features_known_tools(self):
        """Spot-check that well-known tools are found."""
        tools = extract_tool_features(str(SERVER_PATH))
        names = {t.name for t in tools}
        for expected in [
            "send_raw_command",
            "set_intensity",
            "playback_action",
            "navigate_console",
            "search_codebase",
            "list_tool_categories",
        ]:
            assert expected in names, f"Missing expected tool: {expected}"

    def test_structural_vector_dimensions(self):
        tools = extract_tool_features(str(SERVER_PATH))
        expected_dim = ToolFeatures.structural_dim()
        for t in tools:
            vec = t.to_structural_vector()
            assert len(vec) == expected_dim, (
                f"{t.name}: vector dim {len(vec)} != expected {expected_dim}"
            )

    def test_structural_vector_values_in_range(self):
        """All binary/one-hot features should be 0 or 1; scalars ≥ 0."""
        tools = extract_tool_features(str(SERVER_PATH))
        for t in tools:
            vec = t.to_structural_vector()
            # First 8 dims are binary/one-hot
            for i in range(8):
                assert vec[i] in (0.0, 1.0), f"{t.name}[{i}]={vec[i]} not binary"
            # Param counts >= 0
            assert vec[8] >= 0
            assert vec[9] >= 0

    def test_safe_read_tools_detected(self):
        tools = extract_tool_features(str(SERVER_PATH))
        safe_read = [t for t in tools if t.risk_tier == "SAFE_READ"]
        assert len(safe_read) >= 3, f"Expected ≥3 SAFE_READ tools, got {len(safe_read)}"


# ===========================================================================
# K-Means Tests
# ===========================================================================


class TestKMeans:
    """Tests for K-Means clustering implementation."""

    def _make_blobs(self, n_per_cluster=30, k=3, d=2, seed=42):
        """Create well-separated Gaussian blobs for testing."""
        rng = np.random.default_rng(seed)
        centers = np.array([[i * 10, i * 10] for i in range(k)], dtype=np.float64)
        if d > 2:
            centers = np.hstack([centers, np.zeros((k, d - 2))])
        X = np.vstack([
            rng.normal(loc=centers[i], scale=0.5, size=(n_per_cluster, d))
            for i in range(k)
        ])
        true_labels = np.repeat(np.arange(k), n_per_cluster)
        return X, true_labels

    def test_kmeans_convergence(self):
        """K-Means should converge on well-separated blobs."""
        X, _ = self._make_blobs(k=3)
        labels, centroids, inertia = kmeans(X, 3)
        assert labels.shape == (90,)
        assert centroids.shape == (3, 2)
        assert inertia >= 0
        # Check that we get 3 distinct clusters
        assert len(np.unique(labels)) == 3

    def test_kmeans_plus_plus_distinct(self):
        """k-means++ should pick k distinct initial centroids."""
        X, _ = self._make_blobs(k=4)
        centroids = kmeans_plus_plus(X, 4, rng=np.random.default_rng(42))
        assert centroids.shape == (4, 2)
        # All centroids should be distinct
        for i in range(4):
            for j in range(i + 1, 4):
                assert not np.allclose(centroids[i], centroids[j]), (
                    f"Centroids {i} and {j} are identical"
                )

    def test_kmeans_single_cluster(self):
        """k=1 should assign all points to cluster 0."""
        X, _ = self._make_blobs(k=1, n_per_cluster=20)
        labels, centroids, _ = kmeans(X, 1)
        assert np.all(labels == 0)
        assert centroids.shape == (1, 2)

    def test_kmeans_k_equals_n(self):
        """When k == n, each point is its own cluster."""
        X = np.array([[0, 0], [10, 10], [20, 20]], dtype=np.float64)
        labels, centroids, inertia = kmeans(X, 3)
        assert len(np.unique(labels)) == 3
        assert inertia < 1e-6  # near-zero inertia

    def test_kmeans_raises_on_k_gt_n(self):
        X = np.array([[0, 0], [1, 1]], dtype=np.float64)
        with pytest.raises(ValueError, match="k=5 exceeds"):
            kmeans(X, 5)


# ===========================================================================
# Silhouette Tests
# ===========================================================================


class TestSilhouette:
    """Tests for silhouette coefficient computation."""

    def test_silhouette_perfect_clusters(self):
        """Well-separated clusters should have silhouette near 1.0."""
        rng = np.random.default_rng(42)
        X = np.vstack([
            rng.normal(loc=[0, 0], scale=0.1, size=(30, 2)),
            rng.normal(loc=[100, 100], scale=0.1, size=(30, 2)),
        ])
        labels = np.array([0] * 30 + [1] * 30, dtype=np.int64)
        score = silhouette_score(X, labels)
        assert score > 0.9, f"Expected >0.9 for perfect clusters, got {score:.4f}"

    def test_silhouette_random_labels(self):
        """Random labels on structured data should have low silhouette."""
        rng = np.random.default_rng(42)
        X = rng.normal(size=(60, 2))
        labels = rng.integers(0, 3, size=60).astype(np.int64)
        score = silhouette_score(X, labels)
        assert -0.5 < score < 0.5, f"Expected near 0 for random labels, got {score:.4f}"

    def test_silhouette_single_cluster(self):
        """Single cluster should return 0."""
        X = np.random.default_rng(42).normal(size=(20, 2))
        labels = np.zeros(20, dtype=np.int64)
        score = silhouette_score(X, labels)
        assert score == 0.0

    def test_silhouette_samples_shape(self):
        X = np.random.default_rng(42).normal(size=(20, 2))
        labels = np.array([0] * 10 + [1] * 10, dtype=np.int64)
        samples = silhouette_samples(X, labels)
        assert samples.shape == (20,)


# ===========================================================================
# Optimal-k Tests
# ===========================================================================


class TestOptimalK:
    def test_find_optimal_k(self):
        """find_optimal_k should return the k with highest silhouette."""
        rng = np.random.default_rng(42)
        # Create 4 well-separated clusters
        X = np.vstack([
            rng.normal(loc=[i * 20, i * 20], scale=0.5, size=(20, 2))
            for i in range(4)
        ])
        best_k, scores = find_optimal_k(X, k_range=range(2, 7))
        assert best_k in scores
        assert scores[best_k] == max(scores.values())
        # With well-separated clusters, optimal k should be 4
        assert best_k == 4, f"Expected k=4, got k={best_k}"

    def test_find_optimal_k_returns_all_scores(self):
        X = np.random.default_rng(42).normal(size=(30, 2))
        _, scores = find_optimal_k(X, k_range=range(2, 6))
        assert set(scores.keys()) == {2, 3, 4, 5}


# ===========================================================================
# Feature Combination Tests
# ===========================================================================


class TestFeatureCombination:
    def test_normalize_minmax(self):
        X = np.array([[1, 10], [5, 50], [3, 30]], dtype=np.float64)
        normed = normalize_minmax(X)
        assert normed.min() == 0.0
        assert normed.max() == 1.0

    def test_normalize_constant_column(self):
        """Constant columns should not cause division by zero."""
        X = np.array([[5, 1], [5, 2], [5, 3]], dtype=np.float64)
        normed = normalize_minmax(X)
        assert not np.any(np.isnan(normed))
        # Constant column maps to 0
        assert np.allclose(normed[:, 0], 0.0)

    def test_combine_features_zero_embeddings(self):
        """With zero embeddings, should return structural only."""
        structural = np.ones((5, 10), dtype=np.float64)
        embeddings = np.zeros((5, 384), dtype=np.float64)
        combined = combine_features(structural, embeddings, alpha=0.4)
        # Should drop embeddings and return structural
        assert combined.shape == (5, 10)

    def test_combine_features_with_embeddings(self):
        structural = np.ones((5, 10), dtype=np.float64)
        embeddings = np.ones((5, 384), dtype=np.float64)
        combined = combine_features(structural, embeddings, alpha=0.4)
        assert combined.shape == (5, 10 + 384)

    def test_cosine_similarity_identical(self):
        a = np.array([1.0, 2.0, 3.0])
        assert cosine_similarity(a, a) == pytest.approx(1.0)

    def test_cosine_similarity_orthogonal(self):
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 1.0])
        assert cosine_similarity(a, b) == pytest.approx(0.0)

    def test_euclidean_distance(self):
        a = np.array([0.0, 0.0])
        b = np.array([3.0, 4.0])
        assert euclidean_distance(a, b) == pytest.approx(5.0)


# ===========================================================================
# Label Generation Tests
# ===========================================================================


class TestLabeling:
    def test_generate_labels_unique(self):
        """All generated labels should be unique strings."""
        tools = [
            ToolFeatures(name=f"tool_{i}", action_verbs=["list"], risk_tier="SAFE_READ")
            for i in range(10)
        ]
        labels = np.array([0, 0, 0, 1, 1, 1, 2, 2, 2, 2], dtype=np.int64)
        result = generate_labels(tools, labels)
        assert len(result) == 3
        assert len(set(result.values())) == 3, "Labels should be unique"

    def test_generate_labels_playback(self):
        tools = [
            ToolFeatures(name="go", action_verbs=["go", "goto"], command_modules=["playback"]),
            ToolFeatures(name="go_back", action_verbs=["go"], command_modules=["playback"]),
        ]
        labels = np.array([0, 0], dtype=np.int64)
        result = generate_labels(tools, labels)
        assert "Playback" in result[0]

    def test_generate_labels_empty_cluster(self):
        tools = [ToolFeatures(name="t1", action_verbs=["list"])]
        labels = np.array([0], dtype=np.int64)
        result = generate_labels(tools, labels)
        assert 0 in result

    def test_generate_labels_disambiguation(self):
        """When two clusters have the same dominant label, they get disambiguated."""
        tools = [
            ToolFeatures(name="list_a", action_verbs=["list", "info"], risk_tier="SAFE_READ"),
            ToolFeatures(name="list_b", action_verbs=["list", "info"], risk_tier="SAFE_READ"),
            ToolFeatures(name="list_c", action_verbs=["list", "info"], risk_tier="SAFE_READ", command_modules=["info"]),
            ToolFeatures(name="list_d", action_verbs=["list", "info"], risk_tier="SAFE_READ", command_modules=["variables"]),
        ]
        labels = np.array([0, 0, 1, 1], dtype=np.int64)
        result = generate_labels(tools, labels)
        assert len(set(result.values())) == 2, "Disambiguated labels should be unique"


# ===========================================================================
# Taxonomy I/O Tests
# ===========================================================================


class TestTaxonomy:
    def _sample_taxonomy(self) -> dict:
        return {
            "metadata": {
                "tool_count": 3,
                "k": 2,
                "silhouette_score": 0.5,
                "embedding_provider": "zero",
            },
            "categories": {
                "Playback": {
                    "id": 0,
                    "tool_count": 2,
                    "dominant_features": ["go"],
                    "tools": [
                        {"name": "playback_action", "confidence": 0.9},
                        {"name": "execute_sequence", "confidence": 0.8},
                    ],
                },
                "Queries": {
                    "id": 1,
                    "tool_count": 1,
                    "dominant_features": ["list"],
                    "tools": [{"name": "list_shows", "confidence": 1.0}],
                },
            },
            "tool_features": {
                "playback_action": {
                    "structural": [1.0, 0.0, 0.0],
                    "embedding": [0.1, 0.2],
                    "docstring_summary": "Execute playback",
                },
                "execute_sequence": {
                    "structural": [0.8, 0.1, 0.0],
                    "embedding": [0.1, 0.3],
                    "docstring_summary": "Execute sequence",
                },
                "list_shows": {
                    "structural": [0.0, 1.0, 0.0],
                    "embedding": [0.5, 0.0],
                    "docstring_summary": "List shows",
                },
            },
        }

    def test_taxonomy_roundtrip(self):
        """save → load should produce equivalent structure."""
        orig = self._sample_taxonomy()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        save_taxonomy(
            path,
            metadata=orig["metadata"],
            categories=orig["categories"],
            tool_features=orig["tool_features"],
        )
        loaded = load_taxonomy(path)

        assert loaded["metadata"]["tool_count"] == 3
        assert loaded["metadata"]["k"] == 2
        assert "Playback" in loaded["categories"]
        assert "Queries" in loaded["categories"]
        assert "generated_at" in loaded["metadata"]

    def test_taxonomy_schema(self):
        """Output JSON should have required top-level keys."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        save_taxonomy(
            path,
            metadata={"tool_count": 1, "k": 1},
            categories={"Cat1": {"id": 0, "tool_count": 1, "tools": []}},
            tool_features={"tool1": {"structural": [0.0], "embedding": [], "docstring_summary": ""}},
        )
        loaded = load_taxonomy(path)
        assert "metadata" in loaded
        assert "categories" in loaded
        assert "tool_features" in loaded

    def test_get_tools_by_category_all(self):
        taxonomy = self._sample_taxonomy()
        result = get_tools_by_category(taxonomy)
        assert len(result) == 2
        assert "Playback" in result
        assert "Queries" in result

    def test_get_tools_by_category_filter(self):
        taxonomy = self._sample_taxonomy()
        result = get_tools_by_category(taxonomy, "play")
        assert len(result) == 1
        assert "Playback" in result

    def test_get_tools_by_category_no_match(self):
        taxonomy = self._sample_taxonomy()
        result = get_tools_by_category(taxonomy, "nonexistent")
        assert len(result) == 0

    def test_get_feature_matrix(self):
        taxonomy = self._sample_taxonomy()
        names, matrix = get_feature_matrix(taxonomy)
        assert len(names) == 3
        assert matrix.shape[0] == 3
        # structural (3) + embedding (2) = 5 dims
        assert matrix.shape[1] == 5


# ===========================================================================
# End-to-End Pipeline Test
# ===========================================================================


class TestFullPipeline:
    def test_full_pipeline_zero_vector(self):
        """End-to-end: extract → embed(zero) → cluster → taxonomy."""
        # Extract features
        tools = extract_tool_features(str(SERVER_PATH))
        assert len(tools) >= 70

        # Build structural matrix
        structural = np.array([t.to_structural_vector() for t in tools], dtype=np.float64)
        structural_norm = normalize_minmax(structural)

        # Zero-vector embeddings
        n = len(tools)
        dim = 384
        embeddings = np.zeros((n, dim), dtype=np.float64)

        # Combine (should drop zero embeddings)
        combined = combine_features(structural_norm, embeddings, alpha=0.4)
        assert combined.shape[0] == n

        # Cluster
        best_k, scores = find_optimal_k(combined, k_range=range(3, 10))
        assert best_k >= 3
        labels, centroids, inertia = kmeans(combined, best_k)
        assert len(np.unique(labels)) == best_k

        # Labels
        cluster_labels = generate_labels(tools, labels)
        assert len(cluster_labels) == best_k
        assert len(set(cluster_labels.values())) == best_k  # unique

        # Taxonomy roundtrip
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        categories: dict[str, dict] = {}
        for cid, label in cluster_labels.items():
            cluster_tools = [t for t, lbl in zip(tools, labels, strict=False) if int(lbl) == cid]
            categories[label] = {
                "id": cid,
                "tool_count": len(cluster_tools),
                "dominant_features": [],
                "tools": [{"name": t.name, "confidence": 1.0} for t in cluster_tools],
            }

        tool_features_dict = {
            t.name: {
                "structural": structural_norm[i].tolist(),
                "embedding": embeddings[i].tolist(),
                "docstring_summary": t.docstring.split("\n")[0][:100],
            }
            for i, t in enumerate(tools)
        }

        save_taxonomy(
            path,
            metadata={"tool_count": n, "k": best_k, "silhouette_score": silhouette_score(combined, labels)},
            categories=categories,
            tool_features=tool_features_dict,
        )

        loaded = load_taxonomy(path)
        assert loaded["metadata"]["tool_count"] == n
        assert len(loaded["categories"]) == best_k
        assert len(loaded["tool_features"]) == n

        # Verify every tool appears in exactly one category
        all_tools_in_cats = set()
        for cat in loaded["categories"].values():
            for t in cat["tools"]:
                assert t["name"] not in all_tools_in_cats, f"Duplicate: {t['name']}"
                all_tools_in_cats.add(t["name"])
        assert all_tools_in_cats == {t.name for t in tools}
