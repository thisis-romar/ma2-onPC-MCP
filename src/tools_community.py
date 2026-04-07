# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
tools_community.py -- All 20 COMMUNITY-tier MCP tool functions.

These tools are free-tier (not listed in TOOL_LICENSE_TIERS) and will
remain in the public repository after the git submodule split.

Imports the shared ``mcp`` FastMCP instance and ``_handle_errors`` decorator
from ``server_core.py`` so tools register on the same server.
"""

from __future__ import annotations

import asyncio
import json
import logging

from src.auth import OAuthScope, require_scope
from src.commands import (
    attribute_at,
    channel_at,
    fixture_at,
    go_sequence,
    goto_cue,
    group_at,
    pause_sequence,
    select_fixture,
)
from src.commands import clear as build_clear
from src.commands import clear_active as build_clear_active
from src.commands import clear_all as build_clear_all
from src.commands import clear_selection as build_clear_selection
from src.commands import def_go_back as build_def_go_back
from src.commands import def_go_forward as build_def_go_forward
from src.commands import def_go_pause as build_def_go_pause
from src.commands import get_user_var as build_get_user_var
from src.commands import go as build_go
from src.commands import go_back as build_go_back
from src.commands import go_fast_back as build_go_fast_back
from src.commands import go_fast_forward as build_go_fast_forward
from src.commands import goto as build_goto
from src.commands import info as build_info
from src.commands import list_attribute as build_list_attribute
from src.commands import list_cue as build_list_cue
from src.commands import list_group as build_list_group
from src.commands import list_messages as build_list_messages
from src.commands import list_objects as build_list_objects
from src.commands import list_preset as build_list_preset
from src.commands import list_user_var as build_list_user_var
from src.commands import list_var as build_list_var
from src.commands import release_executor as build_release_executor
from src.navigation import get_current_location, list_destination, navigate
import src.server_core as _sc

from src.server_core import (
    _get_sequence_for_executor,
    _GMA_SAFETY_LEVEL,
    _handle_errors,
    _parse_listvar,
    _read_selected_exec,
    _validate_object_exists,
    _vocab_spec,
    mcp,
)

# Re-export for test discoverability (tools use _sc.get_client() for late binding)
get_client = _sc.get_client
from src.vocab import RiskTier, classify_token

logger = logging.getLogger(__name__)


# ============================================================
# Tool 1: execute_sequence
# ============================================================

@mcp.tool()
@require_scope(OAuthScope.PLAYBACK_GO)
@_handle_errors
async def execute_sequence(
    sequence_id: int,
    action: str,
    cue_id: int | None = None,
) -> str:
    """
    Execute sequence-related operations.

    Args:
        sequence_id: Sequence number
        action: Operation type: "go" (execute), "pause" (pause), or "goto" (jump to cue)
        cue_id: (Required for goto) Target cue number

    Returns:
        str: Operation result message

    Examples:
        - Execute sequence 1
        - Pause sequence 2
        - Jump to cue 5 of sequence 1
    """
    client = await _sc.get_client()

    if action == "go":
        cmd = go_sequence(sequence_id)
        await client.send_command(cmd)
        return f"Executed Sequence {sequence_id}"

    elif action == "pause":
        cmd = pause_sequence(sequence_id)
        await client.send_command(cmd)
        return f"Paused Sequence {sequence_id}"

    elif action == "goto":
        if cue_id is None:
            return "Error: goto action requires cue_id to be specified"
        cmd = goto_cue(sequence_id, cue_id)
        await client.send_command(cmd)
        return f"Jumped to Cue {cue_id} of Sequence {sequence_id}"

    return f"Unknown action: {action}, use go, pause, or goto"


# ============================================================
# Tool 2: send_raw_command
# ============================================================

@mcp.tool()
@require_scope(OAuthScope.CUE_STORE)
@_handle_errors
async def send_raw_command(
    command: str,
    confirm_destructive: bool = False,
) -> str:
    """
    Send a raw MA command to grandMA2 and return the console response.

    WARNING: This is a low-level tool that sends commands directly to a LIVE
    lighting console. Prefer the higher-level tools (create_fixture_group,
    execute_sequence) whenever possible.

    SAFETY: Commands are classified by risk tier before sending:
    - SAFE_READ (list, info, cd): Always allowed
    - SAFE_WRITE (at, go, clear, blackout): Allowed in standard and admin mode
    - DESTRUCTIVE (delete, store, assign, shutdown): Blocked unless
      confirm_destructive=True. Set GMA_SAFETY_LEVEL=admin to skip checks.

    Args:
        command: Raw MA command to send
        confirm_destructive: Must be True to send destructive commands
            (delete, store, assign, shutdown, newshow, etc.)

    Returns:
        str: JSON with command_sent, risk_tier, raw_response, and any
            safety block information.

    Examples:
        - go+ executor 1.1
        - list cue
        - store sequence 1 cue 1 (requires confirm_destructive=True)
    """
    # Input sanitization: reject line breaks that could inject commands
    if "\r" in command or "\n" in command:
        return json.dumps({
            "command_sent": None,
            "error": "Command contains line breaks (\\r or \\n) which could "
                     "inject additional commands. Remove them and retry.",
            "blocked": True,
        }, indent=2)

    # Safety gate: classify the first token
    first_token = command.strip().split()[0] if command.strip() else ""
    resolved = classify_token(first_token, _vocab_spec)
    risk = resolved.risk

    # Log and optionally block destructive commands
    if risk == RiskTier.DESTRUCTIVE:
        if _GMA_SAFETY_LEVEL == "admin":
            # Admin mode: allow but still log for audit trail
            logger.warning(
                "ADMIN-MODE destructive command: %r (risk=%s, canonical=%s)",
                command, risk.value, resolved.canonical,
            )
        elif not confirm_destructive:
            logger.warning(
                "BLOCKED destructive command: %r (risk=%s, canonical=%s)",
                command, risk.value, resolved.canonical,
            )
            return json.dumps({
                "command_sent": None,
                "risk_tier": risk.value,
                "canonical_keyword": resolved.canonical,
                "error": (
                    f"Command '{first_token}' is classified as {risk.value}. "
                    f"Set confirm_destructive=True to proceed, or use "
                    f"GMA_SAFETY_LEVEL=admin to disable safety checks."
                ),
                "blocked": True,
            }, indent=2)
        else:
            logger.warning(
                "CONFIRMED destructive command: %r (risk=%s, canonical=%s)",
                command, risk.value, resolved.canonical,
            )

    # Block all write commands in read-only mode
    if _GMA_SAFETY_LEVEL == "read-only" and risk != RiskTier.SAFE_READ:
        logger.warning(
            "BLOCKED non-read command in read-only mode: %r (risk=%s)",
            command, risk.value,
        )
        return json.dumps({
            "command_sent": None,
            "risk_tier": risk.value,
            "error": (
                "Server is in read-only mode (GMA_SAFETY_LEVEL=read-only). "
                "Only SAFE_READ commands (list, info, cd) are allowed."
            ),
            "blocked": True,
        }, indent=2)

    logger.info(
        "Sending command: %r (risk=%s, canonical=%s)",
        command, risk.value, resolved.canonical,
    )

    client = await _sc.get_client()
    raw_response = await client.send_command_with_response(command)

    return json.dumps({
        "command_sent": command,
        "risk_tier": risk.value,
        "canonical_keyword": resolved.canonical,
        "raw_response": raw_response,
        "blocked": False,
    }, indent=2)


# ============================================================
# Tool 3: navigate_console
# ============================================================

@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def navigate_console(
    destination: str,
    object_id: int | None = None,
) -> str:
    """
    Navigate the grandMA2 console's object tree using ChangeDest (cd).

    Sends a cd command and captures the raw telnet response, attempting
    to parse the resulting console prompt to determine the current
    location in the object tree.

    EXPLORATORY: The exact MA2 telnet prompt format is being validated.
    The raw_response field always contains the unmodified telnet output
    for manual inspection, regardless of whether parsing succeeded.

    Args:
        destination: Navigation target. Supported formats:
            - "/" to go to root
            - ".." to go up one level
            - A number (e.g., "5") to navigate by index
            - An object type (e.g., "Group") when object_id is provided
              (uses dot notation: cd [type].[id])
            - A quoted name (e.g., '"MySequence"') to navigate by name
        object_id: Object ID, produces dot notation cd [type].[id]
            (e.g., destination="Group", object_id=1 -> cd Group.1)

    Returns:
        str: JSON with command_sent, raw_response, parsed prompt details,
             and success indicator.

    Examples:
        - Navigate to root: destination="/"
        - Go up one level: destination=".."
        - Navigate to Group 1: destination="Group", object_id=1 -> cd Group.1
        - Navigate by index: destination="5"
        - After navigating, use list_console_destination to enumerate objects
    """
    client = await _sc.get_client()
    result = await navigate(client, destination, object_id)

    return json.dumps(
        {
            "command_sent": result.command_sent,
            "raw_response": result.raw_response,
            "success": result.success,
            "parsed_prompt": {
                "prompt_line": result.parsed_prompt.prompt_line,
                "location": result.parsed_prompt.location,
                "object_type": result.parsed_prompt.object_type,
                "object_id": result.parsed_prompt.object_id,
            },
        },
        indent=2,
    )


# ============================================================
# Tool 4: get_console_location
# ============================================================

@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def get_console_location() -> str:
    """
    Query the current grandMA2 console destination without navigating.

    Sends an empty command to prompt the console to re-display its
    prompt, then parses the response to determine the current location.

    Returns:
        str: JSON with raw_response, parsed prompt details,
             and success indicator.
    """
    client = await _sc.get_client()
    result = await get_current_location(client)

    return json.dumps(
        {
            "command_sent": result.command_sent,
            "raw_response": result.raw_response,
            "success": result.success,
            "parsed_prompt": {
                "prompt_line": result.parsed_prompt.prompt_line,
                "location": result.parsed_prompt.location,
                "object_type": result.parsed_prompt.object_type,
                "object_id": result.parsed_prompt.object_id,
            },
        },
        indent=2,
    )


# ============================================================
# Tool 5: list_console_destination
# ============================================================

@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def list_console_destination(
    object_type: str | None = None,
) -> str:
    """
    List objects at the current grandMA2 console destination.

    After navigating with cd (navigate_console), use this tool to
    enumerate children at the current location.  Parses the list
    feedback to extract object-type, object-id, and element names.

    Args:
        object_type: Optional filter (e.g., "cue", "group", "preset").
            If omitted, lists everything at the current destination.

    Returns:
        str: JSON with command_sent, raw_response, and parsed entries
             (each with object_type, object_id, name).
    """
    client = await _sc.get_client()
    result = await list_destination(client, object_type)

    entries_out = []
    for e in result.parsed_list.entries:
        entry = {
            "object_type": e.object_type,
            "object_id": e.object_id,
            "name": e.name,
            "raw_line": e.raw_line,
        }
        if e.col3 is not None:
            entry["col3"] = e.col3
        if e.columns:
            entry["columns"] = e.columns
        entries_out.append(entry)

    return json.dumps(
        {
            "command_sent": result.command_sent,
            "raw_response": result.raw_response,
            "entries": entries_out,
            "entry_count": len(result.parsed_list.entries),
        },
        indent=2,
    )


# ============================================================
# Tool 6: set_intensity
# ============================================================

@mcp.tool()
@require_scope(OAuthScope.PROGRAMMER_WRITE)
@_handle_errors
async def set_intensity(
    target_type: str,
    target_id: int,
    level: int | float,
    end_id: int | None = None,
) -> str:
    """
    Set the intensity (dimmer) level on fixtures, groups, or channels.

    This is the most fundamental lighting operation — controlling how bright
    lights are. Selects the target and sets it to the specified percentage.

    Args:
        target_type: Object type — "fixture", "group", or "channel"
        target_id: Object ID number
        level: Intensity percentage (0-100). Use 0 for off, 100 for full.
        end_id: End ID for range selection (e.g., fixture 1 thru 10)

    Returns:
        str: JSON with command_sent and raw_response from the console.

    Examples:
        - Set fixture 1 to 50%: target_type="fixture", target_id=1, level=50
        - Set group 3 to full: target_type="group", target_id=3, level=100
        - Set fixtures 1-10 to 75%: target_type="fixture", target_id=1, level=75, end_id=10
    """
    target_type = target_type.lower()

    if target_type == "fixture":
        cmd = fixture_at(target_id, level, end=end_id)
    elif target_type == "group":
        cmd = group_at(target_id, level)
    elif target_type == "channel":
        cmd = channel_at(target_id, level, end=end_id)
    else:
        return json.dumps({
            "error": f"Unknown target_type: {target_type}. Use 'fixture', 'group', or 'channel'.",
            "blocked": True,
        }, indent=2)

    client = await _sc.get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
    }, indent=2)


# ============================================================
# Tool 7: get_object_info
# ============================================================

@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def get_object_info(
    object_type: str,
    object_id: int | str,
) -> str:
    """
    Query information about any object in the show.

    Returns the console's info response for the specified object,
    which includes its properties, status, and metadata.

    Args:
        object_type: Object type (e.g. "fixture", "group", "cue",
            "sequence", "preset", "executor", "macro")
        object_id: Object ID. For presets use "type.id" format
            (e.g. "2.1" for color preset 1).

    Returns:
        str: JSON with command_sent and raw_response containing
            the object's information.

    Examples:
        - Get info on group 3: object_type="group", object_id=3
        - Get info on cue 5: object_type="cue", object_id=5
        - Get info on color preset 1: object_type="preset", object_id="2.1"
    """
    cmd = build_info(object_type, object_id)

    client = await _sc.get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
    }, indent=2)


# ============================================================
# Tool 8: clear_programmer
# ============================================================

@mcp.tool()
@require_scope(OAuthScope.PROGRAMMER_WRITE)
@_handle_errors
async def clear_programmer(
    mode: str = "all",
) -> str:
    """
    Clear the programmer to reset fixture selection and active values.

    The programmer holds the current working state — selected fixtures
    and any values you've applied. Clearing it gives you a clean slate.

    Modes:
    - "all": Empty the entire programmer (selection + values)
    - "selection": Deselect all fixtures but keep active values
    - "active": Deactivate values but keep fixture selection
    - "clear": Sequential clear (selection → active → all on repeated calls)

    Args:
        mode: Clear mode — "all" (default), "selection", "active", or "clear"

    Returns:
        str: JSON with command_sent and raw_response.

    Examples:
        - Full reset: mode="all"
        - Just deselect fixtures: mode="selection"
        - Just drop active values: mode="active"
    """
    mode = mode.lower()
    if mode == "all":
        cmd = build_clear_all()
    elif mode == "selection":
        cmd = build_clear_selection()
    elif mode == "active":
        cmd = build_clear_active()
    elif mode == "clear":
        cmd = build_clear()
    else:
        return json.dumps({
            "error": f"Unknown mode: {mode}. Use 'all', 'selection', 'active', or 'clear'.",
            "blocked": True,
        }, indent=2)

    client = await _sc.get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
    }, indent=2)


# ============================================================
# Tool 9: set_attribute
# ============================================================

@mcp.tool()
@require_scope(OAuthScope.PROGRAMMER_WRITE)
@_handle_errors
async def set_attribute(
    attribute_name: str,
    value: int | float,
    fixture_id: int | None = None,
    fixture_end: int | None = None,
    group_id: int | None = None,
) -> str:
    """
    Set a specific fixture attribute (Pan, Tilt, Zoom, etc.) to a value.

    Controls individual fixture parameters beyond simple dimmer intensity.
    Optionally select fixtures/group first.

    Args:
        attribute_name: Attribute name (e.g. "Pan", "Tilt", "Zoom", "Focus", "Iris")
        value: Attribute value (typically 0-100 for percentage, or degrees for Pan/Tilt)
        fixture_id: Optional fixture to select first (single or range start)
        fixture_end: Optional end fixture for range selection
        group_id: Optional group to select first

    Returns:
        str: JSON with commands_sent and raw_response.

    Examples:
        - Set Pan to 120: attribute_name="Pan", value=120
        - Set Tilt to 50 on group 2: attribute_name="Tilt", value=50, group_id=2
        - Set Zoom on fixtures 1-10: attribute_name="Zoom", value=80, fixture_id=1, fixture_end=10
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

    cmd = attribute_at(attribute_name, value)
    raw_response = await client.send_command_with_response(cmd)
    commands_sent.append(cmd)

    return json.dumps({
        "commands_sent": commands_sent,
        "raw_response": raw_response,
    }, indent=2)


# ============================================================
# Tool 10: query_object_list
# ============================================================

@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def query_object_list(
    object_type: str | None = None,
    object_id: int | str | None = None,
    end: int | None = None,
    sequence_id: int | None = None,
    preset_type: str | int | None = None,
    filename: str | None = None,
    condition: str | None = None,
) -> str:
    """
    List objects from the show file by type — cues, groups, presets, etc.

    Sends typed `list <type>` commands with type-specific options.
    Different from list_console_destination (which lists at the current
    navigation location). This tool queries named object pools directly.

    Args:
        object_type: Object type to list. Typed shortcuts:
            "cue", "group", "preset", "attribute", "messages".
            Or any generic type (e.g. "sequence", "macro", "executor").
            If omitted, lists all objects at the default scope.
        object_id: Optional object ID to list a specific item
        end: Optional end ID for range listing (e.g. cue 1 thru 10)
        sequence_id: Sequence to list cues from (only for object_type="cue")
        preset_type: Preset type name or number (only for object_type="preset",
            e.g. "color", "position", "4")
        filename: Optional filename to export the list output
        condition: Optional filter condition (for "messages" or generic types)

    Returns:
        str: JSON with command_sent and raw_response.

    Examples:
        - List all cues: object_type="cue"
        - List cues in sequence 2: object_type="cue", sequence_id=2
        - List groups: object_type="group"
        - List color presets: object_type="preset", preset_type="color"
        - List attributes: object_type="attribute"
    """
    otype = (object_type or "").lower()

    if otype == "cue":
        cmd = build_list_cue(
            cue_id=object_id, end=end, sequence_id=sequence_id,
            filename=filename,
        )
    elif otype == "group":
        cmd = build_list_group(
            group_id=object_id, end=end, filename=filename,
        )
    elif otype == "preset":
        cmd = build_list_preset(
            preset_type=preset_type, preset_id=object_id,
            end=end, filename=filename,
        )
    elif otype == "attribute":
        cmd = build_list_attribute(filename=filename)
    elif otype == "messages":
        cmd = build_list_messages(condition=condition, filename=filename)
    else:
        cmd = build_list_objects(
            object_type=object_type, object_id=object_id,
            end=end, filename=filename, condition=condition,
        )

    client = await _sc.get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
    }, indent=2)


# ============================================================
# Tool 11: list_system_variables
# ============================================================

@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def list_system_variables(
    filter_prefix: str | None = None,
) -> str:
    """
    List all grandMA2 built-in system variables (SAFE_READ).

    Sends `ListVar` to the console and returns parsed key=value pairs.
    System variables include $SELECTEDEXEC, $TIME, $DATE, $VERSION, $HOSTSTATUS,
    $FADERPAGE, $BUTTONPAGE, $SELECTEDFIXTURESCOUNT, $USER, $HOSTNAME, etc.

    Args:
        filter_prefix: Optional prefix filter (case-insensitive).
            e.g. "SELECTED" returns only $SELECTEDEXEC, $SELECTEDEXECCUE, etc.
            Omit to return all variables.

    Returns:
        str: JSON with `variables` dict (name→value), `variable_count`, and `raw_response`.
    """
    client = await _sc.get_client()
    raw = await client.send_command_with_response("ListVar")

    variables = _parse_listvar(raw, filter_prefix=filter_prefix)
    return json.dumps({
        "variables": variables,
        "variable_count": len(variables),
        "raw_response": raw,
    }, indent=2)


# ============================================================
# Tool 12: playback_action
# ============================================================

@mcp.tool()
@require_scope(OAuthScope.PLAYBACK_GO)
@_handle_errors
async def playback_action(
    action: str,
    object_type: str | None = None,
    object_id: int | list[int] | None = None,
    cue_id: int | float | None = None,
    end: int | None = None,
    cue_mode: str | None = None,
    executor: int | list[int] | None = None,
    sequence: int | None = None,
) -> str:
    """
    Execute playback operations — go, go back, goto, fast forward/back, etc.

    Full-featured playback control with cue_mode and executor targeting.
    Coexists with execute_sequence (which uses legacy go_sequence/pause_sequence).

    Args:
        action: Playback action to perform:
            "go" — fire the next cue (optionally on a specific executor/sequence)
            "go_back" — fire the previous cue
            "goto" — jump to a specific cue (requires cue_id)
            "fast_forward" — skip forward (>>>)
            "fast_back" — skip backward (<<<)
            "def_go" — go on the selected executor (go+); response includes
                       selected_executor and selected_cue_before
            "def_go_back" / "def_goback" — go back on the selected executor;
                       response includes selected_executor and selected_cue_before
            "def_pause" — pause the selected executor; response includes
                       selected_executor and selected_cue_before
        object_type: Object type for go/go_back (e.g. "executor", "sequence")
        object_id: Object ID for go/go_back — single int or list of ints.
                   List produces "N + M + ..." syntax for multi-executor targeting.
        cue_id: Target cue number (required for "goto")
        end: End ID for range (go/go_back)
        cue_mode: Cue execution mode: "normal", "assert", "xassert", "release"
        executor: Executor ID for goto/fast_forward/fast_back — single int or list of ints.
                  List produces "N + M + ..." syntax (e.g. [1,2,3] → ">>> executor 1 + 2 + 3").
        sequence: Sequence ID for goto/fast_forward/fast_back

    Returns:
        str: JSON with command_sent and raw_response.
             def_go/def_go_back/def_pause also include selected_executor and
             selected_cue_before (read from $SELECTEDEXEC before firing).

    Examples:
        - Go on executor 1: action="go", object_type="executor", object_id=1
        - Go on executors 1+2+3: action="go", object_type="executor", object_id=[1,2,3]
        - Go back: action="go_back"
        - Goto cue 5: action="goto", cue_id=5
        - Goto cue 3 on sequence 2: action="goto", cue_id=3, sequence=2
        - Fast forward: action="fast_forward"
        - Fast forward executors 1,2,3: action="fast_forward", executor=[1,2,3]
        - Go on selected executor: action="def_go"
        - Go back on selected executor: action="def_go_back"
    """
    action = action.lower()

    if action == "go":
        cmd = build_go(
            object_type=object_type, object_id=object_id,
            end=end, cue_mode=cue_mode,
        )
    elif action == "go_back":
        cmd = build_go_back(
            object_type=object_type, object_id=object_id,
            end=end, cue_mode=cue_mode,
        )
    elif action == "goto":
        if cue_id is None:
            return json.dumps({
                "error": "goto action requires cue_id to be specified.",
                "blocked": True,
            }, indent=2)

        # Pre-flight: validate cue exists before sending goto
        client = await _sc.get_client()
        validation_info: dict = {}
        resolved_sequence = sequence

        if resolved_sequence is None and executor is not None:
            # Derive sequence from the executor assignment
            resolved_sequence, exec_raw = await _get_sequence_for_executor(
                client, executor
            )
            validation_info["executor_probe_response"] = exec_raw

        if resolved_sequence is not None:
            cue_probe_arg = f"{cue_id} sequence {resolved_sequence}"
            cue_exists, cue_raw = await _validate_object_exists(
                client, "cue", cue_probe_arg
            )
            validation_info["cue_exists"] = cue_exists
            validation_info["cue_probe_response"] = cue_raw
            if not cue_exists:
                return json.dumps({
                    "command_sent": None,
                    "error": (
                        f"Cue {cue_id} does not exist in sequence {resolved_sequence}. "
                        "MA2 would return Error #72 (COMMAND NOT EXECUTED)."
                    ),
                    "hint": "Use list_sequence_cues(sequence_id) to see available cues.",
                    **validation_info,
                    "blocked": True,
                }, indent=2)
        else:
            validation_info["warning"] = (
                "Could not resolve sequence context — command sent without cue "
                "pre-flight check. Provide sequence or executor for validation."
            )

        cmd = build_goto(
            cue_id, executor=executor, sequence=sequence,
            cue_mode=cue_mode,
        )
        raw_response = await client.send_command_with_response(cmd)
        return json.dumps({
            "command_sent": cmd,
            "raw_response": raw_response,
            **validation_info,
        }, indent=2)
    elif action == "fast_forward":
        cmd = build_go_fast_forward(executor=executor, sequence=sequence)
    elif action == "fast_back":
        cmd = build_go_fast_back(executor=executor, sequence=sequence)
    elif action in ("def_go", "def_go_back", "def_goback", "def_pause"):
        client = await _sc.get_client()
        sel_exec, sel_cue = await _read_selected_exec(client)

        if action == "def_go":
            cmd = build_def_go_forward()
        elif action in ("def_go_back", "def_goback"):
            cmd = build_def_go_back()
        else:  # def_pause
            cmd = build_def_go_pause()

        raw_response = await client.send_command_with_response(cmd)
        return json.dumps({
            "command_sent": cmd,
            "raw_response": raw_response,
            "selected_executor": sel_exec,
            "selected_cue_before": sel_cue,
        }, indent=2)
    else:
        return json.dumps({
            "error": (
                f"Unknown action: {action}. Use 'go', 'go_back', 'goto', "
                f"'fast_forward', 'fast_back', 'def_go', 'def_go_back', or 'def_pause'."
            ),
            "blocked": True,
        }, indent=2)

    client = await _sc.get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
    }, indent=2)


# ============================================================
# Tool 13: get_executor_status
# ============================================================

@mcp.tool()
@require_scope(OAuthScope.STATE_READ)
@_handle_errors
async def get_executor_status(
    executor_id: int | None = None,
    page: int | None = None,
) -> str:
    """
    Query the status of one or all executors (SAFE_READ).

    Args:
        executor_id: Executor ID to inspect (optional; lists all if omitted)
        page: Page number for page-qualified addressing (optional)

    Returns:
        str: JSON result with raw console response
    """
    if executor_id is not None:
        ref = f"{page}.{executor_id}" if page is not None else str(executor_id)
        cmd = f"list executor {ref}"
    else:
        cmd = "list executor"

    client = await _sc.get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "SAFE_READ",
    }, indent=2)


# ============================================================
# Tool 14: get_executor_state
# ============================================================

@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def get_executor_state(
    executor_id: int,
    page: int = 1,
) -> str:
    """
    Read all 32 fields of a single executor via 'List Executor page.id' (SAFE_READ).

    Returns all KEY=VALUE fields including Width, Priority, AutoStart, AutoStop,
    Crossfade, SpeedMaster, RateMaster, Filter, PlaybackMaster, etc.

    Must use page-qualified addressing — bare executor IDs return wrong data.

    Args:
        executor_id: Executor ID (e.g. 203).
        page: Page number (default 1).

    Returns:
        str: JSON with fields dict, command_sent, raw_response.
    """
    from src.prompt_parser import parse_executor_list
    cmd = f"List Executor {page}.{executor_id}"
    client = await _sc.get_client()
    raw = await client.send_command_with_response(cmd)
    fields = parse_executor_list(raw)
    return json.dumps({
        "command_sent": cmd,
        "fields": fields,
        "raw_response": raw,
        "risk_tier": "SAFE_READ",
    }, indent=2)


# ============================================================
# Tool 15: discover_fixture_type_attributes
# ============================================================

@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def discover_fixture_type_attributes(
    fixture_type_id: int,
) -> str:
    """
    Discover attribute names for a fixture type via EditSetup tree navigation (SAFE_READ).

    Navigates cd EditSetup → FixtureTypes → type N → first mode → first subfixture → list,
    returning ChannelType rows with attribute library names (e.g. PAN, TILT, COLORRGB1).

    Use this to confirm which attributes a fixture type exposes before building presets.
    Note: Info FixtureType N does NOT return attribute names — this navigation method is
    the correct approach (live-verified 2026-03-31).

    Args:
        fixture_type_id: Fixture type number (e.g. 4 for Mac Viper Profile 16-bit).

    Returns:
        str: JSON with raw_response containing ChannelType rows.
    """
    client = await _sc.get_client()

    async def send(cmd: str) -> str:
        return await client.send_command_with_response(cmd)

    await send("cd /")
    await send("cd EditSetup")
    await send("cd FixtureTypes")
    await send(f"cd {fixture_type_id}")
    await send("cd 1")  # first mode
    await send("cd 1")  # first subfixture
    raw = await send("list")
    await send("cd /")  # return to root

    return json.dumps({
        "fixture_type_id": fixture_type_id,
        "navigation": f"EditSetup → FixtureTypes → {fixture_type_id} → 1 → 1 → list",
        "raw_response": raw,
        "risk_tier": "SAFE_READ",
    }, indent=2)


# ============================================================
# Tool 16: scan_page_executor_layout
# ============================================================

@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def scan_page_executor_layout(
    page: int = 1,
    executor_id_start: int = 201,
    executor_id_end: int = 240,
) -> str:
    """
    Scan a range of executors on a page and return their slot occupancy map (SAFE_READ).

    Queries each executor in the range via 'List Executor page.id' (KEY=VALUE format),
    extracts Name, Sequence, and Width. Builds an occupancy map showing which consecutive
    slots are blocked by wide executors, and lists free slots.

    Use this BEFORE setting width on an executor to confirm the adjacent slot is free.
    A width=2 executor at slot N blocks slot N+1; the console will silently fail or wrap
    if N+1 is already occupied.

    Args:
        page: Page number to scan (default 1).
        executor_id_start: First executor ID to check (default 201).
        executor_id_end: Last executor ID to check (default 240).

    Returns:
        str: JSON with:
          - executors: list of {id, name, sequence, width, slots_occupied}
          - blocked_slots: set of slot IDs consumed by multi-wide executors
          - free_slots: slot IDs in range with no assignment
    """
    from src.prompt_parser import parse_executor_list

    client = await _sc.get_client()
    executor_data: list[dict] = []
    occupied_slots: set[int] = set()

    for exec_id in range(executor_id_start, executor_id_end + 1):
        cmd = f"List Executor {page}.{exec_id}"
        raw = await client.send_command_with_response(cmd)
        fields = parse_executor_list(raw)

        # Skip unassigned slots — no Name and no Sequence
        if not fields.get("Name") and not fields.get("Sequence"):
            continue

        width = int(fields.get("Width", 1))
        name = fields.get("Name", "")
        sequence = fields.get("Sequence", "")
        slots = list(range(exec_id, exec_id + width))

        executor_data.append({
            "id": exec_id,
            "name": name,
            "sequence": sequence,
            "width": width,
            "slots_occupied": slots,
        })
        for s in slots:
            occupied_slots.add(s)

        await asyncio.sleep(0.1)  # avoid flooding telnet

    all_slots = set(range(executor_id_start, executor_id_end + 1))
    free_slots = sorted(all_slots - occupied_slots)

    return json.dumps({
        "page": page,
        "scanned_range": [executor_id_start, executor_id_end],
        "executors": executor_data,
        "occupied_slots": sorted(occupied_slots),
        "free_slots": free_slots,
        "risk_tier": "SAFE_READ",
    }, indent=2)


# ============================================================
# Tool 17: if_filter
# ============================================================

@mcp.tool()
@require_scope(OAuthScope.PROGRAMMER_WRITE)
@_handle_errors
async def if_filter(
    filter_type: str,
    fixture_id: int | None = None,
    attribute_name: str | None = None,
) -> str:
    """
    Apply an If filter to the current selection or command context.

    Args:
        filter_type: "active" (bare 'if'), "fixture" (specific fixture), or "attribute"
        fixture_id: Fixture ID (required for "fixture" and "attribute")
        attribute_name: Attribute name (required for "attribute"; e.g. "Pan")

    Returns:
        str: JSON result with command sent
    """
    if filter_type not in ("active", "fixture", "attribute"):
        return json.dumps(
            {"error": "filter_type must be 'active', 'fixture', or 'attribute'", "blocked": True},
            indent=2,
        )
    if filter_type in ("fixture", "attribute") and fixture_id is None:
        return json.dumps(
            {"error": "fixture_id is required for filter_type != 'active'", "blocked": True},
            indent=2,
        )
    if filter_type == "attribute" and attribute_name is None:
        return json.dumps(
            {"error": "attribute_name is required for filter_type='attribute'", "blocked": True},
            indent=2,
        )

    if filter_type == "active":
        cmd = "if"
    elif filter_type == "fixture":
        cmd = f"if fixture {fixture_id}"
    else:
        cmd = f'if fixture {fixture_id} attribute "{attribute_name}"'

    client = await _sc.get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


# ============================================================
# Tool 18: release_executor
# ============================================================

@mcp.tool()
@require_scope(OAuthScope.PLAYBACK_GO)
@_handle_errors
async def release_executor(
    executor_id: int,
    page: int | None = None,
) -> str:
    """
    Release an executor, returning it to its default state.

    Args:
        executor_id: Executor ID (1-999).
        page: Page number for page-qualified addressing (optional).

    Returns:
        str: JSON with command_sent, raw_response, risk_tier.
    """
    cmd = build_release_executor(executor_id, page=page)
    client = await _sc.get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


# ============================================================
# Tool 19: get_variable
# ============================================================

@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def get_variable(
    action: str,
    var_name: str | None = None,
) -> str:
    """
    Read variables from the console (SAFE_READ).

    Args:
        action: One of:
            "echo"         — read any variable via `Echo $NAME` (system + user vars).
                             Use this for built-in system variables: $SELECTEDEXEC,
                             $TIME, $DATE, $VERSION, $FADERPAGE, $BUTTONPAGE,
                             $SELECTEDFIXTURESCOUNT, $USER, $HOSTNAME, $HOSTSTATUS, etc.
            "get_user"     — read a user variable via GetUserVar.
            "list_var"     — list all global show variables.
            "list_user_var"— list all user-profile variables.
        var_name: Variable name (required for "echo" and "get_user").
                  May include or omit leading $. E.g. "SELECTEDEXEC" or "$mycounter".

    Returns:
        str: JSON with command_sent, raw_response, risk_tier.
             For "echo", also includes `variable` and `value` keys.
    """
    valid_actions = ("echo", "get_user", "list_var", "list_user_var")
    if action not in valid_actions:
        return json.dumps({
            "error": f"action must be one of {valid_actions}",
            "blocked": True,
        }, indent=2)

    if action == "echo":
        if not var_name:
            return json.dumps({
                "error": "var_name is required for echo action",
                "blocked": True,
            }, indent=2)
        clean = var_name.lstrip("$")
        cmd = "ListVar"
        client = await _sc.get_client()
        raw = await client.send_command_with_response(cmd)
        variables = _parse_listvar(raw)
        value = variables.get(f"${clean}") or variables.get(f"${clean.upper()}")
        return json.dumps({
            "variable": f"${clean}",
            "value": value,
            "found": value is not None,
            "command_sent": cmd,
            "raw_response": raw,
            "risk_tier": "SAFE_READ",
        }, indent=2)

    if action == "get_user":
        if not var_name:
            return json.dumps({
                "error": "var_name is required for get_user action",
                "blocked": True,
            }, indent=2)
        cmd = build_get_user_var(var_name)
    elif action == "list_var":
        cmd = build_list_var()
    else:
        cmd = build_list_user_var()

    client = await _sc.get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "SAFE_READ",
    }, indent=2)


# ============================================================
# Tool 20: discover_object_names
# ============================================================

@mcp.tool()
@require_scope(OAuthScope.DISCOVER)
@_handle_errors
async def discover_object_names(destination: str) -> str:
    """
    Navigate to an object pool and return all object names for wildcard pattern building.

    This is the first step in the discover-names → derive-pattern → wildcard-command
    workflow.  The returned names can be used directly with list_objects(),
    info(), label(), etc. by passing them as the ``name`` argument with
    ``match_mode="literal"`` (exact match) or deriving a ``*``-pattern and
    using ``match_mode="wildcard"``.

    CD scope covered
    ----------------
    Any destination accepted by navigate_console() works here:
      - Keyword form:      "Group", "Sequence", "Preset", "Macro", "Effect", …
      - Numeric index:     "22" (Groups), "25" (Sequences), "17" (Presets), …
      - Dot-notation:      "10.3" (LiveSetup/FixtureTypes)

    Object pool destinations (cd 1–42 that have named user objects):
      Group=22, Sequence=25, Preset=17, Macro=13, Effect=24, Gel=16, World=18,
      Filter=19, Form=23, Timer=26, Layout=38, Timecode=35, Agenda=34,
      UserProfile=39, Remote=36.

    System-config branches (cd 1=Showfile, cd 2=TimeConfig, cd 3=Settings,
    cd 4=DMX_Protocols, …) hold property nodes, not named user objects — they
    return empty names and are not useful for wildcard matching.

    After this call the console is left at root (cd /).

    Args:
        destination: Object pool to inspect.  Any format accepted by
            navigate_console: keyword ("Group"), numeric index ("22"),
            or dot path ("10.3").

    Returns:
        str: JSON with destination, entries (id + name), names_only list,
             and a wildcard_tip suggesting how to build a pattern.

    Example workflow::

        discover_object_names("Group")
        # → names: ["Mac700 Front", "Mac700 Back", "Wash", "ALL LASERS"]

        # Derive prefix pattern and use with list_objects:
        # list_objects("group", name="Mac700*", match_mode="wildcard")
        # → "list group Mac700*"
    """
    client = await _sc.get_client()

    # Navigate to the destination
    nav = await navigate(client, destination)

    # List all objects there
    lst = await list_destination(client)

    # Collect non-empty names
    named_entries = [
        {"object_id": e.object_id, "name": e.name}
        for e in lst.parsed_list.entries
        if e.name
    ]
    names_only = [e["name"] for e in named_entries]

    # Build a wildcard tip based on common prefix (if any)
    tip = None
    if names_only:
        first = names_only[0]
        prefix = first.split()[0] if " " in first else first
        if len(names_only) > 1 and all(n.startswith(prefix) for n in names_only):
            tip = f'Common prefix detected — try: name="{prefix}*", match_mode="wildcard"'
        else:
            tip = 'No common prefix — use exact names with match_mode="literal" or derive your own pattern'

    # Return to root
    await navigate(client, "/")

    return json.dumps(
        {
            "destination": destination,
            "navigate_command": nav.command_sent,
            "entry_count": len(lst.parsed_list.entries),
            "named_count": len(named_entries),
            "entries": named_entries,
            "names_only": names_only,
            "wildcard_tip": tip,
        },
        indent=2,
    )
