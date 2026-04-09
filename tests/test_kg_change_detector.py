# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for the change detector."""

from __future__ import annotations

import pytest

from src.knowledge_graph.analysis.change_detector import (
    ChangeSet,
    detect_changes,
    impacted_by_changes,
    symbols_to_hash_map,
)
from src.knowledge_graph.schema import EdgeType, NodeType
from src.knowledge_graph.store import GraphStore


@pytest.fixture
def store():
    s = GraphStore(":memory:")
    s.initialize()
    yield s
    s.close()


class TestDetectChanges:
    def test_added(self):
        cs = detect_changes({}, {"sym:a": "h1"})
        assert cs.added == ["sym:a"]
        assert not cs.removed and not cs.modified

    def test_removed(self):
        cs = detect_changes({"sym:a": "h1"}, {})
        assert cs.removed == ["sym:a"]

    def test_modified(self):
        cs = detect_changes({"sym:a": "h1"}, {"sym:a": "h2"})
        assert cs.modified == ["sym:a"]

    def test_empty(self):
        cs = detect_changes({"sym:a": "h1"}, {"sym:a": "h1"})
        assert cs.is_empty()

    def test_combined(self):
        old = {"a": "1", "b": "2", "c": "3"}
        new = {"a": "1", "b": "X", "d": "4"}
        cs = detect_changes(old, new)
        assert cs.added == ["d"]
        assert cs.removed == ["c"]
        assert cs.modified == ["b"]


class TestImpactedByChanges:
    def test_basic(self, store):
        store.upsert_node("module:m", NodeType.MODULE, label="m")
        store.upsert_node("symbol:m.foo", NodeType.SYMBOL, label="foo")
        store.upsert_edge("module:m", "symbol:m.foo", EdgeType.DEFINES)
        store.upsert_node("module:caller", NodeType.MODULE, label="caller")
        store.upsert_edge("module:caller", "module:m", EdgeType.IMPORTS)
        cs = ChangeSet(modified=["symbol:m.foo"])
        result = impacted_by_changes(store, cs, max_depth=2)
        assert "module:caller" in result


class TestSymbolsToHashMap:
    def test_basic(self, store):
        store.upsert_node("symbol:a", NodeType.SYMBOL, props={"docstring": "hello"})
        store.upsert_node("symbol:b", NodeType.SYMBOL, props={"docstring": "world"})
        hmap = symbols_to_hash_map(store)
        assert len(hmap) == 2
        assert hmap["symbol:a"] != hmap["symbol:b"]
