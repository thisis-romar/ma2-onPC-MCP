# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
MCP Server Module

This module is responsible for creating and running the MCP server,
integrating all tools together. It uses FastMCP to simplify the MCP server setup.

Usage:
    uv run python -m src.server
"""

import asyncio
import functools
import json
import logging
import os
import re
import sys
import time
from datetime import UTC
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from src.agent_memory import LongTermMemory
from src.auth import OAuthScope, has_scope, require_scope
from src.commands import (
    SPECIAL_MASTER_NAMES,
    attribute_at,
    build_assign_world_to_user_profile,
    build_delete_user,
    build_list_users,
    build_store_user,
    call,
    channel_at,
    fixture_at,
    go_macro,
    go_sequence,
    goto_cue,
    group_at,
    label_group,
    pause_sequence,
    select_fixture,
    store_group,
)
from src.commands import (
    add_to_selection as build_add_to_selection,
)
from src.commands import (
    add_user_var as build_add_user_var,
)
from src.commands import (
    add_var as build_add_var,
)
from src.commands import (
    align as build_align,
)
from src.commands import (
    appearance as build_appearance,
)
from src.commands import (
    # assign_object
    assign as build_assign,
)
from src.commands import (
    assign_delay as build_assign_delay,
)
from src.commands import (
    assign_effect_to_executor as build_assign_effect_to_executor,
)
from src.commands import (
    assign_fade as build_assign_fade,
)
from src.commands import (
    assign_function as build_assign_function,
)
from src.commands import (
    assign_to_layout as build_assign_to_layout,
)
from src.commands import (
    at_relative as build_at_relative,
)
from src.commands import (
    blackout as build_blackout,
)
from src.commands import (
    blind_edit as build_blind_edit,
)
from src.commands import (
    block as build_block,
)
from src.commands import (
    build_login as build_console_login,
)
from src.commands import (
    build_logout as build_console_logout,
)
from src.commands import (
    call_plugin as build_call_plugin,
)
from src.commands import (
    chaser_rate as build_chaser_rate,
)
from src.commands import (
    chaser_skip as build_chaser_skip,
)
from src.commands import (
    chaser_speed as build_chaser_speed,
)
from src.commands import (
    chaser_xfade as build_chaser_xfade,
)
from src.commands import (
    clear as build_clear,
)
from src.commands import (
    clear_active as build_clear_active,
)
from src.commands import (
    clear_all as build_clear_all,
)
from src.commands import (
    clear_selection as build_clear_selection,
)
from src.commands import (
    clone as build_clone,
)
from src.commands import (
    copy as build_copy,
)
from src.commands import (
    cut as build_cut,
)
from src.commands import (
    def_go_back as build_def_go_back,
)
from src.commands import (
    def_go_forward as build_def_go_forward,
)
from src.commands import (
    def_go_pause as build_def_go_pause,
)
from src.commands import (
    delete as build_delete,
)
from src.commands import (
    delete_cue as build_delete_cue,
)
from src.commands import (
    delete_fixture as build_delete_fixture,
)
from src.commands import (
    delete_show as build_delete_show,
)
from src.commands import (
    # edit_object
    edit as build_edit,
)
from src.commands import (
    executor_at as build_executor_at,
)
from src.commands import (
    export_object as build_export_object,
)
from src.commands import (
    fade_path as build_fade_path,
)
from src.commands import (
    fix_fixture as build_fix_fixture,
)
from src.commands import (
    flash_executor as build_flash_executor,
)
from src.commands import (
    flash_go as build_flash_go,
)
from src.commands import (
    flash_on as build_flash_on,
)
from src.commands import (
    full_highlight as build_full_highlight,
)
from src.commands import (
    get_user_var as build_get_user_var,
)
from src.commands import (
    # playback_action
    go as build_go,
)
from src.commands import (
    go_back as build_go_back,
)
from src.commands import (
    go_fast_back as build_go_fast_back,
)
from src.commands import (
    go_fast_forward as build_go_fast_forward,
)
from src.commands import (
    goto as build_goto,
)
from src.commands import (
    goto_timecode as build_goto_timecode,
)
from src.commands import (
    highlight as build_highlight,
)
from src.commands import (
    if_active as build_if_active,
)
from src.commands import (
    if_output as build_if_output,
)
from src.commands import (
    if_prog as build_if_prog,
)
from src.commands import (
    import_fixture_type_cmd as build_import_fixture_type_cmd,
)
from src.commands import (
    import_layer_cmd as build_import_layer_cmd,
)
from src.commands import (
    import_object as build_import_object,
)
from src.commands import (
    info as build_info,
)
from src.commands import (
    invert as build_invert,
)
from src.commands import (
    label as build_label,
)
from src.commands import (
    # label_or_appearance
    label_preset as build_label_preset,
)
from src.commands import (
    list_attribute as build_list_attribute,
)
from src.commands import (
    list_cue as build_list_cue,
)
from src.commands import (
    list_effect_library as build_list_effect_library,
)
from src.commands import (
    list_fader_modules as build_list_fader_modules,
)
from src.commands import (
    list_group as build_list_group,
)
from src.commands import (
    list_library as build_list_library,
)
from src.commands import (
    list_macro_library as build_list_macro_library,
)
from src.commands import (
    list_messages as build_list_messages,
)
from src.commands import (
    # query_object_list
    list_objects as build_list_objects,
)
from src.commands import (
    list_oops as build_list_oops,
)
from src.commands import (
    list_plugin_library as build_list_plugin_library,
)
from src.commands import (
    list_preset as build_list_preset,
)
from src.commands import (
    list_shows as build_list_shows,
)
from src.commands import (
    list_update as build_list_update,
)
from src.commands import (
    list_user_var as build_list_user_var,
)
from src.commands import (
    list_var as build_list_var,
)
from src.commands import (
    load_next as build_load_next,
)
from src.commands import (
    load_prev as build_load_prev,
)
from src.commands import (
    load_show as build_load_show,
)
from src.commands import (
    locate as build_locate,
)
from src.commands import (
    lock_console as build_lock_console,
)
from src.commands import (
    manual_xfade as build_manual_xfade,
)
from src.commands import (
    move as build_move,
)
from src.commands import (
    new_show as build_new_show,
)
from src.commands import (
    off_executor as build_off_executor,
)
from src.commands import (
    on_executor as build_on_executor,
)
from src.commands import (
    out_delay as build_out_delay,
)
from src.commands import (
    out_fade as build_out_fade,
)
from src.commands import (
    page_next as build_page_next,
)
from src.commands import (
    page_previous as build_page_previous,
)
from src.commands import (
    park as build_park,
)
from src.commands import (
    paste as build_paste,
)
from src.commands import (
    preview as build_preview,
)
from src.commands import (
    preview_edit as build_preview_edit,
)
from src.commands import (
    preview_executor as build_preview_executor,
)
from src.commands import (
    psr as build_psr,
)
from src.commands import (
    psr_list as build_psr_list,
)
from src.commands import (
    psr_prepare as build_psr_prepare,
)
from src.commands import (
    rdm_automatch as build_rdm_automatch,
)
from src.commands import (
    rdm_autopatch as build_rdm_autopatch,
)
from src.commands import (
    rdm_info as build_rdm_info,
)
from src.commands import (
    rdm_list as build_rdm_list,
)
from src.commands import (
    rdm_setpatch as build_rdm_setpatch,
)
from src.commands import (
    rdm_unmatch as build_rdm_unmatch,
)
from src.commands import (
    release_effects_on_page as build_release_effects_on_page,
)
from src.commands import (
    release_executor as build_release_executor,
)
from src.commands import (
    reload_plugins as build_reload_plugins,
)
from src.commands import (
    # remove_content
    remove as build_remove,
)
from src.commands import (
    remove_effect as build_remove_effect,
)
from src.commands import (
    remove_fixture as build_remove_fixture,
)
from src.commands import (
    remove_from_selection as build_remove_from_selection,
)
from src.commands import (
    remove_preset_type as build_remove_preset_type,
)
from src.commands import (
    remove_selection as build_remove_selection,
)
from src.commands import (
    run_lua as build_run_lua,
)
from src.commands import (
    set_effect_parameter as build_set_effect_parameter,
)
from src.commands import (
    set_effect_rate as build_set_effect_rate,
)
from src.commands import (
    set_effect_speed as build_set_effect_speed,
)
from src.commands import (
    set_special_master as build_set_special_master,
)
from src.commands import (
    set_user_var as build_set_user_var,
)
from src.commands import (
    # manage_variable
    set_var as build_set_var,
)
from src.commands import (
    shuffle_selection as build_shuffle_selection,
)
from src.commands import (
    shuffle_values as build_shuffle_values,
)
from src.commands import (
    snap_percent as build_snap_percent,
)
from src.commands import (
    solo_executor as build_solo_executor,
)
from src.commands import (
    step_fade as build_step_fade,
)
from src.commands import (
    step_in_fade as build_step_in_fade,
)
from src.commands import (
    step_out_fade as build_step_out_fade,
)
from src.commands import (
    stomp_executor as build_stomp_executor,
)
from src.commands import (
    # store_object
    store as build_store_generic,
)
from src.commands import (
    store_cue as build_store_cue,
)
from src.commands import (
    store_cue_timed as build_store_cue_timed,
)
from src.commands import (
    store_preset as build_store_preset,
)
from src.commands import (
    swop_executor as build_swop_executor,
)
from src.commands import (
    swop_go as build_swop_go,
)
from src.commands import (
    swop_on as build_swop_on,
)
from src.commands import (
    temp_fader as build_temp_fader,
)
from src.commands import (
    top_executor as build_top_executor,
)
from src.commands import (
    unblock as build_unblock,
)
from src.commands import (
    unlock_console as build_unlock_console,
)
from src.commands import (
    unpark as build_unpark,
)
from src.commands import (
    update_cue as build_update_cue,
)
from src.commands import (
    zero_page_faders as build_zero_page_faders,
)
from src.context import _current_session_id
from src.credentials import get_operator_identity, resolve_console_credentials
from src.license import get_license_tier, has_tier
from src.license_tiers import TOOL_LICENSE_TIERS
from src.navigation import get_current_location, list_destination, navigate, scan_indexes, set_property
from src.orchestrator import Orchestrator
from src.rights import get_session_ma2_right, is_permitted, min_right_for_tool
from src.server_core import (
    _check_pool_slots,
    _get_sequence_for_executor,
    _get_telemetry,
    _GMA_SAFETY_LEVEL,
    _handle_errors,
    _OBJECT_POOL_DESTINATIONS,
    _parse_listvar,
    _parse_preset_tree_list,
    _read_selected_exec,
    _SEQ_FOR_EXECUTOR_RE,
    _validate_object_exists,
    _vocab_spec,
    get_client,
    mcp,
)
from src.server_orchestration_tools import register_orchestration_tools
from src.session_manager import SessionManager
from src.telemetry import ToolTelemetry, infer_risk_tier
from src.telnet_client import GMA2TelnetClient
from src.tools import set_gma2_client
from src.vocab import RiskTier, build_v39_spec, classify_token

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

import src.tools_community  # noqa: F401 — registers 20 COMMUNITY tools on mcp
import src.tools_professional  # noqa: F401 — registers 124 PROFESSIONAL tools on mcp
import src.tools_enterprise  # noqa: F401 — registers 20 ENTERPRISE tools on mcp

# Re-export COMMUNITY tools so existing `from src.server import X` keeps working
from src.tools_community import (  # noqa: F401
    clear_programmer,
    discover_fixture_type_attributes,
    discover_object_names,
    execute_sequence,
    get_console_location,
    get_executor_state,
    get_executor_status,
    get_object_info,
    get_variable,
    if_filter,
    list_console_destination,
    list_system_variables,
    navigate_console,
    playback_action,
    query_object_list,
    release_executor,
    scan_page_executor_layout,
    send_raw_command,
    set_attribute,
    set_intensity,
)

# Re-export PROFESSIONAL tools so existing `from src.server import X` keeps working
from src.tools_professional import (  # noqa: F401
    adjust_value_relative,
    apply_preset,
    assign_cue_trigger,
    assign_effect_to_executor,
    assign_executor_property,
    assign_object,
    assign_temp_fader,
    assign_world_to_user_profile,
    blackout_toggle,
    block_unblock_cue,
    browse_effect_library,
    browse_macro_library,
    browse_patch_schedule,
    browse_plugin_library,
    browse_preset_type,
    call_plugin_tool,
    check_pool_availability,
    clear_effects_on_page,
    clone_object,
    console_login,
    console_logout,
    control_chaser,
    control_executor,
    control_special_master,
    control_timecode,
    control_timer,
    copy_or_move_object,
    create_console_user,
    create_fixture_group,
    cut_paste_object,
    delete_object,
    delete_show,
    delete_user,
    detect_dmx_address_conflicts,
    discover_filter_attributes,
    edit_object,
    export_objects,
    filter_fixture_selection,
    fix_locate_fixture,
    generate_fixture_layer_xml,
    highlight_fixtures,
    import_fixture_layer,
    import_fixture_type,
    import_objects,
    inspect_sessions,
    label_or_appearance,
    label_world,
    list_agenda_events,
    list_console_users,
    list_effects_pool,
    list_fader_modules,
    list_filters,
    list_fixture_types,
    list_fixtures,
    list_forms,
    list_images,
    list_layers,
    list_layouts,
    list_library,
    list_preset_pool,
    list_sequence_cues,
    list_shows,
    list_timecode_events,
    list_timers,
    list_undo_history,
    list_universes,
    list_update_history,
    list_worlds,
    load_cue,
    load_show,
    lock_console_ui,
    manage_matricks,
    manage_variable,
    manipulate_selection,
    master_control,
    modify_selection,
    modulate_effect,
    navigate_page,
    new_show,
    normalize_page_faders,
    park_fixture,
    patch_fixture,
    plugin_management,
    preview_executor_content,
    programming_action,
    rdm_discover,
    rdm_get_info,
    rdm_patch,
    reload_all_plugins,
    remap_fixture_ids,
    remove_content,
    remove_from_programmer,
    run_lua_script,
    run_macro,
    save_recall_view,
    save_show,
    select_executor,
    select_feature,
    select_fixtures_by_group,
    select_preset_type,
    set_advanced_timing,
    set_cue_timing,
    set_effect_param,
    set_executor_level,
    set_executor_priority,
    set_fixture_type_property,
    set_node_property,
    set_sequence_property,
    store_agenda,
    store_cue_with_timing,
    store_current_cue,
    store_matricks_preset,
    store_new_preset,
    store_object,
    store_timecode_event,
    store_world,
    system_admin,
    toggle_console_mode,
    undo_last_action,
    unlock_console_ui,
    unpark_fixture,
    unpatch_fixture,
    update_cue_data,
    update_object,
)

# Re-export ENTERPRISE tools so existing `from src.server import X` keeps working
from src.tools_enterprise import (  # noqa: F401
    check_pool_slot_availability,
    classify_show_mode,
    create_filter_library,
    create_matricks_library,
    generate_compliance_report,
    get_similar_tools,
    get_telemetry_report,
    list_macro_jump_targets,
    list_psr_objects,
    list_tool_categories,
    partial_show_read,
    plan_agent_goal,
    prepare_partial_show_read,
    recluster_tools,
    resume_agent_run,
    run_agent_goal,
    scan_console_indexes,
    search_codebase,
    suggest_tool_for_task,
    validate_preset_references,
)
# Also re-export helpers used by tests
from src.tools_enterprise import (  # noqa: F401
    _build_tool_registry,
    _discover_filter_attributes,
    _invalidate_taxonomy_cache,
    _load_taxonomy_cached,
    _telnet_send_fn,
    _tool_caller,
)

logger = logging.getLogger(__name__)

# Get configuration from environment variables
_GMA_HOST = os.getenv("GMA_HOST", "127.0.0.1")
_GMA_PORT = int(os.getenv("GMA_PORT", "30000"))
_GMA_USER = os.getenv("GMA_USER", "administrator")
_GMA_PASSWORD = os.getenv("GMA_PASSWORD", "admin")
# _GMA_SAFETY_LEVEL, _vocab_spec, mcp imported from server_core

# Create MCP server
# mcp, session pool, telemetry, get_client(), _handle_errors, and shared
# helpers are now in src/server_core.py — imported above.


# Private helpers (_validate_object_exists, _get_sequence_for_executor,
# _SEQ_FOR_EXECUTOR_RE) are now in src/server_core.py — imported above.










































# ============================================================
# Codebase Search (RAG)


# ============================================================
# New Tools (Tools 30–44)
















































# ============================================================
# New Tools (Tools 45–52) — Quick Start Guide Gap-Fill
























# ============================================================
# Tools 53–54 — Import / Export
# ============================================================

# Valid export types (live-validated on MA2 3.9.60.65)
_EXPORT_TYPES = {
    "group", "preset", "macro", "effect", "sequence", "view", "page",
    "camera", "layout", "form", "plugin", "matricks", "mask", "image",
    "executor", "timecode", "userprofile", "channel", "screen", "filter",
}

# Valid import types (screen excluded — Error #16 RESIZE FORBIDDEN on import)
_IMPORT_TYPES = {
    "group", "preset", "macro", "effect", "sequence", "view", "page",
    "camera", "layout", "form", "plugin", "matricks", "mask", "image",
    "executor", "timecode", "userprofile", "filter",
}

# Type-specific subfolders (informational — MA2 routes automatically)
# macros/ | effects/ | plugins/ | matricks/ | masks/ | importexport/ (default)
_IMPORT_EXPORT_DATA_ROOT = (
    r"C:\ProgramData\MA Lighting Technologies\grandma\gma2_V_3.9.60\importexport"
)






# ============================================================
# Tools 74–76 — Fixture Type / Layer Import + XML Generation






# ============================================================
# Tools 55–56 — Fixture & Sequence/Cue Discovery (SAFE_READ)










# ============================================================
# Tools 70–73: Tier 3 — Fixture Patching Workflow








# ============================================================
# Wildcard Name Discovery




# ============================================================
# Server Startup
# ============================================================


# ============================================================
# Tools 83–86 — ML-Based Tool Categorization














# ============================================================================
# USER MANAGEMENT TOOLS (Tools 98-100)
# Require OAuth scope gma2:user:manage (Tier 5 — Admin only)








# ============================================================
# Tools 102–109: Quick-wins sprint
















# ============================================================
# Agentic Layer — Orchestrator wiring
# ============================================================

_ltm = LongTermMemory()

_orchestrator = Orchestrator(
    tool_caller=_tool_caller,
    telnet_send=_telnet_send_fn,
    ltm=_ltm,
    parallel=False,
)

register_orchestration_tools(mcp, _orchestrator, require_scope, _handle_errors, OAuthScope)

# Register MCP completions (argument autocompletion for prompts + resource templates)
from src.completions import register_completions  # noqa: E402

register_completions(mcp)



# ============================================================
# MCP Resources
# Static and semi-static context exposed as URI-addressable docs
# ============================================================


@mcp.resource("ma2://docs/rights-matrix")
def resource_rights_matrix() -> str:
    """
    MA2 OAuth scope → MA2Right mapping matrix (read-only reference).

    Returns the full JSON rights matrix from doc/ma2-rights-matrix.json.
    Use this resource to look up which OAuth scope is required for any
    MA2 operation before attempting to call a tool.
    """
    rights_path = Path(__file__).parent.parent / "doc" / "ma2-rights-matrix.json"
    try:
        return rights_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return json.dumps({"error": "rights matrix not found at doc/ma2-rights-matrix.json"})


@mcp.resource("ma2://docs/vocab-summary")
def resource_vocab_summary() -> str:
    """
    grandMA2 keyword vocabulary summary — all 141 keywords with RiskTier and category.

    Use this resource to look up the safety tier of any MA2 keyword before
    including it in a command string.  Tier determines whether confirm_destructive
    is required and which OAuthScope must be active.
    """
    from src.vocab import classify_token, load_vocab
    spec = load_vocab()
    summary = {}
    all_keywords = list(spec.function_keywords.keys()) + list(spec.object_keywords.keys())
    for kw in all_keywords:
        resolved = classify_token(kw, spec)
        summary[kw] = {"category": resolved.category, "risk_tier": resolved.risk_tier}
    return json.dumps(summary, indent=2)


@mcp.resource("ma2://docs/tool-taxonomy")
def resource_tool_taxonomy() -> str:
    """
    ML-generated tool taxonomy — 143 tools clustered into 14 categories.

    Each entry includes tool name, category, and docstring summary.
    Use this resource to understand the tool landscape before calling
    suggest_tool_for_task, or to verify a tool exists before invoking it.
    """
    taxonomy = _load_taxonomy_cached()
    # Return a compact summary: category → tool names
    categories = taxonomy.get("categories", {})
    summary = {
        cat: [t["name"] for t in data.get("tools", [])]
        for cat, data in categories.items()
    }
    return json.dumps({"categories": summary, "total_tools": sum(len(v) for v in summary.values())}, indent=2)


@mcp.resource("ma2://docs/responsibility-map")
def resource_responsibility_map() -> str:
    """
    Module responsibility map — every file's primary role and architectural smells.

    Use this resource when making architectural decisions or when adding new
    modules, to ensure the new code is placed in the correct layer.
    """
    map_path = Path(__file__).parent.parent / "doc" / "responsibility-map.md"
    try:
        return map_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "# Responsibility map not found. Run the architecture audit to regenerate."


@mcp.resource("ma2://docs/tool-surface-tiers")
def resource_tool_surface_tiers() -> str:
    """
    Tool surface tier classification — which tools are Tier A (always visible),
    Tier B (retrievable), or Tier C (internal).

    Use this resource to decide whether to add a new tool to the planner-visible
    surface or keep it as a worker-only primitive.
    """
    tiers_path = Path(__file__).parent.parent / "doc" / "tool-surface-tiers.md"
    try:
        return tiers_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "# Tool surface tiers doc not found."


@mcp.resource("ma2://skills/{skill_id}")
def resource_skill_body(skill_id: str) -> str:
    """
    Retrieve a skill's formatted injection payload by ID.

    Returns the skill body formatted as a user message ready for injection,
    but only if the skill is usable (approved or non-DESTRUCTIVE).
    Returns an error message if the skill is not found or not yet approved.

    Use SkillRegistry.get_usable() for the same check with Python access.
    """
    from src.skill import SkillRegistry
    reg = SkillRegistry()
    skill = reg.get_usable(skill_id)
    if skill is None:
        sk = reg.get(skill_id)
        if sk is None:
            return f"Skill '{skill_id}' not found in registry."
        return f"Skill '{skill_id}' exists but is not usable (safety_scope=DESTRUCTIVE, approved=False). Requires SYSTEM_ADMIN approval."
    return skill.as_user_message()


@mcp.resource("ma2://busking/patterns")
def resource_busking_patterns() -> str:
    """
    Best-practice busking patterns for live performance lighting (read-only).

    Covers: fader-per-effect model, song macro page protocol, live recovery
    steps, and color lock technique. Use before designing a busking show.
    """
    return """\
# grandMA2 Busking Patterns

## Fader-Per-Effect Model
Each executor on a fader page runs one effect. The fader controls intensity
(0 = silent, 100 = full). Effects stay armed — zero fader silences, raise
fader restores. Never release effects mid-song; use normalize_page_faders.

Layout convention:
  - Column 1 (Exec 1): Song loader macro (first-button protocol)
  - Columns 2–8 (Exec 2–8): Effect faders (strobe, chase, color, beam...)
  - Columns 9–10: Group masters (intensity override for rig sections)
  - Fixed right page: Global effects that persist across songs

## Song Macro Page Protocol
Each song gets one page. Page name: `SNG_{n}_{SongName}` (e.g. SNG_3_Villains).

**First button (Exec 1) macro lines:**
1. `ClearAll` — reset programmer
2. `Go Preset 4.{palette_id}` — apply song color palette
3. `Go Macro {song_setup_macro}` — recall rig positions and timing
4. `SelectDrive {executor_page}` — jump to this song's effect page

**Remaining buttons:** effect executors — no macros, faders only.

## Live Recovery Protocol
When show state drifts (wrong levels, stuck effects):
1. `normalize_page_faders(page)` — zero all faders silently
2. `clear_effects_on_page(page)` — release stuck executors
3. Re-trigger song loader (Exec 1) to restore clean state
4. Gradually raise faders to rebuild look

## Color Lock Technique
Prevents color bleed when multiple effects are active:
1. Store song color as a Color preset (e.g. Preset 4.30 = deep amber)
2. Apply preset to all fixtures via Group masters before effects start
3. Effects modulate intensity/position only — color preset holds the hue
4. On song change: apply new color preset before raising new effect faders
"""


@mcp.resource("ma2://busking/effect-design")
def resource_effect_design() -> str:
    """
    Effect-to-executor assignment patterns and rate/speed semantics (read-only).

    Covers: assign_effect_to_executor usage, rate vs speed distinction,
    MAtricks layering for busking, and batch release safety.
    """
    return """\
# grandMA2 Effect Design for Busking

## Effect Assignment
Use `assign_effect_to_executor(effect_id, executor_id, page=N)` to bind an
effect from the library to a fader slot. This is DESTRUCTIVE — do during
pre-show programming, not during live performance.

Command generated: `Assign Effect {id} Executor {id}` or `Assign Effect {id} Page {n}.{exec}`

After assignment, the fader controls the effect's master intensity (0-100).
The effect runs continuously while the executor is active.

## Rate vs Speed
| Parameter | Command | Semantics | Range |
|-----------|---------|-----------|-------|
| Rate | `EffectRate {n}` | Relative multiplier — 100 = normal | 1–200 |
| Speed | `EffectSpeed {n}` | Absolute BPM — overrides rate | 20–300 |

Use `modulate_effect(mode="rate", value=150)` to push effects 1.5× faster.
Use `modulate_effect(mode="speed", value=120)` to lock effects to 120 BPM.

Speed and rate affect the *selected* effects globally. To target a specific
executor's effect, select it first with `select_executor(executor_id)`.

## MAtricks Layering
Layer MAtricks patterns over effects for per-fixture phase offsets:
1. Select group, apply MAtricks Interleave
2. Run effect — each fixture gets a phase offset proportional to its index
3. Adjust interleave with `modulate_effect` rate to control chase tightness

## Batch Release Safety
`clear_effects_on_page(page, start_exec=1, end_exec=20)` sends 20 Off
commands in a single chained string. On slow consoles this may cause a
brief flash as effects die in sequence. To avoid: use `normalize_page_faders`
first (silences without visual glitch), then `clear_effects_on_page`.
"""


@mcp.resource("ma2://busking/color-design")
def resource_color_design() -> str:
    """
    Constrained color palette design for busking shows (read-only).

    Covers: HSB palette strategy, preset numbering, monochromatic constraint,
    and color lock via group master. Use when designing song color palettes.
    """
    return """\
# grandMA2 Constrained Color Design for Busking

## HSB vs RGB
Always use HSB for live busking color design. MA2 HSB range: 0-100 (not 0-255).

| Parameter | Flag | Range | Notes |
|-----------|------|-------|-------|
| Hue | `/h=` | 0–360 | Degrees |
| Saturation | `/s=` | 0–100 | 0 = white, 100 = full color |
| Brightness | `/br=` | 0–100 | 0 = black, 100 = full |

Example: `store_preset 4.30 /h=30 /s=95 /br=100` = deep amber.

## Monochromatic Palette Strategy
Each song gets one hue with 4 brightness stops:
- Stop 1: Full intensity (br=100, s=90)
- Stop 2: Mid punch (br=70, s=85)
- Stop 3: Moody fill (br=40, s=80)
- Stop 4: Near-black accent (br=15, s=75)

## Preset Numbering Convention
`preset_id = song_id * 10 + stop_index`

| Song | Stop | Preset |
|------|------|--------|
| Song 1 | 1 (full) | 11 |
| Song 1 | 2 (mid) | 12 |
| Song 3 | 4 (accent) | 34 |

Recall with `apply_preset(preset_type="color", preset_id=34)`.

## Color Lock Technique
1. Before raising effect faders, apply the song's full-intensity color preset
   to all rig fixtures via group masters: `group_at(group_id=99, value=100)`
2. Effects that only modulate intensity/position inherit the locked color
3. Transition between songs: apply new color preset (step 1) BEFORE releasing
   the previous song's effect faders — avoids white flash on crossover
4. For fixtures with separate color channels (CMY movers): store color in a
   Color preset, not in the programmer, so it survives `ClearAll`
"""


@mcp.resource("ma2://docs/volunteer-guide")
def resource_volunteer_guide() -> str:
    """
    Volunteer operator guide — plain-language grandMA2 operation for non-programmers.

    Explains the three-tier access model, Sunday morning preflight procedure,
    and what to do when things go wrong. Designed for church technical directors
    training volunteers and any production environment with tiered staff skill levels.
    """
    return """\
# GrandPA2-Buddy Volunteer Operator Guide

## The Three Safety Tiers

GrandPA2-Buddy enforces three access levels automatically. You cannot accidentally break something outside your tier.

| Your Role | Tier | What You Can Do |
|-----------|------|-----------------|
| New volunteer | SAFE_READ | See console state, verify the show is correct. Zero risk. |
| Trained operator | SAFE_WRITE | Trigger go/pause, adjust faders, apply presets. With guidance. |
| Technical Director | DESTRUCTIVE | Store cues, modify show file, change patch. TD only. |

## Sunday Morning Preflight (Any Volunteer -- SAFE_READ)

Run in order before doors open:

1. Verify show file -- get_showfile_info() -- confirm show name matches expected
2. Check for changes -- assert_showfile_unchanged() -- if this fails, STOP and call TD
3. Hydrate -- hydrate_console_state() -- snapshot everything
4. Check presets -- list_preset_pool(preset_type="color") -- should have entries
5. Check executors -- get_executor_detail(executor_id="1.1") -- confirm sequence assigned
6. Check cues -- query_object_list(object_type="sequence", object_id=1) -- confirm cues present

All GREEN? You are ready. Any RED? Call your TD before service.

## During Service (Trained Volunteer -- SAFE_WRITE)

- Advance cues: playback_action(executor_id, action="go")
- Pause: playback_action(executor_id, action="pause")
- Jump to cue: goto_cue(executor_id, cue_id)

## When Things Go Wrong

| Problem | Action |
|---------|--------|
| Wrong look on stage | Do NOT touch anything. Note cue number. Call TD. |
| Console unresponsive | Run get_console_location(). If error, notify TD. |
| Show file looks different | Run assert_showfile_unchanged(). If fails, STOP, call TD immediately. |
| Executor shows wrong state | Run get_executor_detail(executor_id) and report to TD. |

Rule: If in doubt, do nothing and call your TD.
"""


@mcp.resource("ma2://docs/sb132-compliance")
def resource_sb132_compliance() -> str:
    """
    SB 132 compliance guide — California Film & Television Tax Credit safety documentation
    requirements mapped to GrandPA2-Buddy telemetry fields.

    For gaffers, safety officers, production managers, and insurance brokers on
    productions receiving the California Film & Television Tax Credit (effective July 2025).
    """
    return """\
# SB 132 Compliance Guide for GrandPA2-Buddy

## What SB 132 Requires (July 2025)

California SB 132 applies to productions receiving the CA Film & Television Tax Credit and requires:

1. Dedicated Safety Advisor -- on set daily
2. Written Risk Assessment -- before any high-risk operation
3. Daily Safety Meeting Notes -- documented
4. Final Safety Report -- within 60 days of wrap

## GrandPA2-Buddy Data to SB 132 Mapping

| SB 132 Requirement | GrandPA2-Buddy Source | Tool |
|---|---|---|
| Written risk assessment | risk_tier per operation (SAFE_READ/SAFE_WRITE/DESTRUCTIVE) | get_telemetry_report() |
| Operator identification | operator field in tool_invocations | get_telemetry_report() |
| Daily safety meeting notes | session_id grouped timeline with timestamps | generate_compliance_report() |
| Incident log | error_class field in tool_invocations | get_telemetry_report(risk_tier="DESTRUCTIVE") |
| Final safety report | Full session export | generate_compliance_report(session_id=...) |

## Three-Tier Risk Stratification (for Insurance Underwriters)

GrandPA2-Buddy classifies every lighting control operation:

- SAFE_READ -- Read-only monitoring. Zero risk to console state or physical hardware.
- SAFE_WRITE -- Controlled modifications (level adjustments, go/pause). Standard operational risk.
- DESTRUCTIVE -- High-risk operations (cue storage, show file changes, patch modifications).
  Requires explicit confirm_destructive=True AND elevated OAuth scope. All logged.

## Generating a Compliance Report

Use generate_compliance_report(session_id, production_name, operator_name, days=1)
for a markdown report ready for safety documentation.

Use get_telemetry_report(session_id, format="json") for archival JSON export.

## Insurance Brief Template

All lighting control operations during [PRODUCTION NAME] were processed through
GrandPA2-Buddy's three-tier safety system. [N] operations were classified SAFE_READ
(read-only monitoring, zero risk), [M] were SAFE_WRITE (controlled modifications
requiring standard authorization), and [K] were DESTRUCTIVE (required explicit
authorization and elevated scope). Full telemetry is retained for forensic review
and available upon request from the production safety advisor.

## IATSE Kit Rental

Under the 2024 IATSE-AMPTP contract, AI tools used by union members constitute "covered work"
and operators may charge a kit rental fee. GrandPA2-Buddy's operator field in telemetry
records which union member ran each session, supporting kit rental documentation.
"""


@mcp.resource("ma2://docs/rdm-workflow")
def resource_rdm_workflow() -> str:
    """
    RDM (Remote Device Management) workflow reference — discovery, device info,
    and autopatch best practices for grandMA2 via telnet.
    """
    return """\
# RDM Workflow Reference

## What is RDM?

RDM (Remote Device Management) is a bidirectional extension to DMX512 (ANSI E1.20)
that allows a lighting console to identify, configure, and report status from
intelligent fixtures without additional cabling.

## When to Use RDM

| Use Case | RDM Benefit |
|----------|------------|
| Unknown rig | Identify all fixtures and their current DMX addresses |
| Address conflicts | Read device-reported addresses vs. patch sheet |
| Fixture status | Get lamp hours, temperature, error status |
| Autopatch | Let MA2 suggest addresses based on discovered footprints |

## Tool Sequence

1. Discover all RDM devices on a universe: rdm_discover(universe_id=1)
   Returns: list of {uid, manufacturer, device_model, footprint, current_address}

2. Get detailed info for a specific device: rdm_get_info(uid="0x1234567890AB")
   Returns: full device profile including label, DMX footprint, current address, error status

3. Apply a DMX address (autopatch): rdm_patch(uid="0x1234567890AB", target_address=1, confirm_destructive=True)
   Assigns the fixture to channel 1 on its universe

## Limitations

- Not all fixtures support RDM. Most intelligent fixtures do; dimmers may not.
- RDM requires a proper terminator at the end of the DMX chain.
- RDM discovery can take 10-30 seconds per universe on large rigs.
- After RDM patch, verify with list_fixtures() and detect_dmx_address_conflicts().

## RDM vs Manual Patching

| | RDM | Manual |
|---|---|---|
| Speed | Fast for large rigs | Faster for small rigs |
| Accuracy | Device-reported | Human-verified |
| Risk | Overwrites existing addresses | You control every address |
| Recommended when | Unknown rental rig, >50 fixtures | Known rig, <20 fixtures |
"""


@mcp.resource("ma2://docs/lua-scripting")
def resource_lua_scripting() -> str:
    """
    grandMA2 Lua 5.2 scripting reference — gma.* namespace, plugin lifecycle,
    and common patterns for MCP-driven plugin development.
    """
    return """\
# grandMA2 Lua Scripting Reference

## Environment

grandMA2 uses Lua 5.2 with the gma.* namespace for console integration.
Standard Lua libraries (math, string, table, io) are available.

## Core gma.* Functions

| Function | Description |
|----------|-------------|
| gma.cmd(str) | Execute a MA2 command |
| gma.echo(str) | Print to feedback line |
| gma.show.getvar(name) | Read show variable |
| gma.show.setvar(name, val) | Write show variable |
| gma.user.confirm(msg) | Show OK/Cancel dialog |
| gma.timer.sleep(ms) | Pause execution (ms) |
| gma.gui.confirm(title, msg) | GUI confirmation |

## Plugin vs Macro: Decision Guide

| Need | Use |
|------|-----|
| Simple linear commands | Macro (MA2 command strings) |
| Loop (for/while) | Lua Plugin |
| Math calculation | Lua Plugin |
| Read/write variables | Either (SetVar in macro, gma.show.setvar in Lua) |
| User dialog (confirm/input) | Lua Plugin only |
| Conditional (if/else) | Lua Plugin |

## Common Patterns

Loop over fixture IDs:
  for i = 1, 20 do
      gma.cmd("Fixture " .. i .. " At 100")
      gma.timer.sleep(100)
  end

Read and branch on system variable:
  local pg = tonumber(gma.show.getvar("FADERPAGE"))
  if pg == 1 then gma.cmd("Page 2") else gma.cmd("Page 1") end

User confirmation gate:
  if gma.user.confirm("Delete all cues in Sequence 99?") then
      gma.cmd("Delete Cue 1 Thru 999 Sequence 99")
      gma.echo("Cues deleted.")
  else
      gma.echo("Cancelled.")
  end

## MCP Integration

Use run_lua_script(script_body) to execute inline Lua via MCP.
Use call_plugin_tool(plugin_name, args) to invoke a saved plugin by name.
Use reload_all_plugins() after uploading a new .lua file via USB.

Safety note: Lua scripts executed via gma.cmd() bypass MCP's safety gate.
Ensure scripts that call DESTRUCTIVE commands (Store, Delete, Assign) include
appropriate confirmations via gma.user.confirm().
"""


# ============================================================
# MCP Prompts
# User-initiated workflow templates for console operations
# ============================================================


@mcp.prompt()
def preflight_destructive_change(operation: str, target: str, reason: str = "") -> str:
    """
    Run pre-flight checks before any destructive console operation.

    Use this prompt before calling any DESTRUCTIVE tool to ensure the
    operation is safe to proceed.

    Args:
        operation: The destructive operation to perform (e.g. "delete_object", "store_current_cue").
        target: The object or path being modified (e.g. "Group 5", "Sequence 1 Cue 3").
        reason: Why this change is needed (optional but recommended for audit trail).
    """
    return f"""Perform a safety pre-flight before executing: {operation} on {target}

Reason: {reason or "(not specified)"}

Pre-flight checklist:
1. Read `ma2://docs/rights-matrix` — confirm the current user has sufficient rights for {operation}.
2. Call `list_system_variables` — check $USERRIGHTS and $SHOWFILE.
3. Call `get_object_info` on {target} — confirm the target exists and capture its current state.
4. Check if Blind mode is active (`$BLINDMODE` or `mode_overrides["blind"]`).
5. If the operation affects executors, verify no cue is running on the target executor.

Only proceed with {operation} after all five checks pass.
If any check fails, report the finding and ask the user to confirm before proceeding.
Use `confirm_destructive=True` when calling the tool."""


@mcp.prompt()
def inspect_console(focus: str = "full") -> str:
    """
    Guided console state inspection — Inspect workflow.

    Produces a structured console overview without any mutations.

    Args:
        focus: What to inspect — "full" (default), "playback", "fixtures", "show", or "rights".
    """
    focus_map = {
        "full": "system variables, active executors, programmer state, and current show info",
        "playback": "active executors, running cues, fader levels, and executor assignments",
        "fixtures": "patched fixture types, selected fixtures, programmer content",
        "show": "show file name, universe count, group count, sequence count, and preset pool sizes",
        "rights": "current user, rights level, active world, and active filter",
    }
    scope = focus_map.get(focus, focus_map["full"])
    return f"""Inspect the grandMA2 console — {focus} focus.

Read-only inspection only. No mutations permitted.

Steps:
1. Call `list_system_variables` — capture all 26 system variables.
2. Inspect: {scope}.
3. Call `navigate_console` to `cd /` and `list_console_destination` to see the root object tree.
4. If focus includes executors: call `query_object_list` for active sequences and their cue counts.
5. Summarize findings in this structure:

{{
  "console_version": "$VERSION",
  "show_file": "$SHOWFILE",
  "active_user": "$USER",
  "rights": "$USERRIGHTS",
  "selected_exec": "$SELECTEDEXEC",
  "active_cue": "$SELECTEDEXECCUE",
  "fixture_count": <from list>,
  "findings": ["..."]
}}"""


@mcp.prompt()
def plan_cue_store(
    sequence_id: str,
    cue_number: str,
    fixture_selection: str,
    preset_or_values: str,
) -> str:
    """
    Plan a cue store operation with safety and rights checks — Plan workflow.

    Use this prompt to generate a structured cue store plan before executing.
    The plan includes pre-flight checks, proposed commands, and a verification step.

    Args:
        sequence_id: Sequence number (e.g. "1", "99").
        cue_number: Target cue number (e.g. "1", "3.5").
        fixture_selection: Fixture group or ID range to use (e.g. "Group 1", "Fixture 1 Thru 10").
        preset_or_values: Preset to apply or manual values (e.g. "Preset 4.5", "Full").
    """
    return f"""Plan a cue store operation without executing it yet.

Target: Store Cue {cue_number} in Sequence {sequence_id}
Fixtures: {fixture_selection}
Values/Preset: {preset_or_values}

Plan steps:
1. PRE-FLIGHT: Call `list_system_variables` — confirm $USERRIGHTS has Programmer or higher.
2. PRE-FLIGHT: Call `query_object_list` for Sequence {sequence_id} — check if Cue {cue_number} already exists.
   If it exists: plan a /merge store. If not: plan a clean store.
3. SELECT: Plan `SelFix {fixture_selection}` — verify fixture count > 0.
4. APPLY: Plan `{preset_or_values}` — identify whether this is a preset recall or direct value.
5. STORE PLAN: Emit the exact command to be executed:
   `Store Cue {cue_number} Sequence {sequence_id} /merge`
6. VERIFY PLAN: After store, plan `query_object_list` on Sequence {sequence_id} to confirm Cue {cue_number} exists.

Return the plan as a JSON object with "pre_flight", "commands", and "verify" arrays.
Do NOT execute any commands yet. This is a planning step only."""


@mcp.prompt()
def diagnose_playback_failure(executor_id: str, symptom: str) -> str:
    """
    Diagnose a playback failure on a specific executor — Inspect + Plan workflows.

    Use this prompt when a cue or executor is not behaving as expected.

    Args:
        executor_id: The executor identifier (e.g. "1", "201", "1.1.201").
        symptom: What is observed (e.g. "cue not advancing", "no output", "wrong fixtures responding").
    """
    return f"""Diagnose playback failure on Executor {executor_id}.

Observed symptom: {symptom}

Diagnostic steps:
1. Call `list_system_variables` — check $SELECTEDEXEC, $SELECTEDEXECCUE, $FADERPAGE.
2. Call `query_object_list` for the sequence assigned to Executor {executor_id} — count cues, check for gaps.
3. Call `get_object_info` on Executor {executor_id} — check assignment, priority, options.
4. Call `send_raw_command` with `list Executor {executor_id}` — capture raw executor state.
5. Load skill `ma2://skills/telnet-feedback-triage` — apply FeedbackClass classification to any UNKNOWN COMMAND or WARNING responses.

Common failure patterns:
- "no output": check blind mode ($BLINDMODE), check if output is patched, check DMX universe assignment.
- "cue not advancing": check trigger setting (Time/Go), check MIB settings, check if executor has "Kill" active.
- "wrong fixtures": check world assignment, check if programmer has conflicting values (call `clear_programmer`).

Return structured findings: {{"fault_class": "...", "root_cause": "...", "recommended_actions": [...]}}"""


@mcp.prompt()
def load_show_safely(show_name: str) -> str:
    """
    Safe show loading checklist — prevents accidental Telnet disconnection.

    Use this prompt before any new_show or load_show operation.

    Args:
        show_name: The show file to load (e.g. "my_show_2026").
    """
    return f"""Load show "{show_name}" safely without severing the MCP Telnet connection.

Pre-load checklist:
1. Call `list_system_variables` — record current $SHOWFILE, $HOSTIP, $VERSION.
2. Call `save_show` if any unsaved changes should be preserved.
3. CRITICAL: Verify that the load command will preserve connectivity:
   - For `new_show`: MUST use preserve_connectivity=True (passes /globalsettings /network /protocols).
   - For `load_show`: confirm the target show has Telnet enabled in its global settings.
4. Confirm the operator understands: loading a show with Telnet disabled will disconnect this MCP session.

Only proceed after the checklist is complete.
If loading a completely blank show, the user MUST manually re-enable Telnet in
Setup → Console → Global Settings before the next MCP connection."""


@mcp.prompt()
def bootstrap_rights_users() -> str:
    """
    Bootstrap the standard six-tier MA2 rights user accounts — guided provisioning workflow.

    Use this prompt when setting up a new show file with the standard
    operator rights ladder (Admin, LightOperator, Programmer, PlaybackOperator, Guest, Emergency).
    """
    return """Bootstrap the standard MA2 rights user accounts.

This is a DESTRUCTIVE workflow — it creates user accounts and modifies user profiles.
All steps require confirm_destructive=True.

Steps:
1. INSPECT: Call `list_console_users` — check which accounts already exist.
   Built-in accounts Administrator and Guest always exist and cannot be deleted.
2. READ RESOURCE: Load `ma2://docs/rights-matrix` — review the six-tier rights ladder.
3. PLAN: For each missing account in the standard set:
   - Admin (rights: Admin)
   - LightOperator (rights: Light-Operator)
   - Programmer (rights: Programmer)
   - PlaybackOp (rights: Playback-Operator)
   - Guest (rights: Guest)
4. EXECUTE: For each planned account, call `create_user(username=..., rights=..., confirm_destructive=True)`.
5. VERIFY: Call `list_console_users` again — confirm all accounts were created.
6. SAVE: Call `save_show` to persist the new accounts.

Return a summary of: accounts created, accounts skipped (already existed), any errors."""




# ============================================================
# Wave 1 — Console Session & UI Lock








# ============================================================
# Wave 2 — Read-only list tools (pool discovery)
























# ============================================================
# Wave 3 — Chaser live control & Effect programmer parameters




# ============================================================
# Wave 4 — Plugin / Lua / Special Master








# ============================================================
# Wave 5 — RDM (Remote Device Management)


















# ============================================================
# New Prompts: Volunteer Preflight, Busking Template,
# Pre-Show Health Check, Adapt Show to Venue
# ============================================================


@mcp.prompt()
def volunteer_sunday_preflight(show_name: str = "", campus_name: str = "") -> str:
    """
    Sunday morning preflight checklist for volunteer operators — SAFE_READ guided verification
    that the correct show is loaded, presets are populated, and executors are assigned.
    """
    context = f"Show: {show_name}" if show_name else "Show: (use get_showfile_info to determine)"
    campus = f"Campus: {campus_name}" if campus_name else ""

    return f"""You are running a pre-show safety check for a volunteer operator.
{context}
{campus}

Execute the following SAFE_READ verification sequence in order. Stop and report
immediately if any step returns unexpected results.

STEP 1 -- SHOWFILE VERIFICATION
Call get_showfile_info(). Confirm the show name matches "{show_name or 'the expected show name'}".
Then call assert_showfile_unchanged(). If it returns False, STOP -- the show file has been modified
since the last programmer session. Do not proceed; contact the Technical Director.

STEP 2 -- STATE HYDRATION
Call hydrate_console_state(). Then call get_console_state().
Check for: unexpected parked fixtures (park_ledger not empty), active filter (may restrict fixtures),
unexpected world assignment.

STEP 3 -- PRESET POOL CHECK
Call list_preset_pool(preset_type="color") and list_preset_pool(preset_type="position").
Flag as AMBER if either pool has fewer than 3 entries.

STEP 4 -- EXECUTOR ASSIGNMENT CHECK
Call get_executor_detail(executor_id="1.1") and get_executor_detail(executor_id="1.2").
Confirm each has a sequence assigned and at least 1 cue.

STEP 5 -- CUE INTEGRITY CHECK
Call query_object_list(object_type="sequence", object_id=1).
Confirm the expected number of cues are present and the first cue is labeled.

STEP 6 -- GENERATE REPORT
Return a structured report:
{{
  "show_name": "<from step 1>",
  "campus": "{campus_name or 'N/A'}",
  "overall": "GREEN | AMBER | RED",
  "checks": {{
    "showfile": "GREEN | AMBER | RED",
    "console_state": "GREEN | AMBER | RED",
    "preset_pool": "GREEN | AMBER | RED",
    "executors": "GREEN | AMBER | RED",
    "cue_list": "GREEN | AMBER | RED"
  }},
  "findings": ["..."],
  "action_required": true | false
}}

GREEN = everything nominal. AMBER = non-blocking issue, report to TD. RED = stop, contact TD immediately."""


@mcp.prompt()
def generate_busking_template(
    target_page: str = "2",
    fixture_strategy: str = "by_type"
) -> str:
    """
    Generate a complete grandMA2 busking template from the current patch —
    groups, presets, effects, speed masters, and executor layout.
    """
    return f"""You are building a complete busking template for a grandMA2 rig.

Target executor page: {target_page}
Fixture grouping strategy: {fixture_strategy} (options: by_type, by_position, by_zone)

PHASE 0 -- SURVEY (SAFE_READ, always first -- present findings before proceeding)
1. Call hydrate_console_state() and list_fixtures() -- record total fixture count and types
2. Call list_fixture_types() -- identify unique fixture types in the rig
3. Call list_preset_pool(preset_type="color") -- check if color presets already exist
4. Call list_preset_pool(preset_type="position") -- check position presets
5. Present survey summary to operator and ask: "I found [N] fixtures of [M] types.
   Color pool has [K] existing presets. Shall I proceed with template generation?"
   STOP if operator says no.

PHASE 1 -- GROUP CREATION (confirm before executing DESTRUCTIVE operations)
Using the {fixture_strategy} strategy:
- by_type: one group per fixture type (all washes, all spots, all beams, all strobes)
- by_position: groups by stage position (front, back, left, right, truss)
- by_zone: groups by zone (audience, stage, backlight)

For each group: call create_fixture_group() then label_or_appearance() with HSB color coding.
Ask operator to confirm before executing: "I will create [N] groups in slots [X-Y]. Proceed?"

PHASE 2 -- COLOR PRESETS (8 per group -- confirm first)
Create 8 universal color presets using RGB 0-100 scale:
Red(100,0,0), Orange(100,40,0), Yellow(100,100,0), Green(0,100,0),
Cyan(0,100,100), Blue(0,0,100), Magenta(100,0,100), White(100,100,100)

PHASE 3 -- POSITION PRESETS (movers only -- 4 positions)
For fixture groups with Pan/Tilt attributes: create Home, DownCenter, SL_Top, SR_Top presets.

PHASE 4 -- EXECUTOR LAYOUT (confirm slot assignments before executing)
On page {target_page}:
- Exec 1: Song loader macro (label "LOAD")
- Exec 2-5: Effect sequences per fixture group
- Exec 6-8: Group intensity masters
- Exec 9: Speed master 1 (default 120 BPM)
- Exec 10: Emergency blackout macro

PHASE 5 -- VERIFY AND SAVE
Call get_console_state() to confirm all objects registered.
Call save_show(confirm_destructive=True) -- always save after template build.

At each DESTRUCTIVE phase, pause and confirm with the operator before proceeding.
Never auto-execute DESTRUCTIVE operations without explicit operator confirmation."""


@mcp.prompt()
def pre_show_health_check(sequence_ids: str = "1", strict: bool = False) -> str:
    """
    Full show health audit before going live — checks showfile, presets, executors,
    cue integrity, park ledger, and DMX. Returns GREEN/AMBER/RED per category.
    """
    sequences = sequence_ids or "1"
    mode = "strict" if strict else "standard"

    return f"""You are performing a pre-show health check in {mode} mode.
Target sequences: {sequences}

Run all checks in order. Collect ALL findings before returning the final report.
Do NOT stop at first AMBER -- run all categories.

CATEGORY 1 -- SHOWFILE (GREEN/RED)
Call get_showfile_info() -- record show name and version.
Call assert_showfile_unchanged() -- RED if fails (show was modified unexpectedly).

CATEGORY 2 -- HYDRATION
Call hydrate_console_state() then get_console_state().

CATEGORY 3 -- PRESET POOL (GREEN/AMBER)
For preset types Color, Position, Beam:
  Call list_preset_pool(preset_type=X).
  AMBER if any expected type has 0 entries.
  AMBER if fewer than 3 entries in Color preset pool.

CATEGORY 4 -- EXECUTOR ASSIGNMENTS (GREEN/AMBER/RED)
For each key executor (1.1, 1.2 minimum):
  Call get_executor_detail(executor_id=X).
  AMBER if executor has no assigned sequence.
  RED if main sequence executor has 0 cues.

CATEGORY 5 -- CUE INTEGRITY (GREEN/AMBER)
For each sequence in [{sequences}]:
  Call query_object_list(object_type="sequence", object_id=N).
  AMBER if gap > 10 between consecutive cue numbers.
  AMBER if more than 20% of cues are unlabeled.
  {"RED if any gap found." if strict else "AMBER if cue count < 3."}

CATEGORY 6 -- PARK LEDGER (GREEN/AMBER)
Call get_park_ledger().
AMBER if any fixtures are parked (may be intentional -- report don't assume error).

CATEGORY 7 -- DMX (GREEN/AMBER)
Call list_fixtures() -- count fixtures with no DMX address.
AMBER if any fixture has address 0 or None.

RETURN FORMAT:
{{
  "show_name": "...",
  "audit_mode": "{mode}",
  "overall": "GREEN | AMBER | RED",
  "categories": {{
    "showfile": {{"score": "...", "findings": [...]}},
    "preset_pool": {{"score": "...", "findings": [...]}},
    "executors": {{"score": "...", "findings": [...]}},
    "cue_integrity": {{"score": "...", "findings": [...]}},
    "park_ledger": {{"score": "...", "findings": [...]}},
    "dmx": {{"score": "...", "findings": [...]}}
  }},
  "recommended_actions": [...]
}}

Overall score = worst score across all categories."""


@mcp.prompt()
def adapt_show_to_venue(
    source_show_description: str = "",
    new_venue_notes: str = ""
) -> str:
    """
    Adapt an existing show file to a new venue's fixture rig — guided cross-venue
    adaptation with patch comparison, group remapping, and preset verification.
    """
    return f"""You are adapting a show file to a new venue rig.

Source show context: {source_show_description or "current loaded show"}
New venue notes: {new_venue_notes or "no additional context provided"}

PHASE 0 -- SURVEY (SAFE_READ -- complete before any changes)
1. Call hydrate_console_state()
2. Call list_fixtures() -- document: fixture ID, type, DMX address for ALL fixtures
3. Call list_fixture_types() -- document imported profiles
4. Call list_preset_pool(preset_type="color") and list_preset_pool(preset_type="position")
5. Sample group membership: call query_object_list(object_type="group", object_id=1)

Present comparison to operator:
"Current rig has [N] fixtures of types [A, B, C].
[Describe any type mismatches based on new_venue_notes].
Which types map to which in the new venue?"

WAIT for operator confirmation of the fixture type mapping before proceeding.

PHASE 1 -- IDENTIFY MISMATCHES
Cross-reference fixture types in the show against new venue patch.
Categorize each type as: COMPATIBLE (same attributes), SIMILAR (same Pan/Tilt/Dim but different gobos),
or INCOMPATIBLE (completely different attribute set).

DECISION: If >50% of fixture types are INCOMPATIBLE, recommend using generate_busking_template
prompt to rebuild from scratch rather than adapting.

PHASE 2 -- REMAP GROUPS (confirm before DESTRUCTIVE operations)
For each group containing old fixture IDs:
  Check current membership with query_object_list(object_type="group", object_id=N).
  If fixture type mapping is COMPATIBLE or SIMILAR: use remap_fixture_ids() to update
  group membership with new fixture IDs. Ask operator to confirm before each group.

PHASE 3 -- VERIFY PRESETS
For SIMILAR types: test universal color presets -- call apply_preset(preset_type="color", preset_id=1)
with new fixture selected and verify output.
For INCOMPATIBLE types: presets must be re-recorded. Guide operator through re-recording.

PHASE 4 -- TEST AND VERIFY
Select a sample group: select_fixtures_by_group(group_id=1).
Apply a color preset: apply_preset(preset_type="color", preset_id=1).
Confirm correct fixtures respond.

PHASE 5 -- SAVE
Call save_show(confirm_destructive=True).

At every DESTRUCTIVE phase: present what will change and ask "Proceed? (yes/no)" before executing."""


# ============================================================
# Agent Harness








# ============================================================
# PSR — Partial Show Read Tools, Resource, and Prompt




def psr_guide() -> str:
    """PSR workflow guide — slot conflict resolution, fixture ID verification, post-import diff."""
    return """# grandMA2 Partial Show Read (PSR) Guide

## Overview

Partial Show Read (PSR) imports selected objects from a saved show file into the
current show without replacing the entire show. It is the standard method for
merging cue content, groups, presets, or macros between shows.

## MA2 Console Commands

| MCP Tool | MA2 Command | Purpose |
|----------|-------------|---------|
| prepare_partial_show_read | PSRPrepare "show" | Lock source show for reading |
| list_psr_objects | PSRList "show" | Enumerate available objects |
| partial_show_read | PSR "show" Type [ID] | Import objects |

## Workflow

1. **prepare_partial_show_read(source_show)**  (`PSRPrepare "source_show"`)
   Locks the source show file so MA2 can read it. Run this first.

2. **list_psr_objects(source_show)**  (`PSRList "source_show"`)
   Returns a list of object types and pool slots available in the source show.
   Use this to discover what can be imported before committing.

3. **partial_show_read(source_show, object_type, object_id, merge=False)**  (`PSR "source_show" Type [ID]`)
   Imports objects into the current show. Requires confirm_destructive=True.

## Slot Conflict Rules

- Without /merge: imported objects overwrite any existing objects at the same slot.
- With /merge: imported cue content is merged into existing sequences/cues.
- If the target slot is occupied and you do not want to overwrite it, first
  copy the existing object to a free slot before running PSR.

## Fixture ID Verification

Before importing cue content, verify that the fixture IDs in the source show
match the fixture IDs in the current show. PSR imports cue data by fixture ID —
if IDs differ, cues will apply to the wrong fixtures or produce empty steps.

Check with list_system_variables() ($SHOWFILE) and query_object_list() for
Fixture to compare fixture ID ranges between shows.

## Post-Import Diff Pattern

After running PSR, verify the import succeeded:
1. Call list_psr_objects(source_show) again — imported items should be absent
   from the available list if the console tracks them as consumed.
2. Call query_object_list for the imported object type to confirm slot is populated.
3. If cues were imported: call list_cue(sequence_id) to verify cue numbers.

## Object Types Supported

Cue, Sequence, Group, Preset, Macro, Effect, Timecode, Filter, View, Layout,
World, Plugin, Timer.

## Error Codes

- SLOT CONFLICT: Target slot occupied; use merge=True or clear the slot first.
- SOURCE NOT PREPARED: Call prepare_partial_show_read first.
- FILE NOT FOUND: Verify source_show name matches exactly (case-sensitive on some builds).
- FIXTURE ID MISMATCH: Source fixture IDs do not exist in current show patch.
"""



@mcp.prompt()
def migrate_show_via_psr(
    source_show: str,
    target_objects: str,
    dry_run: bool = True,
) -> str:
    """
    Guided PSR migration — import objects from a source show into the current show.

    Generates a step-by-step plan for selectively copying show content using
    Partial Show Read (PSR). When dry_run=True, only inspection steps run
    and no changes are made to the current show.

    Args:
        source_show: Name of the source show file (without .show extension).
        target_objects: Comma-separated list of object types to import,
                        e.g. "Cue,Sequence,Group" or "Preset,Macro".
        dry_run: If True (default), inspect only — do not import. Set False to execute.
    """
    object_list = [o.strip() for o in target_objects.split(",") if o.strip()]
    mode = (
        "DRY RUN — inspection only, no changes will be made"
        if dry_run
        else "LIVE IMPORT — objects will be written to the current show"
    )

    steps = []
    for obj in object_list:
        if dry_run:
            steps.append(
                f'  - Call list_psr_objects("{source_show}") and filter for {obj} entries'
            )
        else:
            steps.append(
                f'  - Call partial_show_read("{source_show}", "{obj}", '
                f"confirm_destructive=True) to import all {obj} objects"
            )

    steps_text = "\n".join(steps) if steps else "  - (no object types specified)"

    return f"""Perform a PSR migration from '{source_show}' into the current show.

Mode: {mode}
Target objects: {', '.join(object_list) if object_list else '(none specified)'}

## Pre-flight checks (always run these first)

1. Call list_system_variables() — confirm $SHOWFILE (current show) and $USER rights.
2. Call prepare_partial_show_read("{source_show}") — lock the source show for reading.
3. Call list_psr_objects("{source_show}") — record all available object types and slot IDs.
4. For any cue/sequence objects: call query_object_list for Fixture on both shows
   and verify fixture ID ranges match. Warn the operator if they differ.

## Slot conflict check

For each object type to import:
- Call query_object_list for that type in the current show.
- Identify any slot IDs that overlap with the source show objects.
- If overlaps exist: present the conflict list and ask the operator to confirm
  overwrite OR specify a safe target slot range.

## Import steps

{steps_text}

## Post-import verification

For each imported object type:
- Call query_object_list to confirm the slot is now populated.
- For sequences/cues: call list_cue(sequence_id) to verify cue count.
- Report any slots that are still empty after import (possible import failure).

## Notes

- PSR is DESTRUCTIVE — always confirm with the operator before running live.
- Use dry_run=True for the first pass to assess conflicts before committing.
- Oops (undo) is available immediately after PSR if the import produces unexpected results.
"""


# ============================================================
# P4 — Selection Filter Tool
# ============================================================

_FIXTURE_FILTER_MAP = {
    "active": build_if_active,
    "output": build_if_output,
    "programmer": build_if_prog,
}




# ============================================================
# P7 — Advanced Timing Tool
# ============================================================

_VALID_TIMING_ACTIONS = frozenset({
    "fade_path", "out_fade", "out_delay",
    "step_fade", "step_in_fade", "step_out_fade",
    "snap_percent",
})




# ============================================================
# P8 — Preview Mode Tool


# ============================================================
# P5 — Reference Resources (Effects, Timecode, Macro)
# ============================================================


@mcp.resource("ma2://docs/effects-reference")
def effects_reference() -> str:
    """Effects programmer reference — parameters, forms, shapes, phase, stagger."""
    return """# grandMA2 Effects Reference

## Overview

Effects in grandMA2 run continuously on top of playback values. They are
programmed in the Programmer via effect keywords and stored in cues or
the Effect pool.

## MCP Tool

`set_effect_param(param, value)` — set any effect parameter for the current selection.

## Parameter Table

| Parameter | MA2 Keyword | Value Range | Description |
|-----------|-------------|-------------|-------------|
| `bpm` | EffectBPM | 0–600 | Speed in beats per minute |
| `hz` | EffectHZ | 0–10 | Speed in cycles per second |
| `high` | EffectHigh | 0–100 | Upper value limit (%) |
| `low` | EffectLow | 0–100 | Lower value limit (%) |
| `phase` | EffectPhase | 0–359 | Phase offset in degrees (used for stagger) |
| `width` | EffectWidth | 0–100 | Duty cycle — proportion of cycle at high value |
| `attack` | EffectAttack | 0–100 | Rise time within the cycle (%) |
| `decay` | EffectDecay | 0–100 | Fall time within the cycle (%) |
| `delay` | EffectDelay | 0–100 | Delay before effect starts each cycle (%) |
| `fade` | EffectFade | 0–100 | Fade in/out at start and end of effect (%) |

## EffectBPM vs EffectHZ

- Use `bpm` for tempo-based synchronisation (e.g. 120 BPM = 2 Hz).
- Use `hz` for continuous frequency control.
- Setting one resets the other — they are mutually exclusive speed modes.

## Effect Forms / Shapes

grandMA2 includes predefined effect forms accessible via the Effect library:
Sinus, Cosinus, Square, Ramp Up, Ramp Down, Random.
Retrieve with `browse_effect_library()`.

## Phase Stagger Pattern

To create a wave across fixtures, select them in order and fan the phase:
1. Select all fixtures in desired order (e.g. `SelFix Fixture 1 Thru 10`)
2. Set a base effect: `set_effect_param("bpm", 60)`
3. Apply phase spread: `set_effect_param("phase", 0)` on first, through to 359 on last.
   grandMA2 auto-fans phase across a selection when you type a start and end value
   in the Phase column of the programmer.

## Storing Effects

Effects in the programmer are stored with cues automatically when you call
`store_current_cue()` or `store_cue()`. To store an independent Effect pool
object, use the Effect pool editor (Setup → Show → Effects).

## Key Constraints

- Effects only run on fixtures that are in the current selection when stored.
- Effect speed masters (EffectMaster) can override BPM globally.
- Phase is per-fixture — it is stored in cue data, not in the Effect pool object.
"""


@mcp.resource("ma2://docs/timecode-reference")
def timecode_reference() -> str:
    """SMPTE timecode show reference — pool setup, cue triggers, slot management."""
    return """# grandMA2 SMPTE Timecode Reference

## Overview

grandMA2 supports SMPTE timecode for cue-accurate show automation.
Timecode events map specific SMPTE positions to cue/macro triggers.

## MCP Tools

- `store_timecode_event(...)` — store a cue trigger at a SMPTE position
- `control_timecode(action, ...)` — start/stop/goto timecode playback

## Timecode Pool Object

A Timecode pool object represents one timecode track.
Each track maps SMPTE addresses to triggered commands.

Create via: `Store Timecode N`
List via: `List Timecode`
Info via: `Info Timecode N`

## SMPTE Address Format

`HH:MM:SS:FF` — hours:minutes:seconds:frames
Frame rates: 24, 25, 29.97 drop/non-drop, 30 fps.
Set frame rate in Timecode pool properties.

## Event Trigger Syntax

Events are stored as lines inside a Timecode object:
`Store Timecode N "HH:MM:SS:FF" [command]`

Example:
`Store Timecode 1 "00:00:05:00" Go Executor 1`
`Store Timecode 1 "00:00:10:00" Go Executor 2`

## Playback

- `Go Timecode N` — start playback from current position
- `GoTo Timecode N "HH:MM:SS:FF"` — jump to a SMPTE position
- `Stop Timecode N` — stop timecode playback
- Timecode can be driven by internal clock or external LTC input.

## LTC Input Configuration

1. Open Setup → Console → Global Settings → Timecode
2. Select LTC input source (Audio in / USB MIDI / MA-Net)
3. Assign input to Timecode pool slot

## Slot Management

- Each Timecode pool slot (1–N) holds one track.
- Tracks are independent — multiple tracks can run simultaneously.
- To delete events: `Delete Timecode N "HH:MM:SS:FF"`
- To clear all events in a track: `Delete Timecode N`

## Integration with Sequences

Timecode events typically trigger executor Go commands:
`Store Timecode 1 "00:01:00:00" Go Executor 1.203`

Use page-qualified executor addresses for reliable targeting.
"""


@mcp.resource("ma2://docs/macro-reference")
def macro_reference() -> str:
    """Macro scripting reference — SetVar/AddVar, conditionals, jump targets, CmdDelay."""
    return """# grandMA2 Macro Reference

## Overview

Macros are sequences of MA2 command lines stored in the Macro pool.
They support variables, conditionals, loops, and jump targets for
complex automation.

## MCP Builders

- `macro_condition_line(var_name, operator, value, command)` — build a conditional line
- `record_macro(macro_id)` — start key-capture recording
- `macro_with_input_after(command)` — add `@` placeholder at end
- `macro_with_input_before(command)` — add `@` placeholder at beginning

## Line Structure

Each macro line is a plain MA2 command string.
Lines execute sequentially unless a jump redirects.

## Variables

| Command | Syntax | Description |
|---------|--------|-------------|
| SetVar | `SetVar $name = value` | Assign a value to a user variable |
| AddVar | `AddVar $name + value` | Add to a user variable |
| GetVar | `GetVar $name` | Read a variable value |
| ListVar | `ListVar` | List all user variables |

Variable names must start with `$`.

## Conditional Syntax

Conditionals use `[$var op value]` prefix syntax:

```
[$mode == 1] Go Executor 1
[$counter < 10] AddVar $counter + 1
```

Valid operators: `==`, `!=`, `<`, `>`
IMPORTANT: Use `==` for equality, NOT `=`. Single `=` is for SetVar assignment.

Use `macro_condition_line(var_name, operator, value, command)` builder.

## EndIf

`EndIf` closes a conditional block. Required to end multi-line If/While blocks.

## CmdDelay

`CmdDelay N` — pause execution for N tenths of a second.
Example: `CmdDelay 5` = 0.5 seconds delay.

## Jump Targets

Jump to a specific macro line:
`Go Macro N."name".LINE`

Where LINE is 1-based line number (= XML index + 1).

When inserting lines into a macro, update all jump target line numbers.

## Interactive @ Placeholder

`@` in a macro line inserts user input at that position:
- `Load @` — user types show name after executing
- `@ Fade 20` — user input is prepended (CLI must be disabled)

## Popup Macro Pattern

To chain macros and ask for confirmation:
1. Macro A: sets up context, then `Go Macro B`
2. Macro B: validates via `[$var == expected]`, continues or aborts

## Example: Counter Loop

```
SetVar $i = 0
[$i < 5] Go Executor 1
[$i < 5] AddVar $i + 1
[$i < 5] Go Macro 1."loop".2
```
"""


@mcp.resource("ma2://docs/network-session")
def resource_network_session() -> str:
    """MA-Net2 multi-console session management — TakeControl, IP setup, station invite/disconnect."""
    return """\
# grandMA2 Network Session Reference

## Overview
Multiple grandMA2 consoles and onPC stations can share a single MA-Net2 session.
One station holds Control; others are Members. The session shares show data,
universe output, and command execution across all stations.

## Important Note for MCP Users

Network session keywords (JoinSession, TakeControl, SetIP, etc.) do **not** have
command builder or MCP tool coverage in this project (P9 gap — low priority for
Telnet-only single-station use). Use this resource for reference only.

## Session Topology

- **Session Master**: station that created the session; holds Control by default
- **Members**: stations that joined; can request Control
- **Control holder**: only one station can hold Control at a time
- **Output**: all stations contribute to universe output unless in No Output mode

## Keyword Reference (no builders yet — P9)

| Keyword | Syntax | Purpose |
|---------|--------|---------|
| JoinSession | JoinSession "SessionName" | Join an existing MA-Net2 session |
| LeaveSession | LeaveSession | Leave the current session |
| EndSession | EndSession | Terminate the session (master only) |
| TakeControl | TakeControl | Request control of the session |
| DropControl | DropControl | Release control back to the master |
| InviteStation | InviteStation "StationName" | Invite a station to join |
| DisconnectStation | DisconnectStation "StationName" | Disconnect a member station |
| SetIP | SetIP "interface" "address" | Set a network interface IP address |
| SetHostname | SetHostname "name" | Set the station hostname |

## TakeControl Workflow

1. Check current state: list_system_variables() → read $SESSION and $CONTROLHOLDER
2. Send: TakeControl
3. Confirm: $CONTROLHOLDER should update to your station name

## IP Configuration

SetIP requires the interface name (e.g. "eth0", "Ethernet 2") and IP in dotted
notation (e.g. "192.168.0.10"). Requires Admin rights. Changes take effect
immediately — the Telnet session may need to reconnect on the new IP.

## Safety Notes

- EndSession disconnects ALL member stations immediately — coordinate before use
- TakeControl during a live show transfers output control to your station — warn operators
- SetIP may interrupt the active Telnet connection if the local IP changes
- DropControl before leaving a session to avoid leaving other stations without control

## System Variables

| Variable | Value |
|----------|-------|
| $SESSION | Current session name, or "(none)" if not in a session |
| $CONTROLHOLDER | Name of the station currently holding Control |

## Network Details

- MA-Net2 runs on UDP port 6549 by default
- Maximum 8 stations per MA-Net2 session
- All stations must run compatible grandMA2 software versions
"""


# ============================================================
# P6 — Prompts (program_effect, build_timecode_show)
# ============================================================


@mcp.prompt()
def program_effect(
    fixture_group: str,
    effect_type: str,
    speed_bpm: float = 60.0,
) -> str:
    """
    Guided effect programming on a fixture group (SAFE_WRITE workflow).

    Generates a step-by-step plan to create an effect in the programmer,
    apply it to a fixture group, and store it in a cue.

    Args:
        fixture_group: Group number or name to apply the effect to
                       (e.g. "5" or "All Movers").
        effect_type: Type of effect — "dimmer", "color", "position", "gobo", or "custom".
        speed_bpm: Effect speed in BPM (default 60 = 1 Hz).
    """
    preset_type_map = {
        "dimmer": "Dimmer (PresetType 1)",
        "color": "Color (PresetType 4)",
        "position": "Position (PresetType 2)",
        "gobo": "Gobo (PresetType 3)",
        "custom": "custom attribute (set manually)",
    }
    preset_hint = preset_type_map.get(effect_type.lower(), f"{effect_type} (set manually)")

    return f"""Program a {effect_type} effect on fixture group {fixture_group} at {speed_bpm} BPM.

## Pre-flight

1. Call list_system_variables() — confirm $USERRIGHTS has Programmer or higher.
2. Call query_object_list for Group — verify Group {fixture_group} exists.

## Select fixtures

3. Call select_group(group_id={fixture_group!r}) to select the target fixtures.
   Confirm $SELECTEDFIXTURESCOUNT > 0.

## Enter effect in programmer

4. In the Effect programmer, set the following parameters using set_effect_param():
   - param="bpm", value={speed_bpm}   → sets speed to {speed_bpm} BPM
   - param="high", value=100          → full high value
   - param="low", value=0             → zero low value
   - param="phase", value=0           → start phase (fan across fixtures for wave look)
   - param="width", value=50          → 50% duty cycle

5. Effect type: {preset_hint}
   - For dimmer: use EffectBPM on the Dim attribute — produces a chase/strobe.
   - For color: use set_effect_param on a color attribute (e.g. ColorRgb1).
   - For position: use on Pan and Tilt simultaneously with phase offset.
   - For custom: set the attribute first via attribute_at(), then apply effect params.

## Phase stagger (optional, for wave look)

6. To fan the phase across fixtures:
   - Open the programmer and select the Phase column.
   - Enter "0 Thru 359" to distribute phase 0°–359° across all selected fixtures.
   This creates a chasing wave effect rather than all fixtures firing together.

## Store

7. Review the programmer content: call list_system_variables() to confirm fixture count.
8. Call store_current_cue() or store_cue(sequence_id, cue_number, confirm_destructive=True)
   to record the effect.

## Verify

9. Trigger the cue and observe the effect running.
   Call set_effect_param("bpm", {speed_bpm}) again if speed needs adjustment live.

## Notes

- Effects only run on fixtures that had programmer values when stored.
- Use filter_fixture_selection("programmer") to confirm which fixtures are programmed.
- EffectBPM and EffectHZ are mutually exclusive speed modes.
"""


@mcp.prompt()
def build_timecode_show(
    sequence_ids: str,
    smpte_start: str = "00:00:00:00",
) -> str:
    """
    Guided SMPTE timecode show builder — map sequences to timecode triggers.

    Generates a step-by-step plan for creating a timecode track and
    mapping cue triggers to SMPTE positions.

    Args:
        sequence_ids: Comma-separated sequence IDs to include in the show
                      (e.g. "1,2,3" or "1").
        smpte_start: SMPTE start address for the first cue trigger
                     (format HH:MM:SS:FF, default "00:00:00:00").
    """
    seq_list = [s.strip() for s in sequence_ids.split(",") if s.strip()]
    seq_display = ", ".join(f"Sequence {s}" for s in seq_list) if seq_list else "(none specified)"

    return f"""Build a SMPTE timecode show mapping sequences to cue triggers.

Sequences: {seq_display}
Starting SMPTE position: {smpte_start}

## Pre-flight

1. Call list_system_variables() — confirm $USERRIGHTS has Programmer or higher.
2. Call query_object_list for Timecode — list existing timecode pool objects.
   Choose a free slot (e.g. Timecode 1 if empty).
3. Confirm all target sequences exist:
   For each sequence ID in [{', '.join(seq_list) if seq_list else 'none'}]:
   - Call query_object_list for Sequence and verify the ID is present.
   - Call list_cue(sequence_id) to record the cue numbers.

## Create the timecode pool object

4. Call store_timecode(timecode_id=1, confirm_destructive=True) to create Timecode 1.
   (Or use the next free slot identified in step 2.)

## Map cue triggers to SMPTE positions

5. For each cue across all sequences, calculate the SMPTE trigger time.
   Starting from {smpte_start}, add the expected cue duration to each successive position.

6. Store each trigger using store_timecode_event():
   Example mapping:
   - {smpte_start} → Go Executor 1.201  (first cue of {seq_list[0] if seq_list else 'Sequence 1'})
   - 00:00:XX:00   → Go Executor 1.202  (second cue)
   Continue for all cues across all sequences.

## Configure playback

7. Assign the timecode track to a playback executor if using external LTC input.
8. Test with internal clock first:
   - Call control_timecode(action="goto", timecode_id=1, position="{smpte_start}") to reset.
   - Call control_timecode(action="go", timecode_id=1) to start.
   - Observe that cues fire at the expected SMPTE positions.

## Verify

9. Check each executor fires at the correct time.
10. If timing drifts, adjust the SMPTE positions and re-store the affected events.

## Notes

- SMPTE frame rate must match your timecode source — check Setup → Console → Timecode.
- For live LTC input, switch the timecode source AFTER testing with internal clock.
- Use page-qualified executor addresses (e.g. Executor 1.201) for reliable targeting.
- Oops is available if timecode events are stored incorrectly.
"""


# ============================================================
# Server Startup
# ============================================================

_VALID_TRANSPORTS = ("stdio", "sse", "streamable-http")


_LOOPBACK_ADDRESSES = frozenset({"127.0.0.1", "::1", "localhost"})


def _validate_license_tiers() -> None:
    """Warn about tools that look destructive but are not in TOOL_LICENSE_TIERS.

    Tools not in the map default to COMMUNITY (free tier). This check
    flags tools whose names suggest they should be gated but are missing
    from the map — catching typos and oversight.
    """
    from src.license_tiers import TOOL_LICENSE_TIERS

    _DESTRUCTIVE_HINTS = {"store", "delete", "copy", "move", "assign",
                          "import", "export", "create", "remove"}
    try:
        for tool_name in mcp._tool_manager._tools:
            if tool_name not in TOOL_LICENSE_TIERS and any(
                hint in tool_name for hint in _DESTRUCTIVE_HINTS
            ):
                    logger.warning(
                        "Tool '%s' looks destructive but is not in "
                        "TOOL_LICENSE_TIERS (defaulting to COMMUNITY).",
                        tool_name,
                    )
    except Exception:
        pass  # mcp._tool_manager may not be initialized during tests


def _check_network_security() -> None:
    """Emit startup warnings for insecure network configurations.

    Checks three conditions (non-fatal — all warnings, not errors):
    1. GMA_HOST is not loopback → Telnet credentials travel in cleartext
       over the network; the 3-layer permission model can be bypassed by
       anyone who can reach port 30000 directly.
    2. Any security-bypass env var is enabled → an entire permission layer
       is disabled.
    3. Factory-default credentials are still in use.
    """
    # --- Remote host check ---
    if _GMA_HOST not in _LOOPBACK_ADDRESSES:
        logger.warning(
            "GMA_HOST=%s is not loopback. Telnet credentials travel in "
            "cleartext and port %d is reachable from the network — the "
            "OAuth/rights/license permission layers can be bypassed by "
            "anyone with direct network access. See "
            "doc/network-topology.md for the recommended co-located "
            "deployment.",
            _GMA_HOST, _GMA_PORT,
        )

    # --- Bypass env var check ---
    _bypass_vars = {
        "GMA_AUTH_BYPASS": "OAuth scope enforcement",
        "GMA_RIGHTS_BYPASS": "MA2 native rights enforcement",
        "GMA_LICENSE_BYPASS": "license tier gating",
    }
    for var, description in _bypass_vars.items():
        if os.getenv(var, "0") == "1":
            logger.warning(
                "%s=1 — %s is DISABLED. Do not use in production.", var, description,
            )

    # --- Factory-default credential check ---
    if _GMA_USER == "administrator" and _GMA_PASSWORD == "admin":
        logger.warning(
            "Using factory-default credentials (administrator/admin). "
            "Set GMA_USER and GMA_PASSWORD environment variables for "
            "network deployments."
        )

    # --- License tier coverage check ---
    _validate_license_tiers()


def main():
    """MCP Server entry point."""
    logger.info("Starting grandMA2 MCP Server...")
    logger.info(f"Connecting to grandMA2: {_GMA_HOST}:{_GMA_PORT}")

    _check_network_security()

    # Select transport from environment (default: stdio for Claude Code / Claude Desktop)
    transport = os.environ.get("GMA_TRANSPORT", "stdio").lower()
    if transport not in _VALID_TRANSPORTS:
        raise ValueError(
            f"Invalid GMA_TRANSPORT={transport!r}. "
            f"Valid options: {', '.join(_VALID_TRANSPORTS)}"
        )

    if transport != "stdio":
        logger.warning(
            "HTTP transport (%s) has no built-in authentication. "
            "Only use on trusted local networks.", transport,
        )

    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
