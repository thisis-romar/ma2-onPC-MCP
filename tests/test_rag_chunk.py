"""Tests for the RAG chunker (Python AST, markdown, line-based)."""

from rag.ingest.chunk import chunk_file
from rag.types import RepoFile
from rag.utils.hash import sha256


def _make_file(text: str, language: str = "python", path: str = "test.py", kind: str = "source") -> RepoFile:
    return RepoFile(path=path, kind=kind, language=language, text=text, hash=sha256(text))


class TestPythonChunking:
    def test_single_function(self):
        code = 'def hello():\n    """Say hello."""\n    print("hello")\n'
        f = _make_file(code)
        chunks = chunk_file(f, "doc1")
        assert len(chunks) >= 1
        assert any("def hello" in c.text for c in chunks)

    def test_multiple_functions(self):
        code = (
            "import os\n\n"
            "X = 1\n\n"
            "def foo():\n    return 1\n\n"
            "def bar():\n    return 2\n"
        )
        f = _make_file(code)
        chunks = chunk_file(f, "doc1")
        # Should have preamble + at least 2 function chunks
        assert len(chunks) >= 2

    def test_class_chunk(self):
        code = (
            "class MyClass:\n"
            "    def method_a(self):\n"
            "        pass\n\n"
            "    def method_b(self):\n"
            "        pass\n"
        )
        f = _make_file(code)
        chunks = chunk_file(f, "doc1")
        assert len(chunks) >= 1
        assert any("class MyClass" in c.text for c in chunks)

    def test_preserves_line_ranges(self):
        code = "# header\n\ndef foo():\n    return 1\n\ndef bar():\n    return 2\n"
        f = _make_file(code)
        chunks = chunk_file(f, "doc1")
        for c in chunks:
            assert c.start_line >= 1
            assert c.end_line >= c.start_line

    def test_extracts_symbols(self):
        code = "def store_cue(cue_id):\n    return f'store cue {cue_id}'\n"
        f = _make_file(code)
        chunks = chunk_file(f, "doc1")
        all_symbols = []
        for c in chunks:
            all_symbols.extend(c.symbols)
        assert "store_cue" in all_symbols

    def test_syntax_error_fallback(self):
        code = "def broken(\n    x = 1\n    # missing closing paren\n"
        f = _make_file(code)
        chunks = chunk_file(f, "doc1")
        # Should still produce chunks via line-based fallback
        assert len(chunks) >= 1

    def test_empty_file(self):
        f = _make_file("")
        chunks = chunk_file(f, "doc1")
        assert chunks == []

    def test_chunk_ids_are_unique(self):
        code = "def a():\n    pass\n\ndef b():\n    pass\n"
        f = _make_file(code)
        chunks = chunk_file(f, "doc1")
        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids))

    def test_chunk_hash_set(self):
        code = "def a():\n    pass\n"
        f = _make_file(code)
        chunks = chunk_file(f, "doc1")
        for c in chunks:
            assert c.chunk_hash != ""


class TestMarkdownChunking:
    def test_heading_split(self):
        md = "# Title\n\nSome intro text.\n\n## Section A\n\nContent A.\n\n## Section B\n\nContent B.\n"
        f = _make_file(md, language="markdown", path="doc.md", kind="doc")
        chunks = chunk_file(f, "doc1")
        assert len(chunks) >= 2

    def test_heading_symbols(self):
        md = "# My Title\n\nText.\n"
        f = _make_file(md, language="markdown", path="doc.md", kind="doc")
        chunks = chunk_file(f, "doc1")
        all_symbols = []
        for c in chunks:
            all_symbols.extend(c.symbols)
        assert "My Title" in all_symbols

    def test_no_headings_fallback(self):
        md = "Just a paragraph without any headings.\nAnother line.\n"
        f = _make_file(md, language="markdown", path="doc.md", kind="doc")
        chunks = chunk_file(f, "doc1")
        assert len(chunks) >= 1


class TestLineBasedChunking:
    def test_generic_file(self):
        text = "\n".join([f"line {i}" for i in range(200)])
        f = _make_file(text, language="yaml", path="config.yml", kind="config")
        chunks = chunk_file(f, "doc1")
        assert len(chunks) >= 1

    def test_small_file_single_chunk(self):
        text = "key: value\n"
        f = _make_file(text, language="yaml", path="config.yml", kind="config")
        chunks = chunk_file(f, "doc1")
        assert len(chunks) == 1
