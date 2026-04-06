# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
Tool-to-license-tier mapping for feature gating.

Each entry maps a tool *function name* (as registered with ``@mcp.tool()``)
to the minimum ``LicenseTier`` required to invoke it.

Tools **not listed** here default to ``LicenseTier.COMMUNITY`` (free tier).
This keeps the map compact: only PROFESSIONAL and ENTERPRISE tools are explicit.

Maintenance:
    When adding a new MCP tool, decide its tier and add an entry here if it
    is not COMMUNITY.  The ``_handle_errors`` decorator in ``src/server.py``
    reads this map at decoration time — no per-tool decorator changes needed.
"""

from __future__ import annotations

from src.license import LicenseTier

# Shorthand aliases to keep the map readable.
PRO = LicenseTier.PROFESSIONAL
ENT = LicenseTier.ENTERPRISE

# ---------------------------------------------------------------------------
# Tool function name  ->  minimum license tier
# ---------------------------------------------------------------------------
# COMMUNITY tools (free) are NOT listed — absence = COMMUNITY.
# ---------------------------------------------------------------------------

TOOL_LICENSE_TIERS: dict[str, LicenseTier] = {
    # =======================================================================
    # PROFESSIONAL tier — programming, store, presets, sequences, macros,
    # effects, assignment, patch, show management, user management, color,
    # variables, import/export
    # =======================================================================

    # --- Store / Copy / Delete / Move (DESTRUCTIVE) -----------------------
    "create_fixture_group": PRO,
    "store_current_cue": PRO,
    "store_new_preset": PRO,
    "store_object": PRO,
    "copy_or_move_object": PRO,
    "delete_object": PRO,
    "remove_content": PRO,
    "cut_paste_object": PRO,
    "clone_object": PRO,
    "store_cue_with_timing": PRO,
    "store_matricks_preset": PRO,
    "store_timecode_event": PRO,
    "store_world": PRO,
    "store_agenda": PRO,
    "update_object": PRO,

    # --- Assignment -------------------------------------------------------
    "assign_object": PRO,
    "assign_cue_trigger": PRO,
    "assign_executor_property": PRO,
    "set_executor_priority": PRO,
    "assign_temp_fader": PRO,
    "assign_effect_to_executor": PRO,
    "assign_world_to_user_profile": PRO,

    # --- Edit / Label / Appearance ----------------------------------------
    "edit_object": PRO,
    "label_or_appearance": PRO,
    "label_world": PRO,
    "set_node_property": PRO,
    # --- Sequence / Cue management ----------------------------------------
    "update_cue_data": PRO,
    "set_cue_timing": PRO,
    "set_sequence_property": PRO,
    "block_unblock_cue": PRO,
    "load_cue": PRO,

    # --- Selection / Fixture manipulation ---------------------------------
    "select_fixtures_by_group": PRO,
    "modify_selection": PRO,
    "manipulate_selection": PRO,
    "apply_preset": PRO,
    "adjust_value_relative": PRO,
    "fix_locate_fixture": PRO,
    "park_fixture": PRO,
    "unpark_fixture": PRO,
    "highlight_fixtures": PRO,
    "remove_from_programmer": PRO,
    "filter_fixture_selection": PRO,
    "set_advanced_timing": PRO,

    # --- Macro / Variable / Scripting -------------------------------------
    "run_macro": PRO,
    "manage_variable": PRO,
    "programming_action": PRO,

    # --- Effects / MAtricks -----------------------------------------------
    "manage_matricks": PRO,
    "modulate_effect": PRO,
    "set_effect_param": PRO,
    "clear_effects_on_page": PRO,

    # --- Executor / Playback (advanced) -----------------------------------
    "control_executor": PRO,
    "set_executor_level": PRO,
    "select_executor": PRO,
    "normalize_page_faders": PRO,
    "master_control": PRO,
    "control_chaser": PRO,
    "control_special_master": PRO,
    "preview_executor_content": PRO,

    # --- Page / Feature / PresetType navigation ---------------------------
    "navigate_page": PRO,
    "select_feature": PRO,
    "select_preset_type": PRO,
    "browse_preset_type": PRO,

    # --- Timecode / Timer -------------------------------------------------
    "control_timecode": PRO,
    "control_timer": PRO,

    # --- Console mode / Undo ----------------------------------------------
    "toggle_console_mode": PRO,
    "undo_last_action": PRO,

    # --- Patch / Fixture types --------------------------------------------
    "patch_fixture": PRO,
    "unpatch_fixture": PRO,
    "set_fixture_type_property": PRO,
    "remap_fixture_ids": PRO,

    # --- Show management --------------------------------------------------
    "save_show": PRO,
    "load_show": PRO,
    "new_show": PRO,
    "list_shows": PRO,
    "delete_show": PRO,

    # --- Import / Export --------------------------------------------------
    "export_objects": PRO,
    "import_objects": PRO,
    "import_fixture_type": PRO,
    "import_fixture_layer": PRO,
    "generate_fixture_layer_xml": PRO,

    # --- View / Layout ----------------------------------------------------
    "save_recall_view": PRO,

    # --- User management --------------------------------------------------
    "list_console_users": PRO,
    "create_console_user": PRO,
    "delete_user": PRO,
    "console_login": PRO,
    "console_logout": PRO,
    "lock_console_ui": PRO,
    "unlock_console_ui": PRO,
    "inspect_sessions": PRO,

    # --- Listing (specialised pool/object listings) -----------------------
    "list_preset_pool": PRO,
    "list_sequence_cues": PRO,
    "list_fixtures": PRO,
    "list_fixture_types": PRO,
    "list_layers": PRO,
    "list_universes": PRO,
    "list_library": PRO,
    "list_undo_history": PRO,
    "list_fader_modules": PRO,
    "list_update_history": PRO,
    "list_layouts": PRO,
    "list_worlds": PRO,
    "list_timers": PRO,
    "list_filters": PRO,
    "list_effects_pool": PRO,
    "list_images": PRO,
    "list_forms": PRO,
    "list_timecode_events": PRO,
    "list_agenda_events": PRO,

    # --- Blackout / DMX ---------------------------------------------------
    "blackout_toggle": PRO,
    "detect_dmx_address_conflicts": PRO,
    "browse_patch_schedule": PRO,
    "check_pool_availability": PRO,

    # --- System admin (console-level) -------------------------------------
    "system_admin": PRO,

    # --- RDM --------------------------------------------------------------
    "rdm_discover": PRO,
    "rdm_get_info": PRO,
    "rdm_patch": PRO,

    # --- Plugin / Lua -----------------------------------------------------
    "call_plugin_tool": PRO,
    "run_lua_script": PRO,
    "reload_all_plugins": PRO,
    "plugin_management": PRO,

    # --- Browse libraries -------------------------------------------------
    "browse_effect_library": PRO,
    "browse_macro_library": PRO,
    "browse_plugin_library": PRO,

    # --- Filter discovery -------------------------------------------------
    "discover_filter_attributes": PRO,

    # =======================================================================
    # ENTERPRISE tier — RAG search, orchestration, skill system, telemetry,
    # session memory, console state hydration, agent harness, batch/library
    # generation, ML categorisation
    # =======================================================================

    # --- RAG / Semantic search --------------------------------------------
    "search_codebase": ENT,

    # --- Orchestration (server.py) ----------------------------------------
    "scan_console_indexes": ENT,
    "classify_show_mode": ENT,
    "get_telemetry_report": ENT,
    "generate_compliance_report": ENT,
    "validate_preset_references": ENT,
    "list_macro_jump_targets": ENT,
    "check_pool_slot_availability": ENT,

    # --- Agent harness (server.py) ----------------------------------------
    "run_agent_goal": ENT,
    "plan_agent_goal": ENT,

    # --- PSR (Partial Show Read) ------------------------------------------
    "prepare_partial_show_read": ENT,
    "list_psr_objects": ENT,
    "partial_show_read": ENT,

    # --- ML tool categorisation -------------------------------------------
    "list_tool_categories": ENT,
    "recluster_tools": ENT,
    "get_similar_tools": ENT,
    "suggest_tool_for_task": ENT,

    # --- Library generation (batch) ---------------------------------------
    "create_matricks_library": ENT,
    "create_filter_library": ENT,

    # --- Orchestration tools (server_orchestration_tools.py) --------------
    "decompose_task": ENT,
    "run_task": ENT,
    "list_agent_sessions": ENT,
    "recall_agent_session": ENT,
    "agent_token_report": ENT,
    "register_decomposition_rule": ENT,
    "resolve_object_ref": ENT,
    "list_pool_names": ENT,
    "hydrate_console_state": ENT,

    # --- Console state snapshot reads -------------------------------------
    "get_console_state": ENT,
    "get_park_ledger": ENT,
    "get_filter_state": ENT,
    "get_world_state": ENT,
    "get_matricks_state": ENT,
    "get_programmer_selection": ENT,
    "hydrate_sequences": ENT,
    "get_sequence_memory": ENT,
    "assert_selection_count": ENT,
    "assert_preset_exists": ENT,
    "get_executor_detail": ENT,

    # --- State diff / showfile / variable polling -------------------------
    "diff_console_state": ENT,
    "get_showfile_info": ENT,
    "watch_system_var": ENT,

    # --- Safety gates -----------------------------------------------------
    "confirm_destructive_steps": ENT,
    "abort_task": ENT,
    "retry_failed_steps": ENT,
    "assert_fixture_exists": ENT,
    "assert_showfile_unchanged": ENT,

    # --- Skill system (OpenSpace) -----------------------------------------
    "get_tool_metrics": ENT,
    "list_skills": ENT,
    "get_skill": ENT,
    "promote_session_to_skill": ENT,
    "get_improvement_suggestions": ENT,
    "approve_skill": ENT,
}
