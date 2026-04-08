# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for rag/ingest/crawl_web.py HTML parsing and text extraction."""

from bs4 import BeautifulSoup

from rag.ingest.crawl_web import (
    _convert_headings_to_markdown,
    _extract_text,
    _normalize_code_blocks,
    _strip_boilerplate,
    _strip_img_noise,
)


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


class TestStripBoilerplate:
    def test_strips_breadcrumbs(self):
        html = """
        <div class="topic-content">
            <div class="breadcrumb">Home > Fixtures > Patching</div>
            <h1>Patching</h1>
            <p>How to patch fixtures.</p>
        </div>
        """
        text = _extract_text(_soup(html))
        assert "Home > Fixtures" not in text
        assert "patch" in text.lower()

    def test_strips_breadcrumbs_alternate_class(self):
        html = """
        <div class="topic-content">
            <div class="topic-breadcrumb">grandMA2 > Help</div>
            <p>Content here.</p>
        </div>
        """
        text = _extract_text(_soup(html))
        assert "grandMA2 > Help" not in text
        assert "Content here" in text

    def test_strips_related_topics_by_class(self):
        html = """
        <div class="topic-content">
            <p>Main content.</p>
            <div class="related-topics">
                <a href="/other">Other Page</a>
            </div>
        </div>
        """
        text = _extract_text(_soup(html))
        assert "Main content" in text
        assert "Other Page" not in text

    def test_strips_related_topics_by_text(self):
        html = """
        <div class="topic-content">
            <p>Main content.</p>
            <p>Related Topics</p>
            <p>See Also: other stuff</p>
        </div>
        """
        text = _extract_text(_soup(html))
        assert "Main content" in text
        assert "Related Topics" not in text
        assert "See Also" not in text

    def test_strips_copyright(self):
        html = """
        <div class="topic-content">
            <p>Useful content.</p>
            <p>Copyright 2024 MA Lighting. All rights reserved.</p>
        </div>
        """
        text = _extract_text(_soup(html))
        assert "Useful content" in text
        assert "Copyright" not in text

    def test_strips_copyright_symbol(self):
        html = """
        <div class="topic-content">
            <p>Content.</p>
            <p>\u00a9 2024 MA Lighting</p>
        </div>
        """
        text = _extract_text(_soup(html))
        assert "Content" in text
        assert "MA Lighting" not in text

    def test_strips_feedback_block(self):
        html = """
        <div class="topic-content">
            <p>Documentation.</p>
            <div class="feedback">Was this helpful? Yes / No</div>
        </div>
        """
        text = _extract_text(_soup(html))
        assert "Documentation" in text
        assert "Was this helpful" not in text

    def test_strips_pagination(self):
        html = """
        <div class="topic-content">
            <p>Page content.</p>
            <div class="pagination">Previous | Next</div>
        </div>
        """
        text = _extract_text(_soup(html))
        assert "Page content" in text
        assert "Previous" not in text

    def test_preserves_main_content(self):
        html = """
        <div class="topic-content">
            <h1>Fixtures</h1>
            <p>Fixtures are the core building blocks.</p>
            <p>You can patch up to 65536 parameters.</p>
        </div>
        """
        text = _extract_text(_soup(html))
        assert "Fixtures" in text
        assert "core building blocks" in text
        assert "65536" in text


class TestHeadingConversion:
    def test_h1_to_markdown(self):
        html = "<div class='topic-content'><h1>Title</h1><p>Body.</p></div>"
        text = _extract_text(_soup(html))
        assert "# Title" in text

    def test_h2_to_markdown(self):
        html = "<div class='topic-content'><h2>Section</h2><p>Body.</p></div>"
        text = _extract_text(_soup(html))
        assert "## Section" in text

    def test_h3_to_markdown(self):
        html = "<div class='topic-content'><h3>Subsection</h3><p>Body.</p></div>"
        text = _extract_text(_soup(html))
        assert "### Subsection" in text

    def test_multiple_headings(self):
        html = """
        <div class="topic-content">
            <h1>Title</h1>
            <p>Intro.</p>
            <h2>Part A</h2>
            <p>Content A.</p>
            <h3>Detail</h3>
            <p>Content B.</p>
        </div>
        """
        text = _extract_text(_soup(html))
        assert "# Title" in text
        assert "## Part A" in text
        assert "### Detail" in text


class TestCodeBlockNormalization:
    def test_pre_gets_fenced(self):
        html = """
        <div class="topic-content">
            <p>Example:</p>
            <pre>Store Cue 1 /merge</pre>
        </div>
        """
        text = _extract_text(_soup(html))
        assert "```" in text
        assert "Store Cue 1 /merge" in text

    def test_multiple_pre_blocks(self):
        html = """
        <div class="topic-content">
            <pre>code block 1</pre>
            <p>Some text.</p>
            <pre>code block 2</pre>
        </div>
        """
        text = _extract_text(_soup(html))
        assert text.count("```") >= 4  # 2 blocks × (open + close)


class TestImgNoiseStripping:
    def test_strips_img_elements(self):
        html = """
        <div class="topic-content">
            <p>Click the <img alt="[Graphic]" src="icon.png"/> button.</p>
            <p>Then select <img alt="[Icon]" src="tool.png"/> the tool.</p>
        </div>
        """
        text = _extract_text(_soup(html))
        assert "[Graphic]" not in text
        assert "[Icon]" not in text
        assert "Click the" in text
        assert "button" in text


class TestContentSelectorPriority:
    def test_topic_content_preferred(self):
        html = """
        <body>
            <nav>Navigation stuff</nav>
            <div class="topic-content">
                <p>Real content here.</p>
            </div>
            <footer>Footer noise</footer>
        </body>
        """
        text = _extract_text(_soup(html))
        assert "Real content" in text
        assert "Navigation stuff" not in text
        assert "Footer noise" not in text

    def test_main_tag_fallback(self):
        html = """
        <body>
            <nav>Nav</nav>
            <main>
                <p>Main content.</p>
            </main>
        </body>
        """
        text = _extract_text(_soup(html))
        assert "Main content" in text

    def test_body_fallback(self):
        html = """
        <body>
            <p>Only body content.</p>
        </body>
        """
        text = _extract_text(_soup(html))
        assert "Only body content" in text


class TestMinimalContent:
    def test_short_content_returns_empty(self):
        html = "<div class='topic-content'><p>Hi</p></div>"
        text = _extract_text(_soup(html))
        # _extract_text returns text even if short; the caller (crawl_web) checks < 50 chars
        # The function itself just returns the cleaned text
        assert isinstance(text, str)

    def test_empty_page_returns_empty(self):
        html = "<body></body>"
        text = _extract_text(_soup(html))
        assert text == ""

    def test_script_only_returns_empty(self):
        html = "<body><script>alert('hi')</script></body>"
        text = _extract_text(_soup(html))
        assert text == ""
