# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Upgrade zero-vector chunks to real embeddings (batch-friendly).

Reads chunks with embedding_model='zero-vector-stub' from rag.db, embeds them
via the selected provider, and writes the real vectors back. Designed to be
run repeatedly — skips already-upgraded chunks and supports --batch-size
to stay within free-tier API limits across multiple runs.

Usage:
    # Upgrade up to 500 chunks per run (safe for free tier daily quota):
    uv run python scripts/rag_upgrade_embeddings.py --batch-size 500

    # Upgrade everything (requires sufficient API quota):
    uv run python scripts/rag_upgrade_embeddings.py

    # Use OpenRouter instead of GitHub Models:
    uv run python scripts/rag_upgrade_embeddings.py --provider openrouter

    # Re-embed ALL chunks (e.g. switching embedding model/dimensions):
    uv run python scripts/rag_upgrade_embeddings.py --provider openrouter --re-embed-all

    # Dry-run — show what would be upgraded:
    uv run python scripts/rag_upgrade_embeddings.py --dry-run
"""

from __future__ import annotations

import argparse
import logging
import os
import sqlite3
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.ingest.embed import GitHubModelsProvider, OpenRouterProvider

logger = logging.getLogger(__name__)

DEFAULT_DB = Path(__file__).parent.parent / "rag" / "store" / "rag.db"


def _floats_to_blob(floats: list[float]) -> bytes:
    """Pack a list of floats into a raw bytes blob (float32)."""
    return struct.pack(f"{len(floats)}f", *floats)


def main() -> None:
    parser = argparse.ArgumentParser(description="Upgrade zero-vector chunks to real embeddings")
    parser.add_argument("--db", default=str(DEFAULT_DB), help=f"SQLite database path (default: {DEFAULT_DB})")
    parser.add_argument("--batch-size", type=int, default=0, help="Max chunks to upgrade per run (0 = unlimited)")
    parser.add_argument("--embed-batch-size", type=int, default=32, help="Texts per embedding API call (default: 32)")
    parser.add_argument("--embed-delay", type=float, default=4.0, help="Seconds between API calls (default: 4.0)")
    parser.add_argument("--provider", choices=["github", "openrouter"], default="github",
                        help="Embedding provider (default: github)")
    parser.add_argument("--re-embed-all", action="store_true",
                        help="Re-embed ALL chunks, not just zero-vector (use when switching models/dimensions)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be upgraded, don't write")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    # Resolve provider and token
    if args.provider == "openrouter":
        token = os.environ.get("OPENROUTER_API_KEY")
        if not token:
            logger.error("OPENROUTER_API_KEY env var required for --provider openrouter")
            sys.exit(1)
    else:
        token = os.environ.get("GITHUB_MODELS_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token:
            logger.error("GITHUB_MODELS_TOKEN or GITHUB_TOKEN env var required")
            sys.exit(1)

    con = sqlite3.connect(args.db)
    con.execute("PRAGMA foreign_keys=ON")

    # Count chunks by category
    total_zero = con.execute(
        "SELECT COUNT(*) FROM chunks WHERE embedding_model = 'zero-vector-stub'"
    ).fetchone()[0]
    total_real = con.execute(
        "SELECT COUNT(*) FROM chunks WHERE embedding_model != 'zero-vector-stub'"
    ).fetchone()[0]
    total = total_zero + total_real

    logger.info("DB: %d total chunks (%d real, %d zero-vector)", total, total_real, total_zero)

    # Determine target chunks
    if args.re_embed_all:
        where_clause = "WHERE 1=1"  # all chunks
        target_count = total
    else:
        where_clause = "WHERE embedding_model = 'zero-vector-stub'"
        target_count = total_zero

    if target_count == 0:
        logger.info("No chunks to upgrade. Nothing to do.")
        con.close()
        return

    limit_clause = f"LIMIT {args.batch_size}" if args.batch_size > 0 else ""
    rows = con.execute(f"""
        SELECT chunk_id, text FROM chunks
        {where_clause}
        ORDER BY repo_ref, path
        {limit_clause}
    """).fetchall()

    logger.info("Selected %d chunks to upgrade%s%s", len(rows),
                " (re-embed-all)" if args.re_embed_all else "",
                " (dry-run)" if args.dry_run else "")

    if args.dry_run:
        by_repo = {}
        for chunk_id, text in rows:
            repo = con.execute(
                "SELECT repo_ref FROM chunks WHERE chunk_id = ?", (chunk_id,)
            ).fetchone()[0]
            by_repo[repo] = by_repo.get(repo, 0) + 1
        for repo, count in sorted(by_repo.items()):
            logger.info("  %s: %d chunks", repo, count)
        con.close()
        return

    if args.provider == "openrouter":
        provider = OpenRouterProvider(
            token=token,
            batch_size=args.embed_batch_size,
            inter_request_delay=args.embed_delay,
        )
    else:
        provider = GitHubModelsProvider(
            token=token,
            batch_size=args.embed_batch_size,
            inter_request_delay=args.embed_delay,
        )
    model_name = provider.model_name

    # Process in batches
    upgraded = 0
    failed = 0
    batch_sz = args.embed_batch_size

    for i in range(0, len(rows), batch_sz):
        batch = rows[i : i + batch_sz]
        texts = [text for _, text in batch]
        chunk_ids = [cid for cid, _ in batch]

        try:
            embeddings = provider.embed_many(texts)
        except Exception as exc:
            exc_str = str(exc)
            logger.error("Embedding API error at batch %d: %s", i // batch_sz, exc_str)
            failed += len(batch)
            # Stop on rate-limit or quota exhaustion
            if "429" in exc_str or "rate" in exc_str.lower() or "quota" in exc_str.lower():
                logger.warning("Rate/quota limit hit. Stopping. Re-run later to continue.")
                break
            continue

        for cid, emb in zip(chunk_ids, embeddings):
            blob = _floats_to_blob(emb)
            con.execute(
                "UPDATE chunks SET embedding = ?, embedding_model = ? WHERE chunk_id = ?",
                (blob, model_name, cid),
            )

        con.commit()
        upgraded += len(batch)
        logger.info("Upgraded %d / %d chunks (batch %d)", upgraded, len(rows), i // batch_sz + 1)

    con.close()

    pct = (total_real + upgraded) / total * 100 if total else 0
    logger.info(
        "Done: %d upgraded, %d failed, %d remaining zero-vector. Real embedding coverage: %.0f%%",
        upgraded, failed, total_zero - upgraded - failed, pct,
    )


if __name__ == "__main__":
    main()
