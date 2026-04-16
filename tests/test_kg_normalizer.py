# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for the knowledge graph normalizer (ModuleInfo -> graph nodes/edges)."""

from __future__ import annotations

import pytest

from src.knowledge_graph.parsers.extractor import ImportInfo, ModuleInfo, SymbolInfo
from src.knowledge_graph.parsers.normalizer import normalize_to_graph
from src.knowledge_graph.schema import EdgeType, NodeType, node_id
from src.knowledge_graph.store import GraphStore


@pytest.fixture
def store():
    """Create an in-memory GraphStore for testing."""
    s = GraphStore(":memory:")
    s.initialize()
    yield s
    s.close()


class TestModuleAndSymbolNodes:
    def test_creates_module_node(self, store):
        info = ModuleInfo(path="src/server.py", module_name="src.server")
        normalize_to_graph(store, info)

        mod_nid = node_id(NodeType.MODULE, "src.server")
        node = store.get_node(mod_nid)
        assert node is not None
        assert node.node_type == "module"
        assert node.label == "src.server"
        assert node.props["path"] == "src/server.py"

    def test_creates_symbol_nodes(self, store):
        info = ModuleInfo(
            path="src/server.py",
            module_name="src.server",
            symbols=[
                SymbolInfo(name="start", kind="function", line=10, docstring="Start the server."),
                SymbolInfo(name="AppConfig", kind="class", line=25),
            ],
        )
        normalize_to_graph(store, info)

        # Module + 2 symbols
        assert store.node_count(NodeType.SYMBOL) == 2

        sym1_nid = node_id(NodeType.SYMBOL, "src.server.start")
        sym1 = store.get_node(sym1_nid)
        assert sym1 is not None
        assert sym1.label == "start"
        assert sym1.props["kind"] == "function"
        assert sym1.props["line"] == 10
        assert sym1.props["docstring"] == "Start the server."

        sym2_nid = node_id(NodeType.SYMBOL, "src.server.AppConfig")
        sym2 = store.get_node(sym2_nid)
        assert sym2 is not None
        assert sym2.label == "AppConfig"
        assert sym2.props["kind"] == "class"

    def test_symbol_decorators_stored(self, store):
        info = ModuleInfo(
            path="dec.py",
            module_name="dec",
            symbols=[
                SymbolInfo(
                    name="handler",
                    kind="function",
                    line=5,
                    decorators=["app.route", "require_scope"],
                ),
            ],
        )
        normalize_to_graph(store, info)
        sym_nid = node_id(NodeType.SYMBOL, "dec.handler")
        sym = store.get_node(sym_nid)
        assert sym is not None
        assert sym.props["decorators"] == ["app.route", "require_scope"]

    def test_method_parent_class_stored(self, store):
        info = ModuleInfo(
            path="cls.py",
            module_name="cls",
            symbols=[
                SymbolInfo(name="get", kind="method", line=3, parent_class="MyStore"),
            ],
        )
        normalize_to_graph(store, info)
        sym_nid = node_id(NodeType.SYMBOL, "cls.get")
        sym = store.get_node(sym_nid)
        assert sym is not None
        assert sym.props["parent_class"] == "MyStore"


class TestDefinesEdges:
    def test_module_defines_symbols(self, store):
        info = ModuleInfo(
            path="mod.py",
            module_name="mod",
            symbols=[
                SymbolInfo(name="foo", kind="function", line=1),
                SymbolInfo(name="bar", kind="function", line=5),
            ],
        )
        normalize_to_graph(store, info)

        mod_nid = node_id(NodeType.MODULE, "mod")
        edges = store.get_edges_from(mod_nid, EdgeType.DEFINES)
        assert len(edges) == 2
        targets = {e.target_id for e in edges}
        assert node_id(NodeType.SYMBOL, "mod.foo") in targets
        assert node_id(NodeType.SYMBOL, "mod.bar") in targets


class TestImportsEdges:
    def test_imports_create_edges(self, store):
        info = ModuleInfo(
            path="src/server.py",
            module_name="src.server",
            imports=[
                ImportInfo(module="os", names=["path"], line=1),
                ImportInfo(module="src.store", names=["GraphStore"], line=2),
            ],
        )
        normalize_to_graph(store, info)

        mod_nid = node_id(NodeType.MODULE, "src.server")
        edges = store.get_edges_from(mod_nid, EdgeType.IMPORTS)
        assert len(edges) == 2
        targets = {e.target_id for e in edges}
        assert node_id(NodeType.MODULE, "os") in targets
        assert node_id(NodeType.MODULE, "src.store") in targets

    def test_imports_create_stub_module_nodes(self, store):
        info = ModuleInfo(
            path="src/server.py",
            module_name="src.server",
            imports=[
                ImportInfo(module="external.lib", names=["Thing"], line=1),
            ],
        )
        normalize_to_graph(store, info)

        stub_nid = node_id(NodeType.MODULE, "external.lib")
        stub = store.get_node(stub_nid)
        assert stub is not None
        assert stub.props.get("stub") is True

    def test_imports_edge_props(self, store):
        info = ModuleInfo(
            path="src/server.py",
            module_name="src.server",
            imports=[
                ImportInfo(module="schema", names=["NodeType", "EdgeType"], is_relative=True, line=3),
            ],
        )
        normalize_to_graph(store, info)

        mod_nid = node_id(NodeType.MODULE, "src.server")
        edges = store.get_edges_from(mod_nid, EdgeType.IMPORTS)
        assert len(edges) == 1
        assert edges[0].props["names"] == ["NodeType", "EdgeType"]
        assert edges[0].props["is_relative"] is True

    def test_empty_module_import_skipped(self, store):
        """Bare relative imports with empty module name are skipped."""
        info = ModuleInfo(
            path="pkg/__init__.py",
            module_name="pkg",
            imports=[
                ImportInfo(module="", names=["something"], is_relative=True, line=1),
            ],
        )
        normalize_to_graph(store, info)
        mod_nid = node_id(NodeType.MODULE, "pkg")
        edges = store.get_edges_from(mod_nid, EdgeType.IMPORTS)
        assert len(edges) == 0


class TestPackageDetection:
    def test_packages_created_from_path(self, store):
        info = ModuleInfo(
            path="src/knowledge_graph/store.py",
            module_name="src.knowledge_graph.store",
        )
        normalize_to_graph(store, info)

        # Should create packages: "src" and "src.knowledge_graph"
        pkg1 = store.get_node(node_id(NodeType.PACKAGE, "src"))
        assert pkg1 is not None
        assert pkg1.label == "src"

        pkg2 = store.get_node(node_id(NodeType.PACKAGE, "src.knowledge_graph"))
        assert pkg2 is not None
        assert pkg2.label == "src.knowledge_graph"

    def test_contains_edges(self, store):
        info = ModuleInfo(
            path="src/knowledge_graph/store.py",
            module_name="src.knowledge_graph.store",
        )
        normalize_to_graph(store, info)

        # src.knowledge_graph CONTAINS the module
        pkg_nid = node_id(NodeType.PACKAGE, "src.knowledge_graph")
        mod_nid = node_id(NodeType.MODULE, "src.knowledge_graph.store")
        edges = store.get_edges_from(pkg_nid, EdgeType.CONTAINS)
        targets = {e.target_id for e in edges}
        assert mod_nid in targets

        # src CONTAINS src.knowledge_graph
        parent_nid = node_id(NodeType.PACKAGE, "src")
        parent_edges = store.get_edges_from(parent_nid, EdgeType.CONTAINS)
        parent_targets = {e.target_id for e in parent_edges}
        assert pkg_nid in parent_targets

    def test_top_level_module_no_packages(self, store):
        info = ModuleInfo(path="setup.py", module_name="setup")
        normalize_to_graph(store, info)

        assert store.node_count(NodeType.PACKAGE) == 0
        # Module node + no symbols = 1 node
        assert store.node_count(NodeType.MODULE) == 1


class TestIdempotency:
    def test_re_normalize_is_idempotent(self, store):
        info = ModuleInfo(
            path="src/server.py",
            module_name="src.server",
            symbols=[SymbolInfo(name="start", kind="function", line=10)],
            imports=[ImportInfo(module="os", line=1)],
        )

        normalize_to_graph(store, info)
        first_nodes = store.node_count()
        first_edges = store.edge_count()

        # Normalize again — should not duplicate
        normalize_to_graph(store, info)
        assert store.node_count() == first_nodes
        assert store.edge_count() == first_edges


class TestParseErrorModule:
    def test_parse_error_still_creates_module_node(self, store):
        info = ModuleInfo(
            path="broken.py",
            module_name="broken",
            parse_error="invalid syntax (broken.py, line 1)",
        )
        normalize_to_graph(store, info)

        mod_nid = node_id(NodeType.MODULE, "broken")
        node = store.get_node(mod_nid)
        assert node is not None
        assert node.props["parse_error"] == "invalid syntax (broken.py, line 1)"

    def test_counts_returned(self, store):
        info = ModuleInfo(
            path="src/a/b.py",
            module_name="src.a.b",
            symbols=[
                SymbolInfo(name="func1", kind="function", line=1),
                SymbolInfo(name="func2", kind="function", line=5),
            ],
            imports=[ImportInfo(module="os", line=1)],
        )
        counts = normalize_to_graph(store, info)
        # Nodes: 1 module + 2 symbols + 1 stub "os" module + 2 packages ("src", "src.a")
        assert counts["nodes"] >= 4
        # Edges: 2 DEFINES + 1 IMPORTS + CONTAINS edges
        assert counts["edges"] >= 3
