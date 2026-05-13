# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Build per-fixture-type Group / Preset / World pool structure (R2 Python orchestrator).

Phase 1  — All (PT 0) + Dimmer (PT 1) + Color (PT 4) universal presets per FT.
Phase 2  — adds Position/Gobo/Beam/Focus/Control where the FT exposes those attrs.
           (Phase 2 is additive; it never modifies Phase 1 objects.)

Saves scripts/build_ft_pools.lastrun.json so cleanup_ft_pools.py can remove
exactly the objects created — no hardcoded slot ranges.

Usage:
    uv run python scripts/build_ft_pools.py
    uv run python scripts/build_ft_pools.py --phase 1
    uv run python scripts/build_ft_pools.py --dry-run
    uv run python scripts/build_ft_pools.py --ft-group-base 1 --pool-group-base 11 --preset-base 11
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

import dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.telnet_client import GMA2TelnetClient

# ---------------------------------------------------------------------------
# Config from .env
# ---------------------------------------------------------------------------
GMA_HOST = dotenv.get_key(".env", "GMA_HOST") or "127.0.0.1"
GMA_PORT = int(dotenv.get_key(".env", "GMA_PORT") or "30000")
GMA_USER = dotenv.get_key(".env", "GMA_USER") or "administrator"
GMA_PASSWORD = dotenv.get_key(".env", "GMA_PASSWORD") or ""

LASTRUN_PATH = Path(__file__).parent / "build_ft_pools.lastrun.json"
MAX_FT_SCAN = 30  # max FT major to try

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class FTInfo:
    major: int
    total_fixtures: int  # all instances combined


@dataclass
class FTPoolResult:
    phase: int = 1
    show: str = ""
    ft_majors: list[int] = field(default_factory=list)
    groups_created: list[int] = field(default_factory=list)
    presets_created: dict[str, list[int]] = field(
        default_factory=lambda: {"all": [], "dimmer": [], "color": []}
    )
    worlds_created: list[int] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Telnet helpers
# ---------------------------------------------------------------------------

async def _cmd(c: GMA2TelnetClient, cmd: str, dry_run: bool, delay: float = 0.10) -> str:
    if dry_run:
        log.info("  [DRY] %s", cmd)
        return ""
    return await c.send_command_with_response(cmd, timeout=6.0, delay=delay)


async def _listvar(c: GMA2TelnetClient, var: str) -> str:
    resp = await c.send_command_with_response("ListVar", timeout=5.0)
    upper = var.upper()
    for line in resp.split("\n"):
        if upper in line.upper():
            parts = line.split("=")
            return parts[-1].strip() if len(parts) >= 2 else ""
    return ""


async def _selected_count(c: GMA2TelnetClient) -> int:
    try:
        return int(await _listvar(c, "SELECTEDFIXTURESCOUNT"))
    except (ValueError, TypeError):
        return 0


# ---------------------------------------------------------------------------
# Core builder
# ---------------------------------------------------------------------------

async def build_ft_pools(
    c: GMA2TelnetClient,
    *,
    phase: int = 1,
    ft_group_base: int = 1,
    pool_group_base: int = 11,
    preset_base: int = 11,
    world_base: int = 11,
    dry_run: bool = False,
) -> FTPoolResult:
    result = FTPoolResult(phase=phase)

    # --- Read show name ------------------------------------------------
    result.show = await _listvar(c, "SHOWFILE")
    log.info("Show: %s", result.show)

    # --- Enumerate active FT majors ------------------------------------
    log.info("Scanning FT majors 1..%d ...", MAX_FT_SCAN)
    fts: list[FTInfo] = []
    for major in range(1, MAX_FT_SCAN + 1):
        await _cmd(c, "ClearAll", dry_run)
        await _cmd(c, f"FixtureType {major}.1.1 Thru", dry_run, delay=0.12)
        count = await _selected_count(c)
        if count == 0:
            continue
        fts.append(FTInfo(major=major, total_fixtures=count))
        log.info("  FT %d: %d fixtures", major, count)

    await _cmd(c, "ClearAll", dry_run)

    if not fts:
        msg = "No fixture types found — is a show loaded with patched fixtures?"
        log.warning(msg)
        if not dry_run:
            result.errors.append(msg)
        return result

    hue_step = max(1, 360 // len(fts))
    log.info("Found %d FT majors — hue step %d°", len(fts), hue_step)

    # --- Build per-FT objects -----------------------------------------
    for i, ft in enumerate(fts):
        offset = i
        ft_grp = ft_group_base + offset
        pool_grp = pool_group_base + offset
        pslot = preset_base + offset
        wslot = world_base + offset
        hue = (i * hue_step) % 360

        vivid = f"/h={hue} /s=100 /br=100"
        pastel = f"/h={hue} /s=60 /br=100"
        ft_label = f'"FT {ft.major}"'

        log.info(
            "FT %d → ftgrp=%d poolgrp=%d preset=%d world=%d hue=%d",
            ft.major, ft_grp, pool_grp, pslot, wslot, hue,
        )

        # -- FT group (slot 1+offset) from live FixtureType selection --
        await _cmd(c, "ClearAll", dry_run)
        await _cmd(c, f"FixtureType {ft.major}.1.1 Thru", dry_run, delay=0.15)
        await _cmd(c, f"Store Group {ft_grp} /o", dry_run)
        await _cmd(c, f"Label Group {ft_grp} {ft_label} /o", dry_run)
        await _cmd(c, f"Appearance Group {ft_grp} {vivid}", dry_run)

        # -- Pool group (slot 11+offset) same selection ----------------
        await _cmd(c, f"Store Group {pool_grp} /o", dry_run)
        await _cmd(c, f"Label Group {pool_grp} {ft_label} /o", dry_run)
        await _cmd(c, f"Appearance Group {pool_grp} {vivid}", dry_run)

        # -- All preset PT 0 (universal) --------------------------------
        await _cmd(c, "Attribute 1 Thru At Release", dry_run)
        await _cmd(c, f"Store Preset 0.{pslot} /universal /o", dry_run, delay=0.15)
        await _cmd(c, f'Label Preset 0.{pslot} "FT {ft.major} ALL" /o', dry_run)
        await _cmd(c, f"Appearance Preset 0.{pslot} {vivid}", dry_run)

        # -- Dimmer preset PT 1 (universal) ----------------------------
        await _cmd(c, "ClearAll", dry_run)
        await _cmd(c, f"FixtureType {ft.major}.1.1 Thru", dry_run, delay=0.15)
        await _cmd(c, "Attribute 1 Thru At Release", dry_run)
        await _cmd(c, f"Store Preset 1.{pslot} /universal /o", dry_run, delay=0.15)
        await _cmd(c, f'Label Preset 1.{pslot} "FT {ft.major} D" /o', dry_run)
        await _cmd(c, f"Appearance Preset 1.{pslot} {pastel}", dry_run)

        # -- Color preset PT 4 (universal) -----------------------------
        await _cmd(c, "ClearAll", dry_run)
        await _cmd(c, f"FixtureType {ft.major}.1.1 Thru", dry_run, delay=0.15)
        await _cmd(c, "Attribute 1 Thru At Release", dry_run)
        await _cmd(c, f"Store Preset 4.{pslot} /universal /o", dry_run, delay=0.15)
        await _cmd(c, f'Label Preset 4.{pslot} "FT {ft.major} C" /o', dry_run)
        await _cmd(c, f"Appearance Preset 4.{pslot} {pastel}", dry_run)

        # -- World (FT-scoped fixture selection) ----------------------
        await _cmd(c, "ClearAll", dry_run)
        await _cmd(c, f"FixtureType {ft.major}.1.1 Thru", dry_run, delay=0.15)
        await _cmd(c, "Attribute 1 Thru At Release", dry_run)
        await _cmd(c, f"Store World {wslot} /o", dry_run)
        await _cmd(c, f"Label World {wslot} {ft_label} /o", dry_run)
        await _cmd(c, f"Appearance World {wslot} {vivid}", dry_run)

        # -- Track created objects ------------------------------------
        result.ft_majors.append(ft.major)
        result.groups_created.append(ft_grp)
        result.groups_created.append(pool_grp)
        result.presets_created["all"].append(pslot)
        result.presets_created["dimmer"].append(pslot)
        result.presets_created["color"].append(pslot)
        result.worlds_created.append(wslot)

    await _cmd(c, "ClearAll", dry_run)
    return result


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    parser = argparse.ArgumentParser(description="Build FT Pool structure on grandMA2 console")
    parser.add_argument("--phase", type=int, default=1, choices=[1, 2],
                        help="Phase 1 = All+Dimmer+Color; Phase 2 = +Position/Gobo/Beam/Focus/Control")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print commands without sending to console")
    parser.add_argument("--ft-group-base", type=int, default=1,
                        help="Starting Group slot for FT groups (default 1)")
    parser.add_argument("--pool-group-base", type=int, default=11,
                        help="Starting Group slot for pool groups (default 11)")
    parser.add_argument("--preset-base", type=int, default=11,
                        help="Starting Preset slot N for Preset X.N stores (default 11)")
    parser.add_argument("--world-base", type=int, default=11,
                        help="Starting World slot (default 11)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    log.info("build_ft_pools — phase=%d dry_run=%s", args.phase, args.dry_run)

    async with GMA2TelnetClient(GMA_HOST, GMA_PORT, GMA_USER, GMA_PASSWORD) as c:
        result = await build_ft_pools(
            c,
            phase=args.phase,
            ft_group_base=args.ft_group_base,
            pool_group_base=args.pool_group_base,
            preset_base=args.preset_base,
            world_base=args.world_base,
            dry_run=args.dry_run,
        )

    print("\n=== FT Pool Build Result ===")
    print(f"  Show:    {result.show}")
    print(f"  Phase:   {result.phase}")
    print(f"  FTs:     {result.ft_majors}")
    print(f"  Groups:  {sorted(set(result.groups_created))}")
    print(f"  Presets: {dict(result.presets_created)}")
    print(f"  Worlds:  {result.worlds_created}")
    if result.warnings:
        for w in result.warnings:
            print(f"  WARN:    {w}")
    if result.errors:
        for e in result.errors:
            print(f"  ERROR:   {e}")
        sys.exit(1)

    if not args.dry_run and result.ft_majors:
        lastrun = asdict(result)
        lastrun["args"] = {
            "ft_group_base": args.ft_group_base,
            "pool_group_base": args.pool_group_base,
            "preset_base": args.preset_base,
            "world_base": args.world_base,
        }
        LASTRUN_PATH.write_text(json.dumps(lastrun, indent=2))
        log.info("Saved %s", LASTRUN_PATH)

    log.info("Done.")


if __name__ == "__main__":
    asyncio.run(main())
