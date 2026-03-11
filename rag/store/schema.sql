-- RAG pipeline schema: documents and chunks tables

-- Schema version tracking for future migrations
CREATE TABLE IF NOT EXISTS _schema_version (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT NOT NULL           -- ISO 8601
);
INSERT OR IGNORE INTO _schema_version (version, applied_at)
    VALUES (1, datetime('now'));

CREATE TABLE IF NOT EXISTS documents (
    doc_id        TEXT PRIMARY KEY,   -- sha256(repo_ref + path)
    repo_ref      TEXT NOT NULL,      -- branch/commit/tag
    path          TEXT NOT NULL,
    language      TEXT NOT NULL,      -- python, markdown, yaml, etc.
    kind          TEXT NOT NULL,      -- source | test | doc | config
    file_hash     TEXT NOT NULL,      -- sha256 of file content
    created_at    TEXT NOT NULL,      -- ISO 8601
    UNIQUE(repo_ref, path)
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id        TEXT PRIMARY KEY,   -- sha256(doc_id + start_line + end_line)
    doc_id          TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    repo_ref        TEXT NOT NULL,
    path            TEXT NOT NULL,
    kind            TEXT NOT NULL,
    language        TEXT NOT NULL,
    text            TEXT NOT NULL,
    start_line      INTEGER NOT NULL,
    end_line        INTEGER NOT NULL,
    symbols         TEXT NOT NULL DEFAULT '[]',  -- JSON array of identifiers
    chunk_hash      TEXT NOT NULL,               -- sha256 of chunk text
    embedding_model TEXT DEFAULT NULL,
    embedding       BLOB DEFAULT NULL,           -- raw float32 bytes
    created_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chunks_repo_ref ON chunks(repo_ref);
CREATE INDEX IF NOT EXISTS idx_chunks_path ON chunks(path);
CREATE INDEX IF NOT EXISTS idx_chunks_kind ON chunks(kind);
CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id);
