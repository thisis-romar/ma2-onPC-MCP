# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Web crawler for HTML documentation sites.

Crawls from start URLs using BFS, extracts clean text from HTML pages,
and returns RepoFile objects compatible with the RAG ingest pipeline.
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from collections import deque
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup, Tag

from rag.config import MIN_PAGE_TEXT_LENGTH, WEB_CRAWLER_USER_AGENT
from rag.types import RepoFile

logger = logging.getLogger(__name__)

# Elements to strip from the page before text extraction
_STRIP_TAGS = {"script", "style", "nav", "header", "footer", "noscript"}

# CSS selectors for sidebar / navigation trees to remove
_STRIP_SELECTORS = ["#offline-tree", ".topic-tree-container", ".jstree"]

# CSS selectors for boilerplate elements within the content area
_BOILERPLATE_SELECTORS = [
    ".breadcrumb", ".breadcrumbs", ".topic-breadcrumb",
    ".related-topics", ".related-links",
    ".feedback", ".was-helpful", ".rating",
    ".pagination", ".prev-next", ".topic-navigation",
]

# Text patterns that indicate boilerplate paragraphs (matched at start of element text)
_BOILERPLATE_TEXT_RE = re.compile(
    r"^\s*(Related Topics|See Also|Was this helpful|"
    r"\u00a9|©|Copyright|All rights reserved)",
    re.IGNORECASE,
)

# Selectors to try for main content, in priority order
_CONTENT_SELECTORS = [".topic-content", "main", "article", "[role='main']"]

_HEADING_RE = re.compile(r"^(h[1-6])$", re.IGNORECASE)


def crawl_web(
    start_urls: list[str],
    *,
    url_prefix: str | list[str] | None = None,
    delay: float = 0.5,
    max_pages: int = 2000,
) -> list[RepoFile]:
    """Crawl HTML pages starting from *start_urls* and return RepoFile list.

    Parameters
    ----------
    start_urls:
        One or more seed URLs to begin crawling from.
    url_prefix:
        Only follow links whose URL starts with one of these prefixes.
        Accepts a single string or a list of strings.
        If ``None``, one prefix is derived per start URL so that
        multi-domain seed lists work correctly.
    delay:
        Seconds to wait between HTTP requests (politeness).
    max_pages:
        Maximum number of pages to crawl.

    Returns
    -------
    list[RepoFile]
        One RepoFile per successfully crawled page, with ``kind="doc"``,
        ``language="markdown"``, and cleaned text content.
    """
    if not start_urls:
        return []

    # Build the list of allowed URL prefixes
    if url_prefix is None:
        prefixes: list[str] = []
        for url in start_urls:
            parsed = urlparse(url)
            p = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if not p.endswith("/"):
                p = p.rsplit("/", 1)[0] + "/"
            if p not in prefixes:
                prefixes.append(p)
    elif isinstance(url_prefix, str):
        prefixes = [url_prefix]
    else:
        prefixes = list(url_prefix)

    visited: set[str] = set()
    queue: deque[str] = deque()
    files: list[RepoFile] = []

    # Seed the queue
    for url in start_urls:
        normalized = _normalize_url(url)
        if normalized not in visited:
            visited.add(normalized)
            queue.append(normalized)

    client = httpx.Client(
        timeout=30.0,
        follow_redirects=True,
        headers={"User-Agent": WEB_CRAWLER_USER_AGENT},
    )

    # Load robots.txt for each domain (best-effort — skip if unavailable)
    robots_parsers: dict[str, RobotFileParser] = {}
    for url in start_urls:
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        if domain not in robots_parsers:
            rp = RobotFileParser()
            robots_url = f"{domain}/robots.txt"
            try:
                r = client.get(robots_url)
                if r.status_code == 200:
                    rp.parse(r.text.splitlines())
                    logger.info("Loaded robots.txt from %s", robots_url)
                else:
                    rp.allow_all = True
            except (httpx.HTTPError, OSError):
                rp.allow_all = True  # can't fetch → assume allowed
            robots_parsers[domain] = rp

    def _robots_allowed(check_url: str) -> bool:
        parsed = urlparse(check_url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        rp = robots_parsers.get(domain)
        if rp is None or getattr(rp, "allow_all", False):
            return True
        return rp.can_fetch(WEB_CRAWLER_USER_AGENT, check_url)

    try:
        while queue and len(files) < max_pages:
            url = queue.popleft()

            if not _robots_allowed(url):
                logger.info("Blocked by robots.txt: %s", url)
                continue

            try:
                resp = client.get(url)
                resp.raise_for_status()
            except httpx.TimeoutException:
                logger.warning("Timeout (transient) fetching %s — skipping", url)
                continue
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status in {403, 404, 410}:
                    logger.info("Permanent error %d for %s — skipping", status, url)
                else:
                    logger.warning("Transient error %d for %s — skipping", status, url)
                continue
            except httpx.HTTPError as exc:
                logger.warning("Network error fetching %s: %s", url, exc)
                continue

            content_type = resp.headers.get("content-type", "")
            if "text/html" not in content_type:
                logger.debug("Skipping non-HTML: %s (%s)", url, content_type)
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            # Discover links
            for link in _extract_links(soup, url, prefixes):
                if link not in visited:
                    visited.add(link)
                    queue.append(link)

            # Extract text
            text = _extract_text(soup)
            if not text or len(text.strip()) < MIN_PAGE_TEXT_LENGTH:
                logger.debug("Skipping (too little content): %s", url)
                continue

            # Build relative path from URL
            parsed = urlparse(url)
            path = parsed.path.lstrip("/")
            if not path or path.endswith("/"):
                path += "index.html"

            content_hash = hashlib.sha256(text.encode()).hexdigest()

            files.append(RepoFile(
                path=path,
                kind="doc",
                language="markdown",
                text=text,
                hash=content_hash,
            ))

            logger.info("Crawled [%d/%d]: %s (%d chars)", len(files), max_pages, path, len(text))

            if delay > 0:
                time.sleep(delay)

    finally:
        client.close()

    logger.info("Crawl complete: %d pages from %d visited URLs", len(files), len(visited))
    return files


def _normalize_url(url: str) -> str:
    """Normalize a URL by removing fragment and trailing whitespace."""
    parsed = urlparse(url.strip())
    # Remove fragment, keep everything else
    return urlunparse(parsed._replace(fragment=""))


def _extract_links(soup: BeautifulSoup, base_url: str, prefixes: list[str]) -> list[str]:
    """Extract and filter links from a page."""
    links: list[str] = []
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        if isinstance(href, list):
            href = href[0]
        absolute = urljoin(base_url, href)
        normalized = _normalize_url(absolute)

        # Only follow links within one of the allowed prefixes
        if any(normalized.startswith(p) for p in prefixes):
            links.append(normalized)

    return links


def _extract_text(soup: BeautifulSoup) -> str:
    """Extract clean text from an HTML page, converting headings to markdown."""
    # Remove unwanted elements
    for tag_name in _STRIP_TAGS:
        for el in soup.find_all(tag_name):
            el.decompose()

    for selector in _STRIP_SELECTORS:
        for el in soup.select(selector):
            el.decompose()

    # Find the main content container
    content: Tag | None = None
    for selector in _CONTENT_SELECTORS:
        found = soup.select_one(selector)
        if found and isinstance(found, Tag):
            content = found
            break

    if content is None:
        content = soup.body  # type: ignore[assignment]
    if content is None:
        return ""

    # Strip boilerplate and noise within the content area
    _strip_boilerplate(content)
    _normalize_code_blocks(content)
    _strip_img_noise(content)

    # Convert headings to markdown-style before extracting text
    _convert_headings_to_markdown(content)

    text = content.get_text(separator="\n")

    # Clean up excessive blank lines
    lines = text.splitlines()
    cleaned: list[str] = []
    blank_count = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            blank_count += 1
            if blank_count <= 2:
                cleaned.append("")
        else:
            blank_count = 0
            cleaned.append(stripped)

    return "\n".join(cleaned).strip()


def _convert_headings_to_markdown(element: Tag) -> None:
    """Replace <h1>–<h6> tags with markdown heading text in-place."""
    for tag in element.find_all(_HEADING_RE):
        level = int(tag.name[1])  # h1 → 1, h2 → 2, etc.
        prefix = "#" * level
        heading_text = tag.get_text(strip=True)
        tag.string = f"{prefix} {heading_text}"


def _strip_boilerplate(content: Tag) -> None:
    """Remove boilerplate elements from within the content area.

    Two passes:
    1. CSS selector-based: removes breadcrumbs, related-topics, feedback, pagination
    2. Text pattern-based: removes paragraphs starting with known boilerplate text
    """
    # Pass 1: structural removal via CSS selectors
    for selector in _BOILERPLATE_SELECTORS:
        for el in content.select(selector):
            el.decompose()

    # Pass 2: text-based removal for elements without distinctive classes
    for el in content.find_all(["p", "div", "span"]):
        text = el.get_text(strip=True)
        if text and _BOILERPLATE_TEXT_RE.match(text):
            el.decompose()


def _normalize_code_blocks(content: Tag) -> None:
    """Wrap <pre> block content with fenced code markers for better chunking."""
    for pre in content.find_all("pre"):
        code_text = pre.get_text()
        pre.string = f"\n```\n{code_text}\n```\n"


def _strip_img_noise(content: Tag) -> None:
    """Remove <img> elements that produce noisy alt text like '[Graphic]'."""
    for img in content.find_all("img"):
        img.decompose()
