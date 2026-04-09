# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for MCP metadata extraction via AST parsing."""

from __future__ import annotations

import pytest

from src.knowledge_graph.mcp_metadata import extract_mcp_metadata


@pytest.fixture
def mock_server_file(tmp_path):
    """Create a mock server.py with MCP decorators."""
    code = '''\
from mcp import FastMCP

mcp = FastMCP("test")


@mcp.tool()
async def execute_sequence(sequence_id: int, action: str) -> str:
    """Execute a sequence on the console.

    Sends Go/Pause/Off to the specified sequence.
    """
    return "ok"


@mcp.tool()
async def get_variable(var_name: str) -> str:
    """Get a system variable value."""
    return "value"


@mcp.resource("ma2://docs/rights-matrix")
def resource_rights_matrix() -> str:
    """
    MA2 OAuth scope mapping matrix (read-only reference).

    Use execute_sequence for playback control.
    """
    return "{}"


@mcp.resource("ma2://busking/patterns")
def resource_busking_patterns() -> str:
    """Busking patterns for live performance."""
    return ""


@mcp.prompt()
def inspect_console(focus: str = "full") -> str:
    """
    Guided console state inspection.

    Calls get_variable to read system state.
    """
    return "inspect"


@mcp.prompt()
def plan_cue_store(sequence_id: str, cue_number: str) -> str:
    """Plan a cue store operation."""
    return "plan"
'''
    server_file = tmp_path / "server.py"
    server_file.write_text(code)
    return server_file


@pytest.fixture
def mock_tools_file(tmp_path):
    """Create a mock tools_community.py alongside server.py."""
    code = '''\
from somewhere import mcp

@mcp.tool()
async def send_raw_command(command: str) -> str:
    """Send a raw command to the console."""
    return "ok"
'''
    tools_file = tmp_path / "tools_community.py"
    tools_file.write_text(code)
    return tools_file


class TestExtractTools:
    def test_tools_extracted(self, mock_server_file):
        """@mcp.tool() decorators are parsed correctly."""
        meta = extract_mcp_metadata(mock_server_file)
        assert "execute_sequence" in meta.tools
        assert "get_variable" in meta.tools

        tool = meta.tools["execute_sequence"]
        assert tool.name == "execute_sequence"
        assert "sequence_id" in tool.args
        assert "action" in tool.args
        assert "Execute a sequence" in tool.docstring

    def test_tool_module_tracked(self, mock_server_file):
        """Tool's source module is recorded."""
        meta = extract_mcp_metadata(mock_server_file)
        tool = meta.tools["execute_sequence"]
        assert tool.module == "src.server"


class TestExtractResources:
    def test_resources_extracted(self, mock_server_file):
        """@mcp.resource() decorators are parsed with URI."""
        meta = extract_mcp_metadata(mock_server_file)
        assert "ma2://docs/rights-matrix" in meta.resources
        assert "ma2://busking/patterns" in meta.resources

        resource = meta.resources["ma2://docs/rights-matrix"]
        assert resource.uri == "ma2://docs/rights-matrix"
        assert resource.function_name == "resource_rights_matrix"
        assert "OAuth" in resource.docstring or "mapping" in resource.docstring

    def test_resource_without_uri_uses_function_name(self, tmp_path):
        """Resources with empty URI fall back to function name."""
        code = '''\
from mcp import FastMCP
mcp = FastMCP("test")

@mcp.resource("")
def my_resource() -> str:
    """A resource."""
    return ""
'''
        f = tmp_path / "server.py"
        f.write_text(code)
        meta = extract_mcp_metadata(f)
        # Empty string URI maps to function name as key
        assert "my_resource" in meta.resources or "" in meta.resources


class TestExtractPrompts:
    def test_prompts_extracted(self, mock_server_file):
        """@mcp.prompt() decorators are parsed correctly."""
        meta = extract_mcp_metadata(mock_server_file)
        assert "inspect_console" in meta.prompts
        assert "plan_cue_store" in meta.prompts

        prompt = meta.prompts["inspect_console"]
        assert prompt.name == "inspect_console"
        assert "focus" in prompt.args
        assert "console state" in prompt.docstring or "inspection" in prompt.docstring

    def test_prompt_args(self, mock_server_file):
        """Prompt arguments are extracted."""
        meta = extract_mcp_metadata(mock_server_file)
        prompt = meta.prompts["plan_cue_store"]
        assert "sequence_id" in prompt.args
        assert "cue_number" in prompt.args


class TestToolsCommunityScanning:
    def test_tools_community_scanned(self, mock_server_file, mock_tools_file):
        """tools_community.py is also scanned for tools."""
        meta = extract_mcp_metadata(mock_server_file)
        assert "send_raw_command" in meta.tools
        tool = meta.tools["send_raw_command"]
        assert "command" in tool.args


class TestMissingFile:
    def test_missing_file_returns_empty(self, tmp_path):
        """Non-existent server path returns empty metadata."""
        meta = extract_mcp_metadata(tmp_path / "nonexistent.py")
        assert len(meta.tools) == 0
        assert len(meta.resources) == 0
        assert len(meta.prompts) == 0

    def test_none_path_uses_default(self):
        """None path uses default location (may or may not exist)."""
        meta = extract_mcp_metadata(None)
        # Should not raise — gracefully handles missing files
        assert isinstance(meta.tools, dict)
        assert isinstance(meta.resources, dict)
        assert isinstance(meta.prompts, dict)


class TestCombinedCounts:
    def test_all_types_counted(self, mock_server_file, mock_tools_file):
        """All extracted types appear in the metadata."""
        meta = extract_mcp_metadata(mock_server_file)
        assert len(meta.tools) >= 2  # execute_sequence, get_variable (+ send_raw_command)
        assert len(meta.resources) >= 2  # rights-matrix, busking/patterns
        assert len(meta.prompts) >= 2  # inspect_console, plan_cue_store
