# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
cluster_engine.py — Group related modules into logical clusters.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from os.path import commonprefix

import numpy as np

from ..schema import EdgeType, NodeType, node_id
from ..store import GraphStore

logger = logging.getLogger(__name__)


@dataclass
class ClusterResult:
    """A logical grouping of related modules."""

    cluster_id: int
    label: str
    members: list[str] = field(default_factory=list)
    cohesion: float = 0.0

    def to_dict(self) -> dict:
        return {
            "cluster_id": self.cluster_id,
            "label": self.label,
            "members": self.members,
            "cohesion": self.cohesion,
            "size": len(self.members),
        }


def _kmeans(features: np.ndarray, k: int, max_iter: int = 100) -> np.ndarray:
    """Simple K-Means with fixed seed for reproducibility."""
    rng = np.random.default_rng(42)
    n = len(features)
    if n <= k:
        return np.arange(n)
    indices = rng.choice(n, k, replace=False)
    centroids = features[indices].copy()
    labels = np.zeros(n, dtype=int)
    for _ in range(max_iter):
        dists = np.linalg.norm(features[:, None] - centroids[None], axis=2)
        labels = dists.argmin(axis=1)
        new_centroids = np.array([
            features[labels == i].mean(axis=0) if (labels == i).any() else centroids[i]
            for i in range(k)
        ])
        if np.allclose(centroids, new_centroids):
            break
        centroids = new_centroids
    return labels


def _silhouette(features: np.ndarray, labels: np.ndarray) -> float:
    """Simplified silhouette score."""
    n = len(features)
    if n < 3 or len(set(labels)) < 2:
        return -1.0
    scores: list[float] = []
    for i in range(n):
        same = [j for j in range(n) if labels[j] == labels[i] and j != i]
        if not same:
            scores.append(0.0)
            continue
        a = np.mean([np.linalg.norm(features[i] - features[j]) for j in same])
        b_vals: list[float] = []
        for c in set(labels):
            if c == labels[i]:
                continue
            others = [j for j in range(n) if labels[j] == c]
            if others:
                b_vals.append(np.mean([np.linalg.norm(features[i] - features[j]) for j in others]))
        b = min(b_vals) if b_vals else 0.0
        scores.append((b - a) / max(a, b) if max(a, b) > 0 else 0.0)
    return float(np.mean(scores))


def cluster_modules(
    store: GraphStore,
    n_clusters: int = 0,
) -> list[ClusterResult]:
    """Group MODULE nodes into clusters based on import/export features."""
    modules = store.get_nodes_by_type(NodeType.MODULE)
    if len(modules) < 2:
        return []

    # Build feature vectors
    node_ids: list[str] = []
    features_list: list[list[float]] = []
    packages = sorted({n.node_id.rsplit(".", 1)[0] for n in modules if "." in n.node_id})
    pkg_idx = {p: i for i, p in enumerate(packages)}

    for mod in modules:
        imports_out = len(store.get_edges_from(mod.node_id, EdgeType.IMPORTS))
        defines_out = len(store.get_edges_from(mod.node_id, EdgeType.DEFINES))
        imported_by = len(store.get_edges_to(mod.node_id, EdgeType.IMPORTS))
        vec = [float(imports_out), float(defines_out), float(imported_by)]
        # Package membership binary features
        pkg_vec = [0.0] * len(packages)
        mod_pkg = mod.node_id.rsplit(".", 1)[0] if "." in mod.node_id else ""
        if mod_pkg in pkg_idx:
            pkg_vec[pkg_idx[mod_pkg]] = 1.0
        vec.extend(pkg_vec)
        features_list.append(vec)
        node_ids.append(mod.node_id)

    features = np.array(features_list, dtype=float)

    # Auto-detect k or use provided
    if n_clusters <= 0:
        best_k, best_score = 2, -1.0
        for k in range(2, min(9, len(modules))):
            labels = _kmeans(features, k)
            score = _silhouette(features, labels)
            if score > best_score:
                best_k, best_score = k, score
        n_clusters = best_k

    labels = _kmeans(features, n_clusters)

    # Build results
    clusters: list[ClusterResult] = []
    for cid in range(n_clusters):
        members = [node_ids[i] for i in range(len(node_ids)) if labels[i] == cid]
        if not members:
            continue
        # Auto-label from common prefix
        label = commonprefix(members).rstrip(".")
        if not label:
            label = f"cluster_{cid}"
        # Cohesion: ratio of intra-cluster edges to total possible
        intra_edges = 0
        member_set = set(members)
        for m in members:
            for e in store.get_edges_from(m):
                if e.target_id in member_set:
                    intra_edges += 1
        max_edges = len(members) * (len(members) - 1) if len(members) > 1 else 1
        cohesion = intra_edges / max_edges

        clusters.append(ClusterResult(
            cluster_id=cid, label=label, members=members, cohesion=cohesion,
        ))

    return clusters


def assign_cluster_nodes(store: GraphStore, clusters: list[ClusterResult]) -> int:
    """Create CLUSTER nodes and PART_OF edges in the graph."""
    count = 0
    for cl in clusters:
        cl_nid = node_id(NodeType.CLUSTER, str(cl.cluster_id))
        store.upsert_node(cl_nid, NodeType.CLUSTER, label=cl.label, props={
            "cohesion": cl.cohesion, "size": len(cl.members),
        })
        count += 1
        for member in cl.members:
            store.upsert_edge(member, cl_nid, EdgeType.PART_OF)
            count += 1
    return count
