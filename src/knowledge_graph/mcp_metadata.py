# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
mcp_metadata.py — Extract MCP tool/resource/prompt metadata via AST parsing.

Parses ``@mcp.tool()``, ``@mcp.resource()``, and ``@mcp.prompt()`` decorators
from Python source files to build a structured catalogue of the MCP surface.
"""

from __future__ import annotations

import ast
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Default source root for scanning tool modules
_SRC_ROOT = Path(__file__).parent.parent


@dataclass
class ToolMeta:
    """Metadata about an MCP tool."""

    name: str
    docstring: str = ""
    args: list[str] = field(default_factory=list)
    module: str = ""


@dataclass
class ResourceMeta:
    """Metadata about an MCP resource."""

    uri: str
    docstring: str = ""
    function_name: str = ""


@dataclass
class PromptMeta:
    """Metadata about an MCP prompt."""

    name: str
    docstring: str = ""
    args: list[str] = field(default_factory=list)


@dataclass
class MCPMetadata:
    """Aggregated MCP metadata extracted from source files."""

    tools: dict[str, ToolMeta] = field(default_factory=dict)
    resources: dict[str, ResourceMeta] = field(default_factory=dict)
    prompts: dict[str, PromptMeta] = field(default_factory=dict)


def _has_decorator(node: ast.FunctionDef | ast.AsyncFunctionDef, attr: str) -> str | None:
    """Check if a function has a ``@mcp.<attr>(...)`` decorator.

    Returns the first string argument of the decorator call (e.g. the URI
    for ``@mcp.resource("ma2://...")``), or empty string if the decorator
    is called with no args (``@mcp.tool()``).  Returns ``None`` if the
    decorator is not present.
    """
    for dec in node.decorator_list:
        # @mcp.tool() / @mcp.resource("uri") / @mcp.prompt()
        if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)):
            continue
        if dec.func.attr != attr:
            continue
        # Check if it's mcp.attr or _sc.mcp.attr style
        if isinstance(dec.func.value, ast.Name) and dec.func.value.id == "mcp":
            if dec.args and isinstance(dec.args[0], ast.Constant):
                return str(dec.args[0].value)
            return ""
        if isinstance(dec.func.value, ast.Attribute) and dec.func.value.attr == "mcp":
            if dec.args and isinstance(dec.args[0], ast.Constant):
                return str(dec.args[0].value)
            return ""
    return None


def _extract_args(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """Extract argument names from a function, excluding 'self'."""
    return [
        arg.arg
        for arg in node.args.args
        if arg.arg != "self"
    ]


def _extract_from_file(
    filepath: Path,
    module_name: str,
    metadata: MCPMetadata,
) -> None:
    """Parse a single Python file and populate metadata."""
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, OSError) as exc:
        logger.warning("Cannot parse %s: %s", filepath, exc)
        return

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        # Tools: @mcp.tool()
        tool_arg = _has_decorator(node, "tool")
        if tool_arg is not None:
            name = node.name
            docstring = ast.get_docstring(node) or ""
            args = _extract_args(node)
            metadata.tools[name] = ToolMeta(
                name=name,
                docstring=docstring,
                args=args,
                module=module_name,
            )

        # Resources: @mcp.resource("uri")
        resource_arg = _has_decorator(node, "resource")
        if resource_arg is not None:
            uri = resource_arg or node.name
            docstring = ast.get_docstring(node) or ""
            metadata.resources[uri] = ResourceMeta(
                uri=uri,
                docstring=docstring,
                function_name=node.name,
            )

        # Prompts: @mcp.prompt()
        prompt_arg = _has_decorator(node, "prompt")
        if prompt_arg is not None:
            name = node.name
            docstring = ast.get_docstring(node) or ""
            args = _extract_args(node)
            metadata.prompts[name] = PromptMeta(
                name=name,
                docstring=docstring,
                args=args,
            )


def extract_mcp_metadata(server_path: Path | None = None) -> MCPMetadata:
    """Extract MCP tool/resource/prompt metadata from source files.

    Scans ``server.py`` (resources, prompts) and ``tools_community.py``
    (community tools) via AST.  If ``server_path`` is ``None``, uses the
    default location relative to this module.

    Args:
        server_path: Path to ``server.py``.  If ``None``, auto-detects.

    Returns:
        Populated :class:`MCPMetadata` instance.
    """
    metadata = MCPMetadata()

    if server_path is None:
        server_path = _SRC_ROOT / "server.py"

    if server_path.exists():
        _extract_from_file(server_path, "src.server", metadata)

    # Also scan tools_community.py for COMMUNITY tools
    tools_community = server_path.parent / "tools_community.py" if server_path else None
    if tools_community and tools_community.exists():
        _extract_from_file(tools_community, "src.tools_community", metadata)

    # Scan private tool modules if they exist
    private_dir = server_path.parent / "private" if server_path else None
    if private_dir and private_dir.is_dir():
        for module_file in ("tools_professional.py", "tools_enterprise.py"):
            path = private_dir / module_file
            if path.exists():
                _extract_from_file(path, f"src.private.{path.stem}", metadata)

    logger.info(
        "Extracted MCP metadata: %d tools, %d resources, %d prompts",
        len(metadata.tools),
        len(metadata.resources),
        len(metadata.prompts),
    )
    return metadata
