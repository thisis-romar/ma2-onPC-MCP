# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for knowledge graph resource sync."""

from __future__ import annotations

import pytest

from src.knowledge_graph.mcp_metadata import (
    MCPMetadata,
    PromptMeta,
    ResourceMeta,
    ToolMeta,
)
from src.knowledge_graph.resource_sync import sync_resources
from src.knowledge_graph.schema import EdgeType, NodeType, node_id
from src.knowledge_graph.store import GraphStore


@pytest.fixture
def store():
    """Create an in-memory GraphStore for testing."""
    s = GraphStore(":memory:")
    s.initialize()
    yield s
    s.close()


def _make_metadata(
    *,
    tools: dict[str, ToolMeta] | None = None,
    resources: dict[str, ResourceMeta] | None = None,
    prompts: dict[str, PromptMeta] | None = None,
) -> MCPMetadata:
    return MCPMetadata(
        tools=tools or {},
        resources=resources or {},
        prompts=prompts or {},
    )


class TestSyncToolNodes:
    def test_tool_nodes_created(self, store):
        """Tools are synced as MCP_TOOL nodes."""
        meta = _make_metadata(tools={
            "execute_sequence": ToolMeta(
                name="execute_sequence",
                docstring="Execute a sequence on the console.",
                args=["sequence_id", "action"],
                module="src.tools_community",
            ),
            "get_variable": ToolMeta(
                name="get_variable",
                docstring="Get a system variable value.",
                args=["var_name"],
                module="src.tools_community",
            ),
        })

        counts = sync_resources(store, meta)
        assert counts["nodes"] == 2
        assert store.node_count(NodeType.MCP_TOOL) == 2

        nid = node_id(NodeType.MCP_TOOL, "execute_sequence")
        node = store.get_node(nid)
        assert node is not None
        assert node.label == "execute_sequence"
        assert node.props["module"] == "src.tools_community"
        assert "sequence_id" in node.props["args"]

    def test_tool_docstring_truncated(self, store):
        """Long docstrings are truncated to 200 chars."""
        long_doc = "A" * 500
        meta = _make_metadata(tools={
            "long_tool": ToolMeta(name="long_tool", docstring=long_doc),
        })

        sync_resources(store, meta)
        nid = node_id(NodeType.MCP_TOOL, "long_tool")
        node = store.get_node(nid)
        assert node is not None
        assert len(node.props["docstring"]) == 200


class TestSyncResourceNodes:
    def test_resource_nodes_created(self, store):
        """Resources are synced as MCP_RESOURCE nodes."""
        meta = _make_metadata(resources={
            "ma2://docs/rights-matrix": ResourceMeta(
                uri="ma2://docs/rights-matrix",
                docstring="MA2 OAuth scope mapping matrix.",
                function_name="resource_rights_matrix",
            ),
        })

        counts = sync_resources(store, meta)
        assert counts["nodes"] == 1
        assert store.node_count(NodeType.MCP_RESOURCE) == 1

        nid = node_id(NodeType.MCP_RESOURCE, "ma2://docs/rights-matrix")
        node = store.get_node(nid)
        assert node is not None
        assert node.label == "ma2://docs/rights-matrix"
        assert node.props["category"] == "docs"

    def test_resource_category_parsed_from_uri(self, store):
        """Category is extracted from the URI path."""
        meta = _make_metadata(resources={
            "ma2://busking/patterns": ResourceMeta(
                uri="ma2://busking/patterns",
                docstring="Busking patterns.",
                function_name="resource_busking_patterns",
            ),
        })

        sync_resources(store, meta)
        nid = node_id(NodeType.MCP_RESOURCE, "ma2://busking/patterns")
        node = store.get_node(nid)
        assert node is not None
        assert node.props["category"] == "busking"


class TestSyncPromptNodes:
    def test_prompt_nodes_created(self, store):
        """Prompts are synced as MCP_PROMPT nodes."""
        meta = _make_metadata(prompts={
            "inspect_console": PromptMeta(
                name="inspect_console",
                docstring="Guided console state inspection.",
                args=["focus"],
            ),
        })

        counts = sync_resources(store, meta)
        assert counts["nodes"] == 1
        assert store.node_count(NodeType.MCP_PROMPT) == 1

        nid = node_id(NodeType.MCP_PROMPT, "inspect_console")
        node = store.get_node(nid)
        assert node is not None
        assert node.label == "inspect_console"
        assert "focus" in node.props["args"]


class TestDocumentsEdges:
    def test_resource_documents_tool(self, store):
        """DOCUMENTS edges created when resource docstring mentions a tool."""
        meta = _make_metadata(
            tools={
                "execute_sequence": ToolMeta(
                    name="execute_sequence",
                    docstring="Execute a sequence.",
                ),
            },
            resources={
                "ma2://docs/playback": ResourceMeta(
                    uri="ma2://docs/playback",
                    docstring="Playback reference. Use execute_sequence to start playback.",
                    function_name="resource_playback",
                ),
            },
        )

        counts = sync_resources(store, meta)
        assert counts["edges"] >= 1

        resource_nid = node_id(NodeType.MCP_RESOURCE, "ma2://docs/playback")
        tool_nid = node_id(NodeType.MCP_TOOL, "execute_sequence")
        edges = store.get_edges_from(resource_nid, EdgeType.DOCUMENTS)
        assert len(edges) == 1
        assert edges[0].target_id == tool_nid

    def test_no_false_positive_tool_mention(self, store):
        """Tool names must match on word boundaries — no substring matches."""
        meta = _make_metadata(
            tools={
                "go": ToolMeta(name="go", docstring="Go command."),
            },
            resources={
                "ma2://docs/test": ResourceMeta(
                    uri="ma2://docs/test",
                    docstring="This resource is about going forward.",
                    function_name="resource_test",
                ),
            },
        )

        sync_resources(store, meta)
        resource_nid = node_id(NodeType.MCP_RESOURCE, "ma2://docs/test")
        edges = store.get_edges_from(resource_nid, EdgeType.DOCUMENTS)
        # "going" should NOT match "go" on word boundary
        assert len(edges) == 0


class TestOrchestratesEdges:
    def test_prompt_orchestrates_tool(self, store):
        """ORCHESTRATES edges created when prompt docstring mentions a tool."""
        meta = _make_metadata(
            tools={
                "get_object_info": ToolMeta(
                    name="get_object_info",
                    docstring="Get info about an object.",
                ),
            },
            prompts={
                "inspect_console": PromptMeta(
                    name="inspect_console",
                    docstring="Inspect the console. Calls get_object_info for details.",
                    args=["focus"],
                ),
            },
        )

        counts = sync_resources(store, meta)
        assert counts["edges"] >= 1

        prompt_nid = node_id(NodeType.MCP_PROMPT, "inspect_console")
        tool_nid = node_id(NodeType.MCP_TOOL, "get_object_info")
        edges = store.get_edges_from(prompt_nid, EdgeType.ORCHESTRATES)
        assert len(edges) == 1
        assert edges[0].target_id == tool_nid


class TestEmptyMetadata:
    def test_empty_metadata_no_errors(self, store):
        """Empty metadata produces no nodes or edges."""
        meta = _make_metadata()
        counts = sync_resources(store, meta)
        assert counts["nodes"] == 0
        assert counts["edges"] == 0
        assert store.node_count() == 0


class TestResyncIdempotent:
    def test_resync_does_not_duplicate(self, store):
        """Re-syncing same metadata doesn't duplicate nodes."""
        meta = _make_metadata(
            tools={"t1": ToolMeta(name="t1")},
            resources={"ma2://docs/r1": ResourceMeta(uri="ma2://docs/r1", function_name="r1")},
            prompts={"p1": PromptMeta(name="p1")},
        )

        sync_resources(store, meta)
        first_count = store.node_count()

        sync_resources(store, meta)
        second_count = store.node_count()

        assert first_count == second_count
