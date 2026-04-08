# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
tools_professional.py -- All 124 PROFESSIONAL-tier MCP tool functions.

These tools require a PROFESSIONAL license tier and will move to the
private submodule after the git submodule split.

Imports the shared ``mcp`` FastMCP instance and ``_handle_errors`` decorator
from ``server_core.py`` so tools register on the same server.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import UTC

import src.server_core as _sc
from src.auth import OAuthScope, has_scope, require_scope
from src.commands import (
    SPECIAL_MASTER_NAMES,
    build_assign_world_to_user_profile,
    build_delete_user,
    build_list_users,
    build_store_user,
    call,
    go_macro,
    label_group,
    select_fixture,
    store_group,
)
from src.commands import add_to_selection as build_add_to_selection
from src.commands import add_user_var as build_add_user_var
from src.commands import add_var as build_add_var
from src.commands import align as build_align
from src.commands import appearance as build_appearance
from src.commands import assign as build_assign
from src.commands import assign_delay as build_assign_delay
from src.commands import assign_effect_to_executor as build_assign_effect_to_executor
from src.commands import assign_fade as build_assign_fade
from src.commands import assign_function as build_assign_function
from src.commands import assign_to_layout as build_assign_to_layout
from src.commands import at_relative as build_at_relative
from src.commands import blackout as build_blackout
from src.commands import blind_edit as build_blind_edit
from src.commands import block as build_block
from src.commands import block_cue as build_block_cue
from src.commands import build_login as build_console_login
from src.commands import build_logout as build_console_logout
from src.commands import call_plugin as build_call_plugin
from src.commands import chaser_rate as build_chaser_rate
from src.commands import chaser_skip as build_chaser_skip
from src.commands import chaser_speed as build_chaser_speed
from src.commands import chaser_xfade as build_chaser_xfade
from src.commands import clear_selection as build_clear_selection
from src.commands import clone as build_clone
from src.commands import copy as build_copy
from src.commands import cut as build_cut
from src.commands import delete as build_delete
from src.commands import delete_cue as build_delete_cue
from src.commands import delete_fixture as build_delete_fixture
from src.commands import delete_show as build_delete_show
from src.commands import edit as build_edit
from src.commands import executor_at as build_executor_at
from src.commands import export_object as build_export_object
from src.commands import extract as build_extract
from src.commands import fade_path as build_fade_path
from src.commands import fix_fixture as build_fix_fixture
from src.commands import flash_executor as build_flash_executor
from src.commands import flash_go as build_flash_go
from src.commands import flash_on as build_flash_on
from src.commands import flip as build_flip
from src.commands import full_highlight as build_full_highlight
from src.commands import goto_timecode as build_goto_timecode
from src.commands import highlight as build_highlight
from src.commands import if_active as build_if_active
from src.commands import if_output as build_if_output
from src.commands import if_prog as build_if_prog
from src.commands import import_fixture_type_cmd as build_import_fixture_type_cmd
from src.commands import import_layer_cmd as build_import_layer_cmd
from src.commands import import_object as build_import_object
from src.commands import invert as build_invert
from src.commands import label as build_label
from src.commands import label_preset as build_label_preset
from src.commands import learn_executor as build_learn_executor
from src.commands import list_effect_library as build_list_effect_library
from src.commands import list_fader_modules as build_list_fader_modules
from src.commands import list_library as build_list_library
from src.commands import list_macro_library as build_list_macro_library
from src.commands import list_masters as build_list_masters
from src.commands import list_objects as build_list_objects
from src.commands import list_oops as build_list_oops
from src.commands import list_plugin_library as build_list_plugin_library
from src.commands import list_plugin_library as build_list_plugins
from src.commands import list_shows as build_list_shows
from src.commands import list_update as build_list_update
from src.commands import list_user_var as build_list_user_var
from src.commands import list_var as build_list_var
from src.commands import load_next as build_load_next
from src.commands import load_prev as build_load_prev
from src.commands import load_show as build_load_show
from src.commands import locate as build_locate
from src.commands import lock_console as build_lock
from src.commands import lock_console as build_lock_console
from src.commands import lua_execute as build_lua
from src.commands import manual_xfade as build_manual_xfade
from src.commands import master_at as build_master_at
from src.commands import move as build_move
from src.commands import new_show as build_new_show
from src.commands import off_executor as build_off_executor
from src.commands import on_executor as build_on_executor
from src.commands import out_delay as build_out_delay
from src.commands import out_fade as build_out_fade
from src.commands import page_next as build_page_next
from src.commands import page_previous as build_page_previous
from src.commands import park as build_park
from src.commands import paste as build_paste
from src.commands import preview as build_preview
from src.commands import preview_edit as build_preview_edit
from src.commands import preview_executor as build_preview_executor
from src.commands import rdm_automatch as build_rdm_automatch
from src.commands import rdm_autopatch as build_rdm_autopatch
from src.commands import rdm_info as build_rdm_info
from src.commands import rdm_list as build_rdm_list
from src.commands import rdm_setpatch as build_rdm_setpatch
from src.commands import rdm_unmatch as build_rdm_unmatch
from src.commands import reboot_console as build_reboot
from src.commands import record_macro as build_record_macro
from src.commands import release_effects_on_page as build_release_effects_on_page
from src.commands import reload_plugins as build_reload_plugins
from src.commands import remove as build_remove
from src.commands import remove_effect as build_remove_effect
from src.commands import remove_fixture as build_remove_fixture
from src.commands import remove_from_selection as build_remove_from_selection
from src.commands import remove_preset_type as build_remove_preset_type
from src.commands import remove_selection as build_remove_selection
from src.commands import restart_console as build_restart
from src.commands import run_lua as build_run_lua
from src.commands import send_chat as build_chat
from src.commands import set_effect_parameter as build_set_effect_parameter
from src.commands import set_effect_rate as build_set_effect_rate
from src.commands import set_effect_speed as build_set_effect_speed
from src.commands import set_special_master as build_set_special_master
from src.commands import set_user_var as build_set_user_var
from src.commands import set_var as build_set_var
from src.commands import shuffle_selection as build_shuffle_selection
from src.commands import shuffle_values as build_shuffle_values
from src.commands import shutdown_console as build_shutdown
from src.commands import snap_percent as build_snap_percent
from src.commands import solo_executor as build_solo_executor
from src.commands import special_master_at as build_special_master_at
from src.commands import step_fade as build_step_fade
from src.commands import step_in_fade as build_step_in_fade
from src.commands import step_out_fade as build_step_out_fade
from src.commands import stomp_executor as build_stomp_executor
from src.commands import store as build_store_generic
from src.commands import store_cue as build_store_cue
from src.commands import store_cue_timed as build_store_cue_timed
from src.commands import store_look as build_store_look
from src.commands import store_preset as build_store_preset
from src.commands import swop_executor as build_swop_executor
from src.commands import swop_go as build_swop_go
from src.commands import swop_on as build_swop_on
from src.commands import temp_fader as build_temp_fader
from src.commands import top_executor as build_top_executor
from src.commands import unblock as build_unblock
from src.commands import unblock_cue as build_unblock_cue
from src.commands import unlock_console as build_unlock
from src.commands import unlock_console as build_unlock_console
from src.commands import unpark as build_unpark
from src.commands import update as build_update
from src.commands import update_cue as build_update_cue
from src.commands import zero_page_faders as build_zero_page_faders
from src.navigation import list_destination, navigate, set_property
from src.server_core import (
    _check_pool_slots,
    _get_sequence_for_executor,
    _get_session_manager,
    _handle_errors,
    _parse_listvar,
    _parse_preset_tree_list,
    _validate_object_exists,
    mcp,
)

logger = logging.getLogger(__name__)

# Re-export for test discoverability (tools use _sc.get_client() for late binding)
get_client = _sc.get_client


def _get_orchestrator():
    """Lazy accessor for the Orchestrator singleton in server.py.

    Avoids circular import: server.py creates _orchestrator after importing
    this module.
    """
    import src.server as _srv
    return _srv._orchestrator


class _OrchestratorProxy:
    """Attribute proxy that defers to the server's _orchestrator at access time."""
    def __getattr__(self, name):
        return getattr(_get_orchestrator(), name)


_orchestrator = _OrchestratorProxy()


# ---------------------------------------------------------------------------
# Constants used by professional tools
# ---------------------------------------------------------------------------

_EXPORT_TYPES = {
    "group", "preset", "macro", "effect", "sequence", "view", "page",
    "camera", "layout", "form", "plugin", "matricks", "mask", "image",
    "executor", "timecode", "userprofile", "channel", "screen", "filter",
}

_IMPORT_TYPES = {
    "group", "preset", "macro", "effect", "sequence", "view", "page",
    "camera", "layout", "form", "plugin", "matricks", "mask", "image",
    "executor", "timecode", "userprofile", "filter",
}

_FIXTURE_FILTER_MAP = {
    "active": build_if_active,
    "output": build_if_output,
    "programmer": build_if_prog,
}

_VALID_TIMING_ACTIONS = frozenset({
    "fade_path", "out_fade", "out_delay",
    "step_fade", "step_in_fade", "step_out_fade",
    "snap_percent",
})

_IMPORT_EXPORT_DATA_ROOT = (
    r"C:\ProgramData\MA Lighting Technologies\grandma\gma2_V_3.9.60\importexport"
)


# ============================================================


@mcp.tool()
@require_scope(OAuthScope.GROUP_STORE)
@_handle_errors
async def create_fixture_group(
    start_fixture: int,
    end_fixture: int,
    group_id: int,
    group_name: str | None = None,
    confirm_destructive: bool = False,
) -> str:
    """
    Create a group containing a specified range of fixtures (DESTRUCTIVE).

    This tool selects the specified range of fixtures and saves them as a group.
    Optionally, a name can be assigned to the group.

    Args:
        start_fixture: Starting fixture number
        end_fixture: Ending fixture number
        group_id: Group number to save
        group_name: (Optional) Group name, e.g., "Front Wash"
        confirm_destructive: Must be True to execute (DESTRUCTIVE operation)

    Returns:
        str: Operation result message

    Examples:
        - Save fixtures 1 to 10 as group 1
        - Save fixtures 1 to 10 as group 1 with name "Front Wash"
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "Create Fixture Group uses Store (DESTRUCTIVE). Pass confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    client = await _sc.get_client()

    # Select fixtures
    select_cmd = select_fixture(start_fixture, end_fixture)
    await client.send_command(select_cmd)

    # Save as group
    store_cmd = store_group(group_id)
    await client.send_command(store_cmd)

    # Add label if name is provided
    if group_name:
        label_cmd = label_group(group_id, group_name)
        await client.send_command(label_cmd)
        return f'Created Group {group_id} "{group_name}" containing Fixtures {start_fixture} to {end_fixture}'

    return (
        f"Created Group {group_id} containing Fixtures {start_fixture} to {end_fixture}"
    )


@mcp.tool()
@require_scope(OAuthScope.SETUP_CONSOLE)
@_handle_errors
async def set_node_property(
    path: str,
    property_name: str,
    value: str,
    verify: bool = True,
    confirm_destructive: bool = False,
) -> str:
    """
    Set a property on a node in the grandMA2 object tree (DESTRUCTIVE).

    Uses the scan tree path notation (dot-separated indexes) to navigate
    to a node and set an inline property using Assign [index]/property=value.

    The path uses the same index-based notation as the scan tree output.
    Split the path into parent segments and target index:
    - "3.1" → cd 3 (Settings), then Assign 1/property=value (on Global)
    - "4.1" → cd 4 (DMX_Protocols), then Assign 1/property=value (on Art-Net)
    - "3" → at root, Assign 3/property=value (on Settings itself)

    After setting, navigates back to root (cd /).
    If verify=True (default), re-lists and confirms the property changed.

    SAFETY: This modifies live console state. Requires confirm_destructive=True.

    Args:
        path: Dot-separated index path (e.g. "3.1" for Settings/Global)
        property_name: Property to set (e.g. "Telnet", "OutActive")
        value: New value (e.g. "Login Enabled", "On")
        verify: Re-list after setting to confirm the change (default True)
        confirm_destructive: Must be True to execute (DESTRUCTIVE operation)

    Returns:
        str: JSON with commands_sent, success, verified_value, and any errors.

    Examples:
        - Set telnet to disabled: path="3.1", property_name="Telnet", value="Login Disabled"
        - Enable Art-Net output: path="4.1", property_name="OutActive", value="On"
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "Set Node Property uses Assign (DESTRUCTIVE). Pass confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    client = await _sc.get_client()
    result = await set_property(
        client,
        path,
        property_name,
        value,
        verify=verify,
    )

    return json.dumps(
        {
            "path": result.path,
            "property_name": property_name,
            "value": value,
            "commands_sent": result.commands_sent,
            "success": result.success,
            "verified_value": result.verified_value,
            "error": result.error,
        },
        indent=2,
    )


@mcp.tool()
@require_scope(OAuthScope.PROGRAMMER_WRITE)
@_handle_errors
async def apply_preset(
    preset_type: str,
    preset_id: int,
    fixture_id: int | None = None,
    fixture_end: int | None = None,
    group_id: int | None = None,
) -> str:
    """
    Apply a preset to fixtures or groups.

    Presets are stored lighting looks (color, position, gobo, etc.) that
    can be recalled by type and ID. Optionally select fixtures/group first.

    Preset types: "dimmer" (1), "position" (2), "gobo" (3), "color" (4),
    "beam" (5), "focus" (6), "control" (7), "shapers" (8), "video" (9)

    Args:
        preset_type: Preset type name or number (e.g. "color", "position", "4")
        preset_id: Preset number within that type
        fixture_id: Optional fixture to select first (single or range start)
        fixture_end: Optional end fixture for range selection
        group_id: Optional group to select first (alternative to fixture_id)

    Returns:
        str: JSON with commands_sent and raw_response.

    Examples:
        - Apply color preset 3 to current selection: preset_type="color", preset_id=3
        - Apply position preset 1 to group 2: preset_type="position", preset_id=1, group_id=2
        - Apply gobo preset 5 to fixtures 1-10: preset_type="gobo", preset_id=5, fixture_id=1, fixture_end=10
    """
    commands_sent = []
    client = await _sc.get_client()

    # Optionally select fixtures or group first
    if group_id is not None:
        sel_cmd = f"group {group_id}"
        await client.send_command_with_response(sel_cmd)
        commands_sent.append(sel_cmd)
    elif fixture_id is not None:
        sel_cmd = select_fixture(fixture_id, fixture_end)
        await client.send_command_with_response(sel_cmd)
        commands_sent.append(sel_cmd)

    # Build the preset type reference
    preset_type_str = preset_type.lower()
    # Map common names to numbers for the call syntax
    type_map = {
        "dimmer": "1", "position": "2", "gobo": "3", "color": "4",
        "beam": "5", "focus": "6", "control": "7", "shapers": "8", "video": "9",
    }
    type_num = type_map.get(preset_type_str, preset_type_str)

    call_cmd = call(f"preset {type_num}.{preset_id}")
    raw_response = await client.send_command_with_response(call_cmd)
    commands_sent.append(call_cmd)

    return json.dumps({
        "commands_sent": commands_sent,
        "raw_response": raw_response,
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.CUE_STORE)
@_handle_errors
async def store_current_cue(
    cue_number: int,
    sequence_id: int | None = None,
    label: str | None = None,
    merge: bool = False,
    overwrite: bool = False,
    confirm_destructive: bool = False,
) -> str:
    """
    Store the current programmer state as a cue (DESTRUCTIVE).

    Saves whatever is currently in the programmer (selected fixtures +
    active values) into a cue in the specified sequence. This is how
    lighting looks are programmed into a show.

    Executor-sequence relationship:
      When sequence_id is omitted, MA2 stores into the sequence assigned to
      the currently selected executor on the console. Use select_executor()
      first to set the target, or pass sequence_id explicitly to make the
      destination unambiguous regardless of executor selection state.

      select executor N      → sets executor N as the active store target
      Store Cue M            → stores into the sequence on selected executor
      Store Cue M Sequence S → stores into sequence S directly (preferred)

    Args:
        cue_number: Cue number to store (required)
        sequence_id: Sequence to store into. Omit to use the selected executor's
                     sequence (call select_executor() first if needed)
        label: Optional name for the cue
        merge: Merge new values into existing cue (default False)
        overwrite: Replace existing cue completely (default False)
        confirm_destructive: Must be True to execute (DESTRUCTIVE operation)

    Returns:
        str: JSON with commands_sent and raw_response.

    Examples:
        - Store cue 5 (explicit sequence): cue_number=5, sequence_id=1, confirm_destructive=True
        - Store cue 3 named "Opening Look": cue_number=3, label="Opening Look", confirm_destructive=True
        - Merge into cue 1: cue_number=1, merge=True, confirm_destructive=True
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": (
                "Store Cue is a DESTRUCTIVE operation. Pass confirm_destructive=True to proceed. "
                "Tip: pass sequence_id explicitly to target a specific sequence rather than relying "
                "on the currently selected executor."
            ),
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    commands_sent = []
    client = await _sc.get_client()

    # Build store cue command
    store_cmd = build_store_cue(
        cue_id=cue_number,
        sequence_id=sequence_id,
        merge=merge,
        overwrite=overwrite,
    )

    raw_response = await client.send_command_with_response(store_cmd)
    commands_sent.append(store_cmd)

    # Optionally label the cue
    if label and cue_number is not None:
        cue_ref = str(cue_number)
        if sequence_id is not None:
            cue_ref += f" sequence {sequence_id}"
        label_cmd = build_label("cue", cue_ref, label)
        await client.send_command_with_response(label_cmd)
        commands_sent.append(label_cmd)

    return json.dumps({
        "commands_sent": commands_sent,
        "raw_response": raw_response,
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PRESET_UPDATE)
@_handle_errors
async def park_fixture(
    target: str,
    value: int | float | None = None,
) -> str:
    """
    Park a fixture or DMX address at its current or specified output value.

    Parking locks the output so it won't change when cues or programmer
    values change. Useful for testing, worklights, or safety overrides.

    Fixture targets are pre-validated: if the fixture does not exist on the
    console, the command is not sent and an informative error is returned.
    DMX targets (e.g. "dmx 101") bypass pre-validation.

    Args:
        target: What to park (e.g. "fixture 20", "dmx 101", "fixture 20 thru 30")
        value: Optional output value to park at (0-255 for DMX, 0-100 for %)

    Returns:
        str: JSON with command_sent (None if blocked), raw_response, exists.

    Examples:
        - Park fixture 20 at current output: target="fixture 20"
        - Park DMX 101 at 128: target="dmx 101", value=128
        - Park fixture range: target="fixture 20 thru 30"
    """
    client = await _sc.get_client()

    fixture_match = re.match(r"^fixture\s+(\d+)", target.strip(), re.IGNORECASE)
    if fixture_match:
        fixture_id = fixture_match.group(1)
        exists, probe_raw = await _validate_object_exists(client, "fixture", fixture_id)
        if not exists:
            return json.dumps({
                "command_sent": None,
                "exists": False,
                "error": f"Fixture {fixture_id} does not exist on the console.",
                "hint": "Use list_fixtures() to discover valid fixture IDs.",
                "probe_response": probe_raw,
                "blocked": True,
            }, indent=2)
        exists_flag: bool | None = True
    else:
        exists_flag = None  # DMX or other — validation skipped

    cmd = build_park(target, at=value)
    raw_response = await client.send_command_with_response(cmd)

    # Sync park ledger to snapshot write-tracker (Gap 3)
    if snap := _orchestrator.last_snapshot:
        snap.parked_fixtures.add(str(target))

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "exists": exists_flag,
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PRESET_UPDATE)
@_handle_errors
async def unpark_fixture(
    target: str,
) -> str:
    """
    Unpark a previously parked fixture or DMX address.

    Fixture targets are pre-validated before unparking. DMX targets bypass
    pre-validation.

    Args:
        target: What to unpark (e.g. "fixture 20", "dmx 101", "fixture 20 thru 30")

    Returns:
        str: JSON with command_sent (None if blocked), raw_response, exists.

    Examples:
        - Unpark fixture 20: target="fixture 20"
        - Unpark DMX 101: target="dmx 101"
    """
    client = await _sc.get_client()

    fixture_match = re.match(r"^fixture\s+(\d+)", target.strip(), re.IGNORECASE)
    if fixture_match:
        fixture_id = fixture_match.group(1)
        exists, probe_raw = await _validate_object_exists(client, "fixture", fixture_id)
        if not exists:
            return json.dumps({
                "command_sent": None,
                "exists": False,
                "error": f"Fixture {fixture_id} does not exist on the console.",
                "hint": "Use list_fixtures() to discover valid fixture IDs.",
                "probe_response": probe_raw,
                "blocked": True,
            }, indent=2)
        exists_flag: bool | None = True
    else:
        exists_flag = None

    cmd = build_unpark(target)
    raw_response = await client.send_command_with_response(cmd)

    # Sync park ledger to snapshot write-tracker (Gap 3)
    if snap := _orchestrator.last_snapshot:
        snap.parked_fixtures.discard(str(target))

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "exists": exists_flag,
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PLAYBACK_GO)
@_handle_errors
async def run_macro(
    macro_id: int,
) -> str:
    """
    Execute a macro by its ID number.

    Macros are stored command sequences on the console. This triggers
    the macro to run.

    Args:
        macro_id: Macro number to execute

    Returns:
        str: JSON with command_sent and raw_response.

    Examples:
        - Run macro 1: macro_id=1
        - Run macro 99: macro_id=99
    """
    client = await _sc.get_client()
    cmd = go_macro(macro_id)
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.CUE_STORE)
@_handle_errors
async def delete_object(
    object_type: str,
    object_id: int | str,
    end_id: int | None = None,
    confirm_destructive: bool = False,
) -> str:
    """
    Delete an object from the show.

    SAFETY: This is a DESTRUCTIVE operation. Requires confirm_destructive=True.

    Args:
        object_type: Object type (e.g. "cue", "group", "preset", "fixture", "macro")
        object_id: Object ID to delete
        end_id: Optional end ID for range deletion (e.g. cue 1 thru 10)
        confirm_destructive: Must be True to execute (safety gate)

    Returns:
        str: JSON with command_sent, raw_response, or block info.

    Examples:
        - Delete cue 5: object_type="cue", object_id=5, confirm_destructive=True
        - Delete cues 1-10: object_type="cue", object_id=1, end_id=10, confirm_destructive=True
        - Delete group 3: object_type="group", object_id=3, confirm_destructive=True
    """
    if not confirm_destructive:
        return json.dumps({
            "command_sent": None,
            "blocked": True,
            "error": "Delete is a DESTRUCTIVE operation. Set confirm_destructive=True to proceed.",
        }, indent=2)

    if object_type.lower() == "cue":
        cmd = build_delete_cue(object_id, end=end_id, noconfirm=True)
    else:
        cmd = build_delete(object_type, object_id, end=end_id, noconfirm=True)

    client = await _sc.get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "blocked": False,
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.CUE_STORE)
@_handle_errors
async def copy_or_move_object(
    action: str,
    object_type: str,
    source_id: int,
    target_id: int,
    source_end: int | None = None,
    overwrite: bool = False,
    merge: bool = False,
    confirm_destructive: bool = False,
) -> str:
    """
    Copy or move an object to a new location (DESTRUCTIVE).

    SAFETY: Both operations modify show data. Copy duplicates the object,
    move relocates it (deleting the original). Requires confirm_destructive=True.

    Args:
        action: "copy" or "move"
        object_type: Object type (e.g. "group", "cue", "preset", "macro")
        source_id: Source object ID
        target_id: Destination object ID
        source_end: Optional end ID for range copy/move
        overwrite: Overwrite target if it exists (default False)
        merge: Merge into target if it exists (default False)
        confirm_destructive: Must be True to execute (DESTRUCTIVE operation)

    Returns:
        str: JSON with command_sent and raw_response.

    Examples:
        - Copy group 1 to 5: action="copy", object_type="group", source_id=1, target_id=5
        - Move macro 3 to 10: action="move", object_type="macro", source_id=3, target_id=10
        - Copy cue range: action="copy", object_type="cue", source_id=1, target_id=20, source_end=10
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "Copy/Move is a DESTRUCTIVE operation. Pass confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    action = action.lower()

    if action == "copy":
        cmd = build_copy(
            object_type, source_id, target_id,
            end=source_end, overwrite=overwrite, merge=merge,
        )
    elif action == "move":
        cmd = build_move(
            object_type, source_id, target_id,
            end=source_end,
        )
    else:
        return json.dumps({
            "error": f"Unknown action: {action}. Use 'copy' or 'move'.",
            "blocked": True,
        }, indent=2)

    client = await _sc.get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PRESET_UPDATE)
@_handle_errors
async def store_new_preset(
    preset_type: str,
    preset_id: int,
    merge: bool = False,
    overwrite: bool = False,
    universal: bool = False,
    selective: bool = False,
    global_scope: bool = False,
    confirm_destructive: bool = False,
) -> str:
    """
    Store the current programmer values as a preset.

    Saves the active fixture values (from the programmer) into a preset
    slot for later recall with apply_preset.

    Preset types: "dimmer" (1), "position" (2), "gobo" (3), "color" (4),
    "beam" (5), "focus" (6), "control" (7), "shapers" (8), "video" (9)

    Scope flags (mutually exclusive — pick at most one):
      universal   — stores values indexed by fixture type (applies to any fixture
                    of the same profile; not tied to specific fixture IDs).
      selective   — stores values tied to the specific fixtures selected during
                    store. Recalled preset only affects those fixture IDs.
      global_scope — stores absolute values (no relative/tracking offset).

    Workflow for universal color presets:
      1. SelFix 1 Thru 999
      2. attribute "ColorRgb1" at 100
      3. store_new_preset("color", 6, universal=True, overwrite=True, confirm_destructive=True)

    SAFETY: This is a STORE operation which modifies show data.

    Args:
        preset_type: Preset type name (e.g. "color", "position", "gobo")
        preset_id: Preset number within that type
        merge: Merge into existing preset (default False)
        overwrite: Replace existing preset with /overwrite flag (default False)
        universal: Store as universal preset — applies to any fixture of the same type
        selective: Store as selective preset — applies only to selected fixture IDs
        global_scope: Store with global (absolute) values
        confirm_destructive: Must be True to execute (DESTRUCTIVE operation)

    Returns:
        str: JSON with command_sent and raw_response.

    Examples:
        - Store universal color preset: preset_type="color", preset_id=6, universal=True, confirm_destructive=True
        - Overwrite position preset 3: preset_type="position", preset_id=3, overwrite=True, confirm_destructive=True
    """
    if not confirm_destructive:
        return json.dumps({
            "error": "Store Preset is a DESTRUCTIVE operation. Pass confirm_destructive=True to proceed."
        }, indent=2)
    client = await _sc.get_client()
    cmd = build_store_preset(
        preset_type, preset_id,
        merge=merge, overwrite=overwrite,
        universal=universal, selective=selective,
        global_scope=global_scope,
    )
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
    }, indent=2)


# ============================================================
# New Composite Tools (Tools 20-27)






@mcp.tool()
@require_scope(OAuthScope.PROGRAMMER_WRITE)
@_handle_errors
async def manage_variable(
    action: str,
    scope: str,
    var_name: str,
    value: int | float | str | None = None,
    input_dialog: bool = False,
) -> str:
    """
    Set, add to, or list console variables (global or user-scoped).

    Variables are named values stored on the console that can be used in
    macros and command line expressions. The $ prefix is automatically
    added to var_name if not already present.

    Args:
        action: "set" to assign a value, "add" to increment, "list" to show all variables
        scope: "global" for system variables, "user" for user-scoped variables
        var_name: Variable name (e.g. "myvar" or "$myvar" — $ auto-added)
        value: Value to set or add. Required for "add", optional for "set",
            ignored for "list"
        input_dialog: If True with action="set", shows an input dialog
            on the console for the user to enter a value

    Returns:
        str: JSON with command_sent and raw_response.

    Examples:
        - Set global var: action="set", scope="global", var_name="myvar", value=42
        - Set user var: action="set", scope="user", var_name="speed", value=100
        - Add to global: action="add", scope="global", var_name="counter", value=1
        - List global vars: action="list", scope="global"
        - List user vars: action="list", scope="user"
    """
    action = action.lower()
    scope = scope.lower()

    # Auto-prepend $ if not present (MA2 syntax requires $variablename)
    if var_name and not var_name.startswith("$"):
        var_name = f"${var_name}"

    if action == "list":
        if scope == "global":
            cmd = build_list_var()
        elif scope == "user":
            cmd = build_list_user_var()
        else:
            return json.dumps({
                "error": f"Unknown scope: {scope}. Use 'global' or 'user'.",
                "blocked": True,
            }, indent=2)
        client = await _sc.get_client()
        raw_response = await client.send_command_with_response(cmd)
        return json.dumps({
            "command_sent": cmd,
            "raw_response": raw_response,
        }, indent=2)

    if action == "set":
        if scope == "global":
            cmd = build_set_var(var_name, value, input_dialog=input_dialog)
        elif scope == "user":
            cmd = build_set_user_var(var_name, value, input_dialog=input_dialog)
        else:
            return json.dumps({
                "error": f"Unknown scope: {scope}. Use 'global' or 'user'.",
                "blocked": True,
            }, indent=2)
    elif action == "add":
        if value is None:
            return json.dumps({
                "error": "add action requires a value.",
                "blocked": True,
            }, indent=2)
        if scope == "global":
            cmd = build_add_var(var_name, value)
        elif scope == "user":
            cmd = build_add_user_var(var_name, value)
        else:
            return json.dumps({
                "error": f"Unknown scope: {scope}. Use 'global' or 'user'.",
                "blocked": True,
            }, indent=2)
    else:
        return json.dumps({
            "error": f"Unknown action: {action}. Use 'set', 'add', or 'list'.",
            "blocked": True,
        }, indent=2)

    client = await _sc.get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.CUE_STORE)
@_handle_errors
async def label_or_appearance(
    action: str,
    object_type: str,
    object_id: int | str,
    name: str | None = None,
    end: int | None = None,
    preset_type: str | None = None,
    confirm_destructive: bool = False,
    color: str | None = None,
    red: int | None = None,
    green: int | None = None,
    blue: int | None = None,
    hue: int | None = None,
    saturation: int | None = None,
    brightness: int | None = None,
    reset: bool = False,
    source_type: str | None = None,
    source_id: int | str | None = None,
) -> str:
    """
    Label or set the appearance of console objects.

    SAFETY: This is a DESTRUCTIVE operation. Requires confirm_destructive=True.

    Args:
        action: "label" to set a name, "appearance" to set visual styling
        object_type: Object type (e.g. "group", "sequence", "cue", "preset")
        object_id: Object ID
        name: Name to assign (required for action="label")
        end: End ID for range labeling (e.g. group 1 thru 5)
        preset_type: For labeling presets, the preset type (e.g. "color", "position").
            When set, uses the specialized label_preset builder.
        confirm_destructive: Must be True to execute (safety gate)
        color: Hex color string for appearance (e.g. "FF0000")
        red: Red component (0-100) for appearance
        green: Green component (0-100) for appearance
        blue: Blue component (0-100) for appearance
        hue: Hue value for appearance
        saturation: Saturation value for appearance
        brightness: Brightness value for appearance
        reset: Reset appearance to default
        source_type: Copy appearance from this object type
        source_id: Copy appearance from this object ID

    Returns:
        str: JSON with command_sent, raw_response, or block info.

    Examples:
        - Label group 3: action="label", object_type="group", object_id=3, name="Front Wash"
        - Label color preset 1: action="label", object_type="preset", object_id=1,
          preset_type="color", name="Red"
        - Set group appearance: action="appearance", object_type="group", object_id=1,
          color="FF0000"
    """
    if not confirm_destructive:
        return json.dumps({
            "command_sent": None,
            "blocked": True,
            "error": "Label/Appearance is a DESTRUCTIVE operation. Set confirm_destructive=True to proceed.",
        }, indent=2)

    action = action.lower()

    if action == "label":
        if name is None:
            return json.dumps({
                "error": "label action requires 'name' to be specified.",
                "blocked": True,
            }, indent=2)
        if preset_type is not None:
            cmd = build_label_preset(preset_type, object_id, name)
        else:
            cmd = build_label(object_type, object_id, name, end=end)
    elif action == "appearance":
        cmd = build_appearance(
            object_type, object_id, end=end,
            source_type=source_type, source_id=source_id,
            reset=reset, color=color,
            red=red, green=green, blue=blue,
            hue=hue, saturation=saturation, brightness=brightness,
        )
    else:
        return json.dumps({
            "error": f"Unknown action: {action}. Use 'label' or 'appearance'.",
            "blocked": True,
        }, indent=2)

    client = await _sc.get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "blocked": False,
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.GROUP_STORE)
@_handle_errors
async def assign_object(
    mode: str,
    confirm_destructive: bool = False,
    source_type: str | None = None,
    source_id: int | str | None = None,
    target_type: str | None = None,
    target_id: int | str | None = None,
    function: str | None = None,
    fade_time: float | None = None,
    cue_id: int | None = None,
    sequence_id: int | None = None,
    layout_id: int | None = None,
    x: int | None = None,
    y: int | None = None,
    noconfirm: bool = False,
) -> str:
    """
    Assign objects, functions, fades, or layout positions on the console.

    SAFETY: This is a DESTRUCTIVE operation. Requires confirm_destructive=True.

    Args:
        mode: Assignment mode:
            "assign" — assign source object to target (e.g. sequence to executor)
            "function" — assign a function to an executor (e.g. Toggle, Flash)
            "fade" — assign a fade time to a cue
            "layout" — assign an object to a layout position
            "empty" — deactivate an executor (assign empty function)
            "temp_fader" — assign temp fader function to an executor
        confirm_destructive: Must be True to execute (safety gate)
        source_type: Source object type (for "assign" and "layout" modes)
        source_id: Source object ID (for "assign" and "layout" modes)
        target_type: Target object type (for "assign", "function", "empty", "temp_fader")
        target_id: Target object ID
        function: Function name for "function" mode (e.g. "Toggle", "Flash", "Go")
        fade_time: Fade time in seconds for "fade" mode
        cue_id: Cue ID for "fade" mode
        sequence_id: Sequence ID for "fade" mode
        layout_id: Layout ID for "layout" mode
        x: X position for "layout" mode
        y: Y position for "layout" mode
        noconfirm: Skip console confirmation dialog

    Returns:
        str: JSON with command_sent, raw_response, or block info.

    Examples:
        - Assign sequence 1 to executor 6: mode="assign", source_type="sequence",
          source_id=1, target_type="executor", target_id=6
        - Assign Toggle to executor 101: mode="function", function="Toggle",
          target_type="executor", target_id=101
        - Assign fade 3s to cue 5: mode="fade", fade_time=3, cue_id=5
        - Assign group to layout: mode="layout", source_type="group", source_id=1,
          layout_id=1, x=5, y=2
        - Empty executor 1: mode="empty", target_type="executor", target_id=1
    """
    if not confirm_destructive:
        return json.dumps({
            "command_sent": None,
            "blocked": True,
            "error": "Assign is a DESTRUCTIVE operation. Set confirm_destructive=True to proceed.",
        }, indent=2)

    mode = mode.lower()

    if mode == "assign":
        if source_type is None or source_id is None:
            return json.dumps({
                "error": "assign mode requires source_type and source_id.",
                "blocked": True,
            }, indent=2)
        cmd = build_assign(
            source_type, source_id,
            target_type=target_type, target_id=target_id,
            noconfirm=noconfirm,
        )
    elif mode == "function":
        if function is None or target_type is None or target_id is None:
            return json.dumps({
                "error": "function mode requires function, target_type, and target_id.",
                "blocked": True,
            }, indent=2)
        cmd = build_assign_function(function, target_type, target_id)
    elif mode == "fade":
        if fade_time is None or cue_id is None:
            return json.dumps({
                "error": "fade mode requires fade_time and cue_id.",
                "blocked": True,
            }, indent=2)
        cmd = build_assign_fade(fade_time, cue_id, sequence_id=sequence_id)
    elif mode == "layout":
        if source_type is None or source_id is None or layout_id is None:
            return json.dumps({
                "error": "layout mode requires source_type, source_id, and layout_id.",
                "blocked": True,
            }, indent=2)
        cmd = build_assign_to_layout(
            source_type, source_id, layout_id, x=x, y=y,
        )
    elif mode == "empty":
        if target_type is None or target_id is None:
            return json.dumps({
                "error": "empty mode requires target_type and target_id.",
                "blocked": True,
            }, indent=2)
        cmd = build_assign_function("empty", target_type, target_id)
    elif mode == "temp_fader":
        if target_type is None or target_id is None:
            return json.dumps({
                "error": "temp_fader mode requires target_type and target_id.",
                "blocked": True,
            }, indent=2)
        cmd = build_assign_function("tempfader", target_type, target_id)
    else:
        return json.dumps({
            "error": (
                f"Unknown mode: {mode}. Use 'assign', 'function', 'fade', "
                f"'layout', 'empty', or 'temp_fader'."
            ),
            "blocked": True,
        }, indent=2)

    client = await _sc.get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "blocked": False,
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.CUE_STORE)
@_handle_errors
async def edit_object(
    action: str,
    object_type: str | None = None,
    object_id: int | str | None = None,
    target_id: int | str | None = None,
    end: int | str | None = None,
    confirm_destructive: bool = False,
) -> str:
    """
    Edit, cut, or paste objects in the show.

    - edit: Opens an object for editing (SAFE_WRITE)
    - cut: Removes an object and places it on the clipboard (DESTRUCTIVE)
    - paste: Places clipboard contents at a target location (DESTRUCTIVE)

    SAFETY: cut and paste are DESTRUCTIVE and require confirm_destructive=True.
    edit does not require confirmation.

    Args:
        action: "edit", "cut", or "paste"
        object_type: Object type (e.g. "preset", "cue", "group")
        object_id: Object ID (for edit and cut)
        target_id: Target ID for paste destination
        end: End ID for range operations
        confirm_destructive: Must be True for cut/paste (safety gate)

    Returns:
        str: JSON with command_sent, raw_response, or block info.

    Examples:
        - Edit cue 1: action="edit", object_type="cue", object_id=1
        - Cut preset 4.1: action="cut", object_type="preset", object_id="4.1"
        - Paste to group 5: action="paste", object_type="group", target_id=5
    """
    action = action.lower()

    if action in ("cut", "paste") and not confirm_destructive:
        return json.dumps({
            "command_sent": None,
            "blocked": True,
            "error": f"{action.title()} is a DESTRUCTIVE operation. Set confirm_destructive=True to proceed.",
        }, indent=2)

    if action == "edit":
        cmd = build_edit(object_type=object_type, object_id=object_id, end=end)
    elif action == "cut":
        if object_type is None or object_id is None:
            return json.dumps({
                "error": "cut requires object_type and object_id.",
                "blocked": True,
            }, indent=2)
        cmd = build_cut(object_type, object_id, end=end)
    elif action == "paste":
        cmd = build_paste(object_type, target_id)
    else:
        return json.dumps({
            "error": f"Unknown action: {action}. Use 'edit', 'cut', or 'paste'.",
            "blocked": True,
        }, indent=2)

    client = await _sc.get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "blocked": False,
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.CUE_STORE)
@_handle_errors
async def remove_content(
    object_type: str,
    object_id: int | str | None = None,
    end: int | None = None,
    if_filter: str | None = None,
    confirm_destructive: bool = False,
) -> str:
    """
    Remove content from objects (fixtures from groups, effects, preset types, etc.).

    Unlike delete (which removes the object itself), remove takes content out of
    an object. For example, removing a fixture from a group, or removing an effect
    from a cue.

    SAFETY: This is a DESTRUCTIVE operation. Requires confirm_destructive=True.

    Args:
        object_type: What to remove. Special types:
            "selection" — remove the current selection
            "fixture" — remove a fixture (from a group, cue, etc.)
            "effect" — remove an effect
            "presettype" — remove a preset type from the programmer
            Or any generic type for the generic remove command.
        object_id: Object ID to remove (not needed for "selection")
        end: End ID for range removal
        if_filter: Conditional filter (e.g. "PresetType 1")
        confirm_destructive: Must be True to execute (safety gate)

    Returns:
        str: JSON with command_sent, raw_response, or block info.

    Examples:
        - Remove selection: object_type="selection"
        - Remove fixture 1: object_type="fixture", object_id=1
        - Remove fixture with filter: object_type="fixture", object_id=1,
          if_filter="PresetType 1"
        - Remove effect 1: object_type="effect", object_id=1
        - Remove preset type: object_type="presettype", object_id="position"
    """
    if not confirm_destructive:
        return json.dumps({
            "command_sent": None,
            "blocked": True,
            "error": "Remove is a DESTRUCTIVE operation. Set confirm_destructive=True to proceed.",
        }, indent=2)

    otype = object_type.lower()

    if otype == "selection":
        cmd = build_remove_selection()
    elif otype == "fixture":
        if object_id is None:
            return json.dumps({
                "error": "fixture removal requires object_id.",
                "blocked": True,
            }, indent=2)
        cmd = build_remove_fixture(object_id, end=end, if_filter=if_filter)
    elif otype == "effect":
        if object_id is None:
            return json.dumps({
                "error": "effect removal requires object_id.",
                "blocked": True,
            }, indent=2)
        cmd = build_remove_effect(object_id, end=end)
    elif otype == "presettype":
        if object_id is None:
            return json.dumps({
                "error": "presettype removal requires object_id (the preset type name or number).",
                "blocked": True,
            }, indent=2)
        cmd = build_remove_preset_type(object_id, if_filter=if_filter)
    else:
        cmd = build_remove(
            object_type=object_type, object_id=object_id,
            end=end, if_filter=if_filter,
        )

    client = await _sc.get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "blocked": False,
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.CUE_STORE)
@_handle_errors
async def store_object(
    object_type: str,
    object_id: int | str,
    name: str | None = None,
    merge: bool = False,
    overwrite: bool = False,
    noconfirm: bool = False,
    confirm_destructive: bool = False,
) -> str:
    """
    Store (create) a generic object in the show — macros, effects, worlds, etc.

    For cues, use store_current_cue. For presets, use store_new_preset.
    For groups, use create_fixture_group. This tool handles everything else.

    SAFETY: This is a DESTRUCTIVE operation. Requires confirm_destructive=True.

    Args:
        object_type: Object type to store (e.g. "macro", "effect", "world",
            "sequence", "executor", "timecode")
        object_id: Object ID number or slot
        name: Optional name for the stored object
        merge: Merge into existing object if present
        overwrite: Overwrite existing object if present
        noconfirm: Skip console confirmation dialog
        confirm_destructive: Must be True to execute (safety gate)

    Returns:
        str: JSON with command_sent, raw_response, or block info.

    Examples:
        - Store macro 5: object_type="macro", object_id=5
        - Store effect 1 named "Rainbow": object_type="effect", object_id=1, name="Rainbow"
        - Overwrite sequence 3: object_type="sequence", object_id=3, overwrite=True
    """
    if not confirm_destructive:
        return json.dumps({
            "command_sent": None,
            "blocked": True,
            "error": "Store is a DESTRUCTIVE operation. Set confirm_destructive=True to proceed.",
        }, indent=2)

    cmd = build_store_generic(
        object_type, object_id, name,
        merge=merge, overwrite=overwrite, noconfirm=noconfirm,
    )

    client = await _sc.get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "blocked": False,
    }, indent=2)


# ============================================================


@mcp.tool()
@require_scope(OAuthScope.EXECUTOR_CTRL)
@_handle_errors
async def set_executor_level(
    executor_id: int,
    level: float,
    page: int | None = None,
) -> str:
    """
    Set a fader/executor to a specific output level.

    Args:
        executor_id: Executor number (1-999)
        level: Fader level 0.0–100.0
        page: Page number for page-qualified addressing (optional)

    Returns:
        str: JSON result with command sent
    """
    if not (0.0 <= level <= 100.0):
        return json.dumps({"error": "level must be between 0.0 and 100.0", "blocked": True}, indent=2)
    if executor_id < 1:
        return json.dumps({"error": "executor_id must be >= 1", "blocked": True}, indent=2)

    client = await _sc.get_client()
    cmd = build_executor_at(executor_id, level, page=page)
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PLAYBACK_GO)
@_handle_errors
async def navigate_page(
    action: str,
    page_number: int | None = None,
    steps: int | None = None,
    create_if_missing: bool = False,
) -> str:
    """
    Navigate executor pages on the console.

    $FADERPAGE, $BUTTONPAGE, and $CHANNELPAGE are read-only system variables —
    SetVar has no effect on them. Only `Page N` (this tool) changes the active page.

    Args:
        action: "goto" (absolute page), "next" (page +), or "previous" (page -)
        page_number: Target page number (required for "goto"; 1-999)
        steps: Number of pages to advance/go back (optional; for "next"/"previous")
        create_if_missing: If True, sends `Store Page N /noconfirm` before navigating
            to create the page if it does not yet exist. Only applies to action="goto".
            Without this, MA2 returns Error #9 if the page doesn't exist.

    Returns:
        str: JSON result with command sent
    """
    if action not in ("goto", "next", "previous"):
        return json.dumps({"error": "action must be 'goto', 'next', or 'previous'", "blocked": True}, indent=2)
    if action == "goto":
        if page_number is None:
            return json.dumps({"error": "page_number is required for action='goto'", "blocked": True}, indent=2)
        cmd = f"page {page_number}"
    elif action == "next":
        cmd = build_page_next(steps)
    else:
        cmd = build_page_previous(steps)

    client = await _sc.get_client()
    result_steps = []

    if create_if_missing and action == "goto":
        store_cmd = f"Store Page {page_number} /noconfirm"
        store_raw = await client.send_command_with_response(store_cmd)
        result_steps.append({"command": store_cmd, "response": store_raw})

    response = await client.send_command_with_response(cmd)
    result_steps.append({"command": cmd, "response": response})

    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "steps": result_steps,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PROGRAMMER_WRITE)
@_handle_errors
async def select_feature(
    feature_name: str,
) -> str:
    """
    Select the active feature bank on the grandMA2 console (SAFE_WRITE).

    Sends `Feature [name]` which updates $FEATURE.
    $FEATURE is read-only — SetVar has no effect on it.
    Only `Feature [name]` changes the active feature context.

    Feature names are fixture-dependent — only features present on the selected
    fixture's channels are valid. Live-verified names (v3.9.60.65):
      Dimmer, Position, Gobo1, Gobo2, ColorRGB, Shutter, Focus, MSPEED
    Names that may error if fixture lacks the channel: Color, Zoom, Iris, Frost

    Args:
        feature_name: Feature bank to activate (e.g. "Dimmer", "ColorRGB", "MSPEED")

    Returns:
        str: JSON with command_sent, raw_response, risk_tier
    """
    cmd = f"Feature {feature_name}"
    client = await _sc.get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PROGRAMMER_WRITE)
@_handle_errors
async def select_preset_type(
    preset_type: int | str,
) -> str:
    """
    Select the active preset type on the grandMA2 console (SAFE_WRITE).

    Sends `PresetType [id or name]` which jumps the encoder context to the
    first Feature available in that preset type for the selected fixtures.
    Updates $PRESET, $FEATURE, and $ATTRIBUTE simultaneously.

    CD tree location (live-verified, v3.9.60.65):
      cd 10.2        → lists all 9 PresetTypes
      cd 10.2.N      → lists Features under PresetType N
      cd 10.2.N.M    → lists Attributes under Feature M of PresetType N
      cd 10.2.N.M.K  → lists SubAttributes (deepest level)

    Preset types + live-verified $FEATURE on first activation:
      1=Dimmer  ($FEATURE=DIMMER,   $ATTRIBUTE=DIM)
      2=Position ($FEATURE=POSITION, $ATTRIBUTE=PAN)
      3=Gobo    ($FEATURE=GOBO1,    $ATTRIBUTE=GOBO1)
      4=Color   ($FEATURE=COLORRGB, $ATTRIBUTE=COLORRGB1, fixture-dep)
      5=Beam    ($FEATURE=SHUTTER,  $ATTRIBUTE=SHUTTER,   fixture-dep)
      6=Focus   ($FEATURE=FOCUS,    $ATTRIBUTE=FOCUS)
      7=Control ($FEATURE=MSPEED,   $ATTRIBUTE=INTENSITYMSPEED)
      8=Shapers (fixture must have Shapers channels)
      9=Video   (fixture must have Video channels)

    Args:
        preset_type: Preset type number (1-9) or name (e.g. "Color", "Control")

    Returns:
        str: JSON with command_sent, raw_response, risk_tier
    """
    cmd = f"PresetType {preset_type}" if isinstance(preset_type, int) else f'PresetType "{preset_type}"'
    client = await _sc.get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


# _parse_preset_tree_list moved to server_core.py


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def browse_preset_type(
    preset_type_id: int,
    depth: int = 1,
) -> str:
    """
    Browse the feature/attribute tree under a preset type (SAFE_READ).

    Navigates the grandMA2 LiveSetup preset-type cd-tree and lists children
    at the requested depth. The tree structure (live-verified v3.9.60.65):

      cd 10.2.N       → Features under PresetType N
      cd 10.2.N.M     → Attributes under Feature M
      cd 10.2.N.M.K   → SubAttributes under Attribute K  (leaf level)

    Indexes at each level use sequential position (1 = first listed child),
    NOT the internal library ID shown in the output.

    Args:
        preset_type_id: Preset type to browse (1=Dimmer, 2=Position, 3=Gobo,
            4=Color, 5=Beam, 6=Focus, 7=Control, 8=Shapers, 9=Video)
        depth: How deep to traverse (1=features only, 2=+attributes,
            3=+subattributes). Defaults to 1.

    Returns:
        str: JSON with the tree structure at the requested depth.
    """
    if not 1 <= preset_type_id <= 9:
        return json.dumps({"error": "preset_type_id must be 1-9", "blocked": True}, indent=2)
    if not 1 <= depth <= 3:
        return json.dumps({"error": "depth must be 1-3", "blocked": True}, indent=2)

    client = await _sc.get_client()

    async def list_path(path: str) -> tuple[str, list[dict]]:
        await navigate(client, "/")
        await navigate(client, path)
        lst = await list_destination(client)
        raw = lst.raw_response
        entries = _parse_preset_tree_list(raw)
        return raw, entries

    # Depth 1: features under preset type
    raw1, features = await list_path(f"10.2.{preset_type_id}")

    result: dict = {
        "preset_type_id": preset_type_id,
        "cd_path": f"10.2.{preset_type_id}",
        "features": features,
        "risk_tier": "SAFE_READ",
    }

    if depth >= 2:
        for fi, feat in enumerate(features, start=1):
            feat_path = f"10.2.{preset_type_id}.{fi}"
            _, attrs = await list_path(feat_path)
            feat["cd_path"] = feat_path
            feat["attributes"] = attrs

            if depth >= 3:
                for ai, attr in enumerate(attrs, start=1):
                    attr_path = f"10.2.{preset_type_id}.{fi}.{ai}"
                    _, sub_attrs = await list_path(attr_path)
                    attr["cd_path"] = attr_path
                    attr["sub_attributes"] = sub_attrs

    # Return to root
    await navigate(client, "/")
    return json.dumps(result, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PROGRAMMER_WRITE)
@_handle_errors
async def modify_selection(
    action: str,
    fixture_ids: list[int] | None = None,
    end_id: int | None = None,
) -> str:
    """
    Add, remove, replace, or clear the current fixture selection.

    Args:
        action: "add" (+ N), "remove" (- N), "replace" (selfix), or "clear"
        fixture_ids: Fixture IDs to add/remove/replace (required for all except "clear")
        end_id: End of a range (optional; builds thru N)

    Returns:
        str: JSON result with command sent
    """
    if action not in ("add", "remove", "replace", "clear"):
        return json.dumps({"error": "action must be 'add', 'remove', 'replace', or 'clear'", "blocked": True}, indent=2)
    if action != "clear" and not fixture_ids:
        return json.dumps({"error": "fixture_ids is required for action != 'clear'", "blocked": True}, indent=2)

    client = await _sc.get_client()
    if action == "clear":
        cmd = build_clear_selection()
    elif action == "add":
        if len(fixture_ids) == 1 and end_id is not None:
            cmd = build_add_to_selection(fixture_ids[0], end=end_id)
        elif len(fixture_ids) == 1:
            cmd = build_add_to_selection(fixture_ids[0])
        else:
            cmd = build_add_to_selection(fixture_ids)
    elif action == "remove":
        if len(fixture_ids) == 1 and end_id is not None:
            cmd = build_remove_from_selection(fixture_ids[0], end=end_id)
        elif len(fixture_ids) == 1:
            cmd = build_remove_from_selection(fixture_ids[0])
        else:
            cmd = build_remove_from_selection(fixture_ids)
    else:  # replace
        first = fixture_ids[0]
        last = end_id if end_id is not None else (fixture_ids[-1] if len(fixture_ids) > 1 else None)
        cmd = select_fixture(first, last)

    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PROGRAMMER_WRITE)
@_handle_errors
async def adjust_value_relative(
    delta: float,
    attribute_name: str | None = None,
    fixture_ids: list[int] | None = None,
    end_id: int | None = None,
) -> str:
    """
    Nudge an attribute value by a relative delta on the current (or specified) selection.

    Args:
        delta: Relative change (positive or negative, non-zero). E.g. +10 or -5.
        attribute_name: Attribute to target (e.g. "Pan", "Tilt", "Dimmer"). Optional.
        fixture_ids: Select these fixtures before nudging. Optional.
        end_id: End of fixture range. Optional.

    Returns:
        str: JSON result with commands sent
    """
    if delta == 0:
        return json.dumps({"error": "delta cannot be zero", "blocked": True}, indent=2)

    client = await _sc.get_client()
    commands_sent = []

    if fixture_ids:
        first = fixture_ids[0]
        last = end_id if end_id is not None else (fixture_ids[-1] if len(fixture_ids) > 1 else None)
        sel_cmd = select_fixture(first, last)
        await client.send_command(sel_cmd)
        commands_sent.append(sel_cmd)

    if attribute_name:
        attr_cmd = f'attribute "{attribute_name}"'
        await client.send_command(attr_cmd)
        commands_sent.append(attr_cmd)

    nudge_cmd = build_at_relative(delta)
    response = await client.send_command_with_response(nudge_cmd)
    commands_sent.append(nudge_cmd)

    return json.dumps({
        "commands_sent": commands_sent,
        "raw_response": response,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PLAYBACK_GO)
@_handle_errors
async def control_timecode(
    action: str,
    timecode_id: int,
    timecode_position: str | None = None,
) -> str:
    """
    Start, stop, or jump to a position in a timecode show.

    Args:
        action: "start" (go), "stop" (off), or "goto"
        timecode_id: Timecode show ID (1-256)
        timecode_position: HH:MM:SS:FF position string (required for "goto")

    Returns:
        str: JSON result with command sent
    """
    if action not in ("start", "stop", "goto"):
        return json.dumps({"error": "action must be 'start', 'stop', or 'goto'", "blocked": True}, indent=2)
    if action == "goto" and timecode_position is None:
        return json.dumps({"error": "timecode_position is required for action='goto'", "blocked": True}, indent=2)

    client = await _sc.get_client()
    if action == "start":
        cmd = f"go timecode {timecode_id}"
    elif action == "stop":
        cmd = f"off timecode {timecode_id}"
    else:
        cmd = build_goto_timecode(timecode_id, timecode_position)

    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PLAYBACK_GO)
@_handle_errors
async def control_timer(
    action: str,
    timer_id: int,
) -> str:
    """
    Start, stop, or reset a console timer.

    Args:
        action: "start" (go), "stop" (off), or "reset" (goto)
        timer_id: Timer ID (1-256)

    Returns:
        str: JSON result with command sent
    """
    if action not in ("start", "stop", "reset"):
        return json.dumps({"error": "action must be 'start', 'stop', or 'reset'", "blocked": True}, indent=2)
    if timer_id < 1:
        return json.dumps({"error": "timer_id must be >= 1", "blocked": True}, indent=2)

    client = await _sc.get_client()
    if action == "start":
        cmd = f"go timer {timer_id}"
    elif action == "stop":
        cmd = f"off timer {timer_id}"
    else:
        cmd = f"goto timer {timer_id}"

    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PLAYBACK_GO)
@_handle_errors
async def undo_last_action(count: int = 1) -> str:
    """
    Undo the last N actions on the console (sends 'oops' N times).

    Args:
        count: Number of actions to undo (1-20, default 1)

    Returns:
        str: JSON result with all raw responses
    """
    if not (1 <= count <= 20):
        return json.dumps({"error": "count must be between 1 and 20", "blocked": True}, indent=2)

    client = await _sc.get_client()
    responses = []
    for _ in range(count):
        response = await client.send_command_with_response("oops")
        responses.append(response)

    return json.dumps({
        "commands_sent": ["oops"] * count,
        "raw_responses": responses,
        "count": count,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PLAYBACK_GO)
@_handle_errors
async def toggle_console_mode(mode: str) -> str:
    """
    Toggle a console mode on/off (blind, highlight, solo, freeze).

    These are toggle commands — each call flips the current state.

    Args:
        mode: "blind", "highlight", "solo", or "freeze"

    Returns:
        str: JSON result with command sent
    """
    valid = ("blind", "highlight", "solo", "freeze")
    if mode not in valid:
        return json.dumps({"error": f"mode must be one of {valid}", "blocked": True}, indent=2)

    # Blind mode puts the console into the programming layer — requires presets scope.
    if mode == "blind" and not has_scope(OAuthScope.PROGRAMMER_WRITE):
        return json.dumps({
            "blocked": True,
            "error": (
                "Blind mode requires OAuth scope 'gma2:programmer:write' "
                "(tier:2 or higher). Highlight/Solo/Freeze only require tier:1."
            ),
            "scope_required": str(OAuthScope.PROGRAMMER_WRITE),
            "scope_tier": 2,
        }, indent=2)

    client = await _sc.get_client()
    response = await client.send_command_with_response(mode)

    # Sync mode toggle to snapshot write-tracker (Gap 11)
    if snap := _orchestrator.last_snapshot:
        snap.console_modes[mode] = not snap.console_modes.get(mode, False)

    return json.dumps({
        "command_sent": mode,
        "raw_response": response,
        "mode": mode,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.CUE_STORE)
@_handle_errors
async def update_cue_data(
    confirm_destructive: bool = False,
    cue_id: float | None = None,
    sequence_id: int | None = None,
    merge: bool = False,
    overwrite: bool = False,
    cueonly: bool | None = None,
) -> str:
    """
    Update a cue with current programmer values (DESTRUCTIVE).

    Args:
        confirm_destructive: Must be True to execute
        cue_id: Cue number to update (optional; updates active cue if omitted)
        sequence_id: Sequence ID for scoping (optional)
        merge: Merge programmer into existing cue values
        overwrite: Overwrite cue with programmer values
        cueonly: Prevent tracking forward (True) or allow (False)

    Returns:
        str: JSON result with command sent
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "Destructive operation blocked. Set confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    client = await _sc.get_client()
    cmd = build_update_cue(cue_id, sequence_id=sequence_id, merge=merge,
                           overwrite=overwrite, cueonly=cueonly)
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "DESTRUCTIVE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.CUE_STORE)
@_handle_errors
async def set_cue_timing(
    cue_id: int,
    confirm_destructive: bool = False,
    sequence_id: int | None = None,
    fade_time: float | None = None,
    delay_time: float | None = None,
) -> str:
    """
    Set fade and/or delay time on a specific cue (DESTRUCTIVE).

    Args:
        cue_id: Cue number to update
        confirm_destructive: Must be True to execute
        sequence_id: Sequence ID for scoping (optional)
        fade_time: Fade time in seconds (0.0–3600.0, optional)
        delay_time: Delay time in seconds (0.0–3600.0, optional)

    Returns:
        str: JSON result with commands sent
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "Destructive operation blocked. Set confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)
    if fade_time is None and delay_time is None:
        return json.dumps({"error": "At least one of fade_time or delay_time must be provided", "blocked": True}, indent=2)

    client = await _sc.get_client()
    commands_sent = []
    responses = []

    if fade_time is not None:
        cmd = build_assign_fade(fade_time, cue_id, sequence_id=sequence_id)
        response = await client.send_command_with_response(cmd)
        commands_sent.append(cmd)
        responses.append(response)

    if delay_time is not None:
        cmd = build_assign_delay(delay_time, cue_id, sequence_id=sequence_id)
        response = await client.send_command_with_response(cmd)
        commands_sent.append(cmd)
        responses.append(response)

    return json.dumps({
        "commands_sent": commands_sent,
        "raw_responses": responses,
        "risk_tier": "DESTRUCTIVE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PROGRAMMER_WRITE)
@_handle_errors
async def select_fixtures_by_group(
    group_id: int,
    append: bool = False,
) -> str:
    """
    Select all fixtures in a group (replaces or appends to current selection).

    Args:
        group_id: Group ID to select (1-999)
        append: If True, adds group to current selection instead of replacing

    Returns:
        str: JSON result with command sent
    """
    if group_id < 1:
        return json.dumps({"error": "group_id must be >= 1", "blocked": True}, indent=2)

    client = await _sc.get_client()
    cmd = f"+ group {group_id}" if append else f"group {group_id}"
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "group_id": group_id,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.EXECUTOR_CTRL)
@_handle_errors
async def control_executor(
    action: str,
    executor_id: int,
    page: int | None = None,
    speed_value: float | None = None,
    confirm_destructive: bool = False,
) -> str:
    """
    Control an executor: start, stop, flash, swop, solo, top, stomp, set speed,
    flash_go, flash_on, swop_go, swop_on, or manual_xfade.

    set_speed is DESTRUCTIVE (modifies stored data).

    Args:
        action: "on", "off", "flash", "swop", "solo", "top", "stomp", "set_speed",
            "flash_go", "flash_on", "swop_go", "swop_on", or "manual_xfade"
        executor_id: Executor ID (1-999)
        page: Page number for page-qualified addressing (optional)
        speed_value: BPM for set_speed, or crossfade position (0–100) for manual_xfade
        confirm_destructive: Must be True when action="set_speed"

    Returns:
        str: JSON result with command sent
    """
    valid_actions = (
        "on", "off", "flash", "swop", "solo", "top", "stomp", "set_speed",
        "flash_go", "flash_on", "swop_go", "swop_on", "manual_xfade",
    )
    if action not in valid_actions:
        return json.dumps({"error": f"action must be one of {valid_actions}", "blocked": True}, indent=2)
    if executor_id < 1:
        return json.dumps({"error": "executor_id must be >= 1", "blocked": True}, indent=2)

    if action == "set_speed":
        if not confirm_destructive:
            return json.dumps({
                "blocked": True,
                "error": "set_speed is DESTRUCTIVE. Set confirm_destructive=True to proceed.",
                "risk_tier": "DESTRUCTIVE",
            }, indent=2)
        if speed_value is None:
            return json.dumps({"error": "speed_value is required for action='set_speed'", "blocked": True}, indent=2)
        ref = f"{page}.{executor_id}" if page is not None else str(executor_id)
        cmd = f"assign speed {speed_value} at executor {ref}"
        risk_tier = "DESTRUCTIVE"
    elif action == "manual_xfade":
        if speed_value is None:
            return json.dumps({"error": "speed_value (xfade position 0–100) is required for action='manual_xfade'", "blocked": True}, indent=2)
        cmd = build_manual_xfade(executor_id, speed_value, page=page)
        risk_tier = "SAFE_WRITE"
    elif action == "on":
        cmd = build_on_executor(executor_id, page=page)
        risk_tier = "SAFE_WRITE"
    elif action == "off":
        cmd = build_off_executor(executor_id, page=page)
        risk_tier = "SAFE_WRITE"
    elif action == "flash":
        cmd = build_flash_executor(executor_id, page=page)
        risk_tier = "SAFE_WRITE"
    elif action == "flash_go":
        cmd = build_flash_go(executor_id, page=page)
        risk_tier = "SAFE_WRITE"
    elif action == "flash_on":
        cmd = build_flash_on(executor_id, page=page)
        risk_tier = "SAFE_WRITE"
    elif action == "swop":
        cmd = build_swop_executor(executor_id, page=page)
        risk_tier = "SAFE_WRITE"
    elif action == "swop_go":
        cmd = build_swop_go(executor_id, page=page)
        risk_tier = "SAFE_WRITE"
    elif action == "swop_on":
        cmd = build_swop_on(executor_id, page=page)
        risk_tier = "SAFE_WRITE"
    elif action == "top":
        cmd = build_top_executor(executor_id, page=page)
        risk_tier = "SAFE_WRITE"
    elif action == "stomp":
        cmd = build_stomp_executor(executor_id, page=page)
        risk_tier = "SAFE_WRITE"
    else:  # solo
        cmd = build_solo_executor(executor_id, page=page)
        risk_tier = "SAFE_WRITE"

    client = await _sc.get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": risk_tier,
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PLAYBACK_GO)
@_handle_errors
async def load_cue(
    direction: str,
    executor_id: int | None = None,
    sequence_id: int | None = None,
) -> str:
    """
    Pre-load the next or previous cue without executing it (SAFE_WRITE).

    LoadNext / LoadPrev arm the cue for Go without firing it.

    Args:
        direction: "next" or "prev"
        executor_id: Executor ID to load on (optional)
        sequence_id: Sequence ID to load on (optional)

    Returns:
        str: JSON result with command sent
    """
    if direction not in ("next", "prev"):
        return json.dumps({"error": "direction must be 'next' or 'prev'", "blocked": True}, indent=2)

    if direction == "next":
        cmd = build_load_next(executor=executor_id, sequence=sequence_id)
    else:
        cmd = build_load_prev(executor=executor_id, sequence=sequence_id)

    client = await _sc.get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.CUE_STORE)
@_handle_errors
async def cut_paste_object(
    action: str,
    object_type: str | None = None,
    object_id: int | str | None = None,
    target_id: int | str | None = None,
    end: int | str | None = None,
) -> str:
    """
    Cut an object to clipboard, or paste clipboard content at a target (SAFE_WRITE).

    Cut + Paste is a two-step move: Cut prepares the source, Paste places it.
    Does not work with cue objects — use copy_or_move_object for cues.

    Args:
        action: "cut" or "paste"
        object_type: Object type ("group", "preset", "sequence", "macro", etc.)
        object_id: Source object ID (required for cut; ignored for bare paste)
        target_id: Destination ID (for paste)
        end: End ID for range cut (thru syntax)

    Returns:
        str: JSON result with command sent
    """
    if action not in ("cut", "paste"):
        return json.dumps({"error": "action must be 'cut' or 'paste'", "blocked": True}, indent=2)

    if action == "cut":
        if object_type is None or object_id is None:
            return json.dumps({"error": "object_type and object_id required for cut", "blocked": True}, indent=2)
        cmd = build_cut(object_type, object_id, end=end)
    else:
        cmd = build_paste(object_type, target_id)

    client = await _sc.get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.CUE_STORE)
@_handle_errors
async def clone_object(
    object_type: str,
    object_id: int,
    target_id: int,
    end: int | None = None,
    target_end: int | None = None,
    noconfirm: bool = False,
    confirm_destructive: bool = False,
) -> str:
    """
    Clone (duplicate with data) one or more objects to new IDs (DESTRUCTIVE).

    Clone copies all stored data from the source to the target — unlike Copy
    it also migrates all associated cue/preset references.

    Args:
        object_type: Object type ("fixture", "group", "sequence", etc.)
        object_id: Source object ID
        target_id: Destination object ID
        end: End ID for source range (thru syntax)
        target_end: End ID for target range
        noconfirm: Suppress confirmation dialog
        confirm_destructive: Must be True to execute

    Returns:
        str: JSON result with command sent
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "clone_object is DESTRUCTIVE. Set confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    cmd = build_clone(
        object_type, object_id, target_id,
        end=end, target_end=target_end, noconfirm=noconfirm,
    )
    client = await _sc.get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "DESTRUCTIVE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PROGRAMMER_WRITE)
@_handle_errors
async def fix_locate_fixture(
    action: str,
    fixture_ids: list[int] | None = None,
    end: int | None = None,
) -> str:
    """
    Fix (park) or Locate selected/specified fixtures (SAFE_WRITE).

    Fix pins fixture output to current level, overriding playback.
    Locate fires fixtures to their default state (full, open, centre).

    Args:
        action: "fix" or "locate"
        fixture_ids: List of fixture IDs to fix (optional — uses selection if omitted)
        end: End ID for range when a single start ID is given

    Returns:
        str: JSON result with command sent
    """
    if action not in ("fix", "locate"):
        return json.dumps({"error": "action must be 'fix' or 'locate'", "blocked": True}, indent=2)

    if action == "locate":
        cmd = build_locate()
    else:
        if fixture_ids is not None and len(fixture_ids) == 1:
            cmd = build_fix_fixture(fixture_ids[0], end=end)
        elif fixture_ids:
            cmd = build_fix_fixture(fixture_ids)
        else:
            cmd = build_fix_fixture()

    client = await _sc.get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PROGRAMMER_WRITE)
@_handle_errors
async def manipulate_selection(action: str) -> str:
    """
    Invert or Align the current fixture selection / programmer values (SAFE_WRITE).

    Invert: swap selected and unselected fixtures.
    Align: distribute programmer values evenly from first to last fixture.

    Args:
        action: "invert" or "align"

    Returns:
        str: JSON result with command sent
    """
    if action not in ("invert", "align"):
        return json.dumps({"error": "action must be 'invert' or 'align'", "blocked": True}, indent=2)

    cmd = build_invert() if action == "invert" else build_align()
    client = await _sc.get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.SEQUENCE_EDIT)
@_handle_errors
async def block_unblock_cue(
    action: str,
    cue_id: float,
    sequence_id: int | None = None,
    end: float | None = None,
    confirm_destructive: bool = False,
) -> str:
    """
    Block or Unblock a cue (DESTRUCTIVE — modifies cue data in the show file).

    Block makes a cue store all active values and stop tracking from prior cues.
    Unblock removes the block flag, allowing values to track through again.

    Args:
        action: "block" or "unblock"
        cue_id: Cue number to block/unblock
        sequence_id: Sequence ID to scope the command (optional)
        end: End cue ID for range (thru syntax)
        confirm_destructive: Must be True to execute

    Returns:
        str: JSON result with command sent
    """
    if action not in ("block", "unblock"):
        return json.dumps({"error": "action must be 'block' or 'unblock'", "blocked": True}, indent=2)
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": f"{action}_cue is DESTRUCTIVE. Set confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    if action == "block":
        cmd = build_block(cue_id, sequence_id=sequence_id, end=end)
    else:
        cmd = build_unblock(cue_id, sequence_id=sequence_id, end=end)

    client = await _sc.get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "DESTRUCTIVE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.SEQUENCE_EDIT)
@_handle_errors
async def store_timecode_event(
    timecode_id: int,
    cue_id: float,
    sequence_id: int,
    confirm_destructive: bool = False,
    timecode_position: str | None = None,
) -> str:
    """
    Store a timecode trigger event that fires a cue at a specific time (DESTRUCTIVE).

    Args:
        timecode_id: Timecode show ID (1-256)
        cue_id: Cue to trigger
        sequence_id: Sequence containing the cue
        confirm_destructive: Must be True to execute
        timecode_position: HH:MM:SS:FF position string (optional)

    Returns:
        str: JSON result with command sent
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "Destructive operation blocked. Set confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    client = await _sc.get_client()
    if timecode_position:
        cmd = f'assign timecode {timecode_id} cue {cue_id} sequence {sequence_id} "{timecode_position}"'
    else:
        cmd = f"store timecode {timecode_id}"

    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "DESTRUCTIVE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.SEQUENCE_EDIT)
@_handle_errors
async def set_sequence_property(
    sequence_id: int,
    property_name: str,
    value: str,
    confirm_destructive: bool = False,
) -> str:
    """
    Set a property on a sequence object via the console tree (DESTRUCTIVE).

    Navigates to the sequence node, assigns the property, then returns to root.

    Args:
        sequence_id: Sequence ID (1-999)
        property_name: Property name (e.g. "loop", "tracking", "label")
        value: Property value (e.g. "on", "off", "My Sequence")
        confirm_destructive: Must be True to execute

    Returns:
        str: JSON result with commands sent
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "Destructive operation blocked. Set confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    client = await _sc.get_client()
    result = await set_property(
        client,
        path=f"sequence {sequence_id}",
        property_name=property_name,
        value=value,
    )
    return json.dumps({
        "sequence_id": sequence_id,
        "property": property_name,
        "value": value,
        "commands_sent": result.commands_sent,
        "success": result.success,
        "verified_value": result.verified_value,
        "error": result.error,
        "risk_tier": "DESTRUCTIVE",
    }, indent=2)


# ============================================================


@mcp.tool()
@require_scope(OAuthScope.PLAYBACK_GO)
@_handle_errors
async def save_show(
    action: str,
    show_name: str | None = None,
) -> str:
    """
    Save the current show file to disk.

    Args:
        action: "save" (overwrite current) or "saveas" (save under a new name)
        show_name: Show name/path (required for action="saveas")

    Returns:
        str: JSON result with command sent
    """
    if action not in ("save", "saveas"):
        return json.dumps({"error": "action must be 'save' or 'saveas'", "blocked": True}, indent=2)
    if action == "saveas" and not show_name:
        return json.dumps({"error": "show_name is required for action='saveas'", "blocked": True}, indent=2)

    client = await _sc.get_client()
    cmd = "save" if action == "save" else f'saveas "{show_name}"'
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.CUE_STORE)
@_handle_errors
async def store_cue_with_timing(
    cue_id: int,
    confirm_destructive: bool = False,
    fade_time: float | None = None,
    out_time: float | None = None,
    merge: bool = False,
    overwrite: bool = False,
    cue_name: str | None = None,
    sequence_id: int | None = None,
) -> str:
    """
    Store a cue with inline fade and outtime parameters (DESTRUCTIVE).

    When sequence_id is omitted, MA2 stores into the sequence on the currently
    selected executor. Pass sequence_id explicitly to target a specific sequence
    regardless of executor selection state (same behavior as store_current_cue).

    Args:
        cue_id: Cue number to store
        confirm_destructive: Must be True to execute
        fade_time: Fade-in time in seconds (optional)
        out_time: Fade-out time in seconds (optional)
        merge: Merge into existing cue
        overwrite: Overwrite existing cue
        cue_name: Optional cue label
        sequence_id: Sequence to store into (omit to use selected executor)

    Returns:
        str: JSON result with command sent
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "Destructive operation blocked. Set confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    client = await _sc.get_client()
    cmd = build_store_cue_timed(
        cue_id,
        name=cue_name,
        fade_time=fade_time,
        out_time=out_time,
        merge=merge,
        overwrite=overwrite,
    )
    if sequence_id is not None:
        cmd += f" sequence {sequence_id}"
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "DESTRUCTIVE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.EXECUTOR_CTRL)
@_handle_errors
async def select_executor(
    executor_id: int,
    page: int | None = None,
    deselect: bool = False,
) -> str:
    """
    Select an executor on the console.

    IMPORTANT: MA2 telnet 'select executor N' is single-selection only — there
    is no list syntax. You cannot select multiple executors simultaneously via
    this command. Pass only a single executor_id integer.

    After sending the command, $SELECTEDEXEC is read back to confirm the
    selection took effect. A 'warning' field is included in the response if
    the confirmed value does not match the requested executor_id.

    To clear the current selection, pass deselect=True. This sends a bare
    'select' command with no argument. NOTE: bare 'select' behaviour is
    unverified on grandMA2 telnet — it may clear selection, be silently
    ignored, or produce an error. Inspect 'raw_response' to confirm.

    Args:
        executor_id: Executor number (1-999). Single value only.
        page: Page number for page-qualified addressing (optional).
              e.g. page=2, executor_id=5 → 'select executor 2.5'.
              $SELECTEDEXEC returns the executor number only (not page-qualified).
        deselect: If True, send bare 'select' to clear the current selection
                  instead of selecting executor_id. Defaults to False.

    Returns:
        str: JSON with command_sent, raw_response, confirmed_selected_exec,
             and risk_tier. Includes 'warning' if confirmed value doesn't match.
    """
    client = await _sc.get_client()

    if deselect:
        cmd = "select"
        response = await client.send_command_with_response(cmd)
        listvar_raw = await client.send_command_with_response("ListVar")
        confirmed = _parse_listvar(listvar_raw).get("$SELECTEDEXEC")
        return json.dumps({
            "command_sent": cmd,
            "raw_response": response,
            "confirmed_selected_exec": confirmed,
            "note": "Bare 'select' sent to clear selection. Behaviour unverified on grandMA2 telnet.",
            "risk_tier": "SAFE_WRITE",
        }, indent=2)

    ref = f"{page}.{executor_id}" if page is not None else str(executor_id)
    cmd = f"select executor {ref}"
    response = await client.send_command_with_response(cmd)

    listvar_raw = await client.send_command_with_response("ListVar")
    variables = _parse_listvar(listvar_raw)
    confirmed = variables.get("$SELECTEDEXEC")

    result: dict = {
        "command_sent": cmd,
        "raw_response": response,
        "confirmed_selected_exec": confirmed,
        "risk_tier": "SAFE_WRITE",
    }
    # $SELECTEDEXEC stores executor number only (not page-qualified)
    if confirmed is None or confirmed.strip() != str(executor_id):
        result["warning"] = (
            f"$SELECTEDEXEC is '{confirmed}' after command but expected '{executor_id}'. "
            "The selection may not have taken effect."
        )
    return json.dumps(result, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PROGRAMMER_WRITE)
@_handle_errors
async def remove_from_programmer(
    object_type: str,
    object_id: int,
    end_id: int | None = None,
) -> str:
    """
    Remove channels, fixtures, or a group from the programmer using Off.

    Args:
        object_type: "channel", "fixture", or "group"
        object_id: Object ID to remove
        end_id: End of range for channel/fixture (optional; builds thru N)

    Returns:
        str: JSON result with command sent
    """
    if object_type not in ("channel", "fixture", "group"):
        return json.dumps(
            {"error": "object_type must be 'channel', 'fixture', or 'group'", "blocked": True},
            indent=2,
        )
    if end_id is not None and object_type != "group":
        cmd = f"off {object_type} {object_id} thru {end_id}"
    else:
        cmd = f"off {object_type} {object_id}"

    client = await _sc.get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.SEQUENCE_EDIT)
@_handle_errors
async def assign_cue_trigger(
    cue_id: int,
    sequence_id: int,
    trigger_type: str,
    confirm_destructive: bool = False,
    trigger_value: float | None = None,
) -> str:
    """
    Assign a playback trigger type to a cue (DESTRUCTIVE).

    Args:
        cue_id: Cue number to assign the trigger to
        sequence_id: Sequence containing the cue
        trigger_type: "go", "follow", "time", or "bpm"
        confirm_destructive: Must be True to execute
        trigger_value: BPM or time value (required for "bpm" and "time")

    Returns:
        str: JSON result with command sent
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "Destructive operation blocked. Set confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    valid = ("go", "follow", "time", "bpm")
    if trigger_type not in valid:
        return json.dumps({"error": f"trigger_type must be one of {valid}", "blocked": True}, indent=2)
    if trigger_type in ("bpm", "time") and trigger_value is None:
        return json.dumps(
            {"error": f"trigger_value is required for trigger_type='{trigger_type}'", "blocked": True},
            indent=2,
        )

    if trigger_type == "bpm":
        cmd = f"assign trigger bpm {trigger_value} cue {cue_id} sequence {sequence_id}"
    elif trigger_type == "time":
        cmd = f"assign trigger time {trigger_value} cue {cue_id} sequence {sequence_id}"
    else:
        cmd = f"assign trigger {trigger_type} cue {cue_id} sequence {sequence_id}"

    client = await _sc.get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "DESTRUCTIVE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.SETUP_CONSOLE)
@_handle_errors
async def assign_executor_property(
    executor_id: int,
    option: str,
    value: str | int,
    confirm_destructive: bool = False,
    page: int = 1,
) -> str:
    """
    Assign any of the 22 settable options to an executor (DESTRUCTIVE).

    Always uses page-qualified addressing (page.executor_id) to avoid Error #66.

    Valid options (case-sensitive):
      Layout:   width (1-5)
      Priority: priority (low|normal|high|htp|swap|super)
      Start:    autostart, autostop, autofix, autostomp, restart
      Protect:  ooo, swopprotect, killprotect
      Playback: softltp, wrap, crossfade (off|a|b|ab — requires width>=2), chaser
      Timing:   triggerisgo, cmddisable, effectspeed, autogo
      Speed:    speed (0-65535 BPM), speedmaster (speed_individual|speed1-16),
                ratemaster (rate_individual|rate1-16)

    Args:
        executor_id: Executor ID (e.g. 203).
        option: Option name from the list above.
        value: Value to assign (e.g. 2, "on", "high", "speed1").
        confirm_destructive: Must be True to execute.
        page: Page number (default 1). Always included in the address.

    Returns:
        str: JSON with command_sent, raw_response, risk_tier.
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "Destructive operation blocked. Set confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    from src.commands import build_assign_executor_option as _build_opt
    try:
        cmd = _build_opt(executor_id, option, value, page=page)
    except ValueError as exc:
        return json.dumps({"error": str(exc), "blocked": True}, indent=2)

    client = await _sc.get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "DESTRUCTIVE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.SEQUENCE_EDIT)
@_handle_errors
async def set_executor_priority(
    executor_id: int,
    priority: str,
    page: int = 1,
) -> str:
    """
    Set the playback priority of an executor (Tool 130).

    Priority determines how this executor interacts with other active executors
    and the programmer. Uses page-qualified addressing (page.executor_id) to
    avoid Error #66 CANNOT ASSIGN.

    Priority levels (highest → lowest):
      - "super"  — LTP above ALL playbacks + programmer. Only Freeze overrides.
      - "swap"   — LTP > HTP; negative override possible. Affects ALL attributes.
      - "htp"    — Highest intensity value wins. Changes ALL attribute priority.
      - "high"   — High LTP. Overrides Normal/Low but not HTP intensity.
      - "normal" — LTP default. Last triggered value wins.
      - "low"    — Lowest priority. Overridden by everything else.

    Args:
        executor_id: The executor to modify (e.g. 201).
        priority: One of "super", "swap", "htp", "high", "normal", "low".
        page: Page number (default 1). Always included in the address.

    Returns:
        str: JSON with command_sent, raw_response, risk_tier.
    """
    from src.commands import build_set_executor_priority as _build_prio
    try:
        cmd = _build_prio(executor_id, priority, page=page)
    except ValueError as exc:
        return json.dumps({"error": str(exc), "blocked": True}, indent=2)

    client = await _sc.get_client()
    raw = await client.send_command_with_response(cmd)

    # Sync priority to snapshot write-tracker (Gap 10)
    if (snap := _orchestrator.last_snapshot) and executor_id in snap.executor_state:
        snap.executor_state[executor_id].priority = priority

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.CUE_STORE)
@_handle_errors
async def save_recall_view(
    action: str,
    view_id: int,
    screen_id: int = 1,
    view_name: str | None = None,
    confirm_destructive: bool = False,
) -> str:
    """
    Store, recall, or label a screen view (store is DESTRUCTIVE).

    Args:
        action: "store" (save current screen), "recall" (load view), or "label" (name it)
        view_id: View slot ID (1-10)
        screen_id: Screen number (1-4, default 1)
        view_name: Label for the view (required for action="label")
        confirm_destructive: Must be True for action="store"

    Returns:
        str: JSON result with command sent
    """
    if action not in ("store", "recall", "label"):
        return json.dumps(
            {"error": "action must be 'store', 'recall', or 'label'", "blocked": True},
            indent=2,
        )
    if not (1 <= view_id <= 10):
        return json.dumps({"error": "view_id must be between 1 and 10", "blocked": True}, indent=2)
    if not (1 <= screen_id <= 4):
        return json.dumps({"error": "screen_id must be between 1 and 4", "blocked": True}, indent=2)
    if action == "store" and not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "Destructive operation blocked. Set confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)
    if action == "label" and not view_name:
        return json.dumps(
            {"error": "view_name is required for action='label'", "blocked": True},
            indent=2,
        )

    ref = f"{screen_id}.{view_id}"
    if action == "store":
        cmd = f"store ViewButton {ref}"
        risk_tier = "DESTRUCTIVE"
    elif action == "recall":
        cmd = f"ViewButton {ref}"
        risk_tier = "SAFE_WRITE"
    else:
        cmd = f'label ViewButton {ref} "{view_name}"'
        risk_tier = "SAFE_WRITE"

    client = await _sc.get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": risk_tier,
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.CUE_STORE)
@_handle_errors
async def export_objects(
    object_type: str,
    object_id: str,
    filename: str,
    style: str | None = None,
    overwrite: bool = False,
    confirm_destructive: bool = False,
) -> str:
    """
    Export objects from the show file to disk (DESTRUCTIVE — writes files).

    Files are written to the grandMA2 data directory. MA2 routes each type
    to its own subfolder automatically:
      - Macro → macros/    Effect → effects/    Plugin → plugins/
      - MAtricks → matricks/    Mask → masks/
      - All others → importexport/

    On this system: C:\\ProgramData\\MA Lighting Technologies\\grandma\\gma2_V_3.9.60\\

    Supported object types (19 validated):
      group, preset, macro, effect, sequence, view, page, camera, layout,
      form, plugin, matricks, mask, image, executor, timecode, userprofile,
      channel, screen

    Preset syntax for object_id:
      - Single preset:  "1.3"  (type 1=Dimmer, 2=Position, 3=Gobo, 4=Color,
                                 5=Beam, 6=Focus, 7=Control, 8=Shapers, 9=Video)
      - All of a type:  "1"    (exports all dimmer presets)
      - Range:          "1 thru 5"

    Args:
        object_type: Object type (case-insensitive)
        object_id: ID, preset ref ("1.3"), range ("1 thru 5"), or name (UserProfile)
        filename: Output filename — no extension, no path needed
        style: "csv" or "html" — default is xml
        overwrite: Replace existing file without prompting
        confirm_destructive: Must be True to execute

    Returns:
        str: JSON with command_sent, raw_response, risk_tier, data_path
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "Export writes files to disk. Set confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    if object_type.lower() not in _EXPORT_TYPES:
        return json.dumps({
            "error": (
                f"Invalid object_type '{object_type}'. "
                f"Valid types: {sorted(_EXPORT_TYPES)}"
            ),
            "blocked": True,
        }, indent=2)

    if style is not None and style.lower() not in ("csv", "html"):
        return json.dumps(
            {"error": "style must be 'csv' or 'html' (omit for default xml)", "blocked": True},
            indent=2,
        )

    cmd = build_export_object(
        object_type,
        object_id,
        filename,
        overwrite=overwrite,
        noconfirm=True,
        style=style,
    )

    client = await _sc.get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "risk_tier": "DESTRUCTIVE",
        "data_path": _IMPORT_EXPORT_DATA_ROOT,
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.FIXTURE_IMPORT)
@_handle_errors
async def import_objects(
    filename: str,
    destination_type: str,
    destination_id: str | None = None,
    quiet: bool = False,
    confirm_destructive: bool = False,
) -> str:
    """
    Import objects from a file into the show (DESTRUCTIVE — modifies show file).

    MA2 locates the file using the destination type to determine the correct
    subfolder automatically (same routing as export). The file must exist in
    the grandMA2 data directory before calling this tool.

    Files are read from: C:\\ProgramData\\MA Lighting Technologies\\grandma\\gma2_V_3.9.60\\
      - Macro → macros/    Effect → effects/    Plugin → plugins/
      - MAtricks → matricks/    Mask → masks/
      - All others → importexport/

    Supported destination types (17 validated):
      group, preset, macro, effect, sequence, view, page, camera, layout,
      form, plugin, matricks, mask, image, executor, timecode, userprofile

    (Screen is export-only — import gives RESIZE FORBIDDEN error.)

    Preset destination_id format: "T.N"  e.g. "1.99" = Dimmer slot 99

    Args:
        filename: Source filename — no extension, no path needed
        destination_type: Object type for placement (REQUIRED — MA2 Error #28 without it)
        destination_id: Slot number or preset ref ("T.N"). None = next free slot.
        quiet: Suppress MA2 feedback output during import
        confirm_destructive: Must be True to execute

    Returns:
        str: JSON with command_sent, raw_response, risk_tier
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "Import modifies the show file. Set confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    if destination_type.lower() not in _IMPORT_TYPES:
        return json.dumps({
            "error": (
                f"Invalid destination_type '{destination_type}'. "
                f"Valid types: {sorted(_IMPORT_TYPES)}"
            ),
            "blocked": True,
        }, indent=2)

    cmd = build_import_object(
        filename,
        destination_type,
        destination_id,
        noconfirm=True,
        quiet=quiet,
    )

    client = await _sc.get_client()

    # Pre-import slot check — informational only
    slot_status: dict | None = None
    if destination_id is not None:
        try:
            slot_int = int(str(destination_id).split(".")[0])
            avail = await _check_pool_slots(
                client, destination_type,
                start_from=slot_int, scan_up_to=slot_int,
            )
            is_occupied = any(
                s["slot"] == slot_int for s in avail["occupied_slots"]
            )
            slot_status = {"occupied": is_occupied}
            if is_occupied:
                match = next(
                    s for s in avail["occupied_slots"] if s["slot"] == slot_int
                )
                slot_status["previous_name"] = match["name"]
        except (ValueError, TypeError):
            pass  # non-numeric destination_id (e.g. preset "2.5")

    raw_response = await client.send_command_with_response(cmd)

    result: dict = {
        "command_sent": cmd,
        "raw_response": raw_response,
        "risk_tier": "DESTRUCTIVE",
    }
    if slot_status is not None:
        result["slot_status"] = slot_status

    return json.dumps(result, indent=2)


# ============================================================


@mcp.tool()
@require_scope(OAuthScope.FIXTURE_IMPORT)
@_handle_errors
async def import_fixture_type(
    manufacturer: str,
    fixture: str,
    mode: str,
    confirm_destructive: bool = False,
) -> str:
    """
    Import a fixture type from the MA2 library into the show (DESTRUCTIVE).

    Navigates to EditSetup/FixtureTypes context, imports the fixture type
    by 'manufacturer@fixture@mode' key, then returns to root context.

    Use list_library(library_type="fixture") first to find the exact key values.

    Args:
        manufacturer: Manufacturer name exactly as in MA2 library (e.g. "Martin", "Generic")
        fixture: Fixture model name (e.g. "Mac700Profile_Extended")
        mode: Mode name (e.g. "Extended", "Standard")
        confirm_destructive: Must be True to execute

    Returns:
        str: JSON with steps list (command + response per step), fixture_key, risk_tier
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "Import fixture type modifies the show. Set confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    client = await _sc.get_client()
    sequence = [
        'ChangeDest "EditSetup"',
        'ChangeDest "FixtureTypes"',
        build_import_fixture_type_cmd(manufacturer, fixture, mode),
        'ChangeDest /',
    ]
    steps = []
    for cmd in sequence:
        raw = await client.send_command_with_response(cmd)
        steps.append({"command": cmd, "response": raw})

    return json.dumps({
        "steps": steps,
        "fixture_key": f"{manufacturer}@{fixture}@{mode}",
        "risk_tier": "DESTRUCTIVE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.FIXTURE_IMPORT)
@_handle_errors
async def import_fixture_layer(
    filename: str,
    layer_index: int | None = None,
    confirm_destructive: bool = False,
) -> str:
    """
    Import a fixture layer XML file into the show patch (DESTRUCTIVE).

    Navigates to EditSetup/Layers context, imports the XML layer file,
    then returns to root context. Use generate_fixture_layer_xml to
    create the XML file before calling this tool.

    The file must exist in the MA2 importexport directory:
      C:\\ProgramData\\MA Lighting Technologies\\grandma\\gma2_V_3.9.60\\importexport\\

    Args:
        filename: Layer XML filename without extension or path
        layer_index: Target layer slot. None = MA2 picks next free slot
        confirm_destructive: Must be True to execute

    Returns:
        str: JSON with steps list (command + response per step), filename, risk_tier
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "Import fixture layer modifies the show patch. Set confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    client = await _sc.get_client()
    sequence = [
        'ChangeDest "EditSetup"',
        'ChangeDest "Layers"',
        build_import_layer_cmd(filename, layer_index),
        'ChangeDest /',
    ]
    steps = []
    for cmd in sequence:
        raw = await client.send_command_with_response(cmd)
        steps.append({"command": cmd, "response": raw})

    return json.dumps({
        "steps": steps,
        "filename": filename,
        "layer_index": layer_index,
        "risk_tier": "DESTRUCTIVE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def generate_fixture_layer_xml(
    filename: str,
    layer_name: str,
    layer_index: int,
    fixtures: list[dict],
    showfile: str = "grandma2",
    overwrite: bool = False,
    confirm_destructive: bool = False,
) -> str:
    """
    Generate a grandMA2 fixture layer XML file and save it to the importexport directory (DESTRUCTIVE).

    The output file can be imported immediately using import_fixture_layer.
    No telnet connection required — this tool writes a local file only.

    Output directory:
      C:\\ProgramData\\MA Lighting Technologies\\grandma\\gma2_V_3.9.60\\importexport\\

    Each fixture dict must contain:
        fixture_id (int): grandMA2 fixture ID (e.g. 111)
        name (str): Display name (e.g. "Dim 1" or "Mac 700 1")
        fixture_type_no (int): Fixture type number from list_fixture_types()
        fixture_type_name (str): Display name of the fixture type
        dmx_address (int): 1-based DMX start address within its universe
        num_channels (int): Total DMX channel count for this fixture type

    Args:
        filename: Output filename without extension
        layer_name: Layer display name shown in MA2 UI
        layer_index: Layer index number (1-based) for the <Layer> XML element
        fixtures: List of fixture parameter dicts (see schema above)
        showfile: Show name embedded in XML <Info> element
        overwrite: If True, overwrite existing file; if False, return error on conflict
        confirm_destructive: Must be True to execute (writes files to console importexport directory)

    Returns:
        str: JSON with file_path, filename, fixture_count, layer_index, layer_name
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "Generate Fixture Layer XML writes files to disk. Pass confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    from datetime import datetime
    from xml.dom import minidom
    from xml.etree.ElementTree import Element, SubElement, tostring

    output_dir = (
        r"C:\ProgramData\MA Lighting Technologies"
        r"\grandma\gma2_V_3.9.60\importexport"
    )
    file_path = os.path.join(output_dir, f"{filename}.xml")

    if os.path.exists(file_path) and not overwrite:
        return json.dumps({
            "error": (
                f"File already exists: {file_path}. "
                "Pass overwrite=True to replace it."
            ),
        }, indent=2)

    root = Element("MA", {
        "major_vers": "3",
        "minor_vers": "9",
        "stream_vers": "60",
    })
    SubElement(root, "Info", {
        "datetime": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S"),
        "showfile": showfile,
    })
    layer_el = SubElement(root, "Layer", {
        "index": str(layer_index),
        "name": layer_name,
    })

    for idx, fx in enumerate(fixtures):
        fx_el = SubElement(layer_el, "Fixture", {
            "index": str(idx),
            "name": fx["name"],
            "fixture_id": str(fx["fixture_id"]),
        })
        ft_el = SubElement(fx_el, "FixtureType", {"name": fx["fixture_type_name"]})
        SubElement(ft_el, "No").text = str(fx["fixture_type_no"])

        sf_el = SubElement(fx_el, "SubFixture", {
            "index": "0",
            "react_to_grandmaster": "true",
            "color": "ffffff",
        })
        patch_el = SubElement(sf_el, "Patch")
        SubElement(patch_el, "Address").text = str(fx["dmx_address"])

        pos_el = SubElement(sf_el, "AbsolutePosition")
        SubElement(pos_el, "Location", {"x": "0", "y": "0", "z": "0"})
        SubElement(pos_el, "Rotation", {"x": "0", "y": "-0", "z": "0"})
        SubElement(pos_el, "Scaling", {"x": "1", "y": "1", "z": "1"})

        for ch in range(fx["num_channels"]):
            SubElement(sf_el, "Channel", {"index": str(ch)})

    raw_xml = tostring(root, encoding="unicode")
    pretty_bytes = minidom.parseString(raw_xml).toprettyxml(indent="  ", encoding="utf-8")
    # Replace minidom's XML declaration (includes standalone attr) with a clean one
    lines = pretty_bytes.split(b"\n")
    xml_bytes = b'<?xml version="1.0" encoding="utf-8"?>\n' + b"\n".join(lines[1:])

    os.makedirs(output_dir, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(xml_bytes)

    return json.dumps({
        "file_path": file_path,
        "filename": filename,
        "fixture_count": len(fixtures),
        "layer_index": layer_index,
        "layer_name": layer_name,
    }, indent=2)


# ============================================================


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def list_fixtures(
    fixture_id: int | None = None,
) -> str:
    """
    List fixtures defined on the console, or check a specific fixture exists.

    This is the correct way to discover fixture IDs before using park_fixture,
    unpark_fixture, set_intensity, or set_attribute. Note: 'cd Fixture' is NOT
    a valid MA2 navigation destination — this tool uses 'list fixture' instead.

    Args:
        fixture_id: Optional fixture ID to inspect. If None, lists all fixtures.

    Returns:
        str: JSON with command_sent, raw_response, exists (bool), fixture_id.
             exists is always True when fixture_id is None (listing all).

    Examples:
        - List all fixtures: list_fixtures()
        - Check fixture 20: list_fixtures(fixture_id=20)
        - Check fixture 1 (likely missing): list_fixtures(fixture_id=1)
    """
    client = await _sc.get_client()

    if fixture_id is not None:
        cmd = f"list fixture {fixture_id}"
        raw = await client.send_command_with_response(cmd)
        exists = "NO OBJECTS FOUND" not in raw.upper()
    else:
        cmd = "list fixture"
        raw = await client.send_command_with_response(cmd)
        exists = True

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "exists": exists,
        "fixture_id": fixture_id,
        "risk_tier": "SAFE_READ",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def list_sequence_cues(
    sequence_id: int | None = None,
    executor_id: int | None = None,
    executor_page: int = 1,
    cue_id: int | float | None = None,
) -> str:
    """
    List cues in a sequence, or check whether a specific cue exists.

    Supports two ways to identify the sequence:
      - sequence_id: Direct sequence number (e.g. 278)
      - executor_id: Executor number — sequence is resolved via
        'list executor PAGE.ID' before listing cues

    If both are supplied, sequence_id takes precedence.

    Validated MA2 probes used:
      'list cue sequence N'     → all cues in sequence N
      'list cue M sequence N'   → specific cue M in sequence N
      'list executor P.E'       → resolve sequence from executor

    Args:
        sequence_id: Sequence number to inspect.
        executor_id: Executor number — resolved to its linked sequence.
        executor_page: Executor page for resolution (default 1).
        cue_id: Optional specific cue to check for existence.

    Returns:
        str: JSON with command_sent, raw_response, exists, resolved_sequence_id,
             and executor_probe_response (when executor_id was used).

    Examples:
        - All cues in seq 278: list_sequence_cues(sequence_id=278)
        - Cue 5 in seq 278: list_sequence_cues(sequence_id=278, cue_id=5)
        - Cues for executor 1: list_sequence_cues(executor_id=1)
        - Check cue 99 on executor 1: list_sequence_cues(executor_id=1, cue_id=99)
    """
    client = await _sc.get_client()
    executor_probe_response: str | None = None

    resolved_sequence = sequence_id
    if resolved_sequence is None and executor_id is not None:
        resolved_sequence, executor_probe_response = await _get_sequence_for_executor(
            client, executor_id, page=executor_page
        )
        if resolved_sequence is None:
            return json.dumps({
                "command_sent": f"list executor {executor_page}.{executor_id}",
                "raw_response": executor_probe_response,
                "error": (
                    f"Could not resolve a sequence for executor "
                    f"{executor_page}.{executor_id}. "
                    "The executor may not have a sequence assigned."
                ),
                "exists": False,
                "resolved_sequence_id": None,
                "risk_tier": "SAFE_READ",
                "blocked": True,
            }, indent=2)

    if resolved_sequence is None:
        return json.dumps({
            "error": "Must supply either sequence_id or executor_id.",
            "command_sent": None,
            "risk_tier": "SAFE_READ",
            "blocked": True,
        }, indent=2)

    if cue_id is not None:
        cmd = f"list cue {cue_id} sequence {resolved_sequence}"
    else:
        cmd = f"list cue sequence {resolved_sequence}"

    raw = await client.send_command_with_response(cmd)
    exists = "NO OBJECTS FOUND" not in raw.upper() if cue_id is not None else True

    result: dict = {
        "command_sent": cmd,
        "raw_response": raw,
        "exists": exists,
        "resolved_sequence_id": resolved_sequence,
        "risk_tier": "SAFE_READ",
    }
    if executor_probe_response is not None:
        result["executor_probe_response"] = executor_probe_response

    return json.dumps(result, indent=2)


# ============================================================


@mcp.tool()
@require_scope(OAuthScope.PROGRAMMER_WRITE)
@_handle_errors
async def highlight_fixtures(on: bool = True) -> str:
    """
    Toggle highlight mode for the currently selected fixtures.

    Highlight mode temporarily sets selected fixtures to full intensity to help
    identify them on stage. Easily reversible (toggle off).

    Args:
        on: True to enable, False to disable highlight mode.

    Returns:
        str: JSON with command_sent, raw_response, risk_tier.
    """
    cmd = build_highlight(on)
    client = await _sc.get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PLAYBACK_GO)
@_handle_errors
async def blackout_toggle() -> str:
    """
    Toggle master blackout (kills all lighting output).

    Blackout is a toggle — call once to enable, again to disable.
    SAFE_WRITE because it is easily reversible.

    Returns:
        str: JSON with command_sent, raw_response, risk_tier.
    """
    cmd = build_blackout()
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
async def list_shows() -> str:
    """
    List available show files on the console.

    Returns:
        str: JSON with command_sent, raw_response, risk_tier.
    """
    cmd = build_list_shows()
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
async def load_show(
    name: str,
    confirm_destructive: bool = False,
) -> str:
    """
    Load an existing show file (DESTRUCTIVE — replaces current show).

    Args:
        name: Show file name to load.
        confirm_destructive: Must be True to proceed.

    Returns:
        str: JSON with command_sent, raw_response, risk_tier.
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "LoadShow replaces the current show. Set confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    cmd = build_load_show(name)
    client = await _sc.get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "DESTRUCTIVE",
        "blocked": False,
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.SHOW_LOAD)
@_handle_errors
async def new_show(
    name: str,
    confirm_destructive: bool = False,
    preserve_connectivity: bool = True,
    keep_timeconfig: bool = False,
    keep_globalsettings: bool = False,
    keep_localsettings: bool = False,
    keep_protocols: bool = False,
    keep_network: bool = False,
    keep_user: bool = False,
) -> str:
    """
    Create a new empty show (DESTRUCTIVE — replaces current show).

    CONNECTIVITY WARNING
    --------------------
    Creating a new show clears Global Settings, which **disables Telnet login**
    and severs the MCP connection.  ``preserve_connectivity=True`` (the default)
    automatically adds /globalsettings + /network + /protocols so Telnet stays
    enabled and network/DMX config is preserved.

    Set ``preserve_connectivity=False`` only if you intend to manually
    re-enable Telnet on the console afterwards (Setup → Console → Global
    Settings → Telnet → Login Enabled).

    Keep flags (correspond to un-checking "Clear …" in the MA2 New Show dialog):

    | Flag               | Dialog checkbox          | MA2 flag        | Included by preserve_connectivity |
    |--------------------|--------------------------|-----------------|-----------------------------------|
    | keep_globalsettings| Clear Global Settings    | /globalsettings | YES — contains Telnet login       |
    | keep_network       | Clear Network Config     | /network        | YES — IP / MA-Net2 config         |
    | keep_protocols     | Clear Network Protocols  | /protocols      | YES — Art-Net, sACN, etc.         |
    | keep_timeconfig    | Clear Time Config        | /timeconfig     | no                                |
    | keep_localsettings | Clear Local Settings     | /localsettings  | no                                |
    | keep_user          | Clear User Profiles      | /user           | no                                |

    Args:
        name: New show file name.
        confirm_destructive: Must be True to proceed.
        preserve_connectivity: Auto-add /globalsettings + /network + /protocols
            to prevent Telnet being disabled (default True).
        keep_timeconfig: Preserve Time Config from current show.
        keep_globalsettings: Preserve Global Settings (overrides preserve_connectivity).
        keep_localsettings: Preserve Local Settings from current show.
        keep_protocols: Preserve Network Protocol settings (overrides preserve_connectivity).
        keep_network: Preserve Network Config (overrides preserve_connectivity).
        keep_user: Preserve User Profiles from current show.

    Returns:
        str: JSON with command_sent, raw_response, risk_tier,
             and connectivity_flags listing which flags were applied.

    AI assistant guidance
    ---------------------
    Always confirm ``preserve_connectivity=True`` unless the user explicitly
    wants a completely clean show AND understands Telnet will be disabled.
    Ask about keep_timeconfig, keep_localsettings, keep_user separately —
    these have no connectivity impact and are purely about preserving show data.
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "NewShow replaces the current show. Set confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    # Merge preserve_connectivity defaults with explicit flags
    effective_globalsettings = keep_globalsettings or preserve_connectivity
    effective_network = keep_network or preserve_connectivity
    effective_protocols = keep_protocols or preserve_connectivity

    # /noconfirm is always needed — the telnet connection is stateless
    # (each call reconnects) so it cannot answer the console's
    # "save old show first?" dialog mid-stream.
    cmd = build_new_show(
        name,
        noconfirm=True,
        keep_timeconfig=keep_timeconfig,
        keep_globalsettings=effective_globalsettings,
        keep_localsettings=keep_localsettings,
        keep_protocols=effective_protocols,
        keep_network=effective_network,
        keep_user=keep_user,
    )
    client = await _sc.get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "DESTRUCTIVE",
        "blocked": False,
        "preserve_connectivity": preserve_connectivity,
        "connectivity_flags": {
            "globalsettings": effective_globalsettings,
            "network": effective_network,
            "protocols": effective_protocols,
        },
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def list_preset_pool(
    preset_type: str | None = None,
) -> str:
    """
    List presets stored in the show's Global preset pool.

    Without arguments: returns all PresetPool entries with their counts
    (Dimmer, Position, Gobo, Color, Beam, Focus, Control, Shapers, Video).

    With preset_type: navigates into that pool and lists individual presets
    with their slot number, name, and Special field.

    CD tree path navigated:
      cd 17 → cd 1 → list             (pool overview)
      cd 17 → cd 1 → cd N → list      (individual preset type)

    Pool index → type mapping (live-verified v3.9.60.65):
      0=ALL  1=DIMMER  2=POSITION  3=GOBO  4=COLOR
      5=BEAM  6=FOCUS  7=CONTROL  8=SHAPERS  9=VIDEO

    Note: The "Special" column shows "Normal" (standard) or "Embedded" — it
    does NOT indicate Universal vs Selective scope. Scope is an internal flag
    only visible in the console GUI or show XML.

    Args:
        preset_type: Optional type to drill into. Accepts name ("color", "position")
            or number ("4"). If omitted, returns pool overview.

    Returns:
        str: JSON with pool overview or individual preset list.
    """
    from src.commands.constants import PRESET_TYPES

    client = await _sc.get_client()

    # Navigate to Global preset pool
    await navigate(client, "/")
    await navigate(client, "17")
    await navigate(client, "1")

    if preset_type is None:
        # Overview: list all pools
        lst = await list_destination(client)
        await navigate(client, "/")
        return json.dumps({
            "cd_path": "17.1",
            "description": "Global PresetPool overview",
            "raw_response": lst.raw_response if lst else "",
            "entries": [
                {"type": e.object_type, "id": e.object_id, "name": e.name}
                for e in (lst.parsed_list.entries if lst and lst.parsed_list else [])
            ],
            "risk_tier": "SAFE_READ",
        }, indent=2)

    # Resolve preset_type to pool index
    try:
        pool_idx = int(preset_type)
    except (ValueError, TypeError):
        pool_idx = PRESET_TYPES.get(str(preset_type).lower())
        if pool_idx is None:
            await navigate(client, "/")
            return json.dumps({
                "error": f"Unknown preset_type {preset_type!r}. Use name (color, position) or number 1-9."
            }, indent=2)

    await navigate(client, str(pool_idx))
    lst = await list_destination(client)
    await navigate(client, "/")

    return json.dumps({
        "cd_path": f"17.1.{pool_idx}",
        "preset_type": preset_type,
        "pool_index": pool_idx,
        "raw_response": lst.raw_response if lst else "",
        "entries": [
            {"type": e.object_type, "id": e.object_id, "name": e.name}
            for e in (lst.parsed_list.entries if lst and lst.parsed_list else [])
        ],
        "risk_tier": "SAFE_READ",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def list_undo_history() -> str:
    """
    Display the undo (Oops) history.

    Returns:
        str: JSON with command_sent, raw_response, risk_tier.
    """
    cmd = build_list_oops()
    client = await _sc.get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "SAFE_READ",
    }, indent=2)


# ============================================================


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def list_fixture_types() -> str:
    """
    List all fixture types in the show (from LiveSetup/FixtureTypes).

    Navigates to cd 10 (LiveSetup) -> cd 3 (FixtureTypes) -> list -> cd /

    Returns:
        str: JSON with raw_response, entries (fixture type names, manufacturers,
             DMX footprint), risk_tier.
    """
    client = await _sc.get_client()
    commands_sent = []

    # Navigate to root
    nav = await navigate(client, "/")
    commands_sent.append(nav.command_sent)

    # Navigate to LiveSetup
    nav = await navigate(client, "10")
    commands_sent.append(nav.command_sent)

    # Navigate to FixtureTypes
    nav = await navigate(client, "3")
    commands_sent.append(nav.command_sent)

    # List
    lst = await list_destination(client)
    commands_sent.append(lst.command_sent)

    # Return to root
    nav = await navigate(client, "/")
    commands_sent.append(nav.command_sent)

    entries = [
        {"object_type": e.object_type, "object_id": e.object_id, "name": e.name}
        for e in lst.parsed_list.entries
    ]

    return json.dumps({
        "commands_sent": commands_sent,
        "raw_response": lst.raw_response,
        "entries": entries,
        "entry_count": len(entries),
        "risk_tier": "SAFE_READ",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def list_layers() -> str:
    """
    List all fixture layers in the show (from LiveSetup/Layers).

    Navigates to cd 10 (LiveSetup) -> cd 4 (Layers) -> list -> cd /

    Returns:
        str: JSON with raw_response, entries (layer names, fixture ranges),
             risk_tier.
    """
    client = await _sc.get_client()
    commands_sent = []

    nav = await navigate(client, "/")
    commands_sent.append(nav.command_sent)

    nav = await navigate(client, "10")
    commands_sent.append(nav.command_sent)

    nav = await navigate(client, "4")
    commands_sent.append(nav.command_sent)

    lst = await list_destination(client)
    commands_sent.append(lst.command_sent)

    nav = await navigate(client, "/")
    commands_sent.append(nav.command_sent)

    return json.dumps({
        "commands_sent": commands_sent,
        "raw_response": lst.raw_response,
        "risk_tier": "SAFE_READ",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def list_universes(
    max_universes: int = 16,
) -> str:
    """
    List DMX universes and their configuration (from LiveSetup/Universes).

    Navigates to cd 10 (LiveSetup) -> cd 5 (Universes) -> list -> cd /

    Args:
        max_universes: Limit output to first N universes (default 16, max 256).

    Returns:
        str: JSON with raw_response, risk_tier.
    """
    client = await _sc.get_client()
    commands_sent = []

    nav = await navigate(client, "/")
    commands_sent.append(nav.command_sent)

    nav = await navigate(client, "10")
    commands_sent.append(nav.command_sent)

    nav = await navigate(client, "5")
    commands_sent.append(nav.command_sent)

    lst = await list_destination(client)
    commands_sent.append(lst.command_sent)

    nav = await navigate(client, "/")
    commands_sent.append(nav.command_sent)

    # Truncate raw response if too many universes
    entries = [
        {"object_type": e.object_type, "object_id": e.object_id, "name": e.name}
        for e in lst.parsed_list.entries[:max_universes]
    ]

    return json.dumps({
        "commands_sent": commands_sent,
        "raw_response": lst.raw_response[:2000] if len(lst.raw_response) > 2000 else lst.raw_response,
        "entries": entries,
        "entry_count": len(lst.parsed_list.entries),
        "showing": min(max_universes, len(lst.parsed_list.entries)),
        "risk_tier": "SAFE_READ",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def list_library(
    library_type: str = "fixture",
) -> str:
    """
    Browse the console's built-in libraries.

    Args:
        library_type: "fixture" (ListLibrary), "effect" (ListEffectLibrary),
                      or "macro" (ListMacroLibrary).

    Returns:
        str: JSON with command_sent, raw_response, risk_tier.
    """
    valid_types = ("fixture", "effect", "macro")
    if library_type not in valid_types:
        return json.dumps({
            "error": f"library_type must be one of {valid_types}",
            "blocked": True,
        }, indent=2)

    if library_type == "fixture":
        cmd = build_list_library()
    elif library_type == "effect":
        cmd = build_list_effect_library()
    else:
        cmd = build_list_macro_library()

    client = await _sc.get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "SAFE_READ",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PROGRAMMER_WRITE)
@_handle_errors
async def manage_matricks(
    action: str,
    value: int | None = None,
    x: int | None = None,
    y: int | None = None,
    column: int | None = None,
    increment: str | None = None,
    name: str | None = None,
    mode: str | None = None,
    turn_off: bool = False,
) -> str:
    """
    Control MAtricks selection patterns via direct command keywords (SAFE_WRITE).

    Uses grandMA2 MAtricks command keywords that act directly on the current
    fixture selection — no navigation required.

    Actions and their parameters:
      - "interleave": Set virtual grid width. Params: value (width), column, increment (+/-), turn_off.
      - "blocks": Set block size. Params: value (size), x, y (x.y notation), increment (+ N/- N), turn_off.
      - "groups": Set align group size. Params: value (size), x, y (x.y notation), increment (+ N/- N), turn_off.
      - "wings": Set wing/mirror parts. Params: value (parts), increment (+/-), turn_off.
      - "filter": Set sub-selection filter. Params: value (filter_num), name (filter name), increment (+/-), turn_off.
      - "reset": Clear all MAtricks settings. No params.
      - "recall": Recall a MAtricks pool object or toggle mode. Params: value (matricks_id), mode (on/off/toggle).
      - "all": Reset Single X sub-selection. No params.
      - "allrows": Reset Single Y sub-selection. No params.
      - "next": Step forward through Single X sub-selection. No params.
      - "previous": Step backward through Single X sub-selection. No params.
      - "nextrow": Step forward through Single Y (row) sub-selection. No params.

    Args:
        action: The MAtricks action to perform.
        value: Primary numeric value (width/size/parts/filter_num/matricks_id).
        x: X-axis value for blocks/groups x.y notation.
        y: Y-axis value for blocks/groups x.y notation.
        column: Column for interleave column.width notation.
        increment: Step value: "+", "-", "+ N", or "- N".
        name: Filter name (for action="filter").
        mode: "on", "off", or "toggle" (for action="recall").
        turn_off: Send the "Off" variant of the command.

    Returns:
        str: JSON with command_sent, raw_response, risk_tier.
    """
    from src.commands import (
        all_rows_sub_selection as _build_all_rows,
    )
    from src.commands import (
        all_sub_selection as _build_all,
    )
    from src.commands import (
        matricks_blocks as _build_blocks,
    )
    from src.commands import (
        matricks_filter as _build_filter,
    )
    from src.commands import (
        matricks_groups as _build_groups,
    )
    from src.commands import (
        matricks_interleave as _build_interleave,
    )
    from src.commands import (
        matricks_reset as _build_reset,
    )
    from src.commands import (
        matricks_wings as _build_wings,
    )
    from src.commands import (
        next_row_sub_selection as _build_next_row,
    )
    from src.commands import (
        next_sub_selection as _build_next,
    )
    from src.commands import (
        previous_sub_selection as _build_previous,
    )
    from src.commands import (
        recall_matricks as _build_recall,
    )

    action_lower = action.lower()
    try:
        if action_lower == "interleave":
            cmd = _build_interleave(
                width=value, column=column,
                increment=increment, off=turn_off,
            )
        elif action_lower == "blocks":
            cmd = _build_blocks(
                size=value, x=x, y=y,
                increment=increment, off=turn_off,
            )
        elif action_lower == "groups":
            cmd = _build_groups(
                size=value, x=x, y=y,
                increment=increment, off=turn_off,
            )
        elif action_lower == "wings":
            cmd = _build_wings(
                parts=value, increment=increment, off=turn_off,
            )
        elif action_lower == "filter":
            cmd = _build_filter(
                filter_num=value, name=name,
                increment=increment, off=turn_off,
            )
        elif action_lower == "reset":
            cmd = _build_reset()
        elif action_lower == "recall":
            cmd = _build_recall(matricks_id=value, mode=mode)
        elif action_lower == "all":
            cmd = _build_all()
        elif action_lower == "allrows":
            cmd = _build_all_rows()
        elif action_lower == "next":
            cmd = _build_next()
        elif action_lower == "previous":
            cmd = _build_previous()
        elif action_lower == "nextrow":
            cmd = _build_next_row()
        else:
            return json.dumps({
                "error": f"Unknown action: {action!r}. Valid: interleave, blocks, groups, wings, filter, reset, recall, all, allrows, next, previous, nextrow.",
                "risk_tier": "SAFE_WRITE",
            }, indent=2)
    except ValueError as exc:
        return json.dumps({
            "error": str(exc),
            "risk_tier": "SAFE_WRITE",
        }, indent=2)

    client = await _sc.get_client()
    raw = await client.send_command_with_response(cmd)

    # Update in-memory write-tracker (Gap 6 — no telnet readback for MAtricks state)
    if snap := _orchestrator.last_snapshot:
        mt = snap.matricks
        if action_lower == "reset":
            mt.reset()
        elif action_lower == "interleave":
            mt.interleave = None if turn_off else (value or 1)
        elif action_lower == "blocks":
            mt.blocks_x = None if turn_off else (x or value or 1)
            mt.blocks_y = None if turn_off else (y or 1)
        elif action_lower == "groups":
            mt.groups_x = None if turn_off else (x or value or 1)
            mt.groups_y = None if turn_off else (y or 1)
        elif action_lower == "wings":
            mt.wings = None if turn_off else (value or 1)
        elif action_lower == "filter":
            mt.filter_id = None if turn_off else (value or None)
        elif action_lower == "recall":
            mt.active = True
        # all/allrows/next/previous/nextrow are selection steps — no persistent state to track

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.GROUP_STORE)
@_handle_errors
async def store_matricks_preset(
    pool_slot: int,
    name: str,
    interleave: int | None = None,
    blocks: int | None = None,
    blocks_y: int | None = None,
    groups: int | None = None,
    groups_y: int | None = None,
    wings: int | None = None,
    filter_num: int | None = None,
    filter_name: str | None = None,
    reset_first: bool = True,
    confirm_destructive: bool = False,
) -> str:
    """
    Set MAtricks state, store to pool, and label — all in one call (DESTRUCTIVE).

    Workflow:
      1. Optionally resets all MAtricks settings (reset_first=True, default)
      2. Applies specified MAtricks settings (interleave, blocks, groups, wings, filter)
      3. Stores current MAtricks state to the specified pool slot (/overwrite)
      4. Labels the pool object with the given name

    At least one MAtricks setting must be provided.

    Args:
        pool_slot: Pool slot number to store into (e.g. 2).
        name: Label for the stored MAtricks object (e.g. "Wings-2-I4").
        interleave: Virtual grid width (MAtricksInterleave).
        blocks: Block size X (MAtricksBlocks). Use with blocks_y for x.y.
        blocks_y: Block size Y (requires blocks for x.y notation).
        groups: Align group size X (MAtricksGroups). Use with groups_y for x.y.
        groups_y: Align group size Y (requires groups for x.y notation).
        wings: Wing/mirror parts (MAtricksWings).
        filter_num: Filter number (MAtricksFilter).
        filter_name: Filter name (MAtricksFilter, e.g. "OddID").
        reset_first: Reset all MAtricks before applying (default True).
        confirm_destructive: Must be True to execute (DESTRUCTIVE operation).

    Returns:
        str: JSON with commands_sent list, pool_slot, name, risk_tier.
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "store_matricks_preset modifies the MAtricks pool. Pass confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    from src.commands import (
        label as _build_label,
    )
    from src.commands import (
        matricks_blocks as _build_blocks,
    )
    from src.commands import (
        matricks_filter as _build_filter,
    )
    from src.commands import (
        matricks_groups as _build_groups,
    )
    from src.commands import (
        matricks_interleave as _build_interleave,
    )
    from src.commands import (
        matricks_reset as _build_reset,
    )
    from src.commands import (
        matricks_wings as _build_wings,
    )
    from src.commands import (
        store_matricks as _build_store_matricks,
    )

    # Validate: at least one setting must be provided
    has_setting = any(v is not None for v in [
        interleave, blocks, groups, wings, filter_num, filter_name,
    ])
    if not has_setting:
        return json.dumps({
            "error": "At least one MAtricks setting must be provided (interleave, blocks, groups, wings, filter_num, or filter_name).",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    client = await _sc.get_client()
    commands_sent = []

    # Step 1: Reset if requested
    if reset_first:
        cmd = _build_reset()
        await client.send_command(cmd)
        commands_sent.append(cmd)

    # Step 2: Apply settings
    if interleave is not None:
        cmd = _build_interleave(width=interleave)
        await client.send_command(cmd)
        commands_sent.append(cmd)

    if blocks is not None:
        if blocks_y is not None:
            cmd = _build_blocks(x=blocks, y=blocks_y)
        else:
            cmd = _build_blocks(size=blocks)
        await client.send_command(cmd)
        commands_sent.append(cmd)

    if groups is not None:
        if groups_y is not None:
            cmd = _build_groups(x=groups, y=groups_y)
        else:
            cmd = _build_groups(size=groups)
        await client.send_command(cmd)
        commands_sent.append(cmd)

    if wings is not None:
        cmd = _build_wings(parts=wings)
        await client.send_command(cmd)
        commands_sent.append(cmd)

    if filter_num is not None or filter_name is not None:
        cmd = _build_filter(filter_num=filter_num, name=filter_name)
        await client.send_command(cmd)
        commands_sent.append(cmd)

    # Step 3: Store to pool slot
    store_cmd = _build_store_matricks(pool_slot, overwrite=True)
    raw_store = await client.send_command_with_response(store_cmd)
    commands_sent.append(store_cmd)

    # Step 4: Label the pool object
    label_cmd = _build_label("matricks", pool_slot, name)
    raw_label = await client.send_command_with_response(label_cmd)
    commands_sent.append(label_cmd)

    return json.dumps({
        "commands_sent": commands_sent,
        "pool_slot": pool_slot,
        "name": name,
        "store_response": raw_store[:200],
        "label_response": raw_label[:200],
        "risk_tier": "DESTRUCTIVE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def discover_filter_attributes() -> str:
    """
    Discover actual filter attributes from the current show's fixture library (SAFE_READ).

    Browses PresetTypes 1-7 (Dimmer through Control) at depth 2 to collect
    attribute names from all patched fixture types. Returns a dict matching the
    shape of FILTER_ATTRIBUTES in constants.py but with show-specific values.

    Use this before create_filter_library if your show uses fixtures other than
    Mac 700 Profile Extended + Generic Dimmer (the defaults in FILTER_ATTRIBUTES).

    Returns:
        str: JSON dict mapping category names to attribute name lists.
    """
    from src.server import _discover_filter_attributes
    discovered = await _discover_filter_attributes()
    return json.dumps({
        "attributes": discovered,
        "total_attributes": sum(len(v) for v in discovered.values()),
        "note": "Pass these as fixture_attributes to create_filter_library for accurate filters.",
        "risk_tier": "SAFE_READ",
    }, indent=2)


# ============================================================


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def browse_patch_schedule(
    fixture_type_id: int | None = None,
) -> str:
    """
    Browse the fixture patch schedule from LiveSetup.

    If fixture_type_id is provided, drills into that specific fixture type
    to show its instances (fixtures, DMX addresses, channels).

    Args:
        fixture_type_id: Fixture type index to drill into (optional).
                         Omit to see all fixture types.

    Returns:
        str: JSON with raw_response, entries, risk_tier.
    """
    client = await _sc.get_client()
    commands_sent = []

    nav = await navigate(client, "/")
    commands_sent.append(nav.command_sent)

    nav = await navigate(client, "10")
    commands_sent.append(nav.command_sent)

    nav = await navigate(client, "3")
    commands_sent.append(nav.command_sent)

    if fixture_type_id is not None:
        nav = await navigate(client, str(fixture_type_id))
        commands_sent.append(nav.command_sent)

    lst = await list_destination(client)
    commands_sent.append(lst.command_sent)

    nav = await navigate(client, "/")
    commands_sent.append(nav.command_sent)

    entries = [
        {"object_type": e.object_type, "object_id": e.object_id, "name": e.name}
        for e in lst.parsed_list.entries
    ]

    return json.dumps({
        "commands_sent": commands_sent,
        "raw_response": lst.raw_response,
        "entries": entries,
        "entry_count": len(entries),
        "risk_tier": "SAFE_READ",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PATCH_WRITE)
@_handle_errors
async def patch_fixture(
    fixture_id: int,
    dmx_universe: int,
    dmx_address: int,
    fixture_type_id: int | None = None,
    channel_id: int | None = None,
    confirm_destructive: bool = False,
) -> str:
    """
    Patch a fixture to a DMX address (DESTRUCTIVE — modifies the patch).

    Assigns a DMX address to a fixture. Optionally assigns a fixture type first.

    MA2 syntax:
      assign dmx [universe].[address] at fixture [fixture_id]
      assign fixture_type [type_id] at fixture [fixture_id]  (if fixture_type_id given)

    Args:
        fixture_id: Fixture ID to patch.
        dmx_universe: DMX universe number (1-256).
        dmx_address: DMX address within universe (1-512).
        fixture_type_id: Fixture type to assign (optional).
        channel_id: Channel ID to assign (optional).
        confirm_destructive: Must be True to proceed.

    Returns:
        str: JSON with commands_sent, raw_responses, risk_tier.
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "Patching modifies fixture DMX assignments. Set confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    client = await _sc.get_client()
    commands_sent = []
    raw_responses = []

    # Optionally assign fixture type first
    if fixture_type_id is not None:
        from src.commands import assign as build_assign
        cmd = build_assign(
            source_type="fixturetype",
            source_id=str(fixture_type_id),
            target_type="fixture",
            target_id=str(fixture_id),
        )
        raw = await client.send_command_with_response(cmd)
        commands_sent.append(cmd)
        raw_responses.append(raw)

    # Assign DMX address
    from src.commands import assign as build_assign
    dmx_ref = f"{dmx_universe}.{dmx_address}"
    cmd = build_assign(
        source_type="dmx",
        source_id=dmx_ref,
        target_type="fixture",
        target_id=str(fixture_id),
    )
    raw = await client.send_command_with_response(cmd)
    commands_sent.append(cmd)
    raw_responses.append(raw)

    # Optionally assign channel
    if channel_id is not None:
        cmd = build_assign(
            source_type="fixture",
            source_id=str(fixture_id),
            target_type="channel",
            target_id=str(channel_id),
        )
        raw = await client.send_command_with_response(cmd)
        commands_sent.append(cmd)
        raw_responses.append(raw)

    return json.dumps({
        "commands_sent": commands_sent,
        "raw_responses": raw_responses,
        "fixture_id": fixture_id,
        "dmx_address": f"{dmx_universe}.{dmx_address}",
        "risk_tier": "DESTRUCTIVE",
        "blocked": False,
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PATCH_WRITE)
@_handle_errors
async def unpatch_fixture(
    fixture_id: int,
    confirm_destructive: bool = False,
) -> str:
    """
    Unpatch a fixture (remove its DMX assignment) (DESTRUCTIVE).

    MA2 syntax: delete fixture [fixture_id]
    This removes the DMX assignment but does not delete the fixture from the show.

    Args:
        fixture_id: Fixture ID to unpatch.
        confirm_destructive: Must be True to proceed.

    Returns:
        str: JSON with command_sent, raw_response, risk_tier.
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "Unpatching removes DMX assignments. Set confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    cmd = build_delete_fixture(fixture_id)
    client = await _sc.get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "DESTRUCTIVE",
        "blocked": False,
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PATCH_WRITE)
@_handle_errors
async def set_fixture_type_property(
    fixture_type_id: int,
    property_name: str,
    value: str,
    confirm_destructive: bool = False,
) -> str:
    """
    Set a property on a fixture type in LiveSetup (DESTRUCTIVE).

    Navigates to LiveSetup/FixtureTypes/[N] and assigns a property value.
    Path: cd 10 -> cd 3 -> assign [fixture_type_id]/property=value -> cd /

    Args:
        fixture_type_id: Fixture type index (1-based).
        property_name: Property to set (e.g. "Mode", "Name").
        value: New value for the property.
        confirm_destructive: Must be True to proceed.

    Returns:
        str: JSON with commands_sent, success, risk_tier.
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "Modifying fixture type properties is DESTRUCTIVE. Set confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    client = await _sc.get_client()
    result = await set_property(
        client,
        path=f"10.3.{fixture_type_id}",
        property_name=property_name,
        value=value,
    )

    return json.dumps({
        "commands_sent": result.commands_sent,
        "raw_responses": result.raw_responses,
        "success": result.success,
        "verified_value": result.verified_value,
        "error": result.error,
        "risk_tier": "DESTRUCTIVE",
        "blocked": False,
    }, indent=2)


# ============================================================


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def check_pool_availability(
    pool_type: str,
    start_from: int = 1,
    scan_up_to: int = 200,
    needed_slots: int | None = None,
) -> str:
    """
    Check which slots are occupied and free in an object pool (SAFE_READ).

    Navigates to the pool, lists all entries, and computes a full
    availability map: occupied slots (with names), free ranges,
    next 10 free slots, and contiguous-block analysis.

    Use this **before importing XML** to verify target slots are free,
    or to find the best slot range for bulk imports (filters, MAtricks).

    Valid pool types (case-insensitive):
      Group, Sequence, Preset, Macro, Effect, Gel, World, Filter,
      Form, Timer, Layout, Timecode, Agenda, UserProfile, Camera,
      MAtricks, View, Remote

    Numeric cd indexes also accepted (e.g. "13" for Macros, "19" for Filters).

    Args:
        pool_type: Pool keyword or numeric cd index.
        start_from: First slot number to check (default 1).
        scan_up_to: Last slot number to check (default 200).
        needed_slots: If set, checks whether N contiguous free slots
            exist and returns can_fit + suggested_start.

    Returns:
        str: JSON with occupied_slots, free_ranges, next_free_slots,
             total_occupied, total_free_in_range, largest_contiguous,
             can_fit, suggested_start, risk_tier.
    """
    client = await _sc.get_client()
    result = await _check_pool_slots(
        client,
        pool_type,
        start_from=start_from,
        scan_up_to=scan_up_to,
        needed_slots=needed_slots,
    )
    result["risk_tier"] = "SAFE_READ"
    return json.dumps(result, indent=2)


# ============================================================================


@mcp.tool()
@require_scope(OAuthScope.USER_MANAGE)
@_handle_errors
async def list_console_users() -> str:
    """
    List all user accounts in the current show file (SAFE_READ).

    Returns the raw `list user` output from the console, showing all
    user slots with their names, rights levels, and profile assignments.

    Returns:
        str: JSON result with raw console response
    """
    client = await _sc.get_client()
    cmd = build_list_users()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "SAFE_READ",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.USER_MANAGE)
@_handle_errors
async def create_console_user(
    slot: int,
    name: str,
    password: str,
    rights_level: int,
    confirm_destructive: bool = False,
) -> str:
    """
    Create or overwrite a user account in the show file (DESTRUCTIVE — Admin only).

    Requires both gma2:user:manage OAuth scope AND confirm_destructive=True.

    grandMA2 rights levels:
        0 = None     (view/change views only, no programmer)
        1 = Playback (run show, no store)
        2 = Presets  (update existing presets only)
        3 = Program  (full show programming)
        4 = Setup    (patch, fixture import, console setup)
        5 = Admin    (full access + user/session/show management)

    Args:
        slot: User slot number (2-N; slot 1 = Administrator, always exists)
        name: Username (alphanumeric + underscores, no spaces)
        password: Console login password (empty string = no password required)
        rights_level: MA2 rights level 0-5
        confirm_destructive: Must be True to execute

    Returns:
        str: JSON result with command sent
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "create_console_user is DESTRUCTIVE. Set confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)
    if slot < 1:
        return json.dumps({"error": "slot must be >= 1", "blocked": True}, indent=2)
    if rights_level not in range(6):
        return json.dumps({
            "error": f"rights_level must be 0-5, got {rights_level}",
            "blocked": True,
        }, indent=2)
    if not name or not name.replace("_", "").isalnum():
        return json.dumps({
            "error": "name must be alphanumeric (underscores allowed), no spaces",
            "blocked": True,
        }, indent=2)

    cmd = build_store_user(slot, name, password, rights_level)
    client = await _sc.get_client()
    response = await client.send_command_with_response(cmd)
    _rights_names = {0: "None", 1: "Playback", 2: "Presets",
                     3: "Program", 4: "Setup", 5: "Admin"}
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "slot": slot,
        "name": name,
        "rights_level": rights_level,
        "rights_name": _rights_names[rights_level],
        "risk_tier": "DESTRUCTIVE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.USER_MANAGE)
@_handle_errors
async def assign_world_to_user_profile(
    user_profile_slot: int,
    world_slot: int,
    confirm_destructive: bool = False,
) -> str:
    """
    Assign a World (fixture visibility mask) to a User Profile (DESTRUCTIVE — Admin only).

    Restricts all Users assigned to this profile to only access fixtures and attributes
    visible in the specified World. Use world_slot=0 to remove the restriction (None).

    Args:
        user_profile_slot: UserProfile slot number to modify
        world_slot: World slot number (0 = no restriction / remove World assignment)
        confirm_destructive: Must be True to execute

    Returns:
        str: JSON result with command sent
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "assign_world_to_user_profile is DESTRUCTIVE. Set confirm_destructive=True.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)
    if user_profile_slot < 1:
        return json.dumps({"error": "user_profile_slot must be >= 1", "blocked": True}, indent=2)

    cmd = build_assign_world_to_user_profile(user_profile_slot, world_slot)
    client = await _sc.get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "user_profile_slot": user_profile_slot,
        "world_slot": world_slot,
        "risk_tier": "DESTRUCTIVE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.USER_MANAGE)
@_handle_errors
async def inspect_sessions() -> str:
    """
    Inspect active per-operator Telnet session pool (SAFE_READ).

    Returns a snapshot of the session manager's current state: how many
    sessions are open, which console users they are authenticated as, and
    how long each has been idle.  Useful for diagnosing connection issues
    in multi-operator deployments.

    Returns:
        JSON with session_count and a sessions list, each entry containing:
        identity, username, connected, idle_seconds, age_seconds.
    """
    manager = await _get_session_manager()
    return json.dumps({
        "session_count": manager.session_count(),
        "max_sessions": manager._max_sessions,
        "idle_timeout_seconds": manager._idle_timeout,
        "sessions": manager.session_info(),
    }, indent=2)


# ============================================================


@mcp.tool()
@require_scope(OAuthScope.USER_MANAGE)
@_handle_errors
async def delete_user(
    slot: int,
    confirm_destructive: bool = False,
) -> str:
    """
    Delete a console user account by slot number (DESTRUCTIVE).

    The built-in Administrator in slot 1 cannot be deleted.
    Requires confirm_destructive=True to proceed.

    Args:
        slot: User slot number to delete (2–N). Slot 1 is protected.
        confirm_destructive: Must be True to execute (safety gate).

    Returns:
        JSON with command_sent, raw_response, or block info.
    """
    if not confirm_destructive:
        return json.dumps({
            "command_sent": None,
            "blocked": True,
            "risk_tier": "DESTRUCTIVE",
            "error": "Delete User is a DESTRUCTIVE operation. Set confirm_destructive=True to proceed.",
        }, indent=2)

    if slot == 1:
        return json.dumps({
            "command_sent": None,
            "blocked": True,
            "risk_tier": "DESTRUCTIVE",
            "error": "Slot 1 (Administrator) is protected and cannot be deleted.",
        }, indent=2)

    cmd = build_delete_user(slot)
    client = await _sc.get_client()
    raw_response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "risk_tier": "DESTRUCTIVE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def browse_effect_library() -> str:
    """
    Browse the grandMA2 effect library (SAFE_READ).

    Lists all available effect templates that can be applied to fixtures.

    Returns:
        JSON with command_sent and raw_response from the console.
    """
    cmd = build_list_effect_library()
    client = await _sc.get_client()
    raw_response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "risk_tier": "SAFE_READ",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def browse_macro_library() -> str:
    """
    Browse the grandMA2 macro library (SAFE_READ).

    Lists all available macro templates that can be imported into the show.

    Returns:
        JSON with command_sent and raw_response from the console.
    """
    cmd = build_list_macro_library()
    client = await _sc.get_client()
    raw_response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "risk_tier": "SAFE_READ",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def browse_plugin_library() -> str:
    """
    Browse the grandMA2 plugin library (SAFE_READ).

    Lists all available plugin templates installed on the console.

    Returns:
        JSON with command_sent and raw_response from the console.
    """
    cmd = build_list_plugin_library()
    client = await _sc.get_client()
    raw_response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "risk_tier": "SAFE_READ",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def list_fader_modules() -> str:
    """
    List connected fader modules (SAFE_READ).

    Returns information about all fader wing modules currently connected
    to the grandMA2 console.

    Returns:
        JSON with command_sent and raw_response from the console.
    """
    cmd = build_list_fader_modules()
    client = await _sc.get_client()
    raw_response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "risk_tier": "SAFE_READ",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def list_update_history() -> str:
    """
    List programming update history (SAFE_READ).

    Shows the recent update log of programmer changes made in the show.

    Returns:
        JSON with command_sent and raw_response from the console.
    """
    cmd = build_list_update()
    client = await _sc.get_client()
    raw_response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "risk_tier": "SAFE_READ",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.SHOW_LOAD)
@_handle_errors
async def delete_show(
    name: str,
    confirm_destructive: bool = False,
) -> str:
    """
    Delete a show file from disk (DESTRUCTIVE).

    Permanently removes the named show file. This cannot be undone.
    Requires confirm_destructive=True to proceed.

    Args:
        name: Show file name to delete (without extension).
        confirm_destructive: Must be True to execute (safety gate).

    Returns:
        JSON with command_sent, raw_response, or block info.
    """
    if not confirm_destructive:
        return json.dumps({
            "command_sent": None,
            "blocked": True,
            "risk_tier": "DESTRUCTIVE",
            "error": "Delete Show is a DESTRUCTIVE operation. Set confirm_destructive=True to proceed.",
        }, indent=2)

    cmd = build_delete_show(name, noconfirm=True)
    client = await _sc.get_client()
    raw_response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "risk_tier": "DESTRUCTIVE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.EXECUTOR_CTRL)
@_handle_errors
async def assign_temp_fader(
    value: int = 50,
) -> str:
    """
    Set the temp fader level on the currently selected executor (SAFE_WRITE).

    TempFader crossfades the cue on when pulled up and crossfades the cue off
    when pulled down, relative to the given value. The value range is 0–100.

    Args:
        value: Fader level 0–100 (default 50). 0 = full off, 100 = full on.

    Returns:
        JSON with command_sent and raw_response from the console.
    """
    if not (0 <= value <= 100):
        return json.dumps({
            "command_sent": None,
            "blocked": True,
            "error": f"value must be between 0 and 100, got {value}.",
        }, indent=2)

    cmd = build_temp_fader(value)
    client = await _sc.get_client()
    raw_response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


# ============================================================


@mcp.tool()
@require_scope(OAuthScope.CUE_STORE)
@_handle_errors
async def assign_effect_to_executor(
    effect_id: int,
    executor_id: int,
    page: int | None = None,
    confirm_destructive: bool = False,
) -> str:
    """
    Assign an effect template to a fader executor slot (DESTRUCTIVE).

    Binds an effect from the effect library to an executor so the fader controls
    effect intensity in live busking mode. This is the core primitive for the
    fader-per-effect busking model.

    Args:
        effect_id: Effect pool ID to assign (1-based).
        executor_id: Target executor slot number on the page.
        page: Optional page number. When given, qualifies as 'Page {page}.{exec}'.
        confirm_destructive: Must be True to execute (DESTRUCTIVE — modifies executor assignment).

    Returns:
        JSON result with command sent and console response.
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "assign_effect_to_executor is DESTRUCTIVE (modifies executor assignment). Pass confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
            "command_preview": build_assign_effect_to_executor(effect_id, executor_id, page=page),
        }, indent=2)
    client = await _sc.get_client()
    cmd = build_assign_effect_to_executor(effect_id, executor_id, page=page)
    response = await client.send_command(cmd)
    return json.dumps({"command": cmd, "response": response, "effect_id": effect_id, "executor_id": executor_id}, indent=2)


@mcp.tool()
@require_scope(OAuthScope.EXECUTOR_CTRL)
@_handle_errors
async def modulate_effect(
    mode: str,
    value: int,
) -> str:
    """
    Set rate or speed on active effects in real time (SAFE_WRITE).

    Used in busking to live-modulate effect tempo without stopping playback.
    Rate is a relative multiplier (100 = normal, 200 = double).
    Speed is an absolute BPM target (overrides rate).

    Args:
        mode: "rate" (relative 1–200, 100=normal) or "speed" (absolute BPM).
        value: Numeric value for the chosen mode.

    Returns:
        JSON result with command sent and console response.
    """
    if mode == "rate":
        cmd = build_set_effect_rate(value)
    else:
        cmd = build_set_effect_speed(value)
    client = await _sc.get_client()
    response = await client.send_command(cmd)
    return json.dumps({"command": cmd, "mode": mode, "value": value, "response": response}, indent=2)


@mcp.tool()
@require_scope(OAuthScope.EXECUTOR_CTRL)
@_handle_errors
async def clear_effects_on_page(
    page: int,
    start_exec: int = 1,
    end_exec: int = 20,
) -> str:
    """
    Release (kill) all effect executors across a page range (SAFE_WRITE).

    Sends Off commands to every executor in the range, stopping all running
    effects. Use during song transitions to clean up the previous song's state.
    Does not change fader positions — use normalize_page_faders for that.

    Args:
        page: Fader page number.
        start_exec: First executor slot to release (default 1).
        end_exec: Last executor slot to release (default 20).

    Returns:
        JSON result with command count and console response.
    """
    client = await _sc.get_client()
    cmd = build_release_effects_on_page(page, start_exec=start_exec, end_exec=end_exec)
    response = await client.send_command(cmd)
    count = end_exec - start_exec + 1
    return json.dumps({"command_count": count, "page": page, "response": response}, indent=2)


@mcp.tool()
@require_scope(OAuthScope.EXECUTOR_CTRL)
@_handle_errors
async def normalize_page_faders(
    page: int,
    start_exec: int = 1,
    end_exec: int = 20,
) -> str:
    """
    Set all faders on a page to 0 without releasing executors (SAFE_WRITE).

    Silences all effects while keeping them armed for instant recall — the
    standard busking blackout technique. Faders return to zero but executors
    remain active; pushing the fader up immediately restores the effect.

    Args:
        page: Fader page number.
        start_exec: First executor slot (default 1).
        end_exec: Last executor slot (default 20).

    Returns:
        JSON result with command count and console response.
    """
    client = await _sc.get_client()
    cmd = build_zero_page_faders(page, start_exec=start_exec, end_exec=end_exec)
    response = await client.send_command(cmd)
    count = end_exec - start_exec + 1
    return json.dumps({"command_count": count, "page": page, "zeroed": True, "response": response}, indent=2)


# ============================================================


@mcp.tool()
@require_scope(OAuthScope.USER_MANAGE)
@_handle_errors
async def console_login(username: str, password: str) -> str:
    """
    Authenticate to the grandMA2 console as a specific user.

    Sends a Login command over the active Telnet session, switching
    the session to the specified user account and rights level.

    Args:
        username: Console username (e.g. "operator", "administrator")
        password: Console password

    Returns:
        str: JSON with command_sent and raw_response.
    """
    client = await _sc.get_client()
    cmd = build_console_login(username, password)
    raw = await client.send_command_with_response(cmd)
    return json.dumps({"command_sent": cmd, "raw_response": raw}, indent=2)


@mcp.tool()
@require_scope(OAuthScope.USER_MANAGE)
@_handle_errors
async def console_logout() -> str:
    """
    Log out the current Telnet session user on the grandMA2 console.

    Returns:
        str: JSON with command_sent and raw_response.
    """
    client = await _sc.get_client()
    cmd = build_console_logout()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({"command_sent": cmd, "raw_response": raw}, indent=2)


@mcp.tool()
@require_scope(OAuthScope.SETUP_CONSOLE)
@_handle_errors
async def lock_console_ui() -> str:
    """
    Lock the grandMA2 console UI to prevent accidental input.

    Sends the Lock command, which disables all physical panel input
    until unlocked. Useful during live shows to prevent accidental
    key presses.

    Returns:
        str: JSON with command_sent and raw_response.
    """
    client = await _sc.get_client()
    cmd = build_lock_console()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({"command_sent": cmd, "raw_response": raw}, indent=2)


@mcp.tool()
@require_scope(OAuthScope.SETUP_CONSOLE)
@_handle_errors
async def unlock_console_ui(password: str | None = None) -> str:
    """
    Unlock the grandMA2 console UI.

    Args:
        password: Optional unlock password if the console was locked with one.

    Returns:
        str: JSON with command_sent and raw_response.
    """
    client = await _sc.get_client()
    cmd = build_unlock_console(password)
    raw = await client.send_command_with_response(cmd)
    return json.dumps({"command_sent": cmd, "raw_response": raw}, indent=2)


# ============================================================


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def list_layouts() -> str:
    """
    List all Layout pool objects on the grandMA2 console.

    Returns the raw console output of the List Layout command,
    which shows all defined layout views and their IDs.

    Returns:
        str: JSON with command_sent and raw_response.
    """
    client = await _sc.get_client()
    cmd = build_list_objects("Layout")
    raw = await client.send_command_with_response(cmd)
    return json.dumps({"command_sent": cmd, "raw_response": raw}, indent=2)


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def list_worlds() -> str:
    """
    List all World pool objects on the grandMA2 console.

    Worlds are used to restrict which fixtures a user can control.
    Returns the raw console output of the List World command.

    Returns:
        str: JSON with command_sent and raw_response.
    """
    client = await _sc.get_client()
    cmd = build_list_objects("World")
    raw = await client.send_command_with_response(cmd)
    return json.dumps({"command_sent": cmd, "raw_response": raw}, indent=2)


@mcp.tool()
@require_scope(OAuthScope.SETUP_CONSOLE)
@_handle_errors
async def store_world(
    world_id: int,
    name: str | None = None,
    overwrite: bool = False,
    confirm_destructive: bool = False,
) -> str:
    """
    Create (store) a new World pool object on the grandMA2 console. (DESTRUCTIVE)

    Worlds restrict which fixtures a user profile can control. After storing,
    use assign_world_to_user_profile to attach the world to a user.

    Args:
        world_id: World slot number (1-256)
        name: Optional label applied immediately after store
        overwrite: If True, adds /overwrite flag (replaces existing slot)
        confirm_destructive: Must be True to execute

    Returns:
        str: JSON with commands_sent and raw_responses.
    """
    if not confirm_destructive:
        return json.dumps({"blocked": True, "reason": "confirm_destructive required"}, indent=2)

    client = await _sc.get_client()
    flag = " /overwrite" if overwrite else ""
    store_cmd = f"store world {world_id}{flag}"
    raw1 = await client.send_command_with_response(store_cmd)

    commands_sent = [store_cmd]
    raw_responses = [raw1]

    if name:
        label_cmd = build_label("world", world_id, name)
        raw2 = await client.send_command_with_response(label_cmd)
        commands_sent.append(label_cmd)
        raw_responses.append(raw2)

    return json.dumps({
        "commands_sent": commands_sent,
        "raw_responses": raw_responses,
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.SETUP_CONSOLE)
@_handle_errors
async def label_world(
    world_id: int,
    name: str,
    confirm_destructive: bool = False,
) -> str:
    """
    Label an existing World pool object on the grandMA2 console. (DESTRUCTIVE)

    Args:
        world_id: World slot number to label (1-256)
        name: Name to assign to the world
        confirm_destructive: Must be True to execute

    Returns:
        str: JSON with command_sent and raw_response.
    """
    if not confirm_destructive:
        return json.dumps({"blocked": True, "reason": "confirm_destructive required"}, indent=2)

    client = await _sc.get_client()
    cmd = build_label("world", world_id, name)
    raw = await client.send_command_with_response(cmd)
    return json.dumps({"command_sent": cmd, "raw_response": raw}, indent=2)


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def list_timers() -> str:
    """
    List all Timer pool objects on the grandMA2 console.

    Returns the raw console output of the List Timer command,
    which shows all defined countdown / count-up timers.

    Returns:
        str: JSON with command_sent and raw_response.
    """
    client = await _sc.get_client()
    cmd = build_list_objects("Timer")
    raw = await client.send_command_with_response(cmd)
    return json.dumps({"command_sent": cmd, "raw_response": raw}, indent=2)


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def list_filters() -> str:
    """
    List all Filter pool objects on the grandMA2 console.

    Filters restrict which fixture attributes are stored or recalled.
    Returns the raw console output of the List Filter command.

    Returns:
        str: JSON with command_sent and raw_response.
    """
    client = await _sc.get_client()
    cmd = build_list_objects("Filter")
    raw = await client.send_command_with_response(cmd)
    return json.dumps({"command_sent": cmd, "raw_response": raw}, indent=2)


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def list_effects_pool() -> str:
    """
    List all Effect pool objects on the grandMA2 console.

    Returns stored effects (not the effect library) from the
    Effects pool using the List Effect command.

    Returns:
        str: JSON with command_sent and raw_response.
    """
    client = await _sc.get_client()
    cmd = build_list_objects("Effect")
    raw = await client.send_command_with_response(cmd)
    return json.dumps({"command_sent": cmd, "raw_response": raw}, indent=2)


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def list_images() -> str:
    """
    List all Image pool objects on the grandMA2 console.

    Returns the raw console output of the List Image command,
    which shows all user-imported images (for gobo media servers, etc.).

    Returns:
        str: JSON with command_sent and raw_response.
    """
    client = await _sc.get_client()
    cmd = build_list_objects("Image")
    raw = await client.send_command_with_response(cmd)
    return json.dumps({"command_sent": cmd, "raw_response": raw}, indent=2)


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def list_forms() -> str:
    """
    List all Form pool objects on the grandMA2 console.

    Forms define the waveform shapes used by effects. Returns
    the raw console output of the List Form command.

    Returns:
        str: JSON with command_sent and raw_response.
    """
    client = await _sc.get_client()
    cmd = build_list_objects("Form")
    raw = await client.send_command_with_response(cmd)
    return json.dumps({"command_sent": cmd, "raw_response": raw}, indent=2)


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def list_timecode_events() -> str:
    """
    List all Timecode pool objects on the grandMA2 console.

    Returns the raw console output of the List Timecode command,
    which shows all stored timecode tracks and their slot IDs.

    Returns:
        str: JSON with command_sent and raw_response.
    """
    client = await _sc.get_client()
    cmd = build_list_objects("Timecode")
    raw = await client.send_command_with_response(cmd)
    return json.dumps({"command_sent": cmd, "raw_response": raw}, indent=2)


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def list_agenda_events() -> str:
    """
    List all Agenda pool objects on the grandMA2 console.

    Agendas are time-triggered events (sunrise/sunset/specific time) that can
    fire macros or cues automatically. Returns the raw console output of the
    List Agenda command, showing all agenda slots and their IDs.

    Returns:
        str: JSON with command_sent and raw_response.
    """
    client = await _sc.get_client()
    cmd = build_list_objects("Agenda")
    raw = await client.send_command_with_response(cmd)
    return json.dumps({"command_sent": cmd, "raw_response": raw}, indent=2)


@mcp.tool()
@require_scope(OAuthScope.MACRO_EDIT)
@_handle_errors
async def store_agenda(
    agenda_id: int,
    name: str | None = None,
    confirm_destructive: bool = False,
) -> str:
    """
    Create (store) a new Agenda pool object on the grandMA2 console. (DESTRUCTIVE)

    Agendas are time-triggered events (clock/sunrise/sunset) that fire macros or
    cues automatically. After storing, use the assign tool to attach a macro trigger.

    The store command creates the pool slot. To add time triggers to an existing
    agenda, use store_timecode_event with object_type="agenda".

    Args:
        agenda_id: Agenda slot number (1-256)
        name: Optional label applied immediately after store
        confirm_destructive: Must be True to execute

    Returns:
        str: JSON with commands_sent and raw_responses.
    """
    if not confirm_destructive:
        return json.dumps({"blocked": True, "reason": "confirm_destructive required"}, indent=2)

    client = await _sc.get_client()
    store_cmd = f"store agenda {agenda_id}"
    raw1 = await client.send_command_with_response(store_cmd)

    commands_sent = [store_cmd]
    raw_responses = [raw1]

    if name:
        label_cmd = build_label("agenda", agenda_id, name)
        raw2 = await client.send_command_with_response(label_cmd)
        commands_sent.append(label_cmd)
        raw_responses.append(raw2)

    return json.dumps({
        "commands_sent": commands_sent,
        "raw_responses": raw_responses,
    }, indent=2)


# ============================================================


@mcp.tool()
@require_scope(OAuthScope.EXECUTOR_CTRL)
@_handle_errors
async def control_chaser(
    action: str,
    value: float | None = None,
    executor_id: int | None = None,
    page: int = 1,
) -> str:
    """
    Control a running chaser (rate, speed, skip, crossfade mode).

    Actions:
    - "rate"    : Set the rate (0-200, 100 = normal). Requires value.
    - "speed"   : Set the BPM speed (0-65535). Requires value.
    - "skip_fwd": Skip one step forward (SkipPlus).
    - "skip_bk" : Skip one step backward (SkipMinus).
    - "xfade_a" : Set crossfade mode A (CrossFadeA).
    - "xfade_b" : Set crossfade mode B (CrossFadeB).
    - "xfade_ab": Set crossfade mode AB (CrossFadeAB).

    Args:
        action: One of: rate, speed, skip_fwd, skip_bk, xfade_a, xfade_b, xfade_ab
        value: Required for rate and speed actions.
        executor_id: Target executor ID (optional; uses selected if omitted).
        page: Page number (default 1).

    Returns:
        str: JSON with command_sent and raw_response.
    """
    action = action.lower()
    if action in ("rate", "speed") and value is None:
        return json.dumps({"error": f"'value' is required for action '{action}'"}, indent=2)

    if action == "rate":
        cmd = build_chaser_rate(value, executor_id, page)
    elif action == "speed":
        cmd = build_chaser_speed(value, executor_id, page)
    elif action == "skip_fwd":
        cmd = build_chaser_skip("plus", executor_id, page)
    elif action == "skip_bk":
        cmd = build_chaser_skip("minus", executor_id, page)
    elif action in ("xfade_a", "xfade_b", "xfade_ab"):
        mode = action.replace("xfade_", "")
        cmd = build_chaser_xfade(mode, executor_id, page)
    else:
        return json.dumps({
            "error": f"Unknown action '{action}'. Use: rate, speed, skip_fwd, skip_bk, xfade_a, xfade_b, xfade_ab"
        }, indent=2)

    client = await _sc.get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({"command_sent": cmd, "raw_response": raw}, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PROGRAMMER_WRITE)
@_handle_errors
async def set_effect_param(param: str, value: float) -> str:
    """
    Set an effect parameter in the programmer for the current fixture selection.

    Valid parameters (defined by _EFFECT_PARAM_KEYWORDS in system.py — add new
    params there): bpm, hz, high, low, phase, width, attack, decay, delay, fade.

    - bpm / hz   : Effect speed (beats per minute or Hertz)
    - high / low : Upper and lower value limits (0-100)
    - phase      : Phase offset (0-359 degrees)
    - width      : Pulse width (0-100)
    - attack     : Attack time (0-100)
    - decay      : Decay time (0-100)
    - delay      : Delay before effect starts each cycle (0-100)
    - fade       : Fade in/out at start and end of effect (0-100)

    Args:
        param: Parameter name (case-insensitive). ValueError lists valid params.
        value: Numeric value appropriate for the parameter.
        value: Numeric value appropriate for the parameter.

    Returns:
        str: JSON with command_sent and raw_response.
    """
    try:
        cmd = build_set_effect_parameter(param, value)
    except ValueError as exc:
        return json.dumps({"error": str(exc)}, indent=2)
    client = await _sc.get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({"command_sent": cmd, "raw_response": raw}, indent=2)


# ============================================================


@mcp.tool()
@require_scope(OAuthScope.MACRO_EDIT)
@_handle_errors
async def call_plugin_tool(plugin_id: int | str) -> str:
    """
    Execute a plugin on the grandMA2 console by ID or name.

    Plugins are Lua scripts stored in the Plugin pool. This tool
    invokes them using the Plugin keyword.

    Args:
        plugin_id: Plugin number (int) or name (str).

    Returns:
        str: JSON with command_sent and raw_response.
    """
    client = await _sc.get_client()
    cmd = build_call_plugin(plugin_id)
    raw = await client.send_command_with_response(cmd)
    return json.dumps({"command_sent": cmd, "raw_response": raw}, indent=2)


@mcp.tool()
@require_scope(OAuthScope.MACRO_EDIT)
@_handle_errors
async def run_lua_script(script: str) -> str:
    """
    Execute an inline Lua script directly on the grandMA2 console.

    Sends the script using the Lua keyword. Useful for one-off
    automations without creating a persistent Plugin pool entry.

    Args:
        script: Lua source code (e.g. 'print("hello")', 'gma.cmd("Blackout")').

    Returns:
        str: JSON with command_sent and raw_response.
    """
    client = await _sc.get_client()
    cmd = build_run_lua(script)
    raw = await client.send_command_with_response(cmd)
    return json.dumps({"command_sent": cmd, "raw_response": raw}, indent=2)


@mcp.tool()
@require_scope(OAuthScope.MACRO_EDIT)
@_handle_errors
async def reload_all_plugins() -> str:
    """
    Reload all plugins from disk on the grandMA2 console.

    Sends ReloadPlugins, which rescans the plugin folder and reloads
    all Lua plugin files. Use after editing plugin files on disk.

    Returns:
        str: JSON with command_sent and raw_response.
    """
    client = await _sc.get_client()
    cmd = build_reload_plugins()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({"command_sent": cmd, "raw_response": raw}, indent=2)


@mcp.tool()
@require_scope(OAuthScope.EXECUTOR_CTRL)
@_handle_errors
async def control_special_master(master: str, value: float) -> str:
    """
    Set the level of a grandMA2 SpecialMaster (Grand Master, Speed/Rate masters).

    Special masters globally control intensity and timing for all playbacks.

    Valid master names:
    - "grandmaster"     : Grand Master (0-100 %)
    - "playbackmaster"  : Playback Master (0-100 %)
    - "speed1".."speed16" : Speed Masters (BPM)
    - "rate1".."rate16"   : Rate Masters (%)

    Args:
        master: Master name (case-insensitive). See valid names above.
        value: Level value appropriate for the master type.

    Returns:
        str: JSON with command_sent and raw_response.
    """
    try:
        cmd = build_set_special_master(master, value)
    except ValueError as exc:
        return json.dumps({
            "error": str(exc),
            "valid_masters": sorted(SPECIAL_MASTER_NAMES),
        }, indent=2)
    client = await _sc.get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({"command_sent": cmd, "raw_response": raw}, indent=2)


# ============================================================


@mcp.tool()
@require_scope(OAuthScope.PATCH_WRITE)
@_handle_errors
async def rdm_discover(action: str = "automatch") -> str:
    """
    Perform RDM device discovery on the grandMA2 console.

    Actions:
    - "automatch"  : Match discovered RDM devices to existing fixture types (RdmAutomatch).
    - "autopatch"  : Auto-patch discovered RDM devices to free DMX addresses (RdmAutopatch).

    RDM (Remote Device Management) allows two-way communication with
    DMX fixtures that support the RDM protocol.

    Args:
        action: "automatch" or "autopatch" (default: "automatch").

    Returns:
        str: JSON with command_sent and raw_response.
    """
    action = action.lower()
    if action == "automatch":
        cmd = build_rdm_automatch()
    elif action == "autopatch":
        cmd = build_rdm_autopatch()
    else:
        return json.dumps({"error": f"Unknown action '{action}'. Use 'automatch' or 'autopatch'."}, indent=2)
    client = await _sc.get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({"command_sent": cmd, "raw_response": raw}, indent=2)


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def rdm_get_info(
    fixture_id: int | None = None,
    universe: int | None = None,
) -> str:
    """
    Query RDM device information from the grandMA2 console.

    - If fixture_id is provided: returns RDM device info for that fixture (RdmInfo Fixture N).
    - If universe is provided (and no fixture_id): lists RDM devices on that universe (RdmList Universe N).
    - If neither is provided: lists all discovered RDM devices (RdmList).

    Args:
        fixture_id: Fixture ID to query (optional).
        universe: Universe number to filter by (optional).

    Returns:
        str: JSON with command_sent and raw_response.
    """
    if fixture_id is not None:
        cmd = build_rdm_info(fixture_id)
    else:
        cmd = build_rdm_list(universe)
    client = await _sc.get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({"command_sent": cmd, "raw_response": raw}, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PATCH_WRITE)
@_handle_errors
async def rdm_patch(
    fixture_id: int,
    action: str,
    universe: int | None = None,
    address: int | None = None,
) -> str:
    """
    Patch or unmatch an RDM device on the grandMA2 console.

    Actions:
    - "setpatch" : Assign the RDM device at fixture_id to a specific DMX address.
                   Requires universe and address.
    - "unmatch"  : Detach the RDM match for a fixture (RdmUnmatch Fixture N).

    Args:
        fixture_id: Fixture ID of the RDM device.
        action: "setpatch" or "unmatch".
        universe: Target universe number (required for setpatch).
        address: Target DMX address 1-512 (required for setpatch).

    Returns:
        str: JSON with command_sent and raw_response.
    """
    action = action.lower()
    if action == "setpatch":
        if universe is None or address is None:
            return json.dumps({"error": "setpatch requires both 'universe' and 'address'."}, indent=2)
        cmd = build_rdm_setpatch(fixture_id, universe, address)
    elif action == "unmatch":
        cmd = build_rdm_unmatch(fixture_id)
    else:
        return json.dumps({"error": f"Unknown action '{action}'. Use 'setpatch' or 'unmatch'."}, indent=2)
    client = await _sc.get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({"command_sent": cmd, "raw_response": raw}, indent=2)


# ============================================================


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def detect_dmx_address_conflicts(universe_id: int | None = None) -> str:
    """
    Scan the patch for DMX address conflicts — fixtures sharing overlapping channel ranges.

    Queries list_universes and list_fixtures to build a channel-occupancy map,
    then reports any fixtures whose DMX footprint overlaps with another fixture on
    the same universe. Safe to run before any patching operation or during a show
    health check.

    Args:
        universe_id: Check only this universe (1-based). If None, checks all universes.

    Returns JSON with:
    - conflicts: list of {universe, fixture_a, fixture_b, overlap_channels}
    - clean_universes: list of universe IDs with no conflicts
    - total_fixtures_checked: int
    """
    client = await _sc.get_client()
    # Get all fixture data
    raw_fixtures = await client.send_command_with_response("List Fixture")
    _raw_universes = await client.send_command_with_response("List Universe")

    # Build occupancy map: universe -> {channel: fixture_id}
    occupancy: dict[int, dict[int, dict]] = {}
    conflicts = []

    # Parse fixtures from raw response (simplified — real implementation would use prompt_parser)
    lines = [ln.strip() for ln in raw_fixtures.splitlines() if ln.strip() and not ln.startswith("Fixture")]

    fixtures_checked = 0
    for line in lines:
        parts = line.split()
        if len(parts) >= 4:
            try:
                fixture_id = int(parts[0])
                univ = int(parts[-2]) if parts[-2].isdigit() else None
                addr = int(parts[-1]) if parts[-1].isdigit() else None
                if univ is None or addr is None:
                    continue
                if universe_id is not None and univ != universe_id:
                    continue
                fixtures_checked += 1
                if univ not in occupancy:
                    occupancy[univ] = {}
                if addr in occupancy[univ]:
                    conflicts.append({
                        "universe": univ,
                        "fixture_a": occupancy[univ][addr],
                        "fixture_b": fixture_id,
                        "channel": addr
                    })
                else:
                    occupancy[univ][addr] = fixture_id
            except (ValueError, IndexError):
                continue

    clean_universes = [u for u in occupancy if not any(c["universe"] == u for c in conflicts)]

    return json.dumps({
        "conflicts": conflicts,
        "clean_universes": clean_universes,
        "total_fixtures_checked": fixtures_checked,
        "universe_filter": universe_id,
        "status": "PASS" if not conflicts else "FAIL",
        "raw_fixture_response": raw_fixtures[:500]
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PROGRAMMER_WRITE)
@_handle_errors
async def update_object(
    object_type: str,
    object_id: int | str | None = None,
    sequence_id: int | None = None,
    merge: bool = False,
    overwrite: bool = False,
    cueonly: bool | None = None,
    confirm_destructive: bool = False,
) -> str:
    """
    Update any object with current programmer values (DESTRUCTIVE).

    Generic update tool that works with all 16 object types.
    For cue-specific updates with sequence scoping, prefer update_cue_data.

    Args:
        object_type: Object type — cue, group, preset, sequence, effect, macro, etc.
        object_id: Object ID (optional; updates active if omitted for cue)
        sequence_id: Sequence ID for cue-scoped updates (only used when object_type="cue")
        merge: Merge programmer into existing values
        overwrite: Overwrite existing values with programmer
        cueonly: Prevent changes from tracking forward (True) or allow (False)
        confirm_destructive: Must be True to execute

    Returns:
        str: JSON with command_sent, raw_response, risk_tier
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "update_object is DESTRUCTIVE. Set confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    from src.commands import update_cue as build_update_cue
    if object_type.lower() == "cue":
        cmd = build_update_cue(
            object_id, sequence_id=sequence_id,
            merge=merge, overwrite=overwrite, cueonly=cueonly,
        )
    else:
        cmd = build_update(
            object_type, object_id,
            merge=merge, overwrite=overwrite, cueonly=cueonly,
        )

    client = await _sc.get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "DESTRUCTIVE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PROGRAMMER_WRITE)
@_handle_errors
async def programming_action(
    action: str,
    fixture_ids: int | list[int] | None = None,
    end: int | None = None,
    cue_id: int | float | None = None,
    sequence_id: int | None = None,
    macro_id: int | None = None,
    executor_id: int | None = None,
    page: int | None = None,
    look_id: int | None = None,
    mode: str | None = None,
    merge: bool = False,
    overwrite: bool = False,
    confirm_destructive: bool = False,
) -> str:
    """
    Execute programmer operations — align, locate, flip, extract, learn,
    block/unblock cue, record macro, store look.

    Args:
        action: One of:
            SAFE_WRITE: "align", "locate", "flip", "extract", "learn",
                        "shuffle_selection", "shuffle_values",
                        "full_highlight", "blind_edit"
            DESTRUCTIVE: "block", "unblock", "record_macro", "store_look"
        fixture_ids: Fixture number(s) for locate (single int or list)
        end: Ending number for locate range
        cue_id: Cue number for block/unblock
        sequence_id: Sequence ID for block/unblock scoping
        macro_id: Macro pool slot for record_macro
        executor_id: Executor ID for learn
        page: Page for learn page-qualified addressing
        look_id: Look pool slot for store_look
        mode: Alignment mode for align (">" "><" "<>" "<")
        merge: Merge option for store_look
        overwrite: Overwrite option for store_look
        confirm_destructive: Required for block/unblock/record_macro/store_look

    Returns:
        str: JSON with command_sent, raw_response, risk_tier
    """
    from src.commands import (
        align as build_align,
    )
    from src.commands import (
        locate as build_locate,
    )

    valid_actions = {
        "align", "locate", "flip", "extract", "learn",
        "block", "unblock", "record_macro", "store_look",
        "shuffle_selection", "shuffle_values",
        "full_highlight", "blind_edit",
    }
    if action not in valid_actions:
        return json.dumps({
            "error": f"Invalid action '{action}'. Valid: {sorted(valid_actions)}",
            "blocked": True,
        }, indent=2)

    destructive_actions = {"block", "unblock", "record_macro", "store_look"}
    if action in destructive_actions and not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": f"Action '{action}' is DESTRUCTIVE. Set confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    if action == "align":
        cmd = build_align(mode=mode)
    elif action == "locate":
        cmd = build_locate(fixture_ids=fixture_ids, end=end)
    elif action == "flip":
        cmd = build_flip()
    elif action == "extract":
        cmd = build_extract()
    elif action == "learn":
        if executor_id is None:
            return json.dumps({"error": "executor_id required for learn", "blocked": True}, indent=2)
        cmd = build_learn_executor(executor_id, page=page)
    elif action == "block":
        if cue_id is None:
            return json.dumps({"error": "cue_id required for block", "blocked": True}, indent=2)
        cmd = build_block_cue(cue_id, sequence_id=sequence_id)
    elif action == "unblock":
        if cue_id is None:
            return json.dumps({"error": "cue_id required for unblock", "blocked": True}, indent=2)
        cmd = build_unblock_cue(cue_id, sequence_id=sequence_id)
    elif action == "record_macro":
        if macro_id is None:
            return json.dumps({"error": "macro_id required for record_macro", "blocked": True}, indent=2)
        cmd = build_record_macro(macro_id)
    elif action == "store_look":
        cmd = build_store_look(look_id=look_id, merge=merge, overwrite=overwrite)
    elif action == "shuffle_selection":
        cmd = build_shuffle_selection()
    elif action == "shuffle_values":
        cmd = build_shuffle_values()
    elif action == "full_highlight":
        cmd = build_full_highlight()
    elif action == "blind_edit":
        cmd = build_blind_edit()
    else:
        return json.dumps({"error": f"Unhandled action: {action}"}, indent=2)

    risk = "DESTRUCTIVE" if action in destructive_actions else "SAFE_WRITE"
    client = await _sc.get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": risk,
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.EXECUTOR_CTRL)
@_handle_errors
async def master_control(
    action: str,
    master_id: int | None = None,
    master_type: int | None = None,
    level: int | None = None,
) -> str:
    """
    Control master faders — set level, set special master, or list all masters.

    Args:
        action: "set" (SAFE_WRITE), "set_special" (SAFE_WRITE), or "list" (SAFE_READ)
        master_id: Master pool slot number (required for set / set_special)
        master_type: Special master type number (required for set_special)
        level: Level 0-100 (required for set / set_special)

    Returns:
        str: JSON with command_sent, raw_response, risk_tier
    """

    valid_actions = ("set", "set_special", "list")
    if action not in valid_actions:
        return json.dumps({"error": f"action must be one of {valid_actions}", "blocked": True}, indent=2)

    if action == "set":
        if master_id is None or level is None:
            return json.dumps({"error": "master_id and level required for set", "blocked": True}, indent=2)
        cmd = build_master_at(master_id, level)
        risk_tier = "SAFE_WRITE"
    elif action == "set_special":
        if master_type is None or master_id is None or level is None:
            return json.dumps({"error": "master_type, master_id, level required for set_special", "blocked": True}, indent=2)
        cmd = build_special_master_at(master_type, master_id, level)
        risk_tier = "SAFE_WRITE"
    else:
        cmd = build_list_masters()
        risk_tier = "SAFE_READ"

    client = await _sc.get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": risk_tier,
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.SYSTEM_ADMIN)
@_handle_errors
async def system_admin(
    action: str,
    user: str | None = None,
    password: str | None = None,
    script: str | None = None,
    message: str | None = None,
    confirm_destructive: bool = False,
) -> str:
    """
    System administration — login, logout, lock, unlock, lua, chat,
    reboot, restart, shutdown.

    Args:
        action: One of:
            SAFE_READ: "logout"
            SAFE_WRITE: "login", "lock", "unlock", "lua", "chat"
            DESTRUCTIVE: "reboot", "restart", "shutdown"
        user: Username (required for login)
        password: Password (required for login; optional for lock/unlock)
        script: Lua script string (required for lua)
        message: Chat message text (required for chat)
        confirm_destructive: Must be True for reboot/restart/shutdown

    Returns:
        str: JSON with command_sent, raw_response, risk_tier
    """
    from src.commands import (
        build_login,
        build_logout,
    )

    valid_actions = {"login", "logout", "lock", "unlock", "lua", "chat", "reboot", "restart", "shutdown"}
    if action not in valid_actions:
        return json.dumps({"error": f"Invalid action '{action}'. Valid: {sorted(valid_actions)}", "blocked": True}, indent=2)

    destructive_actions = {"reboot", "restart", "shutdown"}
    if action in destructive_actions and not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": f"Action '{action}' is DESTRUCTIVE. Set confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    if action == "login":
        if user is None or password is None:
            return json.dumps({"error": "user and password required for login", "blocked": True}, indent=2)
        cmd = build_login(user, password)
        risk_tier = "SAFE_WRITE"
    elif action == "logout":
        cmd = build_logout()
        risk_tier = "SAFE_READ"
    elif action == "lock":
        cmd = build_lock(password)
        risk_tier = "SAFE_WRITE"
    elif action == "unlock":
        cmd = build_unlock(password)
        risk_tier = "SAFE_WRITE"
    elif action == "lua":
        if script is None:
            return json.dumps({"error": "script required for lua", "blocked": True}, indent=2)
        cmd = build_lua(script)
        risk_tier = "SAFE_WRITE"
    elif action == "chat":
        if message is None:
            return json.dumps({"error": "message required for chat", "blocked": True}, indent=2)
        cmd = build_chat(message)
        risk_tier = "SAFE_WRITE"
    elif action == "reboot":
        cmd = build_reboot()
        risk_tier = "DESTRUCTIVE"
    elif action == "restart":
        cmd = build_restart()
        risk_tier = "DESTRUCTIVE"
    else:
        cmd = build_shutdown()
        risk_tier = "DESTRUCTIVE"

    client = await _sc.get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": risk_tier,
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def plugin_management(action: str) -> str:
    """
    Manage Lua plugins — list available plugins or reload the plugin pool.

    Args:
        action: "list" (SAFE_READ) or "reload" (SAFE_WRITE)

    Returns:
        str: JSON with command_sent, raw_response, risk_tier
    """
    from src.commands import (
        reload_plugins as build_reload_plugins,
    )

    if action == "list":
        cmd = build_list_plugins()
        risk_tier = "SAFE_READ"
    elif action == "reload":
        cmd = build_reload_plugins()
        risk_tier = "SAFE_WRITE"
    else:
        return json.dumps({"error": f"Invalid action '{action}'. Valid: ['list', 'reload']", "blocked": True}, indent=2)

    client = await _sc.get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": risk_tier,
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PROGRAMMER_WRITE)
@_handle_errors
async def remap_fixture_ids(
    source_fixture_id: int,
    target_fixture_id: int,
    scope: str = "groups",
    confirm_destructive: bool = False
) -> str:
    """
    Remap fixture references from one fixture ID to another within groups or presets.

    Used after PSR import or cross-venue adaptation when imported cue data references
    fixture IDs that have changed in the current rig. Updates group membership and/or
    selective preset fixture references.

    DESTRUCTIVE — modifies show data. Use check_pool_slot_availability and
    list_fixtures first to confirm both fixture IDs exist in the current patch.

    Args:
        source_fixture_id: The old fixture ID to replace.
        target_fixture_id: The new fixture ID to use.
        scope: "groups" (update group membership only), "presets" (update selective
               preset references only), or "both".
        confirm_destructive: Must be True to execute.

    Returns JSON with:
    - remapped_objects: list of modified pool objects
    - skipped: list of objects where source_fixture_id was not found
    - command_log: commands sent to console
    """
    if not confirm_destructive:
        return json.dumps({
            "error": "confirm_destructive=True required",
            "detail": (
                f"This will remap fixture {source_fixture_id} -> {target_fixture_id} in {scope}. "
                "Verify both fixtures exist with list_fixtures() before proceeding."
            )
        })

    client = await _sc.get_client()

    src_info = await client.send_command_with_response(f"Info Fixture {source_fixture_id}")
    tgt_info = await client.send_command_with_response(f"Info Fixture {target_fixture_id}")

    if any(x in src_info.upper() for x in ["NOT FOUND", "ERROR"]):
        return json.dumps({"error": f"Source fixture {source_fixture_id} not found in current patch"})
    if any(x in tgt_info.upper() for x in ["NOT FOUND", "ERROR"]):
        return json.dumps({"error": f"Target fixture {target_fixture_id} not found in current patch"})

    commands_sent = []
    remapped = []

    if scope in ("groups", "both"):
        groups_raw = await client.send_command_with_response("List Group")
        group_lines = [
            ln.strip() for ln in groups_raw.splitlines()
            if ln.strip() and ln.strip()[0].isdigit()
        ]

        for gline in group_lines:
            gid = gline.split()[0]
            g_info = await client.send_command_with_response(f"Info Group {gid}")
            if str(source_fixture_id) in g_info:
                cmd = f"Fixture {target_fixture_id} Store Group {gid} /merge"
                await client.send_command_with_response(cmd)
                commands_sent.append(cmd)
                cmd2 = f"Fixture {source_fixture_id} Remove Group {gid}"
                await client.send_command_with_response(cmd2)
                commands_sent.append(cmd2)
                remapped.append(f"Group {gid}")

    return json.dumps({
        "source_fixture_id": source_fixture_id,
        "target_fixture_id": target_fixture_id,
        "scope": scope,
        "remapped_objects": remapped,
        "commands_sent": commands_sent,
        "note": (
            "Selective preset fixture references require re-recording presets with the new fixture "
            "selected — automated remapping of preset fixture IDs is not supported via telnet."
        )
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.PROGRAMMER_WRITE)
@_handle_errors
async def filter_fixture_selection(filter_type: str) -> str:
    """
    Filter the current fixture selection by output or programmer state (SAFE_WRITE).

    Narrows the active fixture selection to only those fixtures matching
    the given state condition. Use after making a broad selection to
    isolate only the fixtures of interest.

    Args:
        filter_type: Filtering condition —
            "active"     → If Active: fixtures with non-zero output
            "output"     → If Output: fixtures contributing any output value
            "programmer" → If Programmer: fixtures with values in the programmer

    Returns:
        str: JSON with command_sent, raw_response, risk_tier.
    """
    if filter_type not in _FIXTURE_FILTER_MAP:
        return json.dumps({
            "blocked": True,
            "error": f"filter_type must be one of {list(_FIXTURE_FILTER_MAP)}",
        }, indent=2)

    cmd = _FIXTURE_FILTER_MAP[filter_type]()
    client = await _sc.get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
@require_scope(OAuthScope.CUE_STORE)
@_handle_errors
async def set_advanced_timing(
    action: str,
    value: float | None = None,
    path_type: str | None = None,
    cue_id: int | None = None,
    sequence_id: int | None = None,
) -> str:
    """
    Set advanced cue/chaser timing parameters (SAFE_WRITE).

    Actions:
      "fade_path"     → FadePath {path_type}  — set fade curve shape
      "out_fade"      → OutFade {value} [Cue N [Sequence M]]
      "out_delay"     → OutDelay {value} [Cue N [Sequence M]]
      "step_fade"     → StepFade {value}  — chaser step crossfade time
      "step_in_fade"  → StepInFade {value}  — chaser step in-fade time
      "step_out_fade" → StepOutFade {value}  — chaser step out-fade time
      "snap_percent"  → SnapPercent {value}  — snap crossfade to a percentage (MA+Top)

    Args:
        action: One of the action names listed above.
        value: Numeric time value in seconds, or percentage for snap_percent
            (required for all actions except fade_path).
        path_type: Fade curve name (required for fade_path):
            linear, easeIn, easeOut, easeInOut, step, brokenLine.
        cue_id: Cue number for out_fade / out_delay scope (optional).
        sequence_id: Sequence number for out_fade / out_delay scope (optional).

    Returns:
        str: JSON with command_sent, raw_response, risk_tier.
    """
    if action not in _VALID_TIMING_ACTIONS:
        return json.dumps({
            "blocked": True,
            "error": f"action must be one of {sorted(_VALID_TIMING_ACTIONS)}",
        }, indent=2)

    if action == "fade_path":
        if not path_type:
            return json.dumps({
                "blocked": True,
                "error": "path_type is required for action='fade_path'",
            }, indent=2)
        try:
            cmd = build_fade_path(path_type)
        except ValueError as exc:
            return json.dumps({"blocked": True, "error": str(exc)}, indent=2)
    elif action == "snap_percent":
        if value is None:
            return json.dumps({"blocked": True, "error": "value is required"}, indent=2)
        cmd = build_snap_percent(value)
    elif action == "out_fade":
        if value is None:
            return json.dumps({"blocked": True, "error": "value is required"}, indent=2)
        cmd = build_out_fade(value, cue_id=cue_id, sequence_id=sequence_id)
    elif action == "out_delay":
        if value is None:
            return json.dumps({"blocked": True, "error": "value is required"}, indent=2)
        cmd = build_out_delay(value, cue_id=cue_id, sequence_id=sequence_id)
    elif action == "step_fade":
        if value is None:
            return json.dumps({"blocked": True, "error": "value is required"}, indent=2)
        cmd = build_step_fade(value)
    elif action == "step_in_fade":
        if value is None:
            return json.dumps({"blocked": True, "error": "value is required"}, indent=2)
        cmd = build_step_in_fade(value)
    else:  # step_out_fade
        if value is None:
            return json.dumps({"blocked": True, "error": "value is required"}, indent=2)
        cmd = build_step_out_fade(value)

    client = await _sc.get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


# ============================================================


@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def preview_executor_content(
    action: str,
    executor_id: int | None = None,
) -> str:
    """
    Enter preview mode for a console executor (SAFE_WRITE).

    Preview mode lets you inspect what a cue will output without
    affecting the live rig. Use preview_edit to open the editor
    in preview mode for non-destructive cue adjustments.

    Actions:
      "preview"        → Preview [Executor N]
      "preview_edit"   → PreviewEdit [Executor N]
      "preview_exec"   → PreviewExecutor N (executor_id required)

    Args:
        action: One of "preview", "preview_edit", "preview_exec".
        executor_id: Executor number (optional for preview/preview_edit,
            required for preview_exec).

    Returns:
        str: JSON with command_sent, raw_response, risk_tier.
    """
    valid_actions = frozenset({"preview", "preview_edit", "preview_exec"})
    if action not in valid_actions:
        return json.dumps({
            "blocked": True,
            "error": f"action must be one of {sorted(valid_actions)}",
        }, indent=2)

    if action == "preview_exec" and executor_id is None:
        return json.dumps({
            "blocked": True,
            "error": "executor_id is required for action='preview_exec'",
        }, indent=2)

    if action == "preview":
        cmd = build_preview(executor_id)
    elif action == "preview_edit":
        cmd = build_preview_edit(executor_id)
    else:  # preview_exec
        cmd = build_preview_executor(executor_id)

    client = await _sc.get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)
