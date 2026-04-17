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

# Auto-load .env file if present (allows background/detached execution)
_env_file = Path(__file__).resolve().parent.parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _, _val = _line.partition("=")
            os.environ.setdefault(_key.strip(), _val.strip().strip('"'))

from rag.ingest.embed import GeminiProvider, GitHubModelsProvider, OpenRouterProvider, VoyageProvider

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
    parser.add_argument("--provider", choices=["github", "openrouter", "gemini", "voyage"], default="github",
                        help="Embedding provider (default: github)")
    parser.add_argument("--re-embed-all", action="store_true",
                        help="Re-embed ALL chunks, not just zero-vector (use when switching models/dimensions)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be upgraded, don't write")
    parser.add_argument("--wait-for-quota", action="store_true",
                        help="When daily quota is hit, sleep until reset instead of stopping")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    # Resolve provider and token
    if args.provider == "gemini":
        token = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not token:
            logger.error("GEMINI_API_KEY or GOOGLE_API_KEY env var required for --provider gemini")
            sys.exit(1)
    elif args.provider == "openrouter":
        token = os.environ.get("OPENROUTER_API_KEY")
        if not token:
            logger.error("OPENROUTER_API_KEY env var required for --provider openrouter")
            sys.exit(1)
    elif args.provider == "voyage":
        token = os.environ.get("VOYAGE_API_KEY")
        if not token:
            logger.error("VOYAGE_API_KEY env var required for --provider voyage")
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

        # Quota estimation
        batches = (len(rows) + args.embed_batch_size - 1) // args.embed_batch_size
        avg_tokens = sum(len(text.split()) for _, text in rows) // max(len(rows), 1)
        total_tokens = len(rows) * avg_tokens
        runtime_secs = batches * args.embed_delay
        logger.info("--- Quota Estimate ---")
        logger.info("  API batches: %d (batch_size=%d)", batches, args.embed_batch_size)
        logger.info("  Avg tokens/chunk: %d, total: ~%s", avg_tokens, f"{total_tokens:,}")
        logger.info("  Est. runtime: %.0f min (at %.1fs delay)", runtime_secs / 60, args.embed_delay)
        logger.info("  GitHub Models: ~150 batches/day => %.1f day(s)", max(batches / 150, 0.1))
        logger.info("  OpenRouter free: ~200 req/min => %.0f min", batches / 200 + runtime_secs / 60)

        con.close()
        return

    if args.provider == "gemini":
        provider = GeminiProvider(
            api_key=token,
            batch_size=args.embed_batch_size,
            inter_request_delay=args.embed_delay,
        )
    elif args.provider == "openrouter":
        provider = OpenRouterProvider(
            token=token,
            batch_size=args.embed_batch_size,
            inter_request_delay=args.embed_delay,
        )
    elif args.provider == "voyage":
        provider = VoyageProvider(
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

    # Disable the FTS update trigger — we only change embedding/embedding_model
    # columns, not text, so re-indexing FTS is unnecessary and the trigger causes
    # "SQL logic error" on content-synced FTS5 tables during UPDATE.
    con.execute("DROP TRIGGER IF EXISTS chunks_fts_update")

    # Process in batches — commit after each batch so progress survives quota stops
    upgraded = 0
    failed = 0
    quota_hit = False
    batch_sz = args.embed_batch_size
    total_batches = (len(rows) + batch_sz - 1) // batch_sz

    for i in range(0, len(rows), batch_sz):
        batch = rows[i : i + batch_sz]
        texts = [text for _, text in batch]
        chunk_ids = [cid for cid, _ in batch]
        batch_num = i // batch_sz + 1

        try:
            embeddings = provider.embed_many(texts)
        except Exception as exc:
            exc_str = str(exc)
            logger.error("Embedding API error at batch %d/%d: %s", batch_num, total_batches, exc_str)
            is_quota = "429" in exc_str or "rate" in exc_str.lower() or "quota" in exc_str.lower()

            if is_quota and args.wait_for_quota:
                # Extract retry-after seconds from error message if available
                import re
                retry_match = re.search(r"retry-after=(\d+)", exc_str)
                wait_secs = int(retry_match.group(1)) + 60 if retry_match else 3600
                logger.info(
                    "Quota hit — waiting %d seconds (%.1f hours) for reset, then resuming...",
                    wait_secs, wait_secs / 3600,
                )
                time.sleep(wait_secs)
                # Retry this same batch after waiting
                try:
                    embeddings = provider.embed_many(texts)
                except Exception as exc2:
                    logger.error("Still failing after quota wait: %s", exc2)
                    failed += len(batch)
                    quota_hit = True
                    break
                # Fall through to the update logic below
            elif is_quota:
                failed += len(batch)
                quota_hit = True
                logger.warning(
                    "Rate/quota limit hit after %d chunks. "
                    "Progress saved — re-run later to continue from where we left off.",
                    upgraded,
                )
                break
            else:
                failed += len(batch)
                continue

        for cid, emb in zip(chunk_ids, embeddings):
            blob = _floats_to_blob(emb)
            con.execute(
                "UPDATE chunks SET embedding = ?, embedding_model = ? WHERE chunk_id = ?",
                (blob, model_name, cid),
            )

        con.commit()
        upgraded += len(batch)
        logger.info(
            "Batch %d/%d: upgraded %d / %d chunks (%.0f%%)",
            batch_num, total_batches, upgraded, len(rows),
            upgraded / len(rows) * 100,
        )

    # Restore the FTS update trigger
    con.execute("""CREATE TRIGGER IF NOT EXISTS chunks_fts_update AFTER UPDATE ON chunks BEGIN
        INSERT INTO chunks_fts(chunks_fts, rowid, chunk_id, text)
            VALUES ('delete', old.rowid, old.chunk_id, old.text);
        INSERT INTO chunks_fts(chunks_fts, rowid, chunk_id, text)
            VALUES ('insert', new.rowid, new.chunk_id, new.text);
    END""")
    con.commit()
    con.close()

    remaining = total_zero - upgraded - failed if not args.re_embed_all else len(rows) - upgraded - failed
    pct = (total_real + upgraded) / total * 100 if total else 0
    logger.info(
        "Done: %d upgraded, %d failed, %d remaining. Real embedding coverage: %.0f%%",
        upgraded, failed, remaining, pct,
    )
    if quota_hit:
        logger.info("Re-run this script to continue upgrading remaining chunks.")


if __name__ == "__main__":
    main()
