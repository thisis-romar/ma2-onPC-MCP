# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for the process engine."""

from __future__ import annotations

import pytest

from src.knowledge_graph.analysis.process_engine import (
    find_entry_points,
    trace_process,
)
from src.knowledge_graph.schema import EdgeType, NodeType
from src.knowledge_graph.store import GraphStore


@pytest.fixture
def store():
    s = GraphStore(":memory:")
    s.initialize()
    yield s
    s.close()


class TestTraceProcess:
    def test_simple_chain(self, store):
        for n in ["a", "b", "c"]:
            store.upsert_node(f"module:{n}", NodeType.MODULE, label=n)
        store.upsert_edge("module:a", "module:b", EdgeType.IMPORTS)
        store.upsert_edge("module:b", "module:c", EdgeType.IMPORTS)
        trace = trace_process(store, "module:a", max_depth=5)
        assert trace.entry_point == "module:a"
        assert len(trace.steps) == 3
        assert trace.steps[0].node_id == "module:a"
        assert trace.steps[-1].node_id == "module:c"

    def test_with_cycle(self, store):
        for n in ["a", "b"]:
            store.upsert_node(f"module:{n}", NodeType.MODULE, label=n)
        store.upsert_edge("module:a", "module:b", EdgeType.IMPORTS)
        store.upsert_edge("module:b", "module:a", EdgeType.IMPORTS)
        trace = trace_process(store, "module:a")
        assert len(trace.steps) == 2  # visits a and b, doesn't loop

    def test_max_depth(self, store):
        for n in ["a", "b", "c", "d"]:
            store.upsert_node(f"module:{n}", NodeType.MODULE, label=n)
        store.upsert_edge("module:a", "module:b", EdgeType.IMPORTS)
        store.upsert_edge("module:b", "module:c", EdgeType.IMPORTS)
        store.upsert_edge("module:c", "module:d", EdgeType.IMPORTS)
        trace = trace_process(store, "module:a", max_depth=1)
        assert len(trace.steps) == 2  # a (depth 0) + b (depth 1)


class TestFindEntryPoints:
    def test_basic(self, store):
        for n in ["root", "lib", "util"]:
            store.upsert_node(f"module:{n}", NodeType.MODULE, label=n)
        store.upsert_edge("module:root", "module:lib", EdgeType.IMPORTS)
        store.upsert_edge("module:root", "module:util", EdgeType.IMPORTS)
        entries = find_entry_points(store)
        assert entries == ["module:root"]

    def test_no_imports_all_entry(self, store):
        store.upsert_node("module:a", NodeType.MODULE)
        store.upsert_node("module:b", NodeType.MODULE)
        entries = find_entry_points(store)
        assert len(entries) == 2
