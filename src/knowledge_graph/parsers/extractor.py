# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
extractor.py — Python AST symbol and import extractor.

Parses a Python source file into a ModuleInfo dataclass containing symbols
(functions, classes, methods, constants) and import relationships.
"""

from __future__ import annotations

import ast
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_DOCSTRING_MAX_LEN = 200


@dataclass
class SymbolInfo:
    """A single symbol (function, class, method, or constant) in a module."""

    name: str
    kind: str  # "function", "class", "method", "constant"
    line: int
    docstring: str | None = None
    decorators: list[str] = field(default_factory=list)
    parent_class: str | None = None


@dataclass
class ImportInfo:
    """A single import statement in a module."""

    module: str  # the module being imported, e.g. "src.knowledge_graph.store"
    names: list[str] = field(default_factory=list)  # specific imports, e.g. ["GraphStore"]
    is_relative: bool = False
    line: int = 0


@dataclass
class ModuleInfo:
    """Extracted information about a Python module."""

    path: str  # relative module path, e.g. "src/server.py"
    module_name: str  # dotted, e.g. "src.server"
    symbols: list[SymbolInfo] = field(default_factory=list)
    imports: list[ImportInfo] = field(default_factory=list)
    parse_error: str | None = None


def _decorator_to_str(node: ast.expr) -> str:
    """Convert a decorator AST node to a string representation."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parts: list[str] = []
        current: ast.expr = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))
    if isinstance(node, ast.Call):
        return _decorator_to_str(node.func)
    return "<unknown>"


def _get_docstring(node: ast.AST) -> str | None:
    """Extract the docstring from a function/class body, truncated to max length."""
    doc = ast.get_docstring(node)
    if doc is None:
        return None
    if len(doc) > _DOCSTRING_MAX_LEN:
        return doc[:_DOCSTRING_MAX_LEN]
    return doc


def _path_to_module_name(path: str) -> str:
    """Convert a file path to a dotted module name.

    Examples:
        "src/server.py" -> "src.server"
        "src/knowledge_graph/__init__.py" -> "src.knowledge_graph"
        "tests/test_kg_store.py" -> "tests.test_kg_store"
    """
    # Normalize separators
    cleaned = path.replace("\\", "/")
    # Strip .py extension
    if cleaned.endswith(".py"):
        cleaned = cleaned[:-3]
    # Handle __init__ — the module is the parent package
    if cleaned.endswith("/__init__"):
        cleaned = cleaned[: -len("/__init__")]
    # Replace / with .
    return cleaned.replace("/", ".")


def _extract_symbols_from_class(
    class_node: ast.ClassDef,
) -> list[SymbolInfo]:
    """Extract methods from a class definition."""
    symbols: list[SymbolInfo] = []
    for node in ast.iter_child_nodes(class_node):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(
                SymbolInfo(
                    name=node.name,
                    kind="method",
                    line=node.lineno,
                    docstring=_get_docstring(node),
                    decorators=[_decorator_to_str(d) for d in node.decorator_list],
                    parent_class=class_node.name,
                )
            )
    return symbols


def _extract_imports(tree: ast.Module) -> list[ImportInfo]:
    """Extract all import statements from the AST."""
    imports: list[ImportInfo] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(
                    ImportInfo(
                        module=alias.name,
                        names=[],
                        is_relative=False,
                        line=node.lineno,
                    )
                )
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            names = [alias.name for alias in node.names]
            imports.append(
                ImportInfo(
                    module=module_name,
                    names=names,
                    is_relative=node.level > 0,
                    line=node.lineno,
                )
            )
    return imports


def extract_module_info(source: str, module_path: str) -> ModuleInfo:
    """Parse a Python source file and extract module-level information.

    Args:
        source: The Python source code as a string.
        module_path: Relative path to the module file (e.g. "src/server.py").

    Returns:
        ModuleInfo with symbols, imports, and any parse error.
    """
    module_name = _path_to_module_name(module_path)

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        logger.debug("AST parse failed for %s: %s", module_path, exc)
        return ModuleInfo(
            path=module_path,
            module_name=module_name,
            parse_error=str(exc),
        )

    symbols: list[SymbolInfo] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(
                SymbolInfo(
                    name=node.name,
                    kind="function",
                    line=node.lineno,
                    docstring=_get_docstring(node),
                    decorators=[_decorator_to_str(d) for d in node.decorator_list],
                )
            )
        elif isinstance(node, ast.ClassDef):
            symbols.append(
                SymbolInfo(
                    name=node.name,
                    kind="class",
                    line=node.lineno,
                    docstring=_get_docstring(node),
                    decorators=[_decorator_to_str(d) for d in node.decorator_list],
                )
            )
            # Also extract methods from the class
            symbols.extend(_extract_symbols_from_class(node))

    imports = _extract_imports(tree)

    return ModuleInfo(
        path=module_path,
        module_name=module_name,
        symbols=symbols,
        imports=imports,
    )
