# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Build per-fixture-type Group / Preset / World pool structure (R2 Python orchestrator).

Phase 1  — All (PT 0) + Dimmer (PT 1) + Color (PT 4) universal presets per FT.
Phase 2  — adds Position/Gobo/Beam/Focus/Control where the FT exposes those attrs.
           (Phase 2 is additive; it never modifies Phase 1 objects.)

Attribute discovery navigates EditSetup to determine which PTs a given FT actually
exposes, so empty preset slots are never created. Physical vs virtual channels are
detected via Coarse address — virtual (None) PAN/TILT channels do not count as movers.

Taxonomy groups are created at tag_group_base (default 101):
  LED       — has any colour attribute (COLORRGB1+ or COLORMIXER)
  LED.WASH  — LED + no physical PAN/TILT (static or virtual-pan LED)
  LED.MOVERS — LED + physical PAN/TILT (real moving heads)

Saves scripts/build_ft_pools.lastrun.json so cleanup_ft_pools.py can remove
exactly the objects created — no hardcoded slot ranges.

Usage:
    uv run python scripts/build_ft_pools.py
    uv run python scripts/build_ft_pools.py --phase 2
    uv run python scripts/build_ft_pools.py --dry-run
    uv run python scripts/build_ft_pools.py --ft-group-base 1 --pool-group-base 11 --preset-base 11
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
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
MAX_FT_SCAN = 30

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Attribute membership sets (upper-cased; from FILTER_ATTRIBUTES in constants.py)
# ---------------------------------------------------------------------------
_COLOR_ATTRS = frozenset({
    "COLOR1", "COLOR1WHEELOFFSET", "COLOR1WHEELSELECTBLINK",
    "COLORRGB1", "COLORRGB2", "COLORRGB3", "COLORMIXER",
    "CYANMINIMUM", "MAGENTAMINIMUM", "YELLOWMINIMUM",
})
_DIMMER_ATTRS = frozenset({"DIM"})
_POSITION_ATTRS = frozenset({"PAN", "TILT", "POSITIONBLINK", "POSITIONOPTIMISATIONMODE", "POSITIONMSPEED"})
_GOBO_ATTRS = frozenset({
    "GOBO1", "GOBO1_POS", "GOBO2",
    "ANIMATIONWHEEL", "ANIMATIONINDEXROTATE",
    "ANIMATIONWHEELINCLINE", "ANIMATIONINDEXROTATEMODE",
})
_BEAM_ATTRS = frozenset({"SHUTTER", "IRIS", "PRISMA1", "EFFECTINDEXROTATE", "EFFECTWHEEL"})
_FOCUS_ATTRS = frozenset({"FOCUS", "ZOOM"})
_CONTROL_ATTRS = frozenset({"LAMPCONTROL", "LAMPPOWER", "FIXTUREGLOBALRESET", "WHEELMODE", "DUMMY", "INTENSITYMSPEED"})

_PT_ATTR_MAP: dict[str, frozenset[str]] = {
    "dimmer":   _DIMMER_ATTRS,
    "position": _POSITION_ATTRS,
    "gobo":     _GOBO_ATTRS,
    "color":    _COLOR_ATTRS,
    "beam":     _BEAM_ATTRS,
    "focus":    _FOCUS_ATTRS,
    "control":  _CONTROL_ATTRS,
}

PT_NAMES_PHASE1 = ["dimmer", "color"]              # stored unconditionally (gated by attr check)
PT_NAMES_PHASE2 = ["position", "gobo", "beam", "focus", "control"]
PT_LABEL_SUFFIX = {"dimmer": "D", "position": "P", "gobo": "G", "color": "C",
                   "beam": "B", "focus": "F", "control": "X"}
PT_NUMBER = {"all": 0, "dimmer": 1, "position": 2, "gobo": 3,
             "color": 4, "beam": 5, "focus": 6, "control": 7}


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class FTInfo:
    major: int
    total_fixtures: int
    attrs: dict[str, bool] = field(default_factory=dict)  # attr_name (upper) → is_physical
    tags: list[str] = field(default_factory=list)          # taxonomy tags e.g. ["LED", "LED.MOVERS"]


@dataclass
class FTPoolResult:
    phase: int = 1
    show: str = ""
    ft_majors: list[int] = field(default_factory=list)
    groups_created: list[int] = field(default_factory=list)
    ft_groups_created: list[int] = field(default_factory=list)
    presets_created: dict[str, list[int]] = field(default_factory=dict)
    presets_skipped: dict[str, list[int]] = field(default_factory=dict)
    worlds_created: list[int] = field(default_factory=list)
    taxonomy_groups: dict[str, list[int]] = field(default_factory=dict)
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
# Attribute discovery
# ---------------------------------------------------------------------------
# ChannelType line format (from live cd EditSetup → FixtureTypes → N → 1 → 1 → list):
#   ChannelType 1 1 DIM (Intensity) 1 1
#   ChannelType 2 1 PAN (None) 1 None
# Coarse address is the last token; "None" means virtual (no DMX channel).

_CHANTYPE_RE = re.compile(
    r"ChannelType\s+\d+\s+\d+\s+(\w+)\s+\([^)]*\)\s+\d+\s+(\S+)"
)


async def _get_ft_attributes(c: GMA2TelnetClient, major: int, dry_run: bool) -> dict[str, bool]:
    """Return {ATTR_NAME_UPPER: is_physical} for the given FT major.

    Navigates cd EditSetup → FixtureTypes → major → 1 → 1 → list.
    Falls back to empty dict on navigation failure (non-fatal).
    """
    if dry_run:
        return {}

    attrs: dict[str, bool] = {}
    try:
        # Navigate into the FT's first module's first mode
        for step in [
            "cd /",
            "cd EditSetup",
            f"cd FixtureTypes",
            f"cd {major}",
            "cd 1",
            "cd 1",
        ]:
            await c.send_command_with_response(step, timeout=4.0)

        listing = await c.send_command_with_response("list", timeout=5.0)
        for line in listing.split("\n"):
            m = _CHANTYPE_RE.search(line)
            if m:
                attr_name = m.group(1).upper()
                coarse = m.group(2)
                is_physical = coarse != "None"
                attrs[attr_name] = is_physical

        # Return to root
        await c.send_command_with_response("cd /", timeout=3.0)
    except Exception as exc:
        log.warning("Attribute discovery failed for FT %d: %s", major, exc)
        try:
            await c.send_command_with_response("cd /", timeout=3.0)
        except Exception:
            pass

    log.debug("  FT %d attrs: %s", major, attrs)
    return attrs


def _has_pt_attrs(ft_attrs: dict[str, bool], pt_name: str) -> bool:
    """True if the FT exposes at least one attribute belonging to this PresetType."""
    wanted = _PT_ATTR_MAP.get(pt_name, frozenset())
    return bool(wanted.intersection(ft_attrs.keys()))


def _classify_ft(ft_attrs: dict[str, bool]) -> list[str]:
    """Return taxonomy tags for an FT based on its attribute set.

    Rules:
    - LED   : has any colour attribute (COLORRGB1+, COLORMIXER, COLOR1, etc.)
    - LED.MOVERS : LED + physical PAN + physical TILT
    - LED.WASH   : LED + no physical PAN/TILT (static wash or virtual-pan)
    """
    tags: list[str] = []
    has_color = bool(_COLOR_ATTRS.intersection(ft_attrs.keys()))
    if has_color:
        tags.append("LED")
        has_phys_pan = ft_attrs.get("PAN", False)
        has_phys_tilt = ft_attrs.get("TILT", False)
        if has_phys_pan and has_phys_tilt:
            tags.append("LED.MOVERS")
        else:
            tags.append("LED.WASH")
    return tags


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
    tag_group_base: int = 101,
    dry_run: bool = False,
) -> FTPoolResult:
    result = FTPoolResult(phase=phase)

    # --- Read show name ------------------------------------------------
    result.show = await _listvar(c, "SHOWFILE")
    log.info("Show: %s", result.show)

    # Determine which PT names to store based on phase
    if phase == 1:
        pt_names = PT_NAMES_PHASE1  # dimmer + color (gated by attr check)
    else:
        pt_names = PT_NAMES_PHASE1 + PT_NAMES_PHASE2  # all 6 gated PTs

    for pt in pt_names + ["all"]:
        result.presets_created[pt] = []
        result.presets_skipped[pt] = []

    # --- Enumerate active FT majors + discover attributes ---------------
    log.info("Scanning FT majors 1..%d (attr discovery) ...", MAX_FT_SCAN)
    fts: list[FTInfo] = []
    for major in range(1, MAX_FT_SCAN + 1):
        await _cmd(c, "ClearAll", dry_run)
        await _cmd(c, f"FixtureType {major}.1.1 Thru", dry_run, delay=0.12)
        count = await _selected_count(c)
        if count == 0:
            continue

        attrs = await _get_ft_attributes(c, major, dry_run)
        tags = _classify_ft(attrs)
        fts.append(FTInfo(major=major, total_fixtures=count, attrs=attrs, tags=tags))
        log.info("  FT %d: %d fixtures  tags=%s", major, count, tags or ["(unclassified)"])

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
        ft_grp  = ft_group_base  + offset
        pool_grp = pool_group_base + offset
        pslot    = preset_base    + offset
        wslot    = world_base     + offset
        hue = (i * hue_step) % 360

        vivid  = f"/h={hue} /s=100 /br=100"
        pastel = f"/h={hue} /s=60 /br=100"
        ft_label = f'"FT {ft.major}"'

        log.info(
            "FT %d → ftgrp=%d poolgrp=%d preset=%d world=%d hue=%d  tags=%s",
            ft.major, ft_grp, pool_grp, pslot, wslot, hue, ft.tags,
        )

        # ----------------------------------------------------------------
        # STORE SEQUENCE:
        # (1) FixtureType + Attribute release → Store PT 0 ALL
        # (2) Repeat select per gated PT
        # (3) ClearAll + Preset 0.pslot recall → Store Group (FT) + Store World
        #     Using preset recall (not FixtureType) to get full physical fixture set,
        #     mirroring original Macro 16 lines 83→87 and v12 fix.
        # ----------------------------------------------------------------

        # -- Pool group (slot 11+offset) from FixtureType selection -----
        await _cmd(c, "ClearAll", dry_run)
        await _cmd(c, f"FixtureType {ft.major}.1.1 Thru", dry_run, delay=0.15)
        await _cmd(c, f"Store Group {pool_grp} /o", dry_run)
        await _cmd(c, f"Label Group {pool_grp} {ft_label} /o", dry_run)
        await _cmd(c, f"Appearance Group {pool_grp} {vivid}", dry_run)

        # -- All preset PT 0 (universal) — same FixtureType selection ---
        await _cmd(c, "Attribute 1 Thru At Release", dry_run)
        await _cmd(c, f"Store Preset 0.{pslot} /universal /o", dry_run, delay=0.15)
        await _cmd(c, f'Label Preset 0.{pslot} "FT {ft.major} ALL" /o', dry_run)
        await _cmd(c, f"Appearance Preset 0.{pslot} {vivid}", dry_run)
        result.presets_created["all"].append(pslot)

        # -- Gated presets PT 1-7 -------------------------------------
        for pt_name in pt_names:
            pt_num = PT_NUMBER[pt_name]
            suffix = PT_LABEL_SUFFIX[pt_name]
            has_attr = _has_pt_attrs(ft.attrs, pt_name)

            if not has_attr and ft.attrs:
                # attrs were discovered and FT lacks this PT's attributes
                log.info("    skip PT %d (%s) — FT %d has no matching attrs", pt_num, pt_name, ft.major)
                result.presets_skipped[pt_name].append(pslot)
                continue

            if not ft.attrs and not dry_run:
                # attr discovery failed (nav error) — store unconditionally as safe fallback
                log.warning("    FT %d attr unknown — storing PT %d (%s) unconditionally", ft.major, pt_num, pt_name)

            await _cmd(c, "ClearAll", dry_run)
            await _cmd(c, f"FixtureType {ft.major}.1.1 Thru", dry_run, delay=0.15)
            await _cmd(c, "Attribute 1 Thru At Release", dry_run)
            await _cmd(c, f"Store Preset {pt_num}.{pslot} /universal /o", dry_run, delay=0.15)
            await _cmd(c, f'Label Preset {pt_num}.{pslot} "FT {ft.major} {suffix}" /o', dry_run)
            await _cmd(c, f"Appearance Preset {pt_num}.{pslot} {pastel}", dry_run)
            result.presets_created[pt_name].append(pslot)

        # -- FT group + World via Preset 0 recall ----------------------
        # CRITICAL: must use preset recall (not FixtureType) to populate programmer
        # with the full physical fixture count before Store Group and Store World.
        await _cmd(c, "ClearAll", dry_run)
        await _cmd(c, f"Preset 0.{pslot}", dry_run, delay=0.25)
        await _cmd(c, f"Store Group {ft_grp} /o", dry_run)
        await _cmd(c, f"Label Group {ft_grp} {ft_label} /o", dry_run)
        await _cmd(c, f"Appearance Group {ft_grp} {vivid}", dry_run)
        await _cmd(c, "Attribute 1 Thru At Release", dry_run)
        await _cmd(c, f"Store World {wslot} /o", dry_run, delay=0.15)
        await _cmd(c, f"Label World {wslot} {ft_label} /o", dry_run)
        await _cmd(c, f"Appearance World {wslot} {vivid}", dry_run)

        result.ft_majors.append(ft.major)
        result.groups_created.append(pool_grp)
        result.ft_groups_created.append(ft_grp)
        result.worlds_created.append(wslot)

    await _cmd(c, "ClearAll", dry_run)

    # --- Taxonomy groups -----------------------------------------------
    # Build one Group per tag, containing all FTs with that tag.
    # tag_group_base offsets: LED=+0, LED.MOVERS=+1, LED.WASH=+2
    tag_offsets = {"LED": 0, "LED.MOVERS": 1, "LED.WASH": 2}
    tag_members: dict[str, list[int]] = {t: [] for t in tag_offsets}

    for i, ft in enumerate(fts):
        for tag in ft.tags:
            if tag in tag_members:
                # Use pool group slot as the member (so operators can use group recall)
                tag_members[tag].append(pool_group_base + i)

    for tag, member_slots in tag_members.items():
        if not member_slots:
            continue
        grp_slot = tag_group_base + tag_offsets[tag]
        log.info("Taxonomy group %r → Group %d (members: %s)", tag, grp_slot, member_slots)

        # Store by recalling each member pool group in sequence
        await _cmd(c, "ClearAll", dry_run)
        for mslot in member_slots:
            await _cmd(c, f"SelFix Group {mslot}", dry_run, delay=0.08)
        await _cmd(c, f"Store Group {grp_slot} /o", dry_run)
        await _cmd(c, f'Label Group {grp_slot} "{tag}" /o', dry_run)
        # Taxonomy groups: neutral grey appearance so they stand apart from per-FT colours
        await _cmd(c, f"Appearance Group {grp_slot} /color=666666", dry_run)

        if tag not in result.taxonomy_groups:
            result.taxonomy_groups[tag] = []
        result.taxonomy_groups[tag].append(grp_slot)

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
    parser.add_argument("--ft-group-base", type=int, default=1)
    parser.add_argument("--pool-group-base", type=int, default=11)
    parser.add_argument("--preset-base", type=int, default=11)
    parser.add_argument("--world-base", type=int, default=11)
    parser.add_argument("--tag-group-base", type=int, default=101,
                        help="Starting Group slot for taxonomy groups LED/LED.MOVERS/LED.WASH (default 101)")
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
            tag_group_base=args.tag_group_base,
            dry_run=args.dry_run,
        )

    print("\n=== FT Pool Build Result ===")
    print(f"  Show:       {result.show}")
    print(f"  Phase:      {result.phase}")
    print(f"  FTs:        {result.ft_majors}")
    print(f"  FT groups:  {sorted(result.ft_groups_created)}")
    print(f"  Pool groups:{sorted(result.groups_created)}")
    print(f"  Presets created:")
    for pt, slots in result.presets_created.items():
        if slots:
            print(f"    PT {PT_NUMBER.get(pt, '?')} ({pt}): {slots}")
    if any(result.presets_skipped.values()):
        print(f"  Presets skipped (no matching attrs):")
        for pt, slots in result.presets_skipped.items():
            if slots:
                print(f"    PT {PT_NUMBER.get(pt, '?')} ({pt}): {slots}")
    print(f"  Worlds:     {result.worlds_created}")
    if result.taxonomy_groups:
        print(f"  Taxonomy groups:")
        for tag, slots in result.taxonomy_groups.items():
            print(f"    {tag}: Group {slots}")
    if result.warnings:
        for w in result.warnings:
            print(f"  WARN:  {w}")
    if result.errors:
        for e in result.errors:
            print(f"  ERROR: {e}")
        sys.exit(1)

    if not args.dry_run and result.ft_majors:
        lastrun = asdict(result)
        lastrun["args"] = {
            "ft_group_base": args.ft_group_base,
            "pool_group_base": args.pool_group_base,
            "preset_base": args.preset_base,
            "world_base": args.world_base,
            "tag_group_base": args.tag_group_base,
        }
        LASTRUN_PATH.write_text(json.dumps(lastrun, indent=2))
        log.info("Saved %s", LASTRUN_PATH)

    log.info("Done.")


if __name__ == "__main__":
    asyncio.run(main())
