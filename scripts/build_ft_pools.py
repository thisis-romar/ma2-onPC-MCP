# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Build per-fixture-type Group / Preset / World pool structure (R2 Python orchestrator).

Phase 1  — All (PT 0) + Dimmer (PT 1) + Color (PT 4) universal presets per FT.
Phase 2  — adds Position/Gobo/Beam/Focus/Control where the FT exposes those attrs.
           (Phase 2 is additive; it never modifies Phase 1 objects.)

Attribute discovery navigates EditSetup to determine which PTs a given FT actually
exposes, so empty preset slots are never created. Physical vs virtual channels are
detected via Coarse address — virtual (None) PAN/TILT channels do not count as movers.

Multi-instance handling mirrors Macro 16's canonical Telnet behavior (live-captured
2026-05-13):
  - instance_count == 1: single-instance branch (pool group + FT group + world from
    universal preset recall)
  - instance_count == 2: multi-instance branch — lump objects labelled "FT N.1.0",
    per-instance objects labelled "FT N.1.I", lump FT group rebuilt via MAtricks merge
    to achieve physical fixture ordering across instances
  - instance_count > 2: falls back to single-instance with a warning

World store uses universal preset recall (ClearAll → Preset 0.N → Attribute … At Release
→ Store World N /o) — NOT a raw FixtureType selection — so the world contains the full
physical fixture count, not just 1 instance.

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
PT_NUM_TO_NAME = {v: k for k, v in PT_NUMBER.items() if k != "all"}
PT_OFFICIAL_NAMES = {1: "Dimmer", 2: "Position", 3: "Gobo", 4: "Color",
                     5: "Beam", 6: "Focus", 7: "Control"}
# Appearance colors matching MA2 UI preset-type palette conventions
PT_APPEARANCE_COLORS = {
    "dimmer":   "/color=ffcc00",
    "position": "/color=0088ff",
    "gobo":     "/color=88cc00",
    "color":    "/color=ff44ff",
    "beam":     "/color=ff6600",
    "focus":    "/color=00cc88",
    "control":  "/color=888888",
}


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class FTInfo:
    major: int
    instance_count: int         # $SELECTEDFIXTURESCOUNT after FixtureType N.1.1 Thru
    attrs: dict[str, bool] = field(default_factory=dict)   # attr_name (upper) → is_physical
    tags: list[str] = field(default_factory=list)           # taxonomy tags e.g. ["LED", "LED.MOVERS"]


@dataclass
class FTPoolResult:
    phase: int = 1
    show: str = ""
    ft_majors: list[int] = field(default_factory=list)
    groups_created: list[int] = field(default_factory=list)
    ft_groups_created: list[int] = field(default_factory=list)
    per_instance_groups: dict[str, list[int]] = field(default_factory=dict)  # "N.1.I" → [grp]
    presets_created: dict[str, list[int]] = field(default_factory=dict)
    presets_skipped: dict[str, list[int]] = field(default_factory=dict)
    worlds_created: list[int] = field(default_factory=list)
    per_instance_worlds: dict[str, list[int]] = field(default_factory=dict)  # "N.1.I" → [world]
    attr_groups: dict[str, int] = field(default_factory=dict)   # "Color" → grp_slot
    attr_worlds: dict[str, int] = field(default_factory=dict)   # "Color" → world_slot
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
        for step in [
            "cd /",
            "cd EditSetup",
            "cd FixtureTypes",
            f"cd {major}",
            "cd 1",
            "cd 1",
        ]:
            await c.send_command_with_response(step, timeout=4.0)
            await asyncio.sleep(0.15)

        listing = await c.send_command_with_response("list", timeout=5.0)
        for line in listing.split("\n"):
            m = _CHANTYPE_RE.search(line)
            if m:
                attr_name = m.group(1).upper()
                coarse = m.group(2)
                is_physical = coarse != "None"
                attrs[attr_name] = is_physical

        await c.send_command_with_response("cd /", timeout=3.0)
        await asyncio.sleep(0.30)
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
    """Return taxonomy tags for an FT based on its attribute set."""
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
# Multi-instance merge helper
# ---------------------------------------------------------------------------

async def _matricks_merge_lump(
    c: GMA2TelnetClient,
    ft_lump_grp: int,
    ft_inst1_grp: int,
    ft_inst2_grp: int,
    dry_run: bool,
) -> None:
    """Rebuild the lump FT group with physical fixture ordering using MAtricks walk.

    Mirrors Macro 16 lines 71-99 (live-captured 2026-05-13):
      For each physical fixture (physLoop 0..physCount-1):
        1. Select instance-1 group, MAtricksBlocks 1 → walk to physLoop-th physical → Store /o or /merge
        2. Select instance-2 group, MAtricksBlocks subsPerPhys → walk to physLoop-th block → Store /merge

    Args:
        ft_lump_grp:   Group slot for the lump FT group (will be overwritten then merged into)
        ft_inst1_grp:  Group slot for per-instance group of instance 1 (firstInstFTGroup)
        ft_inst2_grp:  Group slot for per-instance group of instance 2 (firstInstFTGroup + 1)
    """
    # Get physCount from instance-1 group fixture count
    await _cmd(c, "ClearAll", dry_run, delay=0.10)
    await _cmd(c, f"SelFix Group {ft_inst1_grp}", dry_run, delay=0.12)
    phys_count = await _selected_count(c) if not dry_run else 4
    log.info("    merge: inst1 group %d → physCount=%d", ft_inst1_grp, phys_count)

    # Get inst2Total from instance-2 group fixture count
    await _cmd(c, "ClearAll", dry_run, delay=0.10)
    await _cmd(c, f"SelFix Group {ft_inst2_grp}", dry_run, delay=0.12)
    inst2_total = await _selected_count(c) if not dry_run else 24
    subs_per_phys = max(1, inst2_total // phys_count) if phys_count > 0 else 1
    log.info("    merge: inst2 group %d → inst2Total=%d subsPerPhys=%d",
             ft_inst2_grp, inst2_total, subs_per_phys)

    for phys_loop in range(phys_count):
        # Walk instance-1 group to the phys_loop-th physical fixture
        await _cmd(c, "ClearAll", dry_run, delay=0.08)
        await _cmd(c, f"SelFix Group {ft_inst1_grp}", dry_run, delay=0.10)
        await _cmd(c, "MAtricksReset", dry_run, delay=0.08)
        await _cmd(c, "MAtricksBlocks 1", dry_run, delay=0.08)
        for _ in range(phys_loop + 1):
            await _cmd(c, "Next", dry_run, delay=0.06)
        store_flag = "/o" if phys_loop == 0 else "/merge"
        await _cmd(c, f"Store Group {ft_lump_grp} {store_flag}", dry_run, delay=0.12)

        # Walk instance-2 group to the phys_loop-th block
        await _cmd(c, "ClearAll", dry_run, delay=0.08)
        await _cmd(c, f"SelFix Group {ft_inst2_grp}", dry_run, delay=0.10)
        await _cmd(c, "MAtricksReset", dry_run, delay=0.08)
        await _cmd(c, f"MAtricksBlocks {subs_per_phys}", dry_run, delay=0.08)
        for _ in range(phys_loop + 1):
            await _cmd(c, "Next", dry_run, delay=0.06)
        await _cmd(c, f"Store Group {ft_lump_grp} /merge", dry_run, delay=0.12)

        await _cmd(c, "MAtricksReset", dry_run, delay=0.08)
        await _cmd(c, "ClearAll", dry_run, delay=0.08)

    log.info("    merge done: Group %d rebuilt with %d physical × 2 instances", ft_lump_grp, phys_count)


# ---------------------------------------------------------------------------
# Attribute cross-FT group + world builder
# ---------------------------------------------------------------------------

async def _build_attribute_groups_and_worlds(
    c: GMA2TelnetClient,
    fts: list[FTInfo],
    ft_pslot_map: dict[int, int],
    attr_group_base: int,
    attr_world_base: int,
    result: "FTPoolResult",
    dry_run: bool,
) -> None:
    """Create one Group + one World per MA2 PresetType (PT 1-7).

    Each group/world contains ALL fixtures from FTs that expose that PT's
    attribute set.  Group built via Preset-recall + /merge chain so subfixture
    expansion is correct.  World built from SelFix on the combined group.

    Slot layout (default bases: attr_group_base=101, attr_world_base=51):
        PT 1 Dimmer   → Group 102 / World 52
        PT 2 Position → Group 103 / World 53
        PT 3 Gobo     → Group 104 / World 54
        PT 4 Color    → Group 105 / World 55
        PT 5 Beam     → Group 106 / World 56
        PT 6 Focus    → Group 107 / World 57
        PT 7 Control  → Group 108 / World 58
    """
    for pt_num in range(1, 8):
        pt_name = PT_NUM_TO_NAME[pt_num]
        pt_official = PT_OFFICIAL_NAMES[pt_num]
        color = PT_APPEARANCE_COLORS[pt_name]

        qualifying = [ft for ft in fts if _has_pt_attrs(ft.attrs, pt_name) or not ft.attrs]
        if not qualifying:
            log.info("Attr PT %d (%s): no qualifying FTs — skipping", pt_num, pt_official)
            continue

        attr_grp = attr_group_base + pt_num
        attr_wld = attr_world_base + pt_num
        ft_majors = [ft.major for ft in qualifying]
        log.info(
            "Attr PT %d %-10s → Group %-4d + World %-4d (FTs %s)",
            pt_num, pt_official, attr_grp, attr_wld, ft_majors,
        )

        # Build combined group via Preset 0.N recall + /merge per FT
        first = True
        for ft in qualifying:
            pslot = ft_pslot_map[ft.major]
            flag = "/o" if first else "/merge"
            await _cmd(c, "ClearAll", dry_run)
            await _cmd(c, f"Preset 0.{pslot}", dry_run, delay=0.20)
            await _cmd(c, f"Store Group {attr_grp} {flag}", dry_run)
            first = False

        await _cmd(c, f'Label Group {attr_grp} "{pt_official}" /o', dry_run)
        await _cmd(c, f"Appearance Group {attr_grp} {color}", dry_run)
        result.attr_groups[pt_official] = attr_grp

        # Build world from the combined group
        await _cmd(c, "ClearAll", dry_run)
        await _cmd(c, f"SelFix Group {attr_grp}", dry_run, delay=0.15)
        await _cmd(c, f"Store World {attr_wld} /o", dry_run, delay=0.15)
        await _cmd(c, f'Label World {attr_wld} "{pt_official}" /o', dry_run)
        await _cmd(c, f"Appearance World {attr_wld} {color}", dry_run)
        await _cmd(c, "ClearAll", dry_run)
        result.attr_worlds[pt_official] = attr_wld


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
    attr_group_base: int = 101,
    attr_world_base: int = 51,
    dry_run: bool = False,
) -> FTPoolResult:
    result = FTPoolResult(phase=phase)

    # --- Read show name ------------------------------------------------
    result.show = await _listvar(c, "SHOWFILE")
    log.info("Show: %s", result.show)

    if phase == 1:
        pt_names = PT_NAMES_PHASE1
    else:
        pt_names = PT_NAMES_PHASE1 + PT_NAMES_PHASE2

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
        fts.append(FTInfo(major=major, instance_count=count, attrs=attrs, tags=tags))
        log.info("  FT %d: %d instance(s)  tags=%s", major, count, tags or ["(unclassified)"])

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
    # slot_offset is a running counter: each FT consumes 1 slot for single-instance,
    # or (1 + instance_count) slots for multi-instance (lump + per-instance).
    slot_offset = 0
    ft_pslot_map: dict[int, int] = {}   # ft.major → pslot (for attr groups later)

    for i, ft in enumerate(fts):
        ft_grp   = ft_group_base  + slot_offset
        pool_grp = pool_group_base + slot_offset
        pslot    = preset_base    + slot_offset
        wslot    = world_base     + slot_offset
        ft_pslot_map[ft.major] = pslot
        hue = (i * hue_step) % 360

        vivid  = f"/h={hue} /s=100 /br=100"
        pastel = f"/h={hue} /s=60 /br=100"

        # Multi-instance: FT has >1 instance → lump + per-instance objects
        is_multi = ft.instance_count >= 2
        if ft.instance_count > 2:
            result.warnings.append(
                f"FT {ft.major}: {ft.instance_count} instances — only 2-instance merge supported; "
                "falling back to single-instance lump"
            )
            is_multi = False

        ft_label_lump = f'"FT {ft.major}.1.0"' if is_multi else f'"FT {ft.major}.1.1"'
        log.info(
            "FT %d → ftgrp=%d poolgrp=%d preset=%d world=%d hue=%d  instances=%d  tags=%s",
            ft.major, ft_grp, pool_grp, pslot, wslot, hue, ft.instance_count, ft.tags,
        )

        # ----------------------------------------------------------------
        # 1. Pool group + PT 0 ALL preset (from FixtureType instance-1 selection)
        # ----------------------------------------------------------------
        await _cmd(c, "ClearAll", dry_run)
        await _cmd(c, f"FixtureType {ft.major}.1.1 Thru", dry_run, delay=0.15)
        await _cmd(c, f"Store Group {pool_grp} /o", dry_run)
        await _cmd(c, "Attribute 1 Thru At Release", dry_run)
        await _cmd(c, f"Store Preset 0.{pslot} /universal /o", dry_run, delay=0.15)
        await _cmd(c, f'Label Preset 0.{pslot} "FT {ft.major} ALL" /o', dry_run)
        await _cmd(c, f"Appearance Preset 0.{pslot} {vivid}", dry_run)
        result.presets_created["all"].append(pslot)

        # ----------------------------------------------------------------
        # 2. Gated presets PT 1-7 (from same instance-1 FixtureType selection)
        # ----------------------------------------------------------------
        for pt_name in pt_names:
            pt_num = PT_NUMBER[pt_name]
            suffix = PT_LABEL_SUFFIX[pt_name]
            has_attr = _has_pt_attrs(ft.attrs, pt_name)

            if not has_attr and ft.attrs:
                log.info("    skip PT %d (%s) — FT %d has no matching attrs", pt_num, pt_name, ft.major)
                result.presets_skipped[pt_name].append(pslot)
                continue

            if not ft.attrs and not dry_run:
                log.warning("    FT %d attr unknown — storing PT %d (%s) unconditionally", ft.major, pt_num, pt_name)

            await _cmd(c, "ClearAll", dry_run)
            await _cmd(c, f"FixtureType {ft.major}.1.1 Thru", dry_run, delay=0.15)
            await _cmd(c, "Attribute 1 Thru At Release", dry_run)
            await _cmd(c, f"Store Preset {pt_num}.{pslot} /universal /o", dry_run, delay=0.15)
            await _cmd(c, f'Label Preset {pt_num}.{pslot} "FT {ft.major} {suffix}" /o', dry_run)
            await _cmd(c, f"Appearance Preset {pt_num}.{pslot} {pastel}", dry_run)
            result.presets_created[pt_name].append(pslot)

        # ----------------------------------------------------------------
        # 3. FT group + World via UNIVERSAL PRESET RECALL (not FixtureType).
        #    ClearAll → Preset 0.N → expands to ALL physical fixtures of FT N
        #    across all instances. This gives correct fixture counts in worlds
        #    (e.g. 46 for FT 1, not 1 instance).  [Macro 16 lines 20-21]
        # ----------------------------------------------------------------
        await _cmd(c, "ClearAll", dry_run)
        await _cmd(c, f"Preset 0.{pslot}", dry_run, delay=0.20)
        await _cmd(c, f"Store Group {ft_grp} /o", dry_run)
        await _cmd(c, "Attribute 1 Thru At Release", dry_run)
        await _cmd(c, f"Store World {wslot} /o", dry_run, delay=0.15)
        await _cmd(c, f"Label Group {pool_grp} {ft_label_lump} /o", dry_run)
        await _cmd(c, f"Label Group {ft_grp} {ft_label_lump} /o", dry_run)
        await _cmd(c, f"Label Preset 0.{pslot} {ft_label_lump} /o", dry_run)
        await _cmd(c, f"Label World {wslot} {ft_label_lump} /o", dry_run)
        await _cmd(c, f"Appearance Group {pool_grp} {vivid}", dry_run)
        await _cmd(c, f"Appearance Group {ft_grp} {vivid}", dry_run)
        await _cmd(c, f"Appearance World {wslot} {vivid}", dry_run)
        await _cmd(c, "ClearAll", dry_run)

        result.ft_majors.append(ft.major)
        result.groups_created.append(pool_grp)
        result.ft_groups_created.append(ft_grp)
        result.worlds_created.append(wslot)
        slot_offset += 1

        # ----------------------------------------------------------------
        # 4. Multi-instance branch: per-instance groups + MAtricks merge
        #    Mirrors Macro 16 lines 36-99 (live-captured 2026-05-13).
        # ----------------------------------------------------------------
        if is_multi:
            ft_inst_grp_first = -1
            for inst in range(1, ft.instance_count + 1):
                inst_ft_grp   = ft_group_base  + slot_offset
                inst_pool_grp = pool_group_base + slot_offset
                inst_pslot    = preset_base    + slot_offset
                inst_wslot    = world_base     + slot_offset
                inst_label    = f'"FT {ft.major}.1.{inst}"'

                log.info(
                    "  inst %d → ftgrp=%d poolgrp=%d preset=%d world=%d",
                    inst, inst_ft_grp, inst_pool_grp, inst_pslot, inst_wslot,
                )

                # Per-instance pool group + PT 0 preset (from single-instance FixtureType)
                await _cmd(c, "ClearAll", dry_run)
                await _cmd(c, f"FixtureType {ft.major}.1.{inst}", dry_run, delay=0.15)
                await _cmd(c, f"Store Group {inst_pool_grp} /o", dry_run)
                await _cmd(c, "Attribute 1 Thru At Release", dry_run)
                await _cmd(c, f"Store Preset 0.{inst_pslot} /universal /o", dry_run, delay=0.15)

                # Per-instance FT group + World from preset recall
                await _cmd(c, "ClearAll", dry_run)
                await _cmd(c, f"Preset 0.{inst_pslot}", dry_run, delay=0.15)
                await _cmd(c, f"Store Group {inst_ft_grp} /o", dry_run)
                await _cmd(c, "Attribute 1 Thru At Release", dry_run)
                await _cmd(c, f"Store World {inst_wslot} /o", dry_run, delay=0.15)

                # Labels + appearance (pastel to signal sub-instance)
                await _cmd(c, f"Label Group {inst_pool_grp} {inst_label} /o", dry_run)
                await _cmd(c, f"Label Group {inst_ft_grp} {inst_label} /o", dry_run)
                await _cmd(c, f"Label Preset 0.{inst_pslot} {inst_label} /o", dry_run)
                await _cmd(c, f"Label World {inst_wslot} {inst_label} /o", dry_run)
                await _cmd(c, f"Appearance Group {inst_pool_grp} {pastel}", dry_run)
                await _cmd(c, f"Appearance Group {inst_ft_grp} {pastel}", dry_run)
                await _cmd(c, f"Appearance Preset 0.{inst_pslot} {pastel}", dry_run)
                await _cmd(c, f"Appearance World {inst_wslot} {pastel}", dry_run)
                await _cmd(c, "ClearAll", dry_run)

                key = f"{ft.major}.1.{inst}"
                result.per_instance_groups.setdefault(key, []).append(inst_ft_grp)
                result.per_instance_worlds.setdefault(key, []).append(inst_wslot)

                if inst == 1:
                    ft_inst_grp_first = inst_ft_grp

                slot_offset += 1

            # MAtricks merge: rebuild lump FT group with physical ordering
            if ft_inst_grp_first >= 0:
                log.info("  FT %d: running MAtricks merge on Group %d ...", ft.major, ft_grp)
                await _matricks_merge_lump(
                    c,
                    ft_lump_grp=ft_grp,
                    ft_inst1_grp=ft_inst_grp_first,
                    ft_inst2_grp=ft_inst_grp_first + 1,
                    dry_run=dry_run,
                )

    # --- End: cleanup + MAtricksReset ---------------------------------
    await _cmd(c, "MAtricksReset", dry_run)
    await _cmd(c, "ClearAll", dry_run)

    # --- Attribute groups + worlds (PT 1-7) ----------------------------
    await _build_attribute_groups_and_worlds(
        c, fts, ft_pslot_map,
        attr_group_base=attr_group_base,
        attr_world_base=attr_world_base,
        result=result,
        dry_run=dry_run,
    )

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
    parser.add_argument("--attr-group-base", type=int, default=101,
                        help="Group slot base for PT attribute groups (base+1=Dimmer … base+7=Control)")
    parser.add_argument("--attr-world-base", type=int, default=51,
                        help="World slot base for PT attribute worlds (base+1=Dimmer … base+7=Control)")
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
            attr_group_base=args.attr_group_base,
            attr_world_base=args.attr_world_base,
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
    if result.per_instance_groups:
        print(f"  Per-instance FT groups:")
        for key, grps in sorted(result.per_instance_groups.items()):
            print(f"    FT {key}: {grps}")
    if result.per_instance_worlds:
        print(f"  Per-instance worlds:")
        for key, worlds in sorted(result.per_instance_worlds.items()):
            print(f"    FT {key}: {worlds}")
    if result.attr_groups:
        print(f"  Attribute groups (PT 1-7):")
        for name, slot in sorted(result.attr_groups.items(), key=lambda x: PT_NUMBER.get(x[0].lower(), 99)):
            print(f"    PT {PT_NUMBER.get(name.lower(), '?')} {name}: Group {slot}")
    if result.attr_worlds:
        print(f"  Attribute worlds (PT 1-7):")
        for name, slot in sorted(result.attr_worlds.items(), key=lambda x: PT_NUMBER.get(x[0].lower(), 99)):
            print(f"    PT {PT_NUMBER.get(name.lower(), '?')} {name}: World {slot}")
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
            "attr_group_base": args.attr_group_base,
            "attr_world_base": args.attr_world_base,
        }
        LASTRUN_PATH.write_text(json.dumps(lastrun, indent=2))
        log.info("Saved %s", LASTRUN_PATH)

    log.info("Done.")


if __name__ == "__main__":
    asyncio.run(main())
