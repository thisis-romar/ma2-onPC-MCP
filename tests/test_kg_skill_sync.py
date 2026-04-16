# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for knowledge graph skill sync."""

from __future__ import annotations

import time

import pytest

from src.knowledge_graph.planning import PlanningQueries
from src.knowledge_graph.schema import EdgeType, NodeType, node_id
from src.knowledge_graph.skill_sync import sync_skills
from src.knowledge_graph.store import GraphStore
from src.skill import Skill, SkillRegistry


@pytest.fixture
def store():
    """Create an in-memory GraphStore for testing."""
    s = GraphStore(":memory:")
    s.initialize()
    yield s
    s.close()


@pytest.fixture
def registry(tmp_path):
    """Create a SkillRegistry backed by a temp DB."""
    db = tmp_path / "test_skills.db"
    reg = SkillRegistry(db_path=db)
    yield reg
    reg.close()


def _make_skill(
    *,
    id: str = "sk-1",
    name: str = "wash_look_blue",
    version: int = 1,
    parent_id: str | None = None,
    description: str = "Create a blue wash look",
    body: str = "## Steps\n1. Select group\n2. Set color",
    quality_score: float = 0.8,
    safety_scope: str = "SAFE_WRITE",
    applicable_context: str = "color wash blue",
    approved: bool = True,
    deprecated: bool = False,
) -> Skill:
    now = time.time()
    return Skill(
        id=id,
        version=version,
        parent_id=parent_id,
        name=name,
        description=description,
        body=body,
        quality_score=quality_score,
        safety_scope=safety_scope,
        applicable_context=applicable_context,
        created_at=now,
        updated_at=now,
        source_session_id="sess-001",
        approved=approved,
        deprecated=deprecated,
    )


class TestSyncSkills:
    def _baseline_count(self, store, registry):
        """Return the number of skill nodes created from filesystem skills."""
        sync_skills(store, registry)
        count = store.node_count(NodeType.SKILL)
        store.delete_nodes_by_type(NodeType.SKILL)
        return count

    def test_basic_sync_creates_nodes(self, store, registry):
        """Skills from registry are synced as SKILL nodes."""
        baseline = self._baseline_count(store, registry)

        sk = _make_skill()
        registry.save(sk)

        counts = sync_skills(store, registry)
        assert counts["nodes"] == baseline + 1
        assert store.node_count(NodeType.SKILL) == baseline + 1

        # Verify the node
        nid = node_id(NodeType.SKILL, "sk-1")
        node = store.get_node(nid)
        assert node is not None
        assert node.label == "wash_look_blue"
        assert node.node_type == "skill"

    def test_skill_props_stored(self, store, registry):
        """Skill properties are stored in node props."""
        sk = _make_skill(quality_score=0.9, safety_scope="DESTRUCTIVE", approved=False)
        registry.save(sk)

        sync_skills(store, registry)
        nid = node_id(NodeType.SKILL, "sk-1")
        node = store.get_node(nid)
        assert node is not None
        assert node.props["version"] == 1
        assert node.props["quality_score"] == 0.9
        assert node.props["safety_scope"] == "DESTRUCTIVE"
        assert node.props["approved"] is False
        assert node.props["applicable_context"] == "color wash blue"

    def test_lineage_edge_created(self, store, registry):
        """Parent-child lineage creates IMPROVES_UPON edges."""
        parent = _make_skill(id="sk-parent", name="wash_v1")
        child = _make_skill(id="sk-child", name="wash_v2", version=2, parent_id="sk-parent")
        registry.save(parent)
        registry.save(child)

        counts = sync_skills(store, registry)
        assert counts["edges"] >= 1

        child_nid = node_id(NodeType.SKILL, "sk-child")
        parent_nid = node_id(NodeType.SKILL, "sk-parent")
        edges = store.get_edges_from(child_nid, EdgeType.IMPROVES_UPON)
        assert len(edges) == 1
        assert edges[0].target_id == parent_nid

    def test_resync_is_idempotent(self, store, registry):
        """Re-syncing the same skills does not duplicate nodes."""
        sk = _make_skill()
        registry.save(sk)

        sync_skills(store, registry)
        first_count = store.node_count(NodeType.SKILL)

        sync_skills(store, registry)
        second_count = store.node_count(NodeType.SKILL)

        assert first_count == second_count

    def test_empty_registry(self, store, registry):
        """Empty DB registry syncs only filesystem skills (if any)."""
        counts = sync_skills(store, registry)
        # Filesystem skills from .claude/skills/ are included by list_all()
        assert counts["nodes"] == store.node_count(NodeType.SKILL)
        assert counts["edges"] == 0

    def test_multiple_skills(self, store, registry):
        """Multiple DB skills are all synced in addition to filesystem skills."""
        baseline = self._baseline_count(store, registry)

        for i in range(5):
            sk = _make_skill(id=f"sk-{i}", name=f"skill_{i}")
            registry.save(sk)

        counts = sync_skills(store, registry)
        assert counts["nodes"] == baseline + 5
        assert store.node_count(NodeType.SKILL) == baseline + 5

    def test_deprecated_skill_excluded(self, store, registry):
        """Deprecated skills are excluded by list_all, so DB count stays at baseline."""
        baseline = self._baseline_count(store, registry)

        sk = _make_skill()
        registry.save(sk)
        # Deprecate via the registry method (sets the column properly)
        registry.deprecate(sk.id)

        counts = sync_skills(store, registry)
        # list_all excludes deprecated skills, so only filesystem skills remain
        assert counts["nodes"] == baseline

    def test_lineage_missing_parent_no_edge(self, store, registry):
        """If parent is not in the graph, no IMPROVES_UPON edge is created."""
        baseline = self._baseline_count(store, registry)

        # Only save the child, not the parent — parent won't be in graph
        child = _make_skill(id="sk-orphan", name="orphan", parent_id="sk-missing")
        registry.save(child)

        counts = sync_skills(store, registry)
        assert counts["nodes"] == baseline + 1
        assert counts["edges"] == 0


class TestSkillResolutionInPlanning:
    """Test that synced skills are findable via PlanningQueries."""

    def test_resolve_skill_for_task(self, store, registry):
        """resolve_skill_for_task finds skills by keyword overlap."""
        sk1 = _make_skill(
            id="sk-blue",
            name="wash_blue",
            description="Create a blue wash look",
            applicable_context="color wash blue fixtures",
        )
        sk2 = _make_skill(
            id="sk-red",
            name="wash_red",
            description="Create a red wash look",
            applicable_context="color wash red fixtures",
        )
        registry.save(sk1)
        registry.save(sk2)
        sync_skills(store, registry)

        pq = PlanningQueries(store)
        results = pq.resolve_skill_for_task("blue wash color")
        assert len(results) >= 1
        # The blue skill should rank higher (matches "blue", "wash", "color")
        # while red only matches ("wash", "color")
        assert results[0].label == "wash_blue"

    def test_resolve_skill_for_task_empty(self, store):
        """No skills in graph returns empty list."""
        pq = PlanningQueries(store)
        results = pq.resolve_skill_for_task("anything")
        assert results == []

    def test_resolve_skill_for_task_limit(self, store, registry):
        """Limit parameter caps results."""
        for i in range(10):
            sk = _make_skill(
                id=f"sk-{i}",
                name=f"color_skill_{i}",
                applicable_context="color wash",
            )
            registry.save(sk)
        sync_skills(store, registry)

        pq = PlanningQueries(store)
        results = pq.resolve_skill_for_task("color wash", limit=3)
        assert len(results) == 3

    def test_get_related_skills_for_tool_no_matches(self, store):
        """No IMPLEMENTS edges means empty result."""
        pq = PlanningQueries(store)
        results = pq.get_related_skills_for_tool("nonexistent_tool")
        assert results == []

    def test_get_related_skills_for_tool_with_edge(self, store, registry):
        """IMPLEMENTS edge links a skill to a tool."""
        sk = _make_skill(id="sk-impl", name="impl_skill")
        registry.save(sk)
        sync_skills(store, registry)

        # Create a tool node and an IMPLEMENTS edge
        tool_nid = node_id(NodeType.MCP_TOOL, "execute_sequence")
        store.upsert_node(tool_nid, NodeType.MCP_TOOL, label="execute_sequence")
        skill_nid = node_id(NodeType.SKILL, "sk-impl")
        store.upsert_edge(skill_nid, tool_nid, EdgeType.IMPLEMENTS)

        pq = PlanningQueries(store)
        results = pq.get_related_skills_for_tool("execute_sequence")
        assert len(results) == 1
        assert results[0].label == "impl_skill"
