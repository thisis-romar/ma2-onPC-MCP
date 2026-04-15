# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for the 9 MCP graph tools in src/tools_graph.py."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from src.knowledge_graph.schema import EdgeType, NodeType
from src.knowledge_graph.store import GraphStore


@pytest.fixture()
def graph_store():
    """Create an in-memory GraphStore with test data."""
    s = GraphStore(":memory:")
    s.initialize()
    # Seed some modules and symbols
    s.upsert_node("module:src.server", NodeType.MODULE, label="src.server")
    s.upsert_node("module:src.tools", NodeType.MODULE, label="src.tools")
    s.upsert_node("symbol:src.server.main", NodeType.SYMBOL, label="main",
                  props={"docstring": "Entry point"})
    s.upsert_edge("module:src.server", "symbol:src.server.main", EdgeType.DEFINES)
    s.upsert_edge("module:src.tools", "module:src.server", EdgeType.IMPORTS)
    # Add a cluster
    s.upsert_node("cluster:core", NodeType.CLUSTER, label="core",
                  props={"size": 2, "cohesion": 0.85})
    s.upsert_edge("module:src.server", "cluster:core", EdgeType.PART_OF)
    s.upsert_edge("module:src.tools", "cluster:core", EdgeType.PART_OF)
    return s


# ---------------------------------------------------------------------------
# graph_list_repos
# ---------------------------------------------------------------------------

class TestGraphListRepos:
    @pytest.mark.asyncio
    async def test_list_repos_empty(self):
        from src.tools_graph import graph_list_repos
        result = json.loads(await graph_list_repos())
        assert "repos" in result
        assert result["count"] >= 0

    @pytest.mark.asyncio
    async def test_list_repos_returns_json(self):
        from src.tools_graph import graph_list_repos
        raw = await graph_list_repos()
        data = json.loads(raw)
        assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# graph_analyze_repo
# ---------------------------------------------------------------------------

class TestGraphAnalyzeRepo:
    @pytest.mark.asyncio
    async def test_analyze_repo_store_none(self):
        from src.tools_graph import graph_analyze_repo
        with patch("src.tools_graph.get_graph_store", return_value=None):
            raw = await graph_analyze_repo(path=".")
            data = json.loads(raw)
            assert data.get("error") == "Graph store not initialized"

    @pytest.mark.asyncio
    async def test_analyze_repo_success(self, graph_store):
        from src.tools_graph import graph_analyze_repo
        with (
            patch("src.tools_graph.get_graph_store", return_value=graph_store),
            patch("src.tools_graph.scan_repository", return_value={
                "nodes": 10, "edges": 5, "modules": 4, "symbols": 6,
            }),
            patch("src.knowledge_graph.parsers.repo_registry.get_git_head_sha",
                  return_value="abc123def456"),
        ):
            raw = await graph_analyze_repo(path=".")
            data = json.loads(raw)
            assert data["sha"] == "abc123def456"[:12]
            assert data["modules"] == 4
            assert data["symbols"] == 6
            assert data["nodes_created"] == 10


# ---------------------------------------------------------------------------
# graph_query
# ---------------------------------------------------------------------------

class TestGraphQuery:
    @pytest.mark.asyncio
    async def test_query_store_none(self):
        from src.tools_graph import graph_query
        with patch("src.tools_graph.get_graph_store", return_value=None):
            data = json.loads(await graph_query(node_type="module"))
            assert data.get("error") == "Graph store not initialized"

    @pytest.mark.asyncio
    async def test_query_modules(self, graph_store):
        from src.tools_graph import graph_query
        with patch("src.tools_graph.get_graph_store", return_value=graph_store):
            data = json.loads(await graph_query(node_type="module"))
            assert data["count"] == 2
            labels = {n["label"] for n in data["nodes"]}
            assert "src.server" in labels

    @pytest.mark.asyncio
    async def test_query_with_pattern(self, graph_store):
        from src.tools_graph import graph_query
        with patch("src.tools_graph.get_graph_store", return_value=graph_store):
            data = json.loads(await graph_query(node_type="module", pattern="server"))
            assert data["count"] == 1
            assert data["nodes"][0]["label"] == "src.server"

    @pytest.mark.asyncio
    async def test_query_invalid_type_returns_empty(self, graph_store):
        from src.tools_graph import graph_query
        with patch("src.tools_graph.get_graph_store", return_value=graph_store):
            data = json.loads(await graph_query(node_type="nonexistent_type"))
            assert data["count"] == 0
            assert data["nodes"] == []


# ---------------------------------------------------------------------------
# graph_context
# ---------------------------------------------------------------------------

class TestGraphContext:
    @pytest.mark.asyncio
    async def test_context_store_none(self):
        from src.tools_graph import graph_context
        with patch("src.tools_graph.get_graph_store", return_value=None):
            data = json.loads(await graph_context(node_id="module:src.server"))
            assert data.get("error") == "Graph store not initialized"

    @pytest.mark.asyncio
    async def test_context_valid_node(self, graph_store):
        from src.tools_graph import graph_context
        with patch("src.tools_graph.get_graph_store", return_value=graph_store):
            data = json.loads(await graph_context(node_id="module:src.server"))
            assert "nodes" in data
            assert "edges" in data


# ---------------------------------------------------------------------------
# graph_impact
# ---------------------------------------------------------------------------

class TestGraphImpact:
    @pytest.mark.asyncio
    async def test_impact_store_none(self):
        from src.tools_graph import graph_impact
        with patch("src.tools_graph.get_graph_store", return_value=None):
            data = json.loads(await graph_impact(node_id="module:src.server"))
            assert data.get("error") == "Graph store not initialized"

    @pytest.mark.asyncio
    async def test_impact_valid_node(self, graph_store):
        from src.tools_graph import graph_impact
        with patch("src.tools_graph.get_graph_store", return_value=graph_store):
            data = json.loads(await graph_impact(node_id="module:src.server"))
            assert data["target_node_id"] == "module:src.server"
            assert "direct_dependents" in data
            assert "blast_radius" in data


# ---------------------------------------------------------------------------
# graph_detect_changes
# ---------------------------------------------------------------------------

class TestGraphDetectChanges:
    @pytest.mark.asyncio
    async def test_detect_changes_store_none(self):
        from src.tools_graph import graph_detect_changes
        with patch("src.tools_graph.get_graph_store", return_value=None):
            data = json.loads(await graph_detect_changes())
            assert data.get("error") == "Graph store not initialized"

    @pytest.mark.asyncio
    async def test_detect_changes_with_snapshots(self, graph_store):
        from src.tools_graph import graph_detect_changes
        old = json.dumps({"symbol:a": "hash1"})
        new = json.dumps({"symbol:a": "hash2", "symbol:b": "hash3"})
        with patch("src.tools_graph.get_graph_store", return_value=graph_store):
            data = json.loads(await graph_detect_changes(old_snapshot=old, new_snapshot=new))
            assert "added" in data
            assert "modified" in data
            assert "symbol:b" in data["added"]
            assert "symbol:a" in data["modified"]


# ---------------------------------------------------------------------------
# graph_trace_process
# ---------------------------------------------------------------------------

class TestGraphTraceProcess:
    @pytest.mark.asyncio
    async def test_trace_store_none(self):
        from src.tools_graph import graph_trace_process
        with patch("src.tools_graph.get_graph_store", return_value=None):
            data = json.loads(await graph_trace_process(entry_point="module:src.server"))
            assert data.get("error") == "Graph store not initialized"

    @pytest.mark.asyncio
    async def test_trace_valid_entry(self, graph_store):
        from src.tools_graph import graph_trace_process
        with patch("src.tools_graph.get_graph_store", return_value=graph_store):
            data = json.loads(await graph_trace_process(entry_point="module:src.server"))
            assert data["entry_point"] == "module:src.server"
            assert "steps" in data


# ---------------------------------------------------------------------------
# graph_list_clusters
# ---------------------------------------------------------------------------

class TestGraphListClusters:
    @pytest.mark.asyncio
    async def test_list_clusters_store_none(self):
        from src.tools_graph import graph_list_clusters
        with patch("src.tools_graph.get_graph_store", return_value=None):
            data = json.loads(await graph_list_clusters())
            assert data.get("error") == "Graph store not initialized"

    @pytest.mark.asyncio
    async def test_list_clusters_success(self, graph_store):
        from src.tools_graph import graph_list_clusters
        with patch("src.tools_graph.get_graph_store", return_value=graph_store):
            data = json.loads(await graph_list_clusters(min_size=1))
            assert data["count"] == 1
            assert data["clusters"][0]["label"] == "core"
            assert data["clusters"][0]["size"] == 2

    @pytest.mark.asyncio
    async def test_list_clusters_min_size_filters(self, graph_store):
        from src.tools_graph import graph_list_clusters
        with patch("src.tools_graph.get_graph_store", return_value=graph_store):
            data = json.loads(await graph_list_clusters(min_size=10))
            assert data["count"] == 0


# ---------------------------------------------------------------------------
# graph_generate_skills
# ---------------------------------------------------------------------------

class TestGraphGenerateSkills:
    @pytest.mark.asyncio
    async def test_generate_skills_store_none(self):
        from src.tools_graph import graph_generate_skills
        with patch("src.tools_graph.get_graph_store", return_value=None):
            data = json.loads(await graph_generate_skills())
            assert data.get("error") == "Graph store not initialized"

    @pytest.mark.asyncio
    async def test_generate_skills_success(self, graph_store):
        from src.tools_graph import graph_generate_skills
        with patch("src.tools_graph.get_graph_store", return_value=graph_store):
            data = json.loads(await graph_generate_skills())
            assert data["count"] == 1
            assert data["suggestions"][0]["name"] == "understand-core"

    @pytest.mark.asyncio
    async def test_generate_skills_specific_cluster(self, graph_store):
        from src.tools_graph import graph_generate_skills
        with patch("src.tools_graph.get_graph_store", return_value=graph_store):
            data = json.loads(await graph_generate_skills(cluster_id="cluster:core"))
            assert data["count"] == 1

    @pytest.mark.asyncio
    async def test_generate_skills_nonexistent_cluster(self, graph_store):
        from src.tools_graph import graph_generate_skills
        with patch("src.tools_graph.get_graph_store", return_value=graph_store):
            data = json.loads(await graph_generate_skills(cluster_id="cluster:nope"))
            assert data["count"] == 0
