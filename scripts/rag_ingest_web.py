"""CLI script to crawl web documentation and ingest into the RAG index.

Usage:
    uv run python scripts/rag_ingest_web.py [OPTIONS]
    uv run python scripts/rag_ingest_web.py \
        --url "https://help.malighting.com/grandMA2/en/help/" \
        --url "https://help2.malighting.com/grandMA2/en/help/release_notes/" \
        --provider github -v
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.config import RAG_DB_PATH
from rag.ingest.crawl_web import crawl_web
from rag.ingest.index import ingest

# Reuse the provider factory from the repo ingest script
from scripts.rag_ingest import make_provider

logger = logging.getLogger(__name__)

DEFAULT_URLS = [
    "https://help.malighting.com/grandMA2/en/help/",
    "https://help2.malighting.com/grandMA2/en/help/release_notes/",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Crawl web docs and ingest into the RAG index")
    parser.add_argument(
        "--url", action="append", dest="urls", default=None,
        help="Start URL(s) to crawl (can repeat; defaults to grandMA2 help sites)",
    )
    parser.add_argument("--ref", default="ma2-help-docs", help="Repo reference label (default: ma2-help-docs)")
    parser.add_argument("--db", default=str(RAG_DB_PATH), help=f"SQLite database path (default: {RAG_DB_PATH})")
    parser.add_argument(
        "--provider", choices=["github", "zero"], default=None,
        help="Embedding provider (default: auto-detect from env vars)",
    )
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests in seconds (default: 0.5)")
    parser.add_argument("--max-pages", type=int, default=2000, help="Maximum pages to crawl (default: 2000)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    urls = args.urls or DEFAULT_URLS

    # Ensure the database directory exists
    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    provider = make_provider(args.provider)
    logger.info("Using embedding provider: %s", provider.model_name)

    print(f"Crawling {len(urls)} start URL(s) (max {args.max_pages} pages, {args.delay}s delay)...")
    for u in urls:
        print(f"  - {u}")

    pages = crawl_web(urls, delay=args.delay, max_pages=args.max_pages)
    print(f"\nCrawled {len(pages)} pages")

    if not pages:
        print("No pages to ingest.")
        return

    result = ingest(
        files=pages,
        repo_ref=args.ref,
        embedding_provider=provider,
        db_path=db_path,
    )

    print("\nIngest complete:")
    print(f"  Provider:        {provider.model_name}")
    print(f"  Pages crawled:   {len(pages)}")
    print(f"  Files processed: {result.files_processed}")
    print(f"  Files skipped:   {result.files_skipped}")
    print(f"  Chunks created:  {result.chunks_created}")


if __name__ == "__main__":
    main()
