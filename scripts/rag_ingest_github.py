#!/usr/bin/env python
"""Ingest a GitHub repository into the RAG store.

Usage:
    uv run python scripts/rag_ingest_github.py \\
        --repo https://github.com/MacTirney/GrandMA2-API-Documentation \\
        --ref ma2-lua-api \\
        --provider zero
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from rag.config import RAG_DB_PATH  # noqa: E402
from rag.ingest.ingest_github_repo import ingest_github_repo  # noqa: E402
from scripts.rag_ingest import make_provider  # noqa: E402

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clone a GitHub repo and ingest its files into the RAG store",
    )
    parser.add_argument("--repo", required=True, help="GitHub repo URL")
    parser.add_argument("--ref", default="ma2-lua-api", help="Repo reference label (default: ma2-lua-api)")
    parser.add_argument("--db", default=str(RAG_DB_PATH), help="RAG database path")
    parser.add_argument(
        "--provider",
        choices=["github", "openrouter", "gemini", "zero"],
        default=None,
        help="Embedding provider (default: auto-detect from env)",
    )
    parser.add_argument("--embed-delay", type=float, default=4.0, help="Seconds between embedding API calls")
    parser.add_argument("--embed-batch-size", type=int, default=32, help="Texts per embedding request")
    parser.add_argument("--clone-dir", default=None, help="Persistent clone directory (default: temp)")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    provider = make_provider(
        args.provider,
        inter_request_delay=args.embed_delay,
        batch_size=args.embed_batch_size,
    )
    logger.info("Using embedding provider: %s", provider.model_name)

    clone_dir = Path(args.clone_dir) if args.clone_dir else None

    result = ingest_github_repo(
        repo_url=args.repo,
        repo_ref=args.ref,
        embedding_provider=provider,
        db_path=db_path,
        clone_dir=clone_dir,
    )

    print("\nIngest complete:")
    print(f"  Repo:            {args.repo}")
    print(f"  Repo ref:        {args.ref}")
    print(f"  Provider:        {provider.model_name}")
    print(f"  Files processed: {result['processed']}")
    print(f"  Files skipped:   {result['skipped']}")
    print(f"  Chunks created:  {result['chunks']}")


if __name__ == "__main__":
    main()
