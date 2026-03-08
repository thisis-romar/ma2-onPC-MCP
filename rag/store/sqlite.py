"""SQLite storage backend for the RAG pipeline."""

from __future__ import annotations

import json
import logging
import math
import sqlite3
import struct
from datetime import UTC, datetime
from pathlib import Path

from rag.types import Chunk, DocumentRecord, RagHit

logger = logging.getLogger(__name__)

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class RagStore:
    """SQLite-backed storage for documents and chunks."""

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._db_path = str(db_path)
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Store not initialized — call init_db() first")
        return self._conn

    def init_db(self) -> None:
        """Create tables and indexes from schema.sql."""
        self._conn = sqlite3.connect(self._db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        schema = _SCHEMA_PATH.read_text(encoding="utf-8")
        self._conn.executescript(schema)

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    # ------------------------------------------------------------------
    # Documents
    # ------------------------------------------------------------------

    def upsert_document(self, doc: DocumentRecord) -> None:
        """Insert or replace a document record."""
        now = datetime.now(UTC).isoformat()
        self.conn.execute(
            """
            INSERT OR REPLACE INTO documents (doc_id, repo_ref, path, language, kind, file_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (doc.doc_id, doc.repo_ref, doc.path, doc.language, doc.kind, doc.file_hash, now),
        )
        self.conn.commit()

    def get_document_hash(self, repo_ref: str, path: str) -> str | None:
        """Return the stored file_hash for a document, or None if not found."""
        row = self.conn.execute(
            "SELECT file_hash FROM documents WHERE repo_ref = ? AND path = ?",
            (repo_ref, path),
        ).fetchone()
        return row[0] if row else None

    # ------------------------------------------------------------------
    # Chunks
    # ------------------------------------------------------------------

    def upsert_chunks(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]] | None = None,
        embedding_model: str | None = None,
        repo_ref: str = "worktree",
    ) -> None:
        """Insert or replace chunks, optionally with embeddings."""
        now = datetime.now(UTC).isoformat()
        rows = []
        for i, chunk in enumerate(chunks):
            emb_blob: bytes | None = None
            if embeddings and i < len(embeddings):
                emb_blob = _floats_to_blob(embeddings[i])

            rows.append((
                chunk.chunk_id,
                chunk.doc_id,
                repo_ref,
                chunk.path,
                chunk.kind,
                chunk.language,
                chunk.text,
                chunk.start_line,
                chunk.end_line,
                json.dumps(chunk.symbols),
                chunk.chunk_hash,
                embedding_model,
                emb_blob,
                now,
            ))

        self.conn.executemany(
            """
            INSERT OR REPLACE INTO chunks
            (chunk_id, doc_id, repo_ref, path, kind, language, text,
             start_line, end_line, symbols, chunk_hash, embedding_model, embedding, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        self.conn.commit()

    def delete_chunks_for_doc(self, doc_id: str) -> int:
        """Delete all chunks belonging to a document. Returns count deleted."""
        cursor = self.conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
        self.conn.commit()
        return cursor.rowcount

    def delete_by_repo_ref(self, repo_ref: str) -> None:
        """Delete all documents and their chunks for a given repo_ref."""
        self.conn.execute("DELETE FROM chunks WHERE repo_ref = ?", (repo_ref,))
        self.conn.execute("DELETE FROM documents WHERE repo_ref = ?", (repo_ref,))
        self.conn.commit()

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_by_embedding(self, query_embedding: list[float], top_k: int = 12) -> list[RagHit]:
        """Brute-force cosine similarity search over all chunks with embeddings."""
        rows = self.conn.execute(
            "SELECT chunk_id, path, kind, start_line, end_line, text, embedding FROM chunks WHERE embedding IS NOT NULL"
        ).fetchall()

        scored: list[RagHit] = []
        for chunk_id, path, kind, start_line, end_line, text, emb_blob in rows:
            if emb_blob is None:
                continue
            stored = _blob_to_floats(emb_blob)
            score = _cosine_similarity(query_embedding, stored)
            scored.append(RagHit(
                chunk_id=chunk_id,
                path=path,
                kind=kind,
                start_line=start_line,
                end_line=end_line,
                score=score,
                text=text,
            ))

        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:top_k]

    def search_by_text(self, query: str, top_k: int = 12) -> list[RagHit]:
        """Simple text-based search using SQLite LIKE for keyword matching."""
        pattern = f"%{query}%"
        rows = self.conn.execute(
            """
            SELECT chunk_id, path, kind, start_line, end_line, text
            FROM chunks WHERE text LIKE ? OR symbols LIKE ?
            LIMIT ?
            """,
            (pattern, pattern, top_k),
        ).fetchall()

        return [
            RagHit(
                chunk_id=row[0],
                path=row[1],
                kind=row[2],
                start_line=row[3],
                end_line=row[4],
                score=1.0,  # no scoring for text search
                text=row[5],
            )
            for row in rows
        ]

    def search_by_path(self, path_pattern: str) -> list[Chunk]:
        """Find chunks matching a path pattern (SQL LIKE)."""
        rows = self.conn.execute(
            """
            SELECT chunk_id, doc_id, path, kind, language, text, start_line, end_line, symbols, chunk_hash
            FROM chunks WHERE path LIKE ?
            """,
            (path_pattern,),
        ).fetchall()

        return [
            Chunk(
                chunk_id=row[0],
                doc_id=row[1],
                path=row[2],
                kind=row[3],
                language=row[4],
                text=row[5],
                start_line=row[6],
                end_line=row[7],
                symbols=json.loads(row[8]),
                chunk_hash=row[9],
            )
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> dict[str, int]:
        """Return document and chunk counts."""
        doc_count = self.conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        chunk_count = self.conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        return {"documents": doc_count, "chunks": chunk_count}


# ---------------------------------------------------------------------------
# Embedding serialization helpers
# ---------------------------------------------------------------------------


def _floats_to_blob(floats: list[float]) -> bytes:
    """Pack a list of floats into a raw bytes blob (float32, little-endian)."""
    return struct.pack(f"<{len(floats)}f", *floats)


def _blob_to_floats(blob: bytes) -> list[float]:
    """Unpack a raw bytes blob into a list of floats."""
    count = len(blob) // 4
    return list(struct.unpack(f"<{count}f", blob))


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)
