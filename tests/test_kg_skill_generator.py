# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for the knowledge graph skill generator."""

from __future__ import annotations

import pytest

from src.knowledge_graph.analysis.skill_generator import (
    SkillSuggestion,
    generate_all_skills,
    generate_skill_for_cluster,
)
from src.knowledge_graph.schema import EdgeType, NodeType
from src.knowledge_graph.store import GraphStore


@pytest.fixture()
def store():
    """Create an in-memory GraphStore with test data."""
    s = GraphStore(":memory:")
    s.initialize()
    return s


def _seed_cluster(store: GraphStore, cluster_id: str, label: str, members: int = 3):
    """Seed a cluster with member modules and symbols."""
    store.upsert_node(cluster_id, NodeType.CLUSTER, label=label, props={"size": members})
    for i in range(members):
        mod_id = f"module:{label}.mod{i}"
        store.upsert_node(mod_id, NodeType.MODULE, label=f"{label}.mod{i}")
        store.upsert_edge(mod_id, cluster_id, EdgeType.PART_OF)
        # Add symbols for each module
        for j in range(2):
            sym_id = f"symbol:{label}.mod{i}.func{j}"
            store.upsert_node(sym_id, NodeType.SYMBOL, label=f"func{j}")
            store.upsert_edge(mod_id, sym_id, EdgeType.DEFINES)


class TestGenerateSkillForCluster:
    def test_valid_cluster(self, store):
        _seed_cluster(store, "cluster:nav", "navigation", members=3)
        result = generate_skill_for_cluster(store, "cluster:nav")

        assert result is not None
        assert isinstance(result, SkillSuggestion)
        assert "navigation" in result.name
        assert "navigation" in result.description
        assert "navigation" in result.body
        assert result.source_cluster == "cluster:nav"
        assert result.confidence > 0.0

    def test_nonexistent_cluster_returns_none(self, store):
        result = generate_skill_for_cluster(store, "cluster:does_not_exist")
        assert result is None

    def test_empty_cluster_returns_none(self, store):
        # Cluster node exists but has no PART_OF edges pointing to it
        store.upsert_node("cluster:empty", NodeType.CLUSTER, label="empty", props={"size": 0})
        result = generate_skill_for_cluster(store, "cluster:empty")
        assert result is None

    def test_safety_scope_defaults_to_safe_read(self, store):
        _seed_cluster(store, "cluster:tools", "tools", members=2)
        result = generate_skill_for_cluster(store, "cluster:tools")
        assert result is not None
        assert result.safety_scope == "SAFE_READ"

    def test_confidence_scales_with_members(self, store):
        _seed_cluster(store, "cluster:small", "small", members=1)
        _seed_cluster(store, "cluster:large", "large", members=5)

        small = generate_skill_for_cluster(store, "cluster:small")
        large = generate_skill_for_cluster(store, "cluster:large")

        assert small is not None and large is not None
        assert small.confidence < large.confidence
        assert large.confidence == 1.0  # 5/5 = 1.0

    def test_body_contains_module_names(self, store):
        _seed_cluster(store, "cluster:cmds", "commands", members=2)
        result = generate_skill_for_cluster(store, "cluster:cmds")
        assert result is not None
        assert "commands.mod0" in result.body
        assert "commands.mod1" in result.body

    def test_body_contains_symbol_names(self, store):
        _seed_cluster(store, "cluster:sym", "sym_test", members=1)
        result = generate_skill_for_cluster(store, "cluster:sym")
        assert result is not None
        assert "func0" in result.body
        assert "func1" in result.body

    def test_applicable_context_is_label(self, store):
        _seed_cluster(store, "cluster:ctx", "my_context", members=2)
        result = generate_skill_for_cluster(store, "cluster:ctx")
        assert result is not None
        assert result.applicable_context == "my_context"


class TestSkillSuggestionToDict:
    def test_to_dict_keys(self):
        s = SkillSuggestion(
            name="test-skill",
            description="A test skill",
            body="# Test\nBody content",
            applicable_context="testing",
            safety_scope="SAFE_READ",
            source_cluster="cluster:test",
            confidence=0.8,
        )
        d = s.to_dict()
        assert set(d.keys()) == {
            "name", "description", "body", "applicable_context",
            "safety_scope", "source_cluster", "confidence",
        }
        assert d["name"] == "test-skill"
        assert d["confidence"] == 0.8
        assert d["safety_scope"] == "SAFE_READ"
        assert d["source_cluster"] == "cluster:test"

    def test_to_dict_defaults(self):
        s = SkillSuggestion(
            name="n", description="d", body="b", applicable_context="c",
        )
        d = s.to_dict()
        assert d["safety_scope"] == "SAFE_READ"
        assert d["source_cluster"] == ""
        assert d["confidence"] == 0.0


class TestGenerateAllSkills:
    def test_generates_for_large_clusters_only(self, store):
        _seed_cluster(store, "cluster:big", "big", members=3)
        # Small cluster with 1 member — below default min_cluster_size=2
        store.upsert_node("cluster:tiny", NodeType.CLUSTER, label="tiny", props={"size": 1})
        mod_id = "module:tiny.mod0"
        store.upsert_node(mod_id, NodeType.MODULE, label="tiny.mod0")
        store.upsert_edge(mod_id, "cluster:tiny", EdgeType.PART_OF)

        results = generate_all_skills(store, min_cluster_size=2)
        assert len(results) == 1
        assert results[0].source_cluster == "cluster:big"

    def test_returns_empty_when_no_clusters(self, store):
        results = generate_all_skills(store)
        assert results == []

    def test_custom_min_cluster_size(self, store):
        _seed_cluster(store, "cluster:a", "a", members=2)
        _seed_cluster(store, "cluster:b", "b", members=4)

        results = generate_all_skills(store, min_cluster_size=3)
        assert len(results) == 1
        assert results[0].source_cluster == "cluster:b"
