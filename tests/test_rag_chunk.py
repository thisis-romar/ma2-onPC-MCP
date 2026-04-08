# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for the RAG chunker (Python AST, markdown, line-based)."""

from rag.ingest.chunk import _split_range, chunk_file
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


class TestMarkdownMerging:
    """Tests for _merge_small_ranges merging tiny consecutive Markdown sections."""

    def test_merge_tiny_sections(self):
        """Four tiny H3 sections should merge into fewer chunks."""
        md = (
            "# Title\n\nIntro.\n\n"
            "### A\n\nShort.\n\n"
            "### B\n\nShort.\n\n"
            "### C\n\nShort.\n\n"
            "### D\n\nShort.\n"
        )
        f = _make_file(md, language="markdown", path="doc.md", kind="doc")
        chunks = chunk_file(f, "doc1")
        # Title section + merged tiny sections → fewer than 5 chunks
        assert len(chunks) < 5

    def test_no_merge_across_h1(self):
        """H1 boundaries prevent merging."""
        md = (
            "### Tiny A\n\nX.\n\n"
            "# Major Section\n\nY.\n\n"
            "### Tiny B\n\nZ.\n"
        )
        f = _make_file(md, language="markdown", path="doc.md", kind="doc")
        chunks = chunk_file(f, "doc1")
        # H1 prevents merging Tiny A with Major Section
        assert len(chunks) >= 2

    def test_no_merge_across_h2(self):
        """H2 boundaries prevent merging."""
        md = (
            "### Tiny A\n\nX.\n\n"
            "## Major Section\n\nY.\n\n"
            "### Tiny B\n\nZ.\n"
        )
        f = _make_file(md, language="markdown", path="doc.md", kind="doc")
        chunks = chunk_file(f, "doc1")
        # H2 prevents merging Tiny A with Major Section
        assert len(chunks) >= 2

    def test_no_merge_when_large(self):
        """Sections > MERGE_MIN_CHARS should not be merged."""
        long_text = "x " * 150  # ~300 chars, well above 200
        md = (
            f"### Section A\n\n{long_text}\n\n"
            f"### Section B\n\n{long_text}\n"
        )
        f = _make_file(md, language="markdown", path="doc.md", kind="doc")
        chunks = chunk_file(f, "doc1")
        # Both sections are large → should remain separate
        assert len(chunks) >= 2

    def test_symbols_combined(self):
        """Merged chunks should have symbols from all constituent headings."""
        md = (
            "### Alpha\n\nSmall.\n\n"
            "### Beta\n\nSmall.\n\n"
            "### Gamma\n\nSmall.\n"
        )
        f = _make_file(md, language="markdown", path="doc.md", kind="doc")
        chunks = chunk_file(f, "doc1")
        all_symbols = []
        for c in chunks:
            all_symbols.extend(c.symbols)
        assert "Alpha" in all_symbols
        assert "Beta" in all_symbols
        assert "Gamma" in all_symbols

    def test_merge_respects_target(self):
        """Merging should stop when combined size would exceed target."""
        # Create many sections that are individually small but collectively large
        sections = []
        for i in range(20):
            sections.append(f"### Section {i}\n\n{'word ' * 30}\n\n")  # ~150 chars each
        md = "".join(sections)
        f = _make_file(md, language="markdown", path="doc.md", kind="doc")
        chunks = chunk_file(f, "doc1")
        # 20 × 150 = 3000 chars, target is 2000 → should produce at least 2 chunks
        assert len(chunks) >= 2

    def test_single_section_unchanged(self):
        """A single section should pass through unchanged."""
        md = "### Only\n\nContent.\n"
        f = _make_file(md, language="markdown", path="doc.md", kind="doc")
        chunks = chunk_file(f, "doc1")
        assert len(chunks) == 1


class TestMergeEdgeCases:
    """Edge cases for _merge_small_ranges."""

    def test_empty_markdown_produces_no_crash(self):
        """Empty markdown input should produce zero chunks without error."""
        md = ""
        f = _make_file(md, language="markdown", path="empty.md", kind="doc")
        chunks = chunk_file(f, "doc1")
        assert len(chunks) == 0

    def test_sections_exactly_at_min_chars_boundary(self):
        """Sections at exactly MERGE_MIN_CHARS boundary should not be merged."""
        # MERGE_MIN_CHARS = 200; build sections of exactly ~200 chars
        filler = "x" * 185  # ~185 + heading/newlines ≈ 200 chars
        md = (
            f"### Section A\n\n{filler}\n\n"
            f"### Section B\n\n{filler}\n"
        )
        f = _make_file(md, language="markdown", path="doc.md", kind="doc")
        chunks = chunk_file(f, "doc1")
        # At the boundary, sections should remain separate (not be merge candidates)
        assert len(chunks) >= 2


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


# ---------------------------------------------------------------------------
# Regression tests: infinite-loop guard in _split_range / _chunk_lines
# Trigger condition: avg_line_len > max_chars / overlap_lines (240 chars with defaults)
# ---------------------------------------------------------------------------


class TestSplitRangeOverlapGuard:
    """_split_range must always terminate regardless of overlap vs window size."""

    def _lines(self, count: int, line_len: int = 10) -> list[str]:
        return [("x" * line_len + "\n") for _ in range(count)]

    def test_normal_overlap(self):
        """overlap < lines_per_sub — standard case, must return multiple ranges."""
        lines = self._lines(200, line_len=10)   # avg 11 chars → lines_per_sub >> 20
        result = _split_range(1, 200, lines, max_chars=4800, overlap_lines=20)
        assert len(result) >= 1
        # First range starts at 1
        assert result[0][0] == 1

    def test_overlap_equals_window(self):
        """overlap_lines == lines_per_sub — previously caused infinite loop."""
        # avg_line_len=500 → lines_per_sub = max(10, 4800//500) = max(10,9) = 10
        # overlap_lines=10 == lines_per_sub → infinite loop before fix
        lines = self._lines(50, line_len=500)
        result = _split_range(1, 50, lines, max_chars=4800, overlap_lines=10)
        assert len(result) >= 1
        assert result[-1][1] == 50  # last range ends at end_line

    def test_overlap_exceeds_window(self):
        """overlap_lines > lines_per_sub — the exact failure that caused the MemoryError."""
        # avg_line_len=600 → lines_per_sub = max(10, 4800//600) = max(10,8) = 10
        # overlap_lines=20 > lines_per_sub=10 → infinite loop before fix
        lines = self._lines(30, line_len=600)
        result = _split_range(1, 30, lines, max_chars=4800, overlap_lines=20)
        assert len(result) >= 1
        assert result[-1][1] == 30

    def test_single_chunk_fits(self):
        """Range that fits in one sub-chunk returns exactly 1 tuple."""
        lines = self._lines(5, line_len=10)
        result = _split_range(1, 5, lines, max_chars=4800, overlap_lines=20)
        assert len(result) == 1
        assert result[0] == (1, 5)

    def test_pos_always_advances(self):
        """Each consecutive range starts strictly after the previous one ends minus overlap."""
        lines = self._lines(100, line_len=500)  # long lines → small window
        result = _split_range(1, 100, lines, max_chars=4800, overlap_lines=20)
        for i in range(1, len(result)):
            assert result[i][0] > result[i - 1][0], "pos did not advance between sub-ranges"


class TestChunkLinesLongLines:
    """chunk_file with long-average-line files must terminate (regression for MemoryError)."""

    def _long_line_file(self, n_lines: int = 100, line_len: int = 500) -> RepoFile:
        text = ("a" * line_len + "\n") * n_lines
        return RepoFile(path="big.txt", kind="config", language="text",
                        text=text, hash=sha256(text))

    def test_returns_at_least_one_chunk(self):
        """100 lines × 500 chars = avg 501 chars/line > 240 threshold — must not hang."""
        f = self._long_line_file(100, 500)
        chunks = chunk_file(f, "doc_long")
        assert len(chunks) >= 1

    def test_chunk_text_nonempty(self):
        f = self._long_line_file(50, 600)
        chunks = chunk_file(f, "doc_long2")
        assert all(c.text.strip() for c in chunks)

    def test_all_lines_covered(self):
        """Union of all chunk line ranges must span the whole file."""
        n_lines = 80
        f = self._long_line_file(n_lines, 500)
        chunks = chunk_file(f, "doc_cov")
        covered = set()
        for c in chunks:
            covered.update(range(c.start_line, c.end_line + 1))
        assert min(covered) == 1
        assert max(covered) == n_lines
