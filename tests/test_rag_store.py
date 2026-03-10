"""Tests for the RAG SQLite store."""

import pytest

from rag.store.sqlite import RagStore, _blob_to_floats, _cosine_similarity, _floats_to_blob
from rag.types import Chunk, DocumentRecord


@pytest.fixture
def store():
    """Create an in-memory RagStore for testing."""
    s = RagStore(":memory:")
    s.init_db()
    yield s
    s.close()


class TestStoreInit:
    def test_creates_tables(self, store):
        stats = store.get_stats()
        assert stats["documents"] == 0
        assert stats["chunks"] == 0

    def test_double_init_is_safe(self, store):
        store.init_db()
        stats = store.get_stats()
        assert stats["documents"] == 0


class TestDocumentOps:
    def test_upsert_document(self, store):
        doc = DocumentRecord(
            doc_id="d1", repo_ref="main", path="server.py",
            language="python", kind="source", file_hash="hash1",
        )
        store.upsert_document(doc)
        stats = store.get_stats()
        assert stats["documents"] == 1

    def test_get_document_hash(self, store):
        doc = DocumentRecord(
            doc_id="d1", repo_ref="main", path="server.py",
            language="python", kind="source", file_hash="hash1",
        )
        store.upsert_document(doc)
        assert store.get_document_hash("main", "server.py") == "hash1"

    def test_get_document_hash_missing(self, store):
        assert store.get_document_hash("main", "missing.py") is None

    def test_upsert_replaces(self, store):
        doc1 = DocumentRecord(
            doc_id="d1", repo_ref="main", path="server.py",
            language="python", kind="source", file_hash="hash1",
        )
        doc2 = DocumentRecord(
            doc_id="d1", repo_ref="main", path="server.py",
            language="python", kind="source", file_hash="hash2",
        )
        store.upsert_document(doc1)
        store.upsert_document(doc2)
        assert store.get_document_hash("main", "server.py") == "hash2"
        assert store.get_stats()["documents"] == 1


class TestChunkOps:
    def test_upsert_chunks(self, store):
        doc = DocumentRecord(
            doc_id="d1", repo_ref="main", path="server.py",
            language="python", kind="source", file_hash="hash1",
        )
        store.upsert_document(doc)

        chunks = [
            Chunk(
                chunk_id="c1", doc_id="d1", path="server.py",
                kind="source", language="python", text="def foo(): pass",
                start_line=1, end_line=1, symbols=["foo"], chunk_hash="chash1",
            ),
        ]
        store.upsert_chunks(chunks, repo_ref="main")
        assert store.get_stats()["chunks"] == 1

    def test_upsert_with_embeddings(self, store):
        doc = DocumentRecord(
            doc_id="d1", repo_ref="main", path="server.py",
            language="python", kind="source", file_hash="hash1",
        )
        store.upsert_document(doc)

        chunks = [
            Chunk(
                chunk_id="c1", doc_id="d1", path="server.py",
                kind="source", language="python", text="def foo(): pass",
                start_line=1, end_line=1, chunk_hash="chash1",
            ),
        ]
        embeddings = [[1.0, 0.0, 0.0]]
        store.upsert_chunks(chunks, embeddings=embeddings, embedding_model="test", repo_ref="main")
        assert store.get_stats()["chunks"] == 1

    def test_delete_chunks_for_doc(self, store):
        doc = DocumentRecord(
            doc_id="d1", repo_ref="main", path="server.py",
            language="python", kind="source", file_hash="hash1",
        )
        store.upsert_document(doc)

        chunks = [
            Chunk(
                chunk_id="c1", doc_id="d1", path="server.py",
                kind="source", language="python", text="code",
                start_line=1, end_line=1, chunk_hash="ch1",
            ),
            Chunk(
                chunk_id="c2", doc_id="d1", path="server.py",
                kind="source", language="python", text="more code",
                start_line=2, end_line=3, chunk_hash="ch2",
            ),
        ]
        store.upsert_chunks(chunks, repo_ref="main")
        deleted = store.delete_chunks_for_doc("d1")
        assert deleted == 2
        assert store.get_stats()["chunks"] == 0

    def test_delete_by_repo_ref(self, store):
        for i in range(3):
            doc = DocumentRecord(
                doc_id=f"d{i}", repo_ref="main", path=f"file{i}.py",
                language="python", kind="source", file_hash=f"h{i}",
            )
            store.upsert_document(doc)

        store.delete_by_repo_ref("main")
        assert store.get_stats()["documents"] == 0


class TestSearch:
    def test_search_by_text(self, store):
        doc = DocumentRecord(
            doc_id="d1", repo_ref="main", path="store.py",
            language="python", kind="source", file_hash="h1",
        )
        store.upsert_document(doc)

        chunks = [
            Chunk(
                chunk_id="c1", doc_id="d1", path="store.py",
                kind="source", language="python",
                text="def store_cue(cue_id): return f'store cue {cue_id}'",
                start_line=1, end_line=1, symbols=["store_cue"], chunk_hash="ch1",
            ),
            Chunk(
                chunk_id="c2", doc_id="d1", path="store.py",
                kind="source", language="python",
                text="def delete_cue(cue_id): return f'delete cue {cue_id}'",
                start_line=2, end_line=2, symbols=["delete_cue"], chunk_hash="ch2",
            ),
        ]
        store.upsert_chunks(chunks, repo_ref="main")

        hits = store.search_by_text("store_cue")
        assert len(hits) >= 1
        assert hits[0].path == "store.py"

    def test_search_by_embedding(self, store):
        doc = DocumentRecord(
            doc_id="d1", repo_ref="main", path="store.py",
            language="python", kind="source", file_hash="h1",
        )
        store.upsert_document(doc)

        chunks = [
            Chunk(
                chunk_id="c1", doc_id="d1", path="store.py",
                kind="source", language="python", text="store cue",
                start_line=1, end_line=1, chunk_hash="ch1",
            ),
        ]
        embeddings = [[1.0, 0.5, 0.0]]
        store.upsert_chunks(chunks, embeddings=embeddings, embedding_model="test", repo_ref="main")

        hits = store.search_by_embedding([1.0, 0.5, 0.0], top_k=5)
        assert len(hits) == 1
        assert hits[0].score > 0.99

    def test_search_by_path(self, store):
        doc = DocumentRecord(
            doc_id="d1", repo_ref="main", path="src/commands/store.py",
            language="python", kind="source", file_hash="h1",
        )
        store.upsert_document(doc)

        chunks = [
            Chunk(
                chunk_id="c1", doc_id="d1", path="src/commands/store.py",
                kind="source", language="python", text="code",
                start_line=1, end_line=10, chunk_hash="ch1",
            ),
        ]
        store.upsert_chunks(chunks, repo_ref="main")

        result = store.search_by_path("src/commands/%")
        assert len(result) == 1
        assert result[0].path == "src/commands/store.py"


class TestEmbeddingSerialization:
    def test_roundtrip(self):
        original = [1.0, 2.5, -3.14, 0.0]
        blob = _floats_to_blob(original)
        recovered = _blob_to_floats(blob)
        assert len(recovered) == len(original)
        for a, b in zip(original, recovered, strict=True):
            assert abs(a - b) < 1e-5

    def test_cosine_identical(self):
        v = [1.0, 2.0, 3.0]
        assert abs(_cosine_similarity(v, v) - 1.0) < 1e-6

    def test_cosine_orthogonal(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert abs(_cosine_similarity(a, b)) < 1e-6

    def test_cosine_zero_vector(self):
        a = [0.0, 0.0]
        b = [1.0, 1.0]
        assert _cosine_similarity(a, b) == 0.0
