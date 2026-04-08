# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for GraphRAG entity extraction and context expansion."""

import pytest

from src.knowledge_graph.graph_rag import (
    EntityMention,
    expand_entities,
    extract_entities,
    graph_rag_query,
)
from src.knowledge_graph.query import GraphQuery
from src.knowledge_graph.schema import EdgeType, NodeType
from src.knowledge_graph.store import GraphStore


@pytest.fixture
def store():
    s = GraphStore(":memory:")
    s.initialize()
    yield s
    s.close()


def _populate_sample_graph(store: GraphStore) -> None:
    """Populate a sample graph for entity extraction tests."""
    store.upsert_node("fixture:1", NodeType.FIXTURE, label="Mac700 #1")
    store.upsert_node("fixture:2", NodeType.FIXTURE, label="Mac700 #2")
    store.upsert_node("group:3", NodeType.GROUP, label="Front Wash")
    store.upsert_node("sequence:5", NodeType.SEQUENCE, label="Main Show")
    store.upsert_node("executor:1.1", NodeType.EXECUTOR, label="Exec 1")
    store.upsert_node("cue:5.1.0", NodeType.CUE, label="Blackout")
    store.upsert_node("preset:4.2", NodeType.PRESET, label="Blue")

    store.upsert_edge("fixture:1", "group:3", EdgeType.MEMBER_OF)
    store.upsert_edge("fixture:2", "group:3", EdgeType.MEMBER_OF)
    store.upsert_edge("sequence:5", "cue:5.1.0", EdgeType.HAS_CUE)
    store.upsert_edge("sequence:5", "executor:1.1", EdgeType.ASSIGNED_TO)


class TestExtractEntities:
    def test_extracts_fixture_id(self, store):
        _populate_sample_graph(store)
        entities = extract_entities("select fixture 1 and set to 50%", store)
        assert len(entities) == 1
        assert entities[0].node_type == "fixture"
        assert entities[0].identifier == "1"
        assert entities[0].node_id == "fixture:1"

    def test_extracts_group_id(self, store):
        _populate_sample_graph(store)
        entities = extract_entities("apply color to group 3", store)
        assert len(entities) == 1
        assert entities[0].node_type == "group"
        assert entities[0].node_id == "group:3"

    def test_extracts_sequence_id(self, store):
        _populate_sample_graph(store)
        entities = extract_entities("go sequence 5 cue 1", store)
        # Should find sequence:5 but not cue:1 (cue is "5.1.0" in graph)
        seq_mentions = [e for e in entities if e.node_type == "sequence"]
        assert len(seq_mentions) == 1
        assert seq_mentions[0].node_id == "sequence:5"

    def test_extracts_quoted_name(self, store):
        _populate_sample_graph(store)
        entities = extract_entities('select group "Front Wash" and go', store)
        assert len(entities) == 1
        assert entities[0].node_type == "group"
        assert entities[0].identifier == "Front Wash"
        assert entities[0].node_id == "group:3"

    def test_no_match_for_nonexistent(self, store):
        _populate_sample_graph(store)
        entities = extract_entities("select fixture 999", store)
        assert len(entities) == 0

    def test_multiple_entities(self, store):
        _populate_sample_graph(store)
        entities = extract_entities("assign sequence 5 to executor 1", store)
        # executor:1 doesn't exist (it's executor:1.1), so only sequence found
        seq_mentions = [e for e in entities if e.node_type == "sequence"]
        assert len(seq_mentions) == 1

    def test_empty_text(self, store):
        assert extract_entities("", store) == []

    def test_no_entities_in_prose(self, store):
        _populate_sample_graph(store)
        entities = extract_entities("how do I save the show file?", store)
        assert len(entities) == 0

    def test_deduplication(self, store):
        _populate_sample_graph(store)
        entities = extract_entities("fixture 1 and fixture 1 again", store)
        assert len(entities) == 1


class TestExpandEntities:
    def test_expand_single_entity(self, store):
        _populate_sample_graph(store)
        query_engine = GraphQuery(store)

        entities = [EntityMention("group", "3", "group:3")]
        contexts = expand_entities(entities, query_engine, max_depth=1)
        assert len(contexts) == 1

        ctx = contexts[0]
        assert ctx.entity.node_id == "group:3"
        # Neighbors should include fixture:1 and fixture:2 (member_of edges)
        neighbor_ids = {n["node_id"] for n in ctx.neighbors}
        assert "fixture:1" in neighbor_ids
        assert "fixture:2" in neighbor_ids

    def test_expand_with_edges(self, store):
        _populate_sample_graph(store)
        query_engine = GraphQuery(store)

        entities = [EntityMention("sequence", "5", "sequence:5")]
        contexts = expand_entities(entities, query_engine, max_depth=1)
        assert len(contexts) == 1
        assert len(contexts[0].edges) > 0

    def test_expand_empty_entity_list(self, store):
        query_engine = GraphQuery(store)
        assert expand_entities([], query_engine) == []


class TestGraphRagQuery:
    def test_full_pipeline(self, store):
        _populate_sample_graph(store)
        contexts = graph_rag_query("what is assigned to sequence 5?", store)
        assert len(contexts) >= 1
        assert contexts[0].entity.node_type == "sequence"
        assert len(contexts[0].neighbors) > 0

    def test_no_entities_returns_empty(self, store):
        _populate_sample_graph(store)
        contexts = graph_rag_query("how do I save the show?", store)
        assert contexts == []

    def test_to_dict_format(self, store):
        _populate_sample_graph(store)
        contexts = graph_rag_query("check group 3", store)
        assert len(contexts) == 1
        d = contexts[0].to_dict()
        assert "entity" in d
        assert "neighbors" in d
        assert "edges" in d
        assert d["entity"]["type"] == "group"
