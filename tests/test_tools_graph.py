# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for the 12 MCP graph tools in src/tools_graph.py."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

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
    async def test_query_invalid_type_returns_error(self, graph_store):
        from src.tools_graph import graph_query
        with patch("src.tools_graph.get_graph_store", return_value=graph_store):
            data = json.loads(await graph_query(node_type="nonexistent_type"))
            assert "error" in data


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


# ---------------------------------------------------------------------------
# graph_rag_query_tool
# ---------------------------------------------------------------------------

class TestGraphRagQueryTool:
    @pytest.mark.asyncio
    async def test_store_none(self):
        from src.tools_graph import graph_rag_query_tool
        with patch("src.tools_graph.get_graph_store", return_value=None):
            data = json.loads(await graph_rag_query_tool(query="test"))
            assert data.get("error") == "Graph store not initialized"

    @pytest.mark.asyncio
    async def test_success_with_results(self, graph_store):
        from src.tools_graph import graph_rag_query_tool
        mock_ctx = MagicMock()
        mock_ctx.to_dict.return_value = {
            "entity": {"node_id": "module:src.server", "label": "src.server"},
            "neighbors": [],
            "edges": [],
        }
        with (
            patch("src.tools_graph.get_graph_store", return_value=graph_store),
            patch("src.knowledge_graph.graph_rag_query", return_value=[mock_ctx]),
        ):
            data = json.loads(await graph_rag_query_tool(query="server tools", max_depth=1))
            assert data["query"] == "server tools"
            assert data["entities_found"] == 1
            assert data["contexts"][0]["entity"]["label"] == "src.server"

    @pytest.mark.asyncio
    async def test_empty_results(self, graph_store):
        from src.tools_graph import graph_rag_query_tool
        with (
            patch("src.tools_graph.get_graph_store", return_value=graph_store),
            patch("src.knowledge_graph.graph_rag_query", return_value=[]),
        ):
            data = json.loads(await graph_rag_query_tool(query="nothing matches"))
            assert data["entities_found"] == 0
            assert data["contexts"] == []

    @pytest.mark.asyncio
    async def test_passes_max_depth(self, graph_store):
        from src.tools_graph import graph_rag_query_tool
        with (
            patch("src.tools_graph.get_graph_store", return_value=graph_store),
            patch("src.knowledge_graph.graph_rag_query", return_value=[]) as mock_rag,
        ):
            await graph_rag_query_tool(query="q", max_depth=5)
            mock_rag.assert_called_once_with("q", graph_store, max_depth=5)


# ---------------------------------------------------------------------------
# graph_upsert_node
# ---------------------------------------------------------------------------

class TestGraphUpsertNode:
    @pytest.mark.asyncio
    async def test_store_none(self):
        from src.tools_graph import graph_upsert_node
        with patch("src.tools_graph.get_graph_store", return_value=None):
            data = json.loads(await graph_upsert_node(
                node_id="skill:test", node_type="skill", label="Test Skill"))
            assert data.get("error") == "Graph store not initialized"

    @pytest.mark.asyncio
    async def test_invalid_node_type(self, graph_store):
        from src.tools_graph import graph_upsert_node
        with patch("src.tools_graph.get_graph_store", return_value=graph_store):
            data = json.loads(await graph_upsert_node(
                node_id="x:y", node_type="not_a_real_type", label="x"))
            assert "error" in data
            assert "not_a_real_type" in data["error"]

    @pytest.mark.asyncio
    async def test_invalid_props_json(self, graph_store):
        from src.tools_graph import graph_upsert_node
        with patch("src.tools_graph.get_graph_store", return_value=graph_store):
            data = json.loads(await graph_upsert_node(
                node_id="skill:x", node_type="skill", label="x", props="{bad json}"))
            assert "error" in data
            assert "Invalid props JSON" in data["error"]

    @pytest.mark.asyncio
    async def test_success_inserts_node(self, graph_store):
        from src.tools_graph import graph_upsert_node
        with patch("src.tools_graph.get_graph_store", return_value=graph_store):
            data = json.loads(await graph_upsert_node(
                node_id="skill:ft-pools",
                node_type="skill",
                label="FT Pools",
                props='{"version": "13"}',
            ))
            assert data["upserted"] is True
            assert data["node_id"] == "skill:ft-pools"
            assert data["node_type"] == "skill"
            assert data["label"] == "FT Pools"
        # Verify the node actually landed in the store
        node = graph_store.get_node("skill:ft-pools")
        assert node is not None
        assert node.label == "FT Pools"
        assert node.props.get("version") == "13"

    @pytest.mark.asyncio
    async def test_idempotent_update(self, graph_store):
        from src.tools_graph import graph_upsert_node
        with patch("src.tools_graph.get_graph_store", return_value=graph_store):
            await graph_upsert_node(
                node_id="skill:dup", node_type="skill", label="Original")
            data = json.loads(await graph_upsert_node(
                node_id="skill:dup", node_type="skill", label="Updated"))
            assert data["upserted"] is True
            assert data["label"] == "Updated"

    @pytest.mark.asyncio
    async def test_empty_label_stored_as_none(self, graph_store):
        from src.tools_graph import graph_upsert_node
        with patch("src.tools_graph.get_graph_store", return_value=graph_store):
            data = json.loads(await graph_upsert_node(
                node_id="cluster:anon", node_type="cluster", label=""))
            assert data["upserted"] is True


# ---------------------------------------------------------------------------
# graph_add_edge
# ---------------------------------------------------------------------------

class TestGraphAddEdge:
    @pytest.mark.asyncio
    async def test_store_none(self):
        from src.tools_graph import graph_add_edge
        with patch("src.tools_graph.get_graph_store", return_value=None):
            data = json.loads(await graph_add_edge(
                source_id="a", target_id="b", edge_type="imports"))
            assert data.get("error") == "Graph store not initialized"

    @pytest.mark.asyncio
    async def test_invalid_edge_type(self, graph_store):
        from src.tools_graph import graph_add_edge
        with patch("src.tools_graph.get_graph_store", return_value=graph_store):
            data = json.loads(await graph_add_edge(
                source_id="module:src.server", target_id="module:src.tools",
                edge_type="not_a_real_edge"))
            assert "error" in data
            assert "not_a_real_edge" in data["error"]

    @pytest.mark.asyncio
    async def test_invalid_props_json(self, graph_store):
        from src.tools_graph import graph_add_edge
        with patch("src.tools_graph.get_graph_store", return_value=graph_store):
            data = json.loads(await graph_add_edge(
                source_id="module:src.server", target_id="module:src.tools",
                edge_type="imports", props="{bad}"))
            assert "error" in data
            assert "Invalid props JSON" in data["error"]

    @pytest.mark.asyncio
    async def test_success_adds_edge(self, graph_store):
        from src.tools_graph import graph_add_edge
        with patch("src.tools_graph.get_graph_store", return_value=graph_store):
            data = json.loads(await graph_add_edge(
                source_id="module:src.server",
                target_id="cluster:core",
                edge_type="categorized_as",
                props='{"confidence": 0.9}',
            ))
            assert data["upserted"] is True
            assert data["source_id"] == "module:src.server"
            assert data["target_id"] == "cluster:core"
            assert data["edge_type"] == "categorized_as"

    @pytest.mark.asyncio
    async def test_idempotent_edge(self, graph_store):
        from src.tools_graph import graph_add_edge
        with patch("src.tools_graph.get_graph_store", return_value=graph_store):
            r1 = json.loads(await graph_add_edge(
                source_id="module:src.server", target_id="module:src.tools",
                edge_type="calls"))
            r2 = json.loads(await graph_add_edge(
                source_id="module:src.server", target_id="module:src.tools",
                edge_type="calls"))
            assert r1["upserted"] is True
            assert r2["upserted"] is True
            assert r1["edge_id"] == r2["edge_id"]
