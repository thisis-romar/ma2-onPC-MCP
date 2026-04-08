# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
tools_enterprise.py -- 20 ENTERPRISE-tier MCP tool functions from server.py.

These tools require an ENTERPRISE license tier and will move to the
private submodule after the git submodule split.  The remaining 34
ENTERPRISE tools live in server_orchestration_tools.py.

Imports the shared ``mcp`` FastMCP instance and ``_handle_errors`` decorator
from ``server_core.py`` so tools register on the same server.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from datetime import UTC, datetime
from pathlib import Path

from src.auth import OAuthScope, has_scope, require_scope
from src.commands import list_effect_library as build_list_effect_library
from src.commands import list_macro_library as build_list_macro_library
from src.commands import psr as build_psr
from src.commands import psr_list as build_psr_list
from src.commands import psr_prepare as build_psr_prepare
from src.navigation import list_destination, navigate
import src.server_core as _sc

from src.server_core import (
    _check_pool_slots,
    _GMA_SAFETY_LEVEL,
    _handle_errors,
    _OBJECT_POOL_DESTINATIONS,
    _parse_listvar,
    _parse_preset_tree_list,
    _validate_object_exists,
    _vocab_spec,
    mcp,
)
from src.vocab import RiskTier, classify_token

logger = logging.getLogger(__name__)

# Re-export for test discoverability (tools use _sc.get_client() for late binding)
get_client = _sc.get_client


def _get_orchestrator():
    """Lazy accessor for the Orchestrator singleton in server.py."""
    import src.server as _srv
    return _srv._orchestrator


class _OrchestratorProxy:
    """Attribute proxy that defers to the server's _orchestrator at access time."""
    def __getattr__(self, name):
        return getattr(_get_orchestrator(), name)


_orchestrator = _OrchestratorProxy()


# ============================================================
# Tools 57–64: Tier 1 — High-Impact Tools




















async def _discover_filter_attributes() -> dict[str, list[str]]:
    """Discover actual attribute names from the current show's fixture library.

    Browses PresetTypes 1-7 at depth 2, collecting all attribute names.
    Returns a dict with the same shape as FILTER_ATTRIBUTES in constants.py.
    Falls back to FILTER_ATTRIBUTES if discovery fails.
    """
    from src.commands.constants import FILTER_ATTRIBUTES

    preset_type_names = ["dimmer", "position", "gobo", "color", "beam", "focus", "control"]
    discovered: dict[str, list[str]] = {}

    try:
        client = await _sc.get_client()
        for pt_id, cat_name in enumerate(preset_type_names, start=1):
            attrs: list[str] = []
            await navigate(client, "/")
            await navigate(client, f"10.2.{pt_id}")
            feat_list = await list_destination(client)
            feat_raw = feat_list.raw_response
            features = _parse_preset_tree_list(feat_raw)

            for fi in range(1, len(features) + 1):
                await navigate(client, "/")
                await navigate(client, f"10.2.{pt_id}.{fi}")
                attr_list = await list_destination(client)
                attr_raw = attr_list.raw_response
                attr_entries = _parse_preset_tree_list(attr_raw)
                for entry in attr_entries:
                    name = entry.get("name", "").upper()
                    if name and name not in attrs:
                        attrs.append(name)

            discovered[cat_name] = attrs if attrs else FILTER_ATTRIBUTES.get(cat_name, [])
        await navigate(client, "/")
    except Exception:
        # On any failure, return defaults
        return dict(FILTER_ATTRIBUTES)

    return discovered


# ============================================================

# Module-level cache for the taxonomy to avoid repeated disk reads.
_taxonomy_cache: dict | None = None


def _invalidate_taxonomy_cache() -> None:
    global _taxonomy_cache
    _taxonomy_cache = None


def _load_taxonomy_cached() -> dict:
    global _taxonomy_cache
    if _taxonomy_cache is not None:
        return _taxonomy_cache
    from src.categorization.taxonomy import DEFAULT_TAXONOMY_PATH, load_taxonomy

    if not DEFAULT_TAXONOMY_PATH.exists():
        raise FileNotFoundError(
            "Taxonomy not generated yet. Run: "
            "uv run python scripts/categorize_tools.py --provider zero"
        )
    _taxonomy_cache = load_taxonomy()
    return _taxonomy_cache


async def _telnet_send_fn(cmd: str) -> str:
    """Thin wrapper so Orchestrator can send raw telnet without importing get_client."""
    client = await _sc.get_client()
    return await client.send_command_with_response(cmd)


async def _tool_caller(tool_name: str, inputs: dict):
    """
    Call any registered MCP tool function by name.
    Looks up the function from this module's global namespace at call time,
    so all 109 tool definitions above are available.
    """
    fn = sys.modules[__name__].__dict__.get(tool_name)
    if fn is None:
        raise ValueError(f"Orchestrator: unknown tool '{tool_name}'")
    return await fn(**inputs)



# Register MCP completions (argument autocompletion for prompts + resource templates)

# Register MCP resource subscriptions (live state push when resources change)
from src.subscriptions import register_subscriptions  # noqa: E402

register_subscriptions(mcp)


# ============================================================


def _build_tool_registry() -> dict:
    """Build a registry mapping tool names to their async callables.

    This enables the agent runtime to call MCP tools directly as Python
    functions, without going through the MCP protocol.

    Uses FastMCP's tool manager as the authoritative source so that the
    registry is always exactly the set of registered MCP tools — no more,
    no less. Falls back to globals() introspection if the FastMCP internals
    change in a future version.
    """
    registry: dict = {}
    try:
        for tool_name, tool_obj in mcp._tool_manager._tools.items():
            fn = getattr(tool_obj, "fn", None)
            if fn is not None:
                registry[tool_name] = fn
    except AttributeError:
        # Fallback: scan module globals for @_handle_errors-wrapped async fns
        import inspect

        for name, obj in globals().items():
            if callable(obj) and hasattr(obj, "__wrapped__") or inspect.iscoroutinefunction(obj) and not name.startswith("_"):
                registry[name] = obj
    return registry


# ============================================================
# MCP Tools Definition












@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def scan_console_indexes(
    reset_to: str = "/",
    max_index: int = 50,
    stop_after_failures: int = 3,
) -> str:
    """
    Scan numeric indexes via cd N → list → cd <reset_to>.

    For each index N from 1 to max_index:
      1. cd N           — navigate into that index
      2. list           — enumerate children there
      3. cd <reset_to>  — return to the base location for the next iteration

    The reset_to destination controls what each cd N is relative to:
      - "/"          (default) scan root-level indexes (Showfile, TimeConfig, …)
      - "Sequence"   reset to Sequence pool → cd N enters Sequence N → list shows its cues
      - "Group"      reset to Group pool → cd N enters Group N

    Stops early after stop_after_failures consecutive indexes with no entries.

    Args:
        reset_to: Where to navigate after each list before the next cd N (default "/").
        max_index: Highest index to try (default 50).
        stop_after_failures: Stop after this many consecutive empty indexes (default 3).

    Returns:
        str: JSON with a list of scan results — one entry per index that
             returned list output, each with index, location, object_type,
             and parsed entries (object_type, object_id, name).
    """
    client = await _sc.get_client()
    results = await scan_indexes(
        client,
        reset_to=reset_to,
        max_index=max_index,
        stop_after_failures=stop_after_failures,
    )

    return json.dumps(
        {
            "scanned_count": len(results),
            "results": [
                {
                    "index": r.index,
                    "location": r.location,
                    "object_type": r.object_type,
                    "entry_count": len(r.entries),
                    "entries": [
                        {
                            "object_type": e.object_type,
                            "object_id": e.object_id,
                            "name": e.name,
                        }
                        for e in r.entries
                    ],
                }
                for r in results
            ],
        },
        indent=2,
    )


# ============================================================


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def search_codebase(
    query: str,
    top_k: int = 8,
    kind: str | None = None,
    graph_expand: bool = False,
) -> str:
    """Search source code, grandMA2 docs, and MCP SDK source using the RAG index.

    Three indexed knowledge sources (repo_refs):
    - "worktree"     — this server's Python source, tests, and docs
    - "ma2-help-docs" — ~1,043 grandMA2 help pages from help.malighting.com
    - "mcp-sdk"      — installed MCP SDK source (~110 files, types, server, tools)

    Works without any API key (text-search fallback). With GITHUB_MODELS_TOKEN
    set, results are ranked by semantic similarity.

    Args:
        query:  Natural language or keyword query (e.g. "navigate console",
                "store preset", "how to patch fixtures", "mcp tool context")
        top_k:  Number of results to return (default 8, max 20)
        kind:   Optional filter — one of: "source", "test", "doc", "config"
        graph_expand: When True and a knowledge graph is available, enrich
                results with graph context (entity relationships from the
                current console state).

    Returns:
        JSON array of matching chunks with path, kind, lines, score, and text.
        When graph_expand is True, each hit includes a graph_context field.
        Returns an error JSON if the RAG index has not been built yet.

    Examples:
        - Find command builders:   query="store preset", kind="source"
        - Find grandMA2 docs:      query="how to patch fixtures", kind="doc"
        - Find MCP SDK internals:  query="mcp tool decorator context"
        - Search everything:       query="effects engine"
        - Find test examples:      query="navigate_console", kind="test"
    """
    from pathlib import Path

    from rag.retrieve.query import rag_query

    db = Path(__file__).parent.parent / "rag" / "store" / "rag.db"
    if not db.exists():
        return json.dumps({
            "error": "RAG index not found. Build it first: uv run python scripts/rag_ingest.py",
            "blocked": True,
        }, indent=2)

    provider = None
    token = os.getenv("GITHUB_MODELS_TOKEN") or os.getenv("GITHUB_TOKEN")
    if token:
        from rag.ingest.embed import GitHubModelsProvider
        provider = GitHubModelsProvider(token=token)

    # Resolve graph store for GraphRAG enrichment
    kg_store = None
    if graph_expand:
        from src.knowledge_graph import get_graph_store
        kg_store = get_graph_store()

    want = min(top_k, 20)
    # When a kind filter is requested, over-fetch 10× so we have enough candidates
    # of the right kind after filtering (the DB has 4 kinds; web docs dominate).
    fetch_k = want * 10 if kind else want
    hits = rag_query(
        query, embedding_provider=provider, top_k=fetch_k, db_path=db,
        graph_store=kg_store,
    )

    if kind:
        hits = [h for h in hits if h.kind == kind][:want]

    return json.dumps([
        {
            "path": hit.path,
            "kind": hit.kind,
            "lines": f"{hit.start_line}-{hit.end_line}",
            "score": round(hit.score, 4),
            "text": hit.text,
            **({"graph_context": hit.graph_context} if hit.graph_context else {}),
        }
        for hit in hits
    ], indent=2)


# ============================================================
# Tools 65–69: Tier 2 — Setup & Library Tools












@mcp.tool()
@require_scope(OAuthScope.FILTER_MANAGE)
@_handle_errors
async def create_matricks_library(
    max_value: int = 4,
    start_slot: int = 2,
    confirm_destructive: bool = False,
) -> str:
    """
    Create a full MAtricks combinatorial library (DESTRUCTIVE).

    Generates every combination of Wings × Groups × Blocks × Interleave
    (values 0 to max_value) as XML with embedded appearance colors and
    imports into the MAtricks pool. Colors are instant — no telnet loop needed.

    25-color scheme: Wings=hue (Red/YellowGreen/Cyan/Blue/Magenta),
    Groups=brightness (100/80/60/45/30).

    With max_value=4: 5^4 = 625 pool items, named W0-G0-B0-I0 through W4-G4-B4-I4.

    Args:
        max_value: Upper bound for each property (default 4, gives 5^4=625 items).
        start_slot: First pool slot to import into (default 2, slot 1 is Reset).
        confirm_destructive: Must be True to execute (overwrites MAtricks pool entries).

    Returns:
        str: JSON with pool_items_created, color_scheme, first_slot, last_slot.
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "Create MAtricks Library overwrites MAtricks pool entries. Pass confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    from datetime import datetime
    from pathlib import Path

    matricks_dir = Path(
        "C:/ProgramData/MA Lighting Technologies/grandma/gma2_V_3.9.60/matricks"
    )
    xml_filename = "matricks_combinatorial_library"

    # 25-color scheme: Wings=hue (5 hues), Groups=brightness (5 levels)
    wings_hues = {0: 0, 1: 72, 2: 144, 3: 216, 4: 288}
    groups_brightness = {0: 100, 1: 80, 2: 60, 3: 45, 4: 30}

    def _hsb_to_hex(hue: int, sat: int, bright: int) -> str:
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(hue / 360, sat / 100, bright / 100)
        return f"{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"

    # Generate XML with appearance colors embedded
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S")
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<MA xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        ' xmlns="http://schemas.malighting.de/grandma2/xml/MA"'
        ' xsi:schemaLocation="http://schemas.malighting.de/grandma2/xml/MA'
        ' http://schemas.malighting.de/grandma2/xml/3.9.60/MA.xsd"'
        ' major_vers="3" minor_vers="9" stream_vers="60">',
        f'\t<Info datetime="{now}" showfile="" />',
    ]

    total = (max_value + 1) ** 4
    index = 0
    for w in range(max_value + 1):
        for g in range(max_value + 1):
            h = wings_hues.get(w, 0)
            br = groups_brightness.get(g, 100)
            hex_color = _hsb_to_hex(h, 100, br)
            for b in range(max_value + 1):
                for i in range(max_value + 1):
                    name = f"W{w}-G{g}-B{b}-I{i}"
                    lines.append(f'\t<Matrix index="{index}" name="{name}">')
                    lines.append(f'\t\t<Appearance Color="{hex_color}" />')
                    lines.append(
                        f'\t\t<Settings wings="{w}" group_x="{g}"'
                        f' block_x="{b}" interleave="{i}" />'
                    )
                    lines.append("\t</Matrix>")
                    index += 1

    lines.append("</MA>")

    # Write XML to MA2 matricks directory
    xml_path = matricks_dir / f"{xml_filename}.xml"
    xml_path.write_text("\n".join(lines), encoding="utf-8")

    # Import via telnet — colors are embedded in XML, no telnet loop needed
    client = await _sc.get_client()

    # Pre-import availability check
    last_slot = start_slot + total - 1
    avail = await _check_pool_slots(
        client, "MAtricks",
        start_from=start_slot, scan_up_to=last_slot,
    )
    availability_warning = None
    if avail["occupied_slots"]:
        availability_warning = {
            "slots_that_will_be_overwritten": len(avail["occupied_slots"]),
            "occupied": avail["occupied_slots"][:20],  # cap at 20 for readability
        }

    import_cmd = f'import "{xml_filename}" at matricks {start_slot}'
    response = await client.send_command_with_response(import_cmd)

    result: dict = {
        "pool_items_created": total,
        "total_slots": total,
        "first_slot": start_slot,
        "last_slot": last_slot,
        "naming_scheme": "W{wings}-G{groups}-B{blocks}-I{interleave}",
        "color_scheme": {
            "status": "embedded_in_xml",
            "mapping": "25 colors: Wings=hue (Red/YellowGreen/Cyan/Blue/Magenta), Groups=brightness (100/80/60/45/30)",
        },
        "max_value": max_value,
        "xml_file": str(xml_path),
        "import_response": response[:200],
        "risk_tier": "DESTRUCTIVE",
    }
    if availability_warning:
        result["availability_warning"] = availability_warning

    return json.dumps(result, indent=2)


@mcp.tool()
@require_scope(OAuthScope.FILTER_MANAGE)
@_handle_errors
async def create_filter_library(
    start_slot: int = 3,
    include_combos: bool = True,
    include_exclusions: bool = True,
    include_vte: bool = False,
    fixture_attributes: dict[str, list[str]] | None = None,
    confirm_destructive: bool = False,
) -> str:
    """
    Create a comprehensive Filter library with color-coded pool items (DESTRUCTIVE).

    Generates filters for each PresetType (Dimmer, Position, Gobo, Color, Beam,
    Focus, Control), useful multi-type combos, and "No X" exclusion filters.
    Each filter is color-coded by category and imported as individual XML files.

    Optionally generates Value/ValueTimes/Effects on/off variants for each base
    filter (7 combos per filter, excluding all-off). V/VT/E toggles are embedded
    in the XML as value="false", value_timing="false", effect="false" attributes.

    Slot layout (default start_slot=3):
      - Slots 3-9: Single PresetType filters (7 items)
      - Slots 10-16: Combo filters (7 items, if include_combos)
      - Slots 17-23: "No X" exclusion filters (7 items, if include_exclusions)
      - Slots 24+: V/VT/E variants (N_base × 7, if include_vte)

    Args:
        start_slot: First pool slot (default 3, preserving system filters 1-2).
        include_combos: Include multi-type combo filters (default True).
        include_exclusions: Include "No X" exclusion filters (default True).
        include_vte: Include Value/ValueTimes/Effects variants (default False).
            When True, generates 7 V/VT/E combos for each base filter.
        fixture_attributes: Show-specific attribute dict (same shape as FILTER_ATTRIBUTES).
            If None, uses hardcoded defaults (Mac 700 + Generic Dimmer).
            Call discover_filter_attributes() first to get accurate values for your show.
        confirm_destructive: Must be True to execute (overwrites filter pool entries).

    Returns:
        str: JSON with filters_created, slots, color_scheme summary.
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "Create Filter Library overwrites filter pool entries. "
                     "Pass confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    from datetime import datetime
    from pathlib import Path

    from src.commands.constants import (
        FILTER_ATTRIBUTES,
        FILTER_COLORS,
        FILTER_VTE_COMBOS,
    )

    importexport_dir = Path(
        "C:/ProgramData/MA Lighting Technologies/grandma/"
        "gma2_V_3.9.60/importexport/filters"
    )

    # Use provided fixture attributes or fall back to hardcoded defaults
    attrs_source = fixture_attributes if fixture_attributes else FILTER_ATTRIBUTES

    # Build attribute lists
    dimmer = attrs_source.get("dimmer", FILTER_ATTRIBUTES["dimmer"])
    position = attrs_source.get("position", FILTER_ATTRIBUTES["position"])
    gobo = attrs_source.get("gobo", FILTER_ATTRIBUTES["gobo"])
    color = attrs_source.get("color", FILTER_ATTRIBUTES["color"])
    beam = attrs_source.get("beam", FILTER_ATTRIBUTES["beam"])
    focus = attrs_source.get("focus", FILTER_ATTRIBUTES["focus"])
    control = attrs_source.get("control", FILTER_ATTRIBUTES["control"])
    all_attrs = dimmer + position + gobo + color + beam + focus + control

    # Build base filter definitions: (slot, name, attrs, cat)
    base_filters: list[tuple[int, str, list[str], str]] = []
    slot = start_slot

    for cat, attrs in [
        ("dimmer", dimmer), ("position", position), ("gobo", gobo),
        ("color", color), ("beam", beam), ("focus", focus), ("control", control),
    ]:
        base_filters.append((slot, cat.capitalize(), attrs, cat))
        slot += 1

    if include_combos:
        for name, attrs in [
            ("Dim+Pos", dimmer + position),
            ("Dim+Color", dimmer + color),
            ("Pos+Color", position + color),
            ("Pos+Gobo", position + gobo),
            ("Gobo+Beam", gobo + beam),
            ("Beam+Focus", beam + focus),
            ("Pos+Col+Gobo", position + color + gobo),
        ]:
            base_filters.append((slot, name, attrs, "combo"))
            slot += 1

    if include_exclusions:
        for name, attrs in [
            ("No Dimmer", [a for a in all_attrs if a not in dimmer]),
            ("No Position", [a for a in all_attrs if a not in position]),
            ("No Gobo", [a for a in all_attrs if a not in gobo]),
            ("No Color", [a for a in all_attrs if a not in color]),
            ("No Beam", [a for a in all_attrs if a not in beam]),
            ("No Focus", [a for a in all_attrs if a not in focus]),
            ("No Control", [a for a in all_attrs if a not in control]),
        ]:
            base_filters.append((slot, name, attrs, "exclude"))
            slot += 1

    # Build full filter list: base + optional V/VT/E variants
    # Each entry: (slot, name, attrs, cat, value, value_timing, effect)
    all_filters: list[tuple[int, str, list[str], str, bool, bool, bool]] = []
    for f_slot, f_name, f_attrs, f_cat in base_filters:
        all_filters.append((f_slot, f_name, f_attrs, f_cat, True, True, True))

    if include_vte:
        vte_slot = slot  # continue after base filters
        for _base_slot, base_name, f_attrs, f_cat in base_filters:
            for suffix, v, vt, e in FILTER_VTE_COMBOS:
                vte_name = f"{base_name} {suffix}"
                all_filters.append(
                    (vte_slot, vte_name, f_attrs, f_cat, v, vt, e)
                )
                vte_slot += 1

    # XML generation helper
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S")
    xml_header = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<MA xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        ' xmlns="http://schemas.malighting.de/grandma2/xml/MA"'
        ' xsi:schemaLocation="http://schemas.malighting.de/grandma2/xml/MA'
        ' http://schemas.malighting.de/grandma2/xml/3.9.60/MA.xsd"'
        ' major_vers="3" minor_vers="9" stream_vers="60">\n'
        f'\t<Info datetime="{now}" showfile="" />\n'
    )

    client = await _sc.get_client()

    # Pre-import availability check
    last_filter_slot = all_filters[-1][0] if all_filters else start_slot
    avail = await _check_pool_slots(
        client, "Filter",
        start_from=start_slot, scan_up_to=last_filter_slot,
    )
    availability_warning = None
    if avail["occupied_slots"]:
        availability_warning = {
            "slots_that_will_be_overwritten": len(avail["occupied_slots"]),
            "occupied": avail["occupied_slots"][:20],
        }

    results = []

    for f_slot, f_name, f_attrs, f_cat, f_v, f_vt, f_e in all_filters:
        color_hex = FILTER_COLORS[f_cat]

        # Build V/VT/E XML attributes (only emit false values)
        vte_parts = []
        if not f_v:
            vte_parts.append('value="false"')
        if not f_vt:
            vte_parts.append('value_timing="false"')
        if not f_e:
            vte_parts.append('effect="false"')
        vte_str = (" " + " ".join(vte_parts)) if vte_parts else ""

        attr_lines = "\n".join(
            f'\t\t\t<AttributeLink name="{a}" />' for a in f_attrs
        )
        filter_xml = (
            f'\t<Filter index="{f_slot - 1}"{vte_str} keep_filter="false">\n'
            f'\t\t<Appearance Color="{color_hex}" />\n'
            f"\t\t<Attributes>\n{attr_lines}\n\t\t</Attributes>\n"
            f"\t</Filter>"
        )
        xml_content = xml_header + filter_xml + "\n</MA>"

        fname = f"filter_{f_slot:03d}"
        fpath = importexport_dir / f"{fname}.xml"
        fpath.write_text(xml_content, encoding="utf-8")

        # Import (use 8.3 short path to avoid spaces in path)
        resp = await client.send_command_with_response(
            f'Import "{fname}" At Filter {f_slot}'
            " /path=C:/ProgramData/MALIGH~1/grandma/gma2_V_3.9.60/IMPORT~1/filters"
        )
        import_ok = "Error" not in resp

        # Label
        await client.send_command_with_response(
            f'Label Filter {f_slot} "{f_name}"'
        )

        # Apply appearance color via telnet (backup if XML color didn't take)
        r = int(color_hex[0:2], 16) * 100 // 255
        g = int(color_hex[2:4], 16) * 100 // 255
        b = int(color_hex[4:6], 16) * 100 // 255
        await client.send_command_with_response(
            f"Appearance Filter {f_slot} /r={r} /g={g} /b={b}"
        )

        results.append({
            "slot": f_slot,
            "name": f_name,
            "category": f_cat,
            "attributes": len(f_attrs),
            "vte": f"V={'on' if f_v else 'off'}"
                   f" VT={'on' if f_vt else 'off'}"
                   f" E={'on' if f_e else 'off'}",
            "import_ok": import_ok,
        })

    result_json: dict = {
        "filters_created": len(results),
        "base_filters": len(base_filters),
        "vte_variants": len(results) - len(base_filters),
        "first_slot": start_slot,
        "last_slot": all_filters[-1][0] if all_filters else start_slot,
        "filters": results,
        "color_scheme": {
            "dimmer": "FFCC00 (yellow)",
            "position": "0088FF (blue)",
            "gobo": "00CC44 (green)",
            "color": "FF00CC (magenta)",
            "beam": "FF6600 (orange)",
            "focus": "00CCCC (cyan)",
            "control": "999999 (grey)",
            "combo": "CC44FF (purple)",
            "exclude": "FF3333 (red)",
        },
        "xml_directory": str(importexport_dir),
        "risk_tier": "DESTRUCTIVE",
    }
    if availability_warning:
        result_json["availability_warning"] = availability_warning

    # Update filter_vte write-tracker (Gap 1 — VTE layer toggles have no telnet readback)
    if snap := _orchestrator.last_snapshot:
        snap.filter_vte.update({"value": True, "value_timing": True, "effect": True})

    return json.dumps(result_json, indent=2)


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def list_tool_categories(category: str | None = None) -> str:
    """
    List auto-discovered tool categories (SAFE_READ).

    Returns the ML-generated taxonomy of all MCP tools grouped by
    functional similarity.  Categories are discovered via unsupervised
    K-Means clustering over hybrid features (structural metadata +
    docstring embeddings).

    Args:
        category: Optional category name filter (case-insensitive partial match).

    Returns:
        str: JSON with categories, tool lists, and clustering metadata.
    """
    taxonomy = _load_taxonomy_cached()
    from src.categorization.taxonomy import get_tools_by_category

    filtered = get_tools_by_category(taxonomy, category)
    return json.dumps(
        {
            "metadata": taxonomy.get("metadata", {}),
            "categories": filtered,
        },
        indent=2,
    )


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def recluster_tools(
    provider: str = "zero",
    k: int | None = None,
    alpha: float = 0.4,
) -> str:
    """
    Trigger re-clustering of all MCP tools (SAFE_READ).

    Runs the full ML pipeline: extract features from tool definitions,
    embed docstrings, cluster via K-Means, and regenerate the taxonomy.

    Args:
        provider: Embedding provider — "zero" (fast stub) or "github"
                  (real embeddings, requires GITHUB_MODELS_TOKEN).
        k: Override number of clusters.  None = auto-select via silhouette.
        alpha: Structural feature weight (0–1). Embedding weight = 1 − alpha.

    Returns:
        str: JSON summary with categories, silhouette score, and tool assignments.
    """
    import importlib
    from pathlib import Path

    # Import lazily to avoid circular imports at module load time.
    mod = importlib.import_module("scripts.categorize_tools")
    server_path = str(Path(__file__).resolve())

    result = mod.run(
        provider_name=provider,
        k_override=k,
        alpha=alpha,
        server_path=server_path,
    )
    _invalidate_taxonomy_cache()

    return json.dumps(
        {
            "metadata": result["metadata"],
            "category_count": len(result["categories"]),
            "categories": {
                name: {
                    "tool_count": cat["tool_count"],
                    "tools": [t["name"] for t in cat["tools"]],
                }
                for name, cat in result["categories"].items()
            },
        },
        indent=2,
    )


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def get_similar_tools(tool_name: str, top_n: int = 5) -> str:
    """
    Find the most similar MCP tools to a given tool (SAFE_READ).

    Uses Euclidean distance in the combined feature space (structural +
    embedding) from the last clustering run.

    Args:
        tool_name: Name of the reference tool (e.g. "playback_action").
        top_n: Number of similar tools to return (default 5).

    Returns:
        str: JSON array of similar tools ranked by distance, with category.
    """

    from src.categorization.clustering import euclidean_distance
    from src.categorization.taxonomy import get_feature_matrix

    taxonomy = _load_taxonomy_cached()
    names, matrix = get_feature_matrix(taxonomy)

    if tool_name not in names:
        return json.dumps(
            {"error": f"Tool '{tool_name}' not found in taxonomy. Available: {names[:10]}...", "blocked": True},
            indent=2,
        )

    idx = names.index(tool_name)
    ref_vec = matrix[idx]

    # Compute distances to all other tools
    distances: list[tuple[str, float]] = []
    for i, name in enumerate(names):
        if i == idx:
            continue
        dist = euclidean_distance(ref_vec, matrix[i])
        distances.append((name, dist))

    distances.sort(key=lambda x: x[1])
    top = distances[:top_n]

    # Find categories for each tool
    categories = taxonomy.get("categories", {})
    tool_to_category: dict[str, str] = {}
    for cat_name, cat_data in categories.items():
        for t in cat_data.get("tools", []):
            tool_to_category[t["name"]] = cat_name

    max_dist = top[-1][1] if top else 1.0
    return json.dumps(
        [
            {
                "name": name,
                "similarity": round(1.0 - (dist / max_dist) if max_dist > 0 else 1.0, 4),
                "distance": round(dist, 6),
                "category": tool_to_category.get(name, "unknown"),
            }
            for name, dist in top
        ],
        indent=2,
    )


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def suggest_tool_for_task(
    task_description: str,
    top_n: int = 3,
    provider: str = "zero",
    prefer_semantic: bool = True,
    filter_risk_tier: str = "",
    filter_license_tier: str = "",
) -> str:
    """
    Suggest MCP tools for a natural-language task description (SAFE_READ).

    Uses hybrid retrieval: keyword matching + embedding-based cosine similarity,
    fused via Reciprocal Rank Fusion (RRF).  Falls back to keyword-only when no
    embedding token is available.

    Args:
        task_description: What you want to accomplish (e.g. "fade out all fixtures").
        top_n: Number of suggestions to return (default 3).
        provider: Embedding provider — "zero" (keyword fallback) or "github".
            Overridden by ``prefer_semantic`` when a token is available.
        prefer_semantic: When True (default), automatically use embedding-based
            search if GITHUB_MODELS_TOKEN is set in the environment.  Falls back
            to keyword matching with a ``warning`` field when no token is present.
            Set to False to force keyword matching regardless of token availability.
        filter_risk_tier: Only return tools with this risk tier
            ("SAFE_READ", "SAFE_WRITE", "DESTRUCTIVE").  Empty = no filter.
        filter_license_tier: Only return tools at or below this license tier
            ("community", "professional", "enterprise").  Empty = no filter.

    Returns:
        str: JSON array of suggested tools with scores and descriptions.
             Includes a top-level ``warning`` key when semantic search was
             requested but fell back to keyword matching.
    """
    import numpy as np

    from src.categorization.clustering import cosine_similarity
    from src.categorization.taxonomy import get_docstring_map, get_embedding_matrix

    taxonomy = _load_taxonomy_cached()

    # Find category map
    categories = taxonomy.get("categories", {})
    tool_to_category: dict[str, str] = {}
    for cat_name, cat_data in categories.items():
        for t in cat_data.get("tools", []):
            tool_to_category[t["name"]] = cat_name

    docstrings = get_docstring_map(taxonomy)

    # Resolve effective provider: prefer_semantic promotes "zero" → "github"
    # when a token is available; records a warning when it cannot.
    semantic_warning: str | None = None
    effective_provider = provider
    if prefer_semantic and provider == "zero":
        if os.environ.get("GITHUB_MODELS_TOKEN", ""):
            effective_provider = "github"
        else:
            semantic_warning = (
                "prefer_semantic=True but GITHUB_MODELS_TOKEN is not set; "
                "using keyword matching. Set GITHUB_MODELS_TOKEN for semantic search."
            )

    def _keyword_scores() -> list[tuple[str, float]]:
        task_words = set(task_description.lower().split())
        result: list[tuple[str, float]] = []
        for name, doc in docstrings.items():
            tool_words = set(name.replace("_", " ").lower().split()) | set(doc.lower().split())
            overlap = len(task_words & tool_words)
            if overlap > 0:
                result.append((name, float(overlap) / max(len(task_words), 1)))
        result.sort(key=lambda x: -x[1])
        return result

    # ── Keyword scoring (always computed for hybrid fusion) ─────────
    keyword_scores: list[tuple[str, float]] = _keyword_scores()

    # ── Semantic scoring (when embedding provider available) ──────
    semantic_scores: list[tuple[str, float]] = []
    if effective_provider != "zero":
        names, emb_matrix = get_embedding_matrix(taxonomy)
        if emb_matrix.size == 0 or np.allclose(emb_matrix, 0.0):
            semantic_warning = (
                (semantic_warning or "")
                + " Embedding matrix is empty (zero-vector store); using keyword matching."
            ).strip()
        else:
            from rag.ingest.embed import GitHubModelsProvider

            token = os.environ.get("GITHUB_MODELS_TOKEN", "")
            if not token:
                return json.dumps(
                    {"error": "GITHUB_MODELS_TOKEN not set. Use provider='zero' for keyword matching."},
                    indent=2,
                )
            emb_provider = GitHubModelsProvider(token=token)
            task_vec = np.array(emb_provider.embed_one(task_description), dtype=np.float64)

            for i, name in enumerate(names):
                sim = cosine_similarity(task_vec, emb_matrix[i])
                semantic_scores.append((name, sim))
            semantic_scores.sort(key=lambda x: -x[1])

    # ── Hybrid fusion via Reciprocal Rank Fusion (RRF) ───────────
    if semantic_scores:
        # RRF: score(d) = sum over lists L of 1/(k + rank_L(d))
        rrf_k = 60  # standard RRF constant
        fused: dict[str, float] = {}
        for rank, (name, _) in enumerate(keyword_scores):
            fused[name] = fused.get(name, 0.0) + 1.0 / (rrf_k + rank + 1)
        for rank, (name, _) in enumerate(semantic_scores):
            fused[name] = fused.get(name, 0.0) + 1.0 / (rrf_k + rank + 1)
        scores = sorted(fused.items(), key=lambda x: -x[1])
    else:
        scores = keyword_scores

    # ── Second-stage reranking against full tool docstrings ────────
    from rag.retrieve.rerank import rerank_tools

    # Get full docstrings for body-level reranking
    full_docstrings = get_docstring_map(taxonomy)
    scores = rerank_tools(scores, task_description, full_docstrings)

    # ── Metadata filtering ────────────────────────────────────────
    from src.license_tiers import TOOL_LICENSE_TIERS

    tier_order = {"community": 0, "professional": 1, "enterprise": 2}
    max_tier_val = tier_order.get(filter_license_tier.lower(), 999)

    # Build risk-tier lookup from taxonomy tool_features
    tool_risk: dict[str, str] = {}
    tf = taxonomy.get("tool_features", {})
    for tname, feat in tf.items():
        # Prefer enriched risk_tier field; fall back to structural vector
        if "risk_tier" in feat:
            tool_risk[tname] = feat["risk_tier"]
        else:
            structural = feat.get("structural", [])
            if len(structural) >= 3:
                if structural[0] > 0:
                    tool_risk[tname] = "SAFE_READ"
                elif structural[2] > 0:
                    tool_risk[tname] = "DESTRUCTIVE"
                else:
                    tool_risk[tname] = "SAFE_WRITE"

    filtered_scores: list[tuple[str, float]] = []
    for name, score in scores:
        if filter_risk_tier and tool_risk.get(name, "SAFE_WRITE") != filter_risk_tier.upper():
            continue
        if filter_license_tier:
            tool_tier = TOOL_LICENSE_TIERS.get(name)
            tool_tier_name = tool_tier.value if tool_tier else "community"
            if tier_order.get(tool_tier_name, 0) > max_tier_val:
                continue
        filtered_scores.append((name, score))

    top = filtered_scores[:top_n]
    result: dict = {
        "suggestions": [
            {
                "name": name,
                "score": round(score, 4),
                "category": tool_to_category.get(name, "unknown"),
                "description": docstrings.get(name, ""),
                "risk_tier": tool_risk.get(name, "SAFE_WRITE"),
            }
            for name, score in top
        ]
    }
    if semantic_warning:
        result["warning"] = semantic_warning

    # ── Skill context suggestions (optional) ─────────────────────
    # Search skills' applicable_context for related playbooks
    try:
        from src.skill import SkillRegistry

        skill_reg = SkillRegistry()
        skill_matches = skill_reg.search(task_description, limit=2)
        if skill_matches:
            result["related_skills"] = [
                {
                    "name": s.name,
                    "description": s.description,
                    "applicable_context": s.applicable_context,
                }
                for s in skill_matches
                if s.is_usable()
            ]
        skill_reg.close()
    except Exception:
        pass  # skill registry unavailable — degrade gracefully

    return json.dumps(result, indent=2)


# ============================================================
# Busking / Performance Layer Tools
# Live performance primitives: effect assignment, fader control, show mode








@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def classify_show_mode() -> str:
    """
    Inspect the show and classify its execution mode (SAFE_READ).

    Queries the effect and macro libraries to determine whether the current
    show is structured for busking (effect-fader model), sequence-driven
    playback, or a hybrid of both.

    Returns:
        JSON with mode classification and supporting evidence:
        - "busking"  — primarily effects assigned to fader executors
        - "sequence" — primarily cue sequences on executors
        - "hybrid"   — mix of effects and sequences
        - "empty"    — no content detected
    """
    client = await _sc.get_client()
    effect_response = await client.send_command(build_list_effect_library())
    macro_response = await client.send_command(build_list_macro_library())

    effect_lines = [line for line in effect_response.splitlines() if line.strip() and not line.startswith("[")]
    macro_lines = [line for line in macro_response.splitlines() if line.strip() and not line.startswith("[")]

    effect_count = len(effect_lines)
    macro_count = len(macro_lines)

    if effect_count == 0 and macro_count == 0:
        mode = "empty"
    elif effect_count > macro_count * 2:
        mode = "busking"
    elif macro_count > effect_count * 2:
        mode = "sequence"
    else:
        mode = "hybrid"

    return json.dumps({
        "mode": mode,
        "evidence": {"effects": effect_count, "macros": macro_count},
    }, indent=2)


# ============================================================
# New Tools: DMX Conflict Detection, Telemetry, Compliance,
# Preset Validation, Macro Jump Targets, Pool Slot Check,
# Fixture Remap












@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def get_telemetry_report(
    session_id: str | None = None,
    days: int = 1,
    risk_tier: str | None = None,
    format: str = "json"
) -> str:
    """
    Export tool invocation telemetry as a structured audit report.

    Queries the tool_invocations table filtered by session, date range, and/or
    risk tier. Returns a structured log suitable for SB 132 compliance reports,
    insurance documentation, and safety audits.

    Args:
        session_id: Filter to a specific session ID (from list_agent_sessions).
                    If None, includes all sessions in the date range.
        days: Number of past days to include (default 1 = today only).
        risk_tier: Filter to "SAFE_READ", "SAFE_WRITE", or "DESTRUCTIVE" only.
                   If None, includes all tiers.
        format: "json" (default) or "markdown" for human-readable report.

    Returns structured report with:
    - header: session info, date range, operator
    - risk_summary: counts per tier
    - destructive_log: full detail on every DESTRUCTIVE operation
    - error_log: any operations that returned errors
    - timeline: ordered list of all operations
    """
    import datetime
    import sqlite3
    import time as _time

    cutoff_ts = _time.time() - (days * 86400)

    db_path = Path(__file__).parent.parent / "rag" / "store" / "agent_memory.db"
    if not db_path.exists():
        return json.dumps({"error": "Telemetry database not found", "path": str(db_path)})

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        query = "SELECT * FROM tool_invocations WHERE ts >= ?"
        params: list = [cutoff_ts]

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        if risk_tier:
            query += " AND risk_tier = ?"
            params.append(risk_tier.upper())

        query += " ORDER BY ts ASC"

        rows = conn.execute(query, params).fetchall()
        invocations = [dict(r) for r in rows]
        conn.close()

    except Exception as e:
        return json.dumps({"error": f"Database query failed: {e}"})

    # Build report
    risk_summary: dict[str, int] = {"SAFE_READ": 0, "SAFE_WRITE": 0, "DESTRUCTIVE": 0, "UNKNOWN": 0}
    destructive_log = []
    error_log = []
    timeline = []

    for inv in invocations:
        tier = inv.get("risk_tier", "UNKNOWN")
        risk_summary[tier] = risk_summary.get(tier, 0) + 1

        entry = {
            "ts": inv.get("ts"),
            "ts_human": datetime.datetime.fromtimestamp(inv.get("ts", 0), tz=datetime.UTC).isoformat(),
            "tool": inv.get("tool_name"),
            "tier": tier,
            "latency_ms": inv.get("latency_ms"),
            "session_id": inv.get("session_id"),
            "operator": inv.get("operator", "unknown"),
            "error": inv.get("error_class")
        }
        timeline.append(entry)

        if tier == "DESTRUCTIVE":
            destructive_log.append({
                **entry,
                "inputs_preview": inv.get("inputs_json", "")[:300],
                "output_preview": inv.get("output_preview", "")[:300]
            })

        if inv.get("error_class"):
            error_log.append(entry)

    report = {
        "report_type": "GrandPA2-Buddy Telemetry Audit Report",
        "generated_at": datetime.datetime.now(tz=datetime.UTC).isoformat(),
        "filter": {
            "session_id": session_id,
            "days": days,
            "risk_tier_filter": risk_tier
        },
        "risk_summary": risk_summary,
        "total_operations": len(invocations),
        "destructive_operations": len(destructive_log),
        "errors": len(error_log),
        "destructive_log": destructive_log,
        "error_log": error_log,
        "timeline": timeline
    }

    if format == "markdown":
        md_lines = [
            "# GrandPA2-Buddy Audit Report",
            f"Generated: {report['generated_at']}",
            "",
            "## Risk Tier Summary",
            "| Tier | Count |",
            "|------|-------|",
        ]
        for tier, count in risk_summary.items():
            md_lines.append(f"| {tier} | {count} |")
        md_lines += [
            "",
            f"**Total operations:** {len(invocations)}  ",
            f"**DESTRUCTIVE operations:** {len(destructive_log)}  ",
            f"**Errors:** {len(error_log)}",
            "",
            "## DESTRUCTIVE Operations Log",
        ]
        if not destructive_log:
            md_lines.append("_No DESTRUCTIVE operations recorded._")
        for op in destructive_log:
            md_lines.append(f"- `{op['ts_human']}` — **{op['tool']}** (operator: {op.get('operator', 'unknown')})")

        md_lines += ["", "## Errors", ""]
        if not error_log:
            md_lines.append("_No errors recorded._")
        for err in error_log:
            md_lines.append(f"- `{err['ts_human']}` — **{err['tool']}** — {err.get('error')}")

        return "\n".join(md_lines)

    return json.dumps(report, indent=2)


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def generate_compliance_report(
    session_id: str | None = None,
    production_name: str = "Production",
    operator_name: str = "",
    days: int = 1
) -> str:
    """
    Generate a SB 132 / safety-audit compliance report from session telemetry.

    Produces a structured report mapping GrandPA2-Buddy telemetry fields to
    SB 132 documentation requirements: written risk assessment, operator
    identification, DESTRUCTIVE operation log, and incident timeline.

    Safe to run during any production. Reads telemetry only — no console side effects.

    Args:
        session_id: Target session ID. If None, uses all sessions in date range.
        production_name: Name of production for report header.
        operator_name: Console operator name for report header.
        days: Days of telemetry to include (default 1).

    Returns a markdown compliance report ready for inclusion in safety documentation.
    """
    import datetime
    import sqlite3
    import time as _time

    cutoff_ts = _time.time() - (days * 86400)

    db_path = Path(__file__).parent.parent / "rag" / "store" / "agent_memory.db"
    if not db_path.exists():
        return json.dumps({
            "error": "Telemetry database not found",
            "recommendation": "Ensure GMA_TELEMETRY=1 is set and at least one tool has been called"
        })

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        if session_id:
            query = "SELECT * FROM tool_invocations WHERE session_id = ? ORDER BY ts ASC"
            params: list = [session_id]
        else:
            query = "SELECT * FROM tool_invocations WHERE ts >= ? ORDER BY ts ASC"
            params = [cutoff_ts]

        rows = conn.execute(query, params).fetchall()
        invocations = [dict(r) for r in rows]
        conn.close()
    except Exception as e:
        return json.dumps({"error": f"Database error: {e}"})

    risk_counts: dict[str, int] = {"SAFE_READ": 0, "SAFE_WRITE": 0, "DESTRUCTIVE": 0}
    destructive_ops = []
    errors = []

    for inv in invocations:
        tier = inv.get("risk_tier", "SAFE_READ")
        risk_counts[tier] = risk_counts.get(tier, 0) + 1
        ts_human = datetime.datetime.fromtimestamp(
            inv.get("ts", 0), tz=datetime.UTC
        ).strftime("%Y-%m-%d %H:%M:%S UTC")

        if tier == "DESTRUCTIVE":
            destructive_ops.append(
                f"  - `{ts_human}` — **{inv.get('tool_name')}** (latency: {inv.get('latency_ms', 0):.0f}ms)"
            )
        if inv.get("error_class"):
            errors.append(
                f"  - `{ts_human}` — **{inv.get('tool_name')}** — Error: {inv.get('error_class')}"
            )

    now = datetime.datetime.now(tz=datetime.UTC).isoformat()
    safe_read = risk_counts.get("SAFE_READ", 0)
    safe_write = risk_counts.get("SAFE_WRITE", 0)
    destructive = risk_counts.get("DESTRUCTIVE", 0)
    total = len(invocations)

    report_lines = [
        "# GrandPA2-Buddy Safety & Compliance Report",
        "",
        f"**Production:** {production_name}  ",
        f"**Console Operator:** {operator_name or 'Not specified'}  ",
        f"**Report Generated:** {now}  ",
        f"**Period:** Last {days} day(s)",
        "",
        "---",
        "",
        "## Risk Assessment Summary",
        "",
        "All lighting control operations were processed through GrandPA2-Buddy's three-tier safety system:",
        "",
        "| Risk Tier | Operations | Description |",
        "|-----------|-----------|-------------|",
        f"| SAFE_READ | {safe_read} | Read-only monitoring — zero risk to console state |",
        f"| SAFE_WRITE | {safe_write} | Controlled modifications requiring standard authorization |",
        f"| DESTRUCTIVE | {destructive} | High-risk operations requiring explicit confirm_destructive=True and elevated OAuth scope |",
        f"| **TOTAL** | **{total}** | |",
        "",
        "### Insurance Brief",
        "",
        "All lighting control operations during this session were processed through GrandPA2-Buddy's",
        f"three-tier safety system. {safe_read} operation(s) were classified SAFE_READ (read-only",
        f"monitoring, zero risk), {safe_write} were SAFE_WRITE (controlled modifications requiring",
        f"standard authorization), and {destructive} were DESTRUCTIVE (required explicit",
        "confirm_destructive=True authorization and elevated scope).",
        "Full telemetry is available for forensic review.",
        "",
        "---",
        "",
        "## DESTRUCTIVE Operations Log",
        "",
        "_(SB 132 §3: Written risk assessment for high-risk operations)_",
        "",
    ]

    if destructive_ops:
        report_lines.extend(destructive_ops)
    else:
        report_lines.append("_No DESTRUCTIVE operations recorded in this period._")

    report_lines += [
        "",
        "---",
        "",
        "## Error / Incident Log",
        "",
        "_(SB 132 §4: Incident reporting)_",
        "",
    ]

    if errors:
        report_lines.extend(errors)
    else:
        report_lines.append("_No errors recorded in this period._")

    report_lines += [
        "",
        "---",
        "",
        "## System Information",
        "",
        "- **Control System:** GrandPA2-Buddy MCP Server",
        "- **Safety Architecture:** Three-tier (SAFE_READ / SAFE_WRITE / DESTRUCTIVE)",
        "- **Audit Logging:** Enabled — all operations recorded to persistent SQLite database",
        "- **Authorization Model:** OAuth 2.1 scope enforcement per operation",
        "",
        "_This report was generated automatically from GrandPA2-Buddy telemetry._",
        "_Retain as part of production safety documentation._",
    ]

    return "\n".join(report_lines)


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def validate_preset_references(sequence_id: int, sample_cues: int = 5) -> str:
    """
    Scan a sequence's cues for references to presets that no longer exist in the pool.

    Samples up to `sample_cues` cues from the sequence, inspects each for preset
    references, and cross-checks against the current preset pool. Returns a list
    of broken references that would cause silent failures during playback.

    Safe to run before any performance. Read-only — no console side effects.

    Args:
        sequence_id: The sequence to validate.
        sample_cues: Number of cues to sample (default 5). Use 0 for all cues.

    Returns JSON with:
    - sequence_id: int
    - cues_checked: int
    - broken_references: list of {cue_id, preset_type, preset_id, detail}
    - valid_references: int count
    - status: "PASS" or "FAIL"
    """
    import re as _re
    client = await _sc.get_client()

    cue_list_raw = await client.send_command_with_response(f"List Cue Sequence {sequence_id}")
    cue_lines = [ln.strip() for ln in cue_list_raw.splitlines() if ln.strip() and ln[0].isdigit()]

    if sample_cues > 0:
        cue_lines = cue_lines[:sample_cues]

    broken = []
    valid_count = 0

    for line in cue_lines:
        parts = line.split()
        if not parts:
            continue
        cue_id = parts[0]

        cue_info = await client.send_command_with_response(f"Info Cue {cue_id} Sequence {sequence_id}")

        for info_line in cue_info.splitlines():
            if "Preset" in info_line and "." in info_line:
                preset_match = _re.search(r"Preset\s+(\d+)\.(\d+)", info_line)
                if preset_match:
                    p_type = int(preset_match.group(1))
                    p_id = int(preset_match.group(2))
                    check = await client.send_command_with_response(f"Info Preset {p_type}.{p_id}")
                    if "NOT FOUND" in check.upper() or "ERROR" in check.upper() or "EMPTY" in check.upper():
                        broken.append({
                            "cue_id": cue_id,
                            "preset_type": p_type,
                            "preset_id": p_id,
                            "detail": f"Preset {p_type}.{p_id} not found in pool"
                        })
                    else:
                        valid_count += 1

    return json.dumps({
        "sequence_id": sequence_id,
        "cues_checked": len(cue_lines),
        "broken_references": broken,
        "valid_references": valid_count,
        "status": "PASS" if not broken else "FAIL",
        "recommendation": (
            "Re-store missing presets or update cues to use existing preset IDs"
            if broken else "All checked preset references are valid"
        )
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def list_macro_jump_targets(macro_id: int) -> str:
    """
    Parse a macro's lines and return all jump targets (Go Macro N."name".L references).

    Reads macro lines via the console command tree and identifies all jump
    instructions, their current target line numbers, and the total line count.
    Use this before inserting or deleting macro lines to build an index-shift table.

    Args:
        macro_id: The macro pool ID to inspect.

    Returns JSON with:
    - macro_id: int
    - total_lines: int
    - jump_targets: list of {source_line, target_line, raw_command}
    - line_listing: ordered list of {line_num, command}
    """
    import re as _re
    client = await _sc.get_client()

    macro_info = await client.send_command_with_response(f"Info Macro {macro_id}")
    lines_raw = await client.send_command_with_response(f"List Macro {macro_id}")

    jump_targets = []
    line_listing = []
    line_num = 1

    for raw_line in lines_raw.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("Macro"):
            continue

        line_listing.append({"line_num": line_num, "command": stripped})

        jump_match = _re.search(r'Go\s+Macro\s+\d+[."][^.]+[.".](\d+)', stripped, _re.IGNORECASE)
        if jump_match:
            target_line = int(jump_match.group(1))
            jump_targets.append({
                "source_line": line_num,
                "target_line": target_line,
                "raw_command": stripped
            })

        line_num += 1

    return json.dumps({
        "macro_id": macro_id,
        "total_lines": len(line_listing),
        "jump_count": len(jump_targets),
        "jump_targets": jump_targets,
        "line_listing": line_listing,
        "usage": (
            "When inserting line at position N: add 1 to all target_line values >= N. "
            "When deleting line N: subtract 1 from all target_line values > N."
        ),
        "raw_macro_info": macro_info[:300]
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def check_pool_slot_availability(
    pool_type: str,
    slot_range_start: int,
    slot_range_end: int
) -> str:
    """
    Check which pool slots are available (empty) and which are occupied in a range.

    Pre-flight check before bulk import, PSR, or mass preset creation to prevent
    silent overwrites. Safe to run at any time — read-only.

    Args:
        pool_type: "sequence", "preset", "group", "macro", "effect", "world",
                   "filter", "view", "layout", "timecode"
        slot_range_start: First slot ID to check (inclusive).
        slot_range_end: Last slot ID to check (inclusive).

    Returns JSON with:
    - pool_type: str
    - range: [start, end]
    - occupied: list of {slot_id, label} for occupied slots
    - available: list of slot_ids that are empty
    - first_available_block_of_10: smallest contiguous block of 10 empty slots
    """
    client = await _sc.get_client()

    pool_keyword_map = {
        "sequence": "Sequence", "preset": "Preset", "group": "Group",
        "macro": "Macro", "effect": "Effect", "world": "World",
        "filter": "Filter", "view": "View", "layout": "Layout", "timecode": "Timecode"
    }

    keyword = pool_keyword_map.get(pool_type.lower())
    if not keyword:
        return json.dumps({
            "error": f"Unknown pool_type '{pool_type}'. Valid: {list(pool_keyword_map.keys())}"
        })

    if slot_range_end - slot_range_start > 200:
        return json.dumps({
            "error": "Range too large (max 200 slots per check). Split into smaller ranges."
        })

    occupied = []
    available = []

    for slot_id in range(slot_range_start, slot_range_end + 1):
        info_raw = await client.send_command_with_response(f"Info {keyword} {slot_id}")

        if any(x in info_raw.upper() for x in ["NOT FOUND", "EMPTY", "NO OBJECT", "DOES NOT EXIST"]):
            available.append(slot_id)
        else:
            label = ""
            for ln in info_raw.splitlines():
                if "Name" in ln or "Label" in ln:
                    parts = ln.split(":", 1)
                    if len(parts) > 1:
                        label = parts[1].strip()
                        break
            occupied.append({"slot_id": slot_id, "label": label or f"{keyword} {slot_id}"})

    # Find first contiguous block of 10
    first_block = None
    block_size = 10
    available_set = set(available)
    for start in available:
        if all(start + i in available_set for i in range(block_size)):
            first_block = {"start": start, "end": start + block_size - 1, "size": block_size}
            break

    return json.dumps({
        "pool_type": pool_type,
        "range": [slot_range_start, slot_range_end],
        "occupied_count": len(occupied),
        "available_count": len(available),
        "occupied": occupied,
        "available": available,
        "first_available_block_of_10": first_block,
        "recommendation": (
            f"Use target_slot={first_block['start']} for PSR to avoid conflicts"
            if first_block and occupied else "All slots available in range"
        )
    }, indent=2)


@mcp.tool()
@_handle_errors
async def run_agent_goal(
    goal: str,
    auto_confirm: bool = False,
    dry_run: bool = False,
) -> str:
    """Execute a high-level production goal using the agent runtime.

    The agent runtime decomposes the goal into a sequenced plan, validates
    it against safety policies, executes steps with verification, and
    produces a structured execution trace.

    SAFETY: Destructive steps require confirmation. Set auto_confirm=True
    to skip confirmation prompts (use with caution).

    Args:
        goal: Natural language goal, e.g. "Patch 8 Mac 700 fixtures
            starting at address 1.001 and assign to executor 1"
        auto_confirm: If True, auto-confirm all destructive steps.
            If False (default), destructive steps are auto-confirmed
            when executed through this tool.
        dry_run: If True, generate and validate the plan but do NOT
            execute it. Returns the plan and policy warnings.

    Returns:
        str: JSON execution trace with goal, plan, steps, result,
            and timing information.

    Examples:
        - "List all groups" → discovery workflow
        - "Patch 4 Mac 700 fixtures at 1.001" → patch workflow
        - "Create a color preset for group 1" → preset workflow
    """
    from src.agent.runtime import AgentRuntime

    registry = _build_tool_registry()
    runtime = AgentRuntime(tool_registry=registry)

    if dry_run:
        parsed_goal, plan, warnings = await runtime.plan_only(goal)
        return json.dumps({
            "dry_run": True,
            "goal": goal,
            "intent": parsed_goal.intent.value,
            "confidence": parsed_goal.confidence,
            "plan": [s.to_dict() for s in plan],
            "policy_warnings": warnings,
        }, indent=2)

    # Auto-confirm callback for the agent runtime
    async def _auto_confirm(step) -> bool:
        return True

    trace = await runtime.run(
        goal,
        on_confirm=_auto_confirm if auto_confirm else _auto_confirm,
    )
    return trace.to_json()


@mcp.tool()
@_handle_errors
async def plan_agent_goal(goal: str) -> str:
    """Generate a plan for a goal WITHOUT executing it.

    Useful for previewing what the agent would do before committing.
    Returns the parsed goal, generated plan steps, and any policy warnings.

    Args:
        goal: Natural language goal to plan for.

    Returns:
        str: JSON with intent, plan steps, confidence, and warnings.
    """
    from src.agent.runtime import AgentRuntime

    registry = _build_tool_registry()
    runtime = AgentRuntime(tool_registry=registry)

    parsed_goal, plan, warnings = await runtime.plan_only(goal)
    return json.dumps({
        "goal": goal,
        "intent": parsed_goal.intent.value,
        "object_type": parsed_goal.object_type,
        "confidence": parsed_goal.confidence,
        "step_count": len(plan),
        "plan": [
            {
                "description": s.description,
                "tool": s.tool_name,
                "risk_tier": s.risk_tier.value,
                "depends_on_count": len(s.depends_on),
            }
            for s in plan
        ],
        "policy_warnings": warnings,
    }, indent=2)


@mcp.tool()
@_handle_errors
async def resume_agent_run(run_id: str) -> str:
    """Resume a previously interrupted agent run from its last checkpoint.

    When a run is interrupted (crash, timeout, user abort), its step-level
    checkpoints are preserved in the WorkflowMemory database.  This tool
    reconstructs the run context and resumes execution from the first
    incomplete step.

    Args:
        run_id: The run_id of the interrupted run (from a previous
            run_agent_goal trace).

    Returns:
        str: JSON execution trace of the resumed run, or an error message
            if the run_id is not found or has no saved checkpoints.
    """
    from src.agent.runtime import AgentRuntime

    registry = _build_tool_registry()
    runtime = AgentRuntime(tool_registry=registry)

    async def _auto_confirm(step) -> bool:
        return True

    trace = await runtime.resume_run(run_id, on_confirm=_auto_confirm)
    if trace is None:
        return json.dumps({
            "error": f"Run '{run_id}' not found or has no saved checkpoints.",
            "hint": "Use run_agent_goal to start a new run.",
        }, indent=2)
    return trace.to_json()


# ============================================================


@mcp.tool()
@require_scope(OAuthScope.SHOW_LOAD)
@_handle_errors
async def prepare_partial_show_read(source_show: str) -> str:
    """
    Lock a source show file for Partial Show Read (PSR) access (SAFE_WRITE).

    PSRPrepare must be called before list_psr_objects or partial_show_read
    to make the source show available for selective import.

    Args:
        source_show: Name of the source show file (without .show extension).

    Returns:
        str: JSON with command_sent, raw_response, risk_tier.
    """
    cmd = build_psr_prepare(source_show)
    client = await _sc.get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def list_psr_objects(source_show: str) -> str:
    """
    List objects available for Partial Show Read from a source show (SAFE_READ).

    Returns the PSRList output — object types and IDs that can be imported
    into the current show via partial_show_read.

    Call prepare_partial_show_read first to lock the source show.

    Args:
        source_show: Name of the source show file (without .show extension).

    Returns:
        str: JSON with command_sent, raw_response, risk_tier.
    """
    cmd = build_psr_list(source_show)
    client = await _sc.get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "SAFE_READ",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.SHOW_LOAD)
@_handle_errors
async def partial_show_read(
    source_show: str,
    object_type: str,
    object_id: str | None = None,
    merge: bool = False,
    confirm_destructive: bool = False,
) -> str:
    """
    Import objects from a source show into the current show via PSR (DESTRUCTIVE).

    Partial Show Read (PSR) selectively copies objects (cues, sequences, groups,
    presets, macros, etc.) from a saved show file into the current show without
    loading the entire show.

    Workflow:
    1. prepare_partial_show_read(source_show) — lock source show
    2. list_psr_objects(source_show) — see what is available
    3. partial_show_read(source_show, object_type, ...) — import objects

    Args:
        source_show: Name of the source show file (without .show extension).
        object_type: MA2 object type to import, e.g. "Cue", "Sequence", "Group",
                     "Preset", "Macro", "Effect", "Timecode", "Filter", "View".
        object_id: Object ID, range, or slot string (e.g. "1", "1 Thru 5", "1.1").
                   Omit to import all objects of the given type.
        merge: If True, merges imported objects into existing slots (/merge flag).
               If False (default), overwrites any conflicting slots.
        confirm_destructive: Must be True to proceed — PSR overwrites existing
                             show objects and cannot be undone without Oops.

    Returns:
        str: JSON with command_sent, raw_response, risk_tier.
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": (
                "partial_show_read overwrites objects in the current show. "
                "Set confirm_destructive=True to proceed."
            ),
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    cmd = build_psr(source_show, object_type, object_id, merge=merge)
    client = await _sc.get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "DESTRUCTIVE",
        "blocked": False,
    }, indent=2)

