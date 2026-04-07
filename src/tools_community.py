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
from src.server_core import (
    _get_sequence_for_executor,
    _GMA_SAFETY_LEVEL,
    _handle_errors,
    _parse_listvar,
    _read_selected_exec,
    _validate_object_exists,
    _vocab_spec,
    get_client,
    mcp,
)
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
    client = await get_client()

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

    client = await get_client()
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
    client = await get_client()
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
    client = await get_client()
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
    client = await get_client()
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
