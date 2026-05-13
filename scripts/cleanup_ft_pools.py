# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Remove the FT Pool objects created by build_ft_pools.py.

Reads scripts/build_ft_pools.lastrun.json and deletes exactly the Group /
Preset / World objects that were created — no hardcoded slot ranges.

Usage:
    uv run python scripts/cleanup_ft_pools.py
    uv run python scripts/cleanup_ft_pools.py --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

import dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.telnet_client import GMA2TelnetClient

GMA_HOST = dotenv.get_key(".env", "GMA_HOST") or "127.0.0.1"
GMA_PORT = int(dotenv.get_key(".env", "GMA_PORT") or "30000")
GMA_USER = dotenv.get_key(".env", "GMA_USER") or "administrator"
GMA_PASSWORD = dotenv.get_key(".env", "GMA_PASSWORD") or ""

LASTRUN_PATH = Path(__file__).parent / "build_ft_pools.lastrun.json"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


async def _cmd(c: GMA2TelnetClient, cmd: str, dry_run: bool) -> str:
    if dry_run:
        log.info("  [DRY] %s", cmd)
        return ""
    return await c.send_command_with_response(cmd, timeout=6.0, delay=0.10)


async def cleanup(c: GMA2TelnetClient, lastrun: dict, *, dry_run: bool) -> list[str]:
    errors: list[str] = []

    groups = sorted(set(lastrun.get("groups_created", [])))
    presets: dict[str, list[int]] = lastrun.get("presets_created", {})
    worlds = sorted(set(lastrun.get("worlds_created", [])))

    # Delete Groups
    for g in groups:
        resp = await _cmd(c, f"Delete Group {g}", dry_run)
        log.info("Deleted Group %d%s", g, " [DRY]" if dry_run else "")

    # Delete Presets by PresetType key
    pt_map = {"all": 0, "dimmer": 1, "position": 2, "gobo": 3,
              "color": 4, "beam": 5, "focus": 6, "control": 7}
    for pt_name, slots in presets.items():
        pt_num = pt_map.get(pt_name, 0)
        for s in sorted(set(slots)):
            resp = await _cmd(c, f"Delete Preset {pt_num}.{s}", dry_run)
            log.info("Deleted Preset %d.%d%s", pt_num, s, " [DRY]" if dry_run else "")

    # Delete Worlds
    for w in worlds:
        resp = await _cmd(c, f"Delete World {w}", dry_run)
        log.info("Deleted World %d%s", w, " [DRY]" if dry_run else "")

    await _cmd(c, "ClearAll", dry_run)
    return errors


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove FT Pool objects created by build_ft_pools.py"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Print commands without sending to console")
    parser.add_argument("--lastrun", type=Path, default=LASTRUN_PATH,
                        help="Path to lastrun JSON (default: scripts/build_ft_pools.lastrun.json)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not args.lastrun.exists():
        print(f"ERROR: {args.lastrun} not found — run build_ft_pools.py first", file=sys.stderr)
        sys.exit(1)

    lastrun = json.loads(args.lastrun.read_text())
    log.info("Loaded lastrun (phase=%s show=%s)", lastrun.get("phase"), lastrun.get("show"))

    async with GMA2TelnetClient(GMA_HOST, GMA_PORT, GMA_USER, GMA_PASSWORD) as c:
        errors = await cleanup(c, lastrun, dry_run=args.dry_run)

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if not args.dry_run:
        args.lastrun.unlink(missing_ok=True)
        log.info("Removed %s", args.lastrun)

    log.info("Done.")


if __name__ == "__main__":
    asyncio.run(main())
