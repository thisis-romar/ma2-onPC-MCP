# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
repo_scanner.py — Walk a directory tree and index all Python files.

Discovers .py files, extracts symbols and imports, and normalizes them
into a GraphStore as MODULE, SYMBOL, and PACKAGE nodes with their edges.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ..schema import EdgeType, NodeType, node_id
from ..store import GraphStore
from .extractor import extract_module_info
from .normalizer import normalize_to_graph

logger = logging.getLogger(__name__)

_DEFAULT_EXCLUDE = [
    ".git",
    "__pycache__",
    ".venv",
    "node_modules",
    ".pytest_cache",
]


def scan_repository(
    store: GraphStore,
    root: Path,
    exclude_patterns: list[str] | None = None,
) -> dict[str, int]:
    """Walk a directory tree and index all Python files into the graph.

    Creates MODULE, SYMBOL, and PACKAGE nodes with DEFINES, IMPORTS,
    and CONTAINS edges.

    Args:
        store: The GraphStore to populate.
        root: Root directory to scan.
        exclude_patterns: Directory names to skip. Defaults to common
            non-source directories (.git, __pycache__, .venv, etc.).

    Returns:
        Aggregate counts: {"modules": N, "symbols": N, "packages": N,
                           "nodes": N, "edges": N}
    """
    excludes = set(exclude_patterns if exclude_patterns is not None else _DEFAULT_EXCLUDE)

    total_nodes = 0
    total_edges = 0
    module_count = 0
    symbol_count = 0

    # First pass: detect packages (dirs with __init__.py) and index all .py files
    packages_seen: set[str] = set()
    root_resolved = root.resolve()

    for py_file in sorted(root_resolved.rglob("*.py")):
        # Check if any parent directory is in the exclude list
        rel = py_file.relative_to(root_resolved)
        if any(part in excludes for part in rel.parts):
            continue

        module_path = str(rel)
        try:
            source = py_file.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            logger.warning("Cannot read %s: %s", py_file, exc)
            continue

        # Extract and normalize
        info = extract_module_info(source, module_path)
        counts = normalize_to_graph(store, info, repo_root=str(root_resolved))
        total_nodes += counts["nodes"]
        total_edges += counts["edges"]
        module_count += 1
        symbol_count += len(info.symbols)

        # Track packages from this module's path
        parts = rel.parts[:-1]  # directory parts (exclude filename)
        for i in range(len(parts)):
            pkg_dir = root_resolved / Path(*parts[: i + 1])
            pkg_name = ".".join(parts[: i + 1])
            if pkg_name not in packages_seen and (pkg_dir / "__init__.py").exists():
                packages_seen.add(pkg_name)

    # Ensure all detected packages have PACKAGE nodes and CONTAINS edges
    # (normalize_to_graph already creates packages from module paths,
    # but explicit __init__.py detection catches packages that only contain
    # sub-packages with no direct .py files)
    for pkg_name in sorted(packages_seen):
        pkg_nid = node_id(NodeType.PACKAGE, pkg_name)
        existing = store.get_node(pkg_nid)
        if existing is None:
            store.upsert_node(pkg_nid, NodeType.PACKAGE, label=pkg_name)
            total_nodes += 1

        # Ensure parent->child CONTAINS edges for explicit packages
        parts = pkg_name.split(".")
        if len(parts) > 1:
            parent_name = ".".join(parts[:-1])
            parent_nid = node_id(NodeType.PACKAGE, parent_name)
            parent_existing = store.get_node(parent_nid)
            if parent_existing is None:
                store.upsert_node(parent_nid, NodeType.PACKAGE, label=parent_name)
                total_nodes += 1
            # Upsert is idempotent — safe to call even if the edge exists
            store.upsert_edge(parent_nid, pkg_nid, EdgeType.CONTAINS)
            # Don't increment edge_count since upsert may not create new

    package_count = store.node_count(NodeType.PACKAGE)

    return {
        "modules": module_count,
        "symbols": symbol_count,
        "packages": package_count,
        "nodes": total_nodes,
        "edges": total_edges,
    }
