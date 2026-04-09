# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
normalizer.py — Convert ModuleInfo into graph nodes and edges.

Takes the output of the extractor and writes MODULE, SYMBOL, and PACKAGE
nodes plus DEFINES, IMPORTS, and CONTAINS edges to a GraphStore.
"""

from __future__ import annotations

import logging

from ..schema import EdgeType, NodeType, node_id
from ..store import GraphStore
from .extractor import ModuleInfo

logger = logging.getLogger(__name__)


def _package_parts(module_name: str) -> list[str]:
    """Return all parent package dotted names for a module.

    Example:
        "src.knowledge_graph.store" -> ["src", "src.knowledge_graph"]
    """
    parts = module_name.split(".")
    packages: list[str] = []
    for i in range(1, len(parts)):
        packages.append(".".join(parts[:i]))
    return packages


def normalize_to_graph(
    store: GraphStore,
    module_info: ModuleInfo,
    repo_root: str = "",
) -> dict[str, int]:
    """Convert a ModuleInfo into graph nodes and edges.

    Creates:
    - MODULE node for the module itself
    - SYMBOL nodes for each extracted symbol (function, class, method)
    - DEFINES edges from module to each symbol
    - IMPORTS edges from module to each imported module
    - PACKAGE nodes for parent packages, with CONTAINS edges

    Args:
        store: The GraphStore to write to.
        module_info: Extracted module information.
        repo_root: Optional repo root prefix (unused, for future path normalization).

    Returns:
        Counts dict: {"nodes": N, "edges": N}
    """
    node_count = 0
    edge_count = 0

    # --- MODULE node ---
    mod_nid = node_id(NodeType.MODULE, module_info.module_name)
    mod_props: dict[str, str | None] = {"path": module_info.path}
    if module_info.parse_error:
        mod_props["parse_error"] = module_info.parse_error
    store.upsert_node(mod_nid, NodeType.MODULE, label=module_info.module_name, props=mod_props)
    node_count += 1

    # --- SYMBOL nodes + DEFINES edges ---
    for sym in module_info.symbols:
        qualified_name = f"{module_info.module_name}.{sym.name}"
        sym_nid = node_id(NodeType.SYMBOL, qualified_name)
        sym_props: dict[str, object] = {
            "kind": sym.kind,
            "line": sym.line,
        }
        if sym.docstring:
            sym_props["docstring"] = sym.docstring
        if sym.decorators:
            sym_props["decorators"] = sym.decorators
        if sym.parent_class:
            sym_props["parent_class"] = sym.parent_class

        store.upsert_node(sym_nid, NodeType.SYMBOL, label=sym.name, props=sym_props)
        node_count += 1

        # DEFINES edge: module -> symbol
        store.upsert_edge(mod_nid, sym_nid, EdgeType.DEFINES)
        edge_count += 1

    # --- IMPORTS edges ---
    for imp in module_info.imports:
        if not imp.module:
            continue  # Skip bare relative imports with no module name

        target_mod_nid = node_id(NodeType.MODULE, imp.module)

        # Create a stub MODULE node for the target if it doesn't exist yet
        existing = store.get_node(target_mod_nid)
        if existing is None:
            store.upsert_node(
                target_mod_nid,
                NodeType.MODULE,
                label=imp.module,
                props={"stub": True},
            )
            node_count += 1

        # IMPORTS edge: this module -> imported module
        edge_props: dict[str, object] = {}
        if imp.names:
            edge_props["names"] = imp.names
        if imp.is_relative:
            edge_props["is_relative"] = True
        store.upsert_edge(mod_nid, target_mod_nid, EdgeType.IMPORTS, props=edge_props)
        edge_count += 1

    # --- PACKAGE nodes + CONTAINS edges ---
    packages = _package_parts(module_info.module_name)
    for pkg_name in packages:
        pkg_nid = node_id(NodeType.PACKAGE, pkg_name)
        existing = store.get_node(pkg_nid)
        if existing is None:
            store.upsert_node(pkg_nid, NodeType.PACKAGE, label=pkg_name)
            node_count += 1

    # CONTAINS edges: each package contains the module or child package
    if packages:
        # Innermost package contains the module
        innermost_pkg = packages[-1]
        pkg_nid = node_id(NodeType.PACKAGE, innermost_pkg)
        store.upsert_edge(pkg_nid, mod_nid, EdgeType.CONTAINS)
        edge_count += 1

        # Each package contains its direct child package
        for i in range(len(packages) - 1):
            parent_nid = node_id(NodeType.PACKAGE, packages[i])
            child_nid = node_id(NodeType.PACKAGE, packages[i + 1])
            store.upsert_edge(parent_nid, child_nid, EdgeType.CONTAINS)
            edge_count += 1

    return {"nodes": node_count, "edges": edge_count}
