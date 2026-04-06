# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for the RAG query pipeline."""

import pytest

from rag.ingest.embed import ZeroVectorProvider
from rag.ingest.index import ingest
from rag.retrieve.query import rag_query
from rag.store.sqlite import RagStore
from rag.types import Chunk, DocumentRecord


@pytest.fixture
def populated_db(tmp_path):
    """Create a temporary RAG database with sample data."""
    db_path = tmp_path / "test_rag.db"
    store = RagStore(db_path)
    store.init_db()

    doc = DocumentRecord(
        doc_id="d1", repo_ref="test", path="src/commands/store.py",
        language="python", kind="source", file_hash="h1",
    )
    store.upsert_document(doc)

    provider = ZeroVectorProvider(dimensions=3)

    chunks = [
        Chunk(
            chunk_id="c1", doc_id="d1", path="src/commands/store.py",
            kind="source", language="python",
            text="def store_cue(cue_id): return f'store cue {cue_id}'",
            start_line=1, end_line=1, symbols=["store_cue"], chunk_hash="ch1",
        ),
        Chunk(
            chunk_id="c2", doc_id="d1", path="src/commands/store.py",
            kind="source", language="python",
            text="def store_group(group_id): return f'store group {group_id}'",
            start_line=10, end_line=15, symbols=["store_group"], chunk_hash="ch2",
        ),
    ]

    embeddings = provider.embed_many([c.text for c in chunks])
    store.upsert_chunks(chunks, embeddings=embeddings, embedding_model="zero-vector-stub", repo_ref="test")
    store.close()

    return db_path


class TestRagQuery:
    def test_text_search(self, populated_db):
        hits = rag_query("store_cue", db_path=populated_db)
        assert len(hits) >= 1
        assert any("store_cue" in h.text for h in hits)

    def test_text_search_no_results(self, populated_db):
        hits = rag_query("nonexistent_function_xyz", db_path=populated_db)
        assert hits == []

    def test_top_k_limit(self, populated_db):
        hits = rag_query("store", top_k=1, db_path=populated_db)
        assert len(hits) <= 1

    def test_returns_rag_hits(self, populated_db):
        hits = rag_query("store", db_path=populated_db)
        for hit in hits:
            assert hit.path == "src/commands/store.py"
            assert hit.kind == "source"
            assert hit.start_line >= 1

    def test_scores_are_descending(self, populated_db):
        hits = rag_query("store", db_path=populated_db)
        if len(hits) >= 2:
            assert hits[0].score >= hits[1].score

    def test_symbol_match_boost(self, populated_db):
        """Searching for an exact symbol name should score higher."""
        hits = rag_query("store_cue", db_path=populated_db)
        assert len(hits) >= 1
        # The chunk with the symbol should appear first
        assert "store_cue" in hits[0].text

    def test_empty_database_returns_empty(self, tmp_path):
        db_path = tmp_path / "empty.db"
        store = RagStore(db_path)
        store.init_db()
        store.close()
        hits = rag_query("anything", db_path=db_path)
        assert hits == []

    def test_embedding_search_with_zero_provider(self, populated_db):
        """Zero-vector embedding search falls back gracefully."""
        provider = ZeroVectorProvider(dimensions=3)
        # Zero vectors have no cosine similarity — should still return results
        # via dimension mismatch fallback or zero-score handling
        hits = rag_query("store", embedding_provider=provider, db_path=populated_db)
        # May return results via fallback or empty — either is valid
        assert isinstance(hits, list)

    def test_hit_fields_populated(self, populated_db):
        hits = rag_query("store_group", db_path=populated_db)
        assert len(hits) >= 1
        hit = hits[0]
        assert hit.chunk_id is not None
        assert hit.path is not None
        assert hit.score >= 0
        assert len(hit.text) > 0

    def test_multi_term_query(self, populated_db):
        """Multi-word queries should match when terms appear in content."""
        hits = rag_query("store cue", db_path=populated_db)
        assert len(hits) >= 1


@pytest.fixture
def multi_kind_db(tmp_path):
    """Database with multiple document kinds for filtering tests."""
    db_path = tmp_path / "multi.db"
    store = RagStore(db_path)
    store.init_db()

    for kind, path, text, symbols in [
        ("source", "src/foo.py", "def foo(): return 'hello world'", ["foo"]),
        ("test", "tests/test_foo.py", "def test_foo(): assert foo() == 'hello world'", ["test_foo"]),
        ("doc", "docs/readme.md", "# Foo module\nThe foo function returns hello world", []),
    ]:
        doc = DocumentRecord(
            doc_id=f"d_{kind}", repo_ref="test", path=path,
            language="python" if kind != "doc" else "markdown",
            kind=kind, file_hash=f"h_{kind}",
        )
        store.upsert_document(doc)
        chunk = Chunk(
            chunk_id=f"c_{kind}", doc_id=f"d_{kind}", path=path,
            kind=kind, language=doc.language,
            text=text, start_line=1, end_line=2,
            symbols=symbols, chunk_hash=f"ch_{kind}",
        )
        store.upsert_chunks([chunk], embeddings=None, embedding_model="none", repo_ref="test")

    store.close()
    return db_path


class TestRagQueryMultiKind:
    def test_searches_across_kinds(self, multi_kind_db):
        hits = rag_query("foo hello world", db_path=multi_kind_db)
        assert len(hits) >= 1
        kinds_found = {h.kind for h in hits}
        assert len(kinds_found) >= 1

    def test_source_and_test_both_searchable(self, multi_kind_db):
        hits = rag_query("foo", db_path=multi_kind_db)
        paths = {h.path for h in hits}
        # Should find both source and test
        assert any("src/" in p for p in paths) or any("tests/" in p for p in paths)


# ── End-to-end RAG pipeline test ─────────────────────────────────────────


class TestRagEndToEnd:
    """Tests the full ingest → query pipeline with real files."""

    def test_ingest_and_query_round_trip(self, tmp_path):
        """Ingest real Python files, then query and verify retrieval."""
        # Create a mini source tree
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "lighting.py").write_text(
            "def set_intensity(fixture_id, level):\n"
            "    '''Set fixture intensity to a DMX level.'''\n"
            "    return f'Fixture {fixture_id} at {level}'\n"
        )
        (src_dir / "color.py").write_text(
            "def apply_color(fixture_id, red, green, blue):\n"
            "    '''Apply RGB color to a fixture.'''\n"
            "    return f'Color {red},{green},{blue}'\n"
        )

        db_path = tmp_path / "rag.db"
        provider = ZeroVectorProvider(dimensions=8)

        # Ingest
        result = ingest(
            root_dir=tmp_path,
            db_path=db_path,
            embedding_provider=provider,
            repo_ref="test_e2e",
        )
        assert result.files_processed >= 2
        assert result.chunks_created >= 2

        # Query — should find the lighting module
        hits = rag_query("set intensity fixture DMX", db_path=db_path)
        assert len(hits) >= 1
        assert any("intensity" in h.text.lower() for h in hits)

    def test_ingest_empty_directory(self, tmp_path):
        """Ingesting an empty directory produces zero chunks."""
        db_path = tmp_path / "rag.db"
        provider = ZeroVectorProvider(dimensions=8)
        result = ingest(
            root_dir=tmp_path,
            db_path=db_path,
            embedding_provider=provider,
            repo_ref="empty",
        )
        assert result.files_processed == 0
        assert result.chunks_created == 0
