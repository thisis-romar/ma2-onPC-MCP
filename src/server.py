"""
MCP Server Module

This module is responsible for creating and running the MCP server,
integrating all tools together. It uses FastMCP to simplify the MCP server setup.

Usage:
    uv run python -m src.server
"""

import functools
import json
import logging
import os
import re

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from src.commands import (
    add_user_var as build_add_user_var,
)
from src.commands import (
    add_var as build_add_var,
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
    assign_fade as build_assign_fade,
)
from src.commands import (
    assign_function as build_assign_function,
)
from src.commands import (
    assign_to_layout as build_assign_to_layout,
)
from src.commands import (
    attribute_at,
    call,
    channel_at,
    executor_at as build_executor_at,
    fixture_at,
    flash_executor as build_flash_executor,
    go_macro,
    go_sequence,
    goto_cue,
    goto_timecode as build_goto_timecode,
    group_at,
    label_group,
    off_executor as build_off_executor,
    on_executor as build_on_executor,
    pause_sequence,
    select_fixture,
    solo_executor as build_solo_executor,
    store_group,
    update_cue as build_update_cue,
)
from src.commands import (
    export_object as build_export_object,
)
from src.commands import (
    import_object as build_import_object,
)
from src.commands import (
    import_fixture_type_cmd as build_import_fixture_type_cmd,
)
from src.commands import (
    import_layer_cmd as build_import_layer_cmd,
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
    copy as build_copy,
)
from src.commands import (
    cut as build_cut,
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
    # edit_object
    edit as build_edit,
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
    info as build_info,
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
    list_group as build_list_group,
)
from src.commands import (
    list_messages as build_list_messages,
)
from src.commands import (
    # query_object_list
    list_objects as build_list_objects,
)
from src.commands import (
    list_preset as build_list_preset,
)
from src.commands import (
    move as build_move,
)
from src.commands import (
    park as build_park,
)
from src.commands import (
    paste as build_paste,
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
    remove_preset_type as build_remove_preset_type,
)
from src.commands import (
    remove_selection as build_remove_selection,
)
from src.commands import (
    add_to_selection as build_add_to_selection,
    at_relative as build_at_relative,
    clear_selection as build_clear_selection2,
    page_next as build_page_next,
    page_previous as build_page_previous,
    remove_from_selection as build_remove_from_selection,
)
from src.commands import (
    set_user_var as build_set_user_var,
)
from src.commands import (
    # manage_variable
    set_var as build_set_var,
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
    unpark as build_unpark,
)
from src.commands import (
    blackout as build_blackout,
    delete_fixture as build_delete_fixture,
    get_user_var as build_get_user_var,
    highlight as build_highlight,
    list_effect_library as build_list_effect_library,
    list_library as build_list_library,
    list_macro_library as build_list_macro_library,
    list_oops as build_list_oops,
    list_shows as build_list_shows,
    list_user_var as build_list_user_var,
    list_var as build_list_var,
    load_show as build_load_show,
    new_show as build_new_show,
    release_executor as build_release_executor,
)
from src.navigation import get_current_location, list_destination, navigate, scan_indexes, set_property
from src.telnet_client import GMA2TelnetClient
from src.tools import set_gma2_client
from src.vocab import CD_INVALID_INDEXES, CD_NUMERIC_INDEX, RiskTier, build_v39_spec, classify_token

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Get configuration from environment variables
_GMA_HOST = os.getenv("GMA_HOST", "127.0.0.1")
_GMA_PORT = int(os.getenv("GMA_PORT", "30000"))
_GMA_USER = os.getenv("GMA_USER", "administrator")
_GMA_PASSWORD = os.getenv("GMA_PASSWORD", "admin")
_GMA_SAFETY_LEVEL = os.getenv("GMA_SAFETY_LEVEL", "standard").lower()

# Build vocab spec once for token classification / safety gating
_vocab_spec = build_v39_spec()

# Create MCP server
mcp = FastMCP(
    name="grandMA2-MCP",
    instructions="""
    This is an MCP server for controlling grandMA2 lighting console.
    You can use the following 73 tools to operate grandMA2:

    --- Navigation & Inspection ---
    1. navigate_console - Navigate the console object tree (cd)
    2. get_console_location - Query current console destination
    3. list_console_destination - List objects at current destination
    4. scan_console_indexes - Batch scan numeric indexes at any tree level

    --- Lighting Control ---
    5. set_intensity - Set dimmer level on fixtures, groups, or channels
    6. set_attribute - Set attribute values (Pan, Tilt, Zoom, etc.)
    7. apply_preset - Apply a stored preset (color, position, gobo, etc.)
    8. execute_sequence - Legacy sequence playback (go/pause/goto)
    9. playback_action - Full playback control (go, go_back, goto, fast_forward, etc.)
    10. clear_programmer - Clear programmer state (all, selection, active)
    11. park_fixture - Park a fixture/DMX at current or specified output
    12. unpark_fixture - Release a parked fixture/DMX

    --- Programming ---
    13. create_fixture_group - Select fixtures and save as a named group
    14. store_current_cue - Store programmer into a cue (DESTRUCTIVE)
    15. store_new_preset - Store programmer as a preset (DESTRUCTIVE)
    16. store_object - Store generic objects: macros, effects, worlds (DESTRUCTIVE)
    17. set_node_property - Set a property on a node via tree path
    18. copy_or_move_object - Copy or move objects between slots
    19. delete_object - Delete any object (DESTRUCTIVE)
    20. run_macro - Execute a stored macro by ID

    --- Assignment & Layout ---
    21. assign_object - Assign objects, functions, fades, or layout positions (DESTRUCTIVE)
    22. label_or_appearance - Label or style objects (DESTRUCTIVE)
    23. edit_object - Edit, cut, or paste objects (cut/paste DESTRUCTIVE)
    24. remove_content - Remove content from objects (DESTRUCTIVE)

    --- Info & Queries ---
    25. get_object_info - Query info on any object
    26. query_object_list - List cues, groups, presets, attributes, messages
    27. manage_variable - Set or add to console variables (global/user)
    28. send_raw_command - Send any MA command directly (safety-gated)

    --- Codebase & Documentation Search ---
    29. search_codebase - Semantic/keyword search across this server's own source code,
        tests, docs, AND the official grandMA2 help documentation (when indexed).
        Use this to discover command builder signatures, safety rules,
        implementation details, or grandMA2 console operation instructions.

    SAFETY: DESTRUCTIVE tools require confirm_destructive=True.
    """,
)

# Global telnet client instance
_client: GMA2TelnetClient | None = None
_connected: bool = False


async def get_client() -> GMA2TelnetClient:
    """
    Get or create a telnet client instance (async).

    On first call, establishes connection and login. Subsequent calls return
    the already connected client. If the connection has dropped, reconnects
    automatically.
    """
    global _client, _connected

    # Check if existing connection is still healthy
    if _client is not None and _connected and _client._writer is None:
        logger.warning("Connection lost, reconnecting...")
        _connected = False

    if _client is None or not _connected:
        _client = GMA2TelnetClient(
            host=_GMA_HOST,
            port=_GMA_PORT,
            user=_GMA_USER,
            password=_GMA_PASSWORD,
        )
        try:
            await _client.connect()
            await _client.login()
            _connected = True
            set_gma2_client(_client)
            logger.info(f"Connected to grandMA2: {_GMA_HOST}:{_GMA_PORT}")
        except Exception:
            _connected = False
            raise

    return _client


def _handle_errors(func):
    """Decorator that catches exceptions in MCP tools and returns JSON errors."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> str:
        try:
            return await func(*args, **kwargs)
        except ConnectionError as e:
            logger.error("Connection error in %s: %s", func.__name__, e)
            return json.dumps({"error": f"Connection failed: {e}", "blocked": True}, indent=2)
        except RuntimeError as e:
            logger.error("Runtime error in %s: %s", func.__name__, e)
            return json.dumps({"error": f"Runtime error: {e}", "blocked": True}, indent=2)
        except Exception as e:
            logger.error("Unexpected error in %s: %s", func.__name__, e, exc_info=True)
            return json.dumps({"error": f"Unexpected error: {e}", "blocked": True}, indent=2)

    return wrapper


# ============================================================
# Private helpers — object existence probing
# ============================================================

# Regex to parse sequence ID from "list executor PAGE.ID" response.
# Matches "Sequence=Seq 278" and "Sequence=Seq 278(2)".
_SEQ_FOR_EXECUTOR_RE = re.compile(r"Sequence=Seq\s+(\d+)", re.IGNORECASE)


async def _validate_object_exists(
    client: GMA2TelnetClient,
    object_type: str,
    object_id: int | str,
) -> tuple[bool, str]:
    """
    Probe whether an object exists using 'list {object_type} {object_id}'.

    MA2 returns "NO OBJECTS FOUND FOR LIST" when the object does not exist.
    Any other response (including data rows) is treated as existence confirmed.

    Not decorated with @_handle_errors — exceptions propagate to the
    enclosing tool's decorator.

    Args:
        client: Connected GMA2TelnetClient (already obtained by the caller).
        object_type: MA2 keyword, e.g. "fixture", "cue", "group".
        object_id: Integer ID or compound string, e.g. "99 sequence 278".

    Returns:
        (exists: bool, raw_response: str)
    """
    probe_cmd = f"list {object_type} {object_id}"
    raw = await client.send_command_with_response(probe_cmd)
    exists = "NO OBJECTS FOUND" not in raw.upper()
    logger.debug("_validate_object_exists %r → exists=%s", probe_cmd, exists)
    return exists, raw


async def _get_sequence_for_executor(
    client: GMA2TelnetClient,
    executor_id: int,
    page: int = 1,
) -> tuple[int | None, str]:
    """
    Resolve the sequence linked to an executor via 'list executor PAGE.ID'.

    Parses "Sequence=Seq N" from the response. Returns (None, raw) if the
    executor has no sequence assigned or is not found.

    Args:
        client: Connected GMA2TelnetClient (already obtained by the caller).
        executor_id: Executor number within the page.
        page: Executor page number (default 1).

    Returns:
        (sequence_id: int | None, raw_response: str)
    """
    probe_cmd = f"list executor {page}.{executor_id}"
    raw = await client.send_command_with_response(probe_cmd)
    m = _SEQ_FOR_EXECUTOR_RE.search(raw)
    if m:
        seq_id = int(m.group(1))
        logger.debug(
            "_get_sequence_for_executor: executor %d.%d → sequence %d",
            page, executor_id, seq_id,
        )
        return seq_id, raw
    logger.debug(
        "_get_sequence_for_executor: executor %d.%d — no sequence in response",
        page, executor_id,
    )
    return None, raw


# ============================================================
# MCP Tools Definition
# ============================================================


@mcp.tool()
@_handle_errors
async def create_fixture_group(
    start_fixture: int,
    end_fixture: int,
    group_id: int,
    group_name: str | None = None,
) -> str:
    """
    Create a group containing a specified range of fixtures.

    This tool selects the specified range of fixtures and saves them as a group.
    Optionally, a name can be assigned to the group.

    Args:
        start_fixture: Starting fixture number
        end_fixture: Ending fixture number
        group_id: Group number to save
        group_name: (Optional) Group name, e.g., "Front Wash"

    Returns:
        str: Operation result message

    Examples:
        - Save fixtures 1 to 10 as group 1
        - Save fixtures 1 to 10 as group 1 with name "Front Wash"
    """
    client = await get_client()

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


@mcp.tool()
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


@mcp.tool()
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
              (uses dot notation: cd Group.1)
            - A quoted name (e.g., '"MySequence"') to navigate by name
        object_id: Object ID, produces dot notation cd [type].[id]
            (e.g., destination="Group", object_id=1 → cd Group.1)

    Returns:
        str: JSON with command_sent, raw_response, parsed prompt details,
             and success indicator.

    Examples:
        - Navigate to root: destination="/"
        - Go up one level: destination=".."
        - Navigate to Group 1: destination="Group", object_id=1 → cd Group.1
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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
    client = await get_client()
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


@mcp.tool()
@_handle_errors
async def set_node_property(
    path: str,
    property_name: str,
    value: str,
    verify: bool = True,
) -> str:
    """
    Set a property on a node in the grandMA2 object tree.

    Uses the scan tree path notation (dot-separated indexes) to navigate
    to a node and set an inline property using Assign [index]/property=value.

    The path uses the same index-based notation as the scan tree output.
    Split the path into parent segments and target index:
    - "3.1" → cd 3 (Settings), then Assign 1/property=value (on Global)
    - "4.1" → cd 4 (DMX_Protocols), then Assign 1/property=value (on Art-Net)
    - "3" → at root, Assign 3/property=value (on Settings itself)

    After setting, navigates back to root (cd /).
    If verify=True (default), re-lists and confirms the property changed.

    SAFETY: This modifies live console state. Double-check property names
    and values before calling. Use list_console_destination to inspect
    current values first.

    Args:
        path: Dot-separated index path (e.g. "3.1" for Settings/Global)
        property_name: Property to set (e.g. "Telnet", "OutActive")
        value: New value (e.g. "Login Enabled", "On")
        verify: Re-list after setting to confirm the change (default True)

    Returns:
        str: JSON with commands_sent, success, verified_value, and any errors.

    Examples:
        - Set telnet to disabled: path="3.1", property_name="Telnet", value="Login Disabled"
        - Enable Art-Net output: path="4.1", property_name="OutActive", value="On"
    """
    client = await get_client()
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

    client = await get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
    }, indent=2)


@mcp.tool()
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
    client = await get_client()

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
    client = await get_client()

    # Build store cue command
    store_cmd = build_store_cue(
        cue_id=cue_number,
        merge=merge,
        overwrite=overwrite,
    )
    if sequence_id is not None:
        store_cmd += f" sequence {sequence_id}"

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

    client = await get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
    }, indent=2)


@mcp.tool()
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

    client = await get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
    }, indent=2)


@mcp.tool()
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
    client = await get_client()

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


@mcp.tool()
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
    client = await get_client()

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

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "exists": exists_flag,
    }, indent=2)


@mcp.tool()
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
    client = await get_client()

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

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "exists": exists_flag,
    }, indent=2)


@mcp.tool()
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
    client = await get_client()
    cmd = go_macro(macro_id)
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
    }, indent=2)


@mcp.tool()
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

    client = await get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "blocked": False,
    }, indent=2)


@mcp.tool()
@_handle_errors
async def copy_or_move_object(
    action: str,
    object_type: str,
    source_id: int,
    target_id: int,
    source_end: int | None = None,
    overwrite: bool = False,
    merge: bool = False,
) -> str:
    """
    Copy or move an object to a new location.

    SAFETY: Both operations modify show data. Copy duplicates the object,
    move relocates it (deleting the original).

    Args:
        action: "copy" or "move"
        object_type: Object type (e.g. "group", "cue", "preset", "macro")
        source_id: Source object ID
        target_id: Destination object ID
        source_end: Optional end ID for range copy/move
        overwrite: Overwrite target if it exists (default False)
        merge: Merge into target if it exists (default False)

    Returns:
        str: JSON with command_sent and raw_response.

    Examples:
        - Copy group 1 to 5: action="copy", object_type="group", source_id=1, target_id=5
        - Move macro 3 to 10: action="move", object_type="macro", source_id=3, target_id=10
        - Copy cue range: action="copy", object_type="cue", source_id=1, target_id=20, source_end=10
    """
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

    client = await get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
    }, indent=2)


@mcp.tool()
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
    client = await get_client()
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
# ============================================================


@mcp.tool()
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

    client = await get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
    }, indent=2)


def _parse_listvar(raw: str, filter_prefix: str | None = None) -> dict[str, str]:
    """Parse ListVar telnet output into a {$NAME: value} dict.

    ListVar lines have the format:  $Global : $VARNAME = VALUE
    """
    variables: dict[str, str] = {}
    for line in raw.splitlines():
        line = line.strip()
        if "=" not in line or line.startswith("["):
            continue
        # Strip scope prefix: "$Global : $VARNAME = VALUE" → "$VARNAME = VALUE"
        if " : " in line:
            _, _, line = line.partition(" : ")
            line = line.strip()
        name, _, value = line.partition("=")
        name = name.strip().lstrip("$")
        value = value.strip()
        if not name:
            continue
        if filter_prefix is None or name.upper().startswith(filter_prefix.upper()):
            variables[f"${name}"] = value
    return variables


@mcp.tool()
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
    client = await get_client()
    raw = await client.send_command_with_response("ListVar")

    variables = _parse_listvar(raw, filter_prefix=filter_prefix)
    return json.dumps({
        "variables": variables,
        "variable_count": len(variables),
        "raw_response": raw,
    }, indent=2)


@mcp.tool()
@_handle_errors
async def playback_action(
    action: str,
    object_type: str | None = None,
    object_id: int | None = None,
    cue_id: int | float | None = None,
    end: int | None = None,
    cue_mode: str | None = None,
    executor: int | None = None,
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
            "def_go" — go on the selected executor (go+)
            "def_pause" — pause the selected executor
        object_type: Object type for go/go_back (e.g. "executor", "sequence")
        object_id: Object ID for go/go_back
        cue_id: Target cue number (required for "goto")
        end: End ID for range (go/go_back)
        cue_mode: Cue execution mode: "normal", "assert", "xassert", "release"
        executor: Executor ID for goto/fast_forward/fast_back
        sequence: Sequence ID for goto/fast_forward/fast_back

    Returns:
        str: JSON with command_sent and raw_response.

    Examples:
        - Go on executor 1: action="go", object_type="executor", object_id=1
        - Go back: action="go_back"
        - Goto cue 5: action="goto", cue_id=5
        - Goto cue 3 on sequence 2: action="goto", cue_id=3, sequence=2
        - Fast forward: action="fast_forward"
        - Go on selected executor: action="def_go"
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
        client = await get_client()
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
    elif action == "def_go":
        cmd = build_def_go_forward()
    elif action == "def_pause":
        cmd = build_def_go_pause()
    else:
        return json.dumps({
            "error": (
                f"Unknown action: {action}. Use 'go', 'go_back', 'goto', "
                f"'fast_forward', 'fast_back', 'def_go', or 'def_pause'."
            ),
            "blocked": True,
        }, indent=2)

    client = await get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
    }, indent=2)


@mcp.tool()
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
        client = await get_client()
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

    client = await get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
    }, indent=2)


@mcp.tool()
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
        red: Red component (0-255) for appearance
        green: Green component (0-255) for appearance
        blue: Blue component (0-255) for appearance
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

    client = await get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "blocked": False,
    }, indent=2)


@mcp.tool()
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

    client = await get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "blocked": False,
    }, indent=2)


@mcp.tool()
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

    client = await get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "blocked": False,
    }, indent=2)


@mcp.tool()
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

    client = await get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "blocked": False,
    }, indent=2)


@mcp.tool()
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

    client = await get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "blocked": False,
    }, indent=2)


# ============================================================
# Codebase Search (RAG)
# ============================================================


@mcp.tool()
@_handle_errors
async def search_codebase(
    query: str,
    top_k: int = 8,
    kind: str | None = None,
) -> str:
    """Search this server's source code and grandMA2 documentation using the RAG index.

    Use this to look up command builders, safety rules, module internals,
    or any grandMA2 console operation detail. Works without any API key
    (text search fallback). If a RAG index has been built with embeddings,
    results are ranked by semantic similarity.

    Args:
        query:  Natural language or keyword query (e.g. "navigate console",
                "store preset", "how to patch fixtures")
        top_k:  Number of results to return (default 8, max 20)
        kind:   Optional filter — one of: "source", "test", "doc", "config"

    Returns:
        JSON array of matching code/doc chunks with path, line range, score, and text.
        Returns an error JSON if the RAG index has not been built yet.

    Examples:
        - Find command builders: query="store preset", kind="source"
        - Find grandMA2 docs: query="how to patch fixtures", kind="doc"
        - Search everything: query="effects engine"
        - Find test examples: query="navigate_console", kind="test"
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

    hits = rag_query(query, embedding_provider=provider, top_k=min(top_k, 20), db_path=db)

    if kind:
        hits = [h for h in hits if h.kind == kind]

    return json.dumps([
        {
            "path": hit.path,
            "kind": hit.kind,
            "lines": f"{hit.start_line}-{hit.end_line}",
            "score": round(hit.score, 4),
            "text": hit.text,
        }
        for hit in hits
    ], indent=2)


# ============================================================
# New Tools (Tools 30–44)
# ============================================================


@mcp.tool()
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

    client = await get_client()
    cmd = build_executor_at(executor_id, level, page=page)
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
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

    client = await get_client()
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
    client = await get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
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
    client = await get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


def _parse_preset_tree_list(raw: str) -> list[dict]:
    """Parse grandMA2 list output from the PresetType cd-tree.

    Handles rows of the form:
      ``PresetType N  LibName  ScreenName  ...``
      ``Feature N  LibName  ScreenName  ...``
      ``Attribute N  LibName  ScreenName  ...``
      ``SubAttribute N  LibName  ScreenName  ...``

    These rows have only one numeric ID (not the two required by the standard
    tabular parser), so they are skipped by parse_list_output().
    """
    import re
    _ANSI = re.compile(r"\x1b\[[0-9;]*m|\x1b\[K")
    _ROW = re.compile(
        r"^\s*(PresetType|Feature|Attribute|SubAttribute)\s+(\d+)\s+(\S+)\s+(.*?)\s*$",
        re.IGNORECASE,
    )
    entries = []
    for line in raw.splitlines():
        line = _ANSI.sub("", line).strip()
        m = _ROW.match(line)
        if m:
            obj_type, obj_id, lib_name, rest = m.group(1), m.group(2), m.group(3), m.group(4)
            # rest may contain "ScreenName  IdentifiedAs  DefaultScope  (count)"
            parts = re.split(r"\s{2,}", rest)
            entry = {
                "type": obj_type,
                "id": int(obj_id),
                "library_name": lib_name,
            }
            if parts:
                entry["screen_name"] = parts[0].strip()
            if len(parts) > 1:
                entry["identified_as"] = parts[1].strip()
            if len(parts) > 2:
                entry["extra"] = parts[2].strip()
            entries.append(entry)
    return entries


@mcp.tool()
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

    client = await get_client()

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

    client = await get_client()
    if action == "clear":
        cmd = build_clear_selection2()
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

    client = await get_client()
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

    client = await get_client()
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

    client = await get_client()
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

    client = await get_client()
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

    client = await get_client()
    response = await client.send_command_with_response(mode)
    return json.dumps({
        "command_sent": mode,
        "raw_response": response,
        "mode": mode,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
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

    client = await get_client()
    cmd = build_update_cue(cue_id, sequence_id=sequence_id, merge=merge,
                           overwrite=overwrite, cueonly=cueonly)
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "DESTRUCTIVE",
    }, indent=2)


@mcp.tool()
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

    client = await get_client()
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

    client = await get_client()
    cmd = f"+ group {group_id}" if append else f"group {group_id}"
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "group_id": group_id,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
@_handle_errors
async def control_executor(
    action: str,
    executor_id: int,
    page: int | None = None,
    speed_value: float | None = None,
    confirm_destructive: bool = False,
) -> str:
    """
    Control an executor: start, stop, flash, solo, or set speed (set_speed is DESTRUCTIVE).

    Args:
        action: "on", "off", "flash", "solo", or "set_speed"
        executor_id: Executor ID (1-999)
        page: Page number for page-qualified addressing (optional)
        speed_value: BPM value for set_speed (0.0–999.0; required for set_speed)
        confirm_destructive: Must be True when action="set_speed"

    Returns:
        str: JSON result with command sent
    """
    valid_actions = ("on", "off", "flash", "solo", "set_speed")
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
    elif action == "on":
        cmd = build_on_executor(executor_id, page=page)
        risk_tier = "SAFE_WRITE"
    elif action == "off":
        cmd = build_off_executor(executor_id, page=page)
        risk_tier = "SAFE_WRITE"
    elif action == "flash":
        cmd = build_flash_executor(executor_id, page=page)
        risk_tier = "SAFE_WRITE"
    else:  # solo
        cmd = build_solo_executor(executor_id, page=page)
        risk_tier = "SAFE_WRITE"

    client = await get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": risk_tier,
    }, indent=2)


@mcp.tool()
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

    client = await get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "SAFE_READ",
    }, indent=2)


@mcp.tool()
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

    client = await get_client()
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

    client = await get_client()
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
# New Tools (Tools 45–52) — Quick Start Guide Gap-Fill
# ============================================================


@mcp.tool()
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

    client = await get_client()
    cmd = "save" if action == "save" else f'saveas "{show_name}"'
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
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

    client = await get_client()
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
@_handle_errors
async def select_executor(
    executor_id: int,
    page: int | None = None,
) -> str:
    """
    Select an executor on the console.

    Args:
        executor_id: Executor number (1-999)
        page: Page number for page-qualified addressing (optional)

    Returns:
        str: JSON result with command sent
    """
    ref = f"{page}.{executor_id}" if page is not None else str(executor_id)
    cmd = f"select executor {ref}"
    client = await get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
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

    client = await get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
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

    client = await get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "DESTRUCTIVE",
    }, indent=2)


@mcp.tool()
@_handle_errors
async def assign_executor_property(
    property_name: str,
    confirm_destructive: bool = False,
    executor_id: int | None = None,
    sequence_id: int | None = None,
    value: str | int | float | None = None,
) -> str:
    """
    Assign a property (width, priority, rate) to an executor or sequence (DESTRUCTIVE).

    Args:
        property_name: "width", "priority", or "rate"
        confirm_destructive: Must be True to execute
        executor_id: Executor ID (required for "width" and "rate")
        sequence_id: Sequence ID (required for "priority")
        value: Property value (e.g. 2 for width, "high" for priority)

    Returns:
        str: JSON result with command sent
    """
    if not confirm_destructive:
        return json.dumps({
            "blocked": True,
            "error": "Destructive operation blocked. Set confirm_destructive=True to proceed.",
            "risk_tier": "DESTRUCTIVE",
        }, indent=2)

    valid = ("width", "priority", "rate")
    if property_name not in valid:
        return json.dumps({"error": f"property_name must be one of {valid}", "blocked": True}, indent=2)

    if property_name == "width":
        if executor_id is None or value is None:
            return json.dumps(
                {"error": "executor_id and value are required for property_name='width'", "blocked": True},
                indent=2,
            )
        cmd = f"assign executor {executor_id} /width={value}"
    elif property_name == "priority":
        if sequence_id is None or value is None:
            return json.dumps(
                {"error": "sequence_id and value are required for property_name='priority'", "blocked": True},
                indent=2,
            )
        cmd = f"assign priority {value} sequence {sequence_id}"
    else:  # rate
        if executor_id is None:
            return json.dumps(
                {"error": "executor_id is required for property_name='rate'", "blocked": True},
                indent=2,
            )
        cmd = f"assign rate executor {executor_id}"

    client = await get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "DESTRUCTIVE",
    }, indent=2)


@mcp.tool()
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

    client = await get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
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

    client = await get_client()
    response = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": response,
        "risk_tier": risk_tier,
    }, indent=2)


# ============================================================
# Tools 53–54 — Import / Export
# ============================================================

# Valid export types (live-validated on MA2 3.9.60.65)
_EXPORT_TYPES = {
    "group", "preset", "macro", "effect", "sequence", "view", "page",
    "camera", "layout", "form", "plugin", "matricks", "mask", "image",
    "executor", "timecode", "userprofile", "channel", "screen",
}

# Valid import types (screen excluded — Error #16 RESIZE FORBIDDEN on import)
_IMPORT_TYPES = {
    "group", "preset", "macro", "effect", "sequence", "view", "page",
    "camera", "layout", "form", "plugin", "matricks", "mask", "image",
    "executor", "timecode", "userprofile",
}

# Type-specific subfolders (informational — MA2 routes automatically)
# macros/ | effects/ | plugins/ | matricks/ | masks/ | importexport/ (default)
_IMPORT_EXPORT_DATA_ROOT = (
    r"C:\ProgramData\MA Lighting Technologies\grandma\gma2_V_3.9.60\importexport"
)


@mcp.tool()
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

    client = await get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "risk_tier": "DESTRUCTIVE",
        "data_path": _IMPORT_EXPORT_DATA_ROOT,
    }, indent=2)


@mcp.tool()
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

    client = await get_client()
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
        "risk_tier": "DESTRUCTIVE",
    }, indent=2)


# ============================================================
# Tools 74–76 — Fixture Type / Layer Import + XML Generation
# ============================================================


@mcp.tool()
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

    client = await get_client()
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

    client = await get_client()
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
@_handle_errors
async def generate_fixture_layer_xml(
    filename: str,
    layer_name: str,
    layer_index: int,
    fixtures: list[dict],
    showfile: str = "grandma2",
    overwrite: bool = False,
) -> str:
    """
    Generate a grandMA2 fixture layer XML file and save it to the importexport directory.

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

    Returns:
        str: JSON with file_path, filename, fixture_count, layer_index, layer_name
    """
    import os
    from datetime import datetime, timezone
    from xml.etree.ElementTree import Element, SubElement, tostring
    from xml.dom import minidom

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
        "datetime": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
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
# Tools 55–56 — Fixture & Sequence/Cue Discovery (SAFE_READ)
# ============================================================


@mcp.tool()
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
    client = await get_client()

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
    client = await get_client()
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
# Tools 57–64: Tier 1 — High-Impact Tools
# ============================================================


@mcp.tool()
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
    client = await get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
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
    client = await get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
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
    client = await get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


@mcp.tool()
@_handle_errors
async def list_shows() -> str:
    """
    List available show files on the console.

    Returns:
        str: JSON with command_sent, raw_response, risk_tier.
    """
    cmd = build_list_shows()
    client = await get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "SAFE_READ",
    }, indent=2)


@mcp.tool()
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
    client = await get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "DESTRUCTIVE",
        "blocked": False,
    }, indent=2)


@mcp.tool()
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
    client = await get_client()
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
        client = await get_client()
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

    client = await get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "SAFE_READ",
    }, indent=2)


@mcp.tool()
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

    client = await get_client()

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
@_handle_errors
async def list_undo_history() -> str:
    """
    Display the undo (Oops) history.

    Returns:
        str: JSON with command_sent, raw_response, risk_tier.
    """
    cmd = build_list_oops()
    client = await get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "SAFE_READ",
    }, indent=2)


# ============================================================
# Tools 65–69: Tier 2 — Setup & Library Tools
# ============================================================


@mcp.tool()
@_handle_errors
async def list_fixture_types() -> str:
    """
    List all fixture types in the show (from LiveSetup/FixtureTypes).

    Navigates to cd 10 (LiveSetup) -> cd 3 (FixtureTypes) -> list -> cd /

    Returns:
        str: JSON with raw_response, entries (fixture type names, manufacturers,
             DMX footprint), risk_tier.
    """
    client = await get_client()
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
@_handle_errors
async def list_layers() -> str:
    """
    List all fixture layers in the show (from LiveSetup/Layers).

    Navigates to cd 10 (LiveSetup) -> cd 4 (Layers) -> list -> cd /

    Returns:
        str: JSON with raw_response, entries (layer names, fixture ranges),
             risk_tier.
    """
    client = await get_client()
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
    client = await get_client()
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

    client = await get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "SAFE_READ",
    }, indent=2)


@mcp.tool()
@_handle_errors
async def manage_matricks(
    property_name: str,
    value: str,
) -> str:
    """
    Configure MAtricks selection pattern properties (fan, symmetry, etc.).

    Uses the set_property navigation pattern on the MAtricks object.

    Args:
        property_name: Property to set (e.g. "Wings", "Groups", "Interleave").
        value: New value for the property.

    Returns:
        str: JSON with commands_sent, success, verified_value, risk_tier.
    """
    client = await get_client()

    # Navigate to root, then cd MAtricks
    nav = await navigate(client, "/")
    nav = await navigate(client, "MAtricks")

    # Use assign property pattern
    from src.commands import assign_property as _build_assign_property
    assign_cmd = _build_assign_property("1", property_name, value)
    raw = await client.send_command_with_response(assign_cmd)

    # Return to root
    await navigate(client, "/")

    return json.dumps({
        "command_sent": assign_cmd,
        "raw_response": raw,
        "risk_tier": "SAFE_WRITE",
    }, indent=2)


# ============================================================
# Tools 70–73: Tier 3 — Fixture Patching Workflow
# ============================================================


@mcp.tool()
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
    client = await get_client()
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

    client = await get_client()
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
    client = await get_client()
    raw = await client.send_command_with_response(cmd)
    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw,
        "risk_tier": "DESTRUCTIVE",
        "blocked": False,
    }, indent=2)


@mcp.tool()
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

    client = await get_client()
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
# Wildcard Name Discovery
# ============================================================

# Object pool destinations that hold user-nameable objects.
# Keyword form (e.g. "Group") and numeric cd-index form (e.g. "22") are both accepted.
# Reference: CD_NUMERIC_INDEX in src/vocab.py — live-verified on MA2 3.9.60.65.
# NOTE: System-config branches (cd 1=Showfile, cd 2=TimeConfig, cd 3=Settings …)
#       are NOT object pools — they have property nodes, not named user objects.
_OBJECT_POOL_DESTINATIONS: dict[str, str] = {
    # keyword        numeric cd index
    "Group":         "22",
    "Sequence":      "25",
    "Preset":        "17",
    "Macro":         "13",
    "Effect":        "24",
    "Gel":           "16",
    "World":         "18",
    "Filter":        "19",
    "Form":          "23",
    "Timer":         "26",
    "Layout":        "38",
    "Timecode":      "35",
    "Agenda":        "34",
    "UserProfile":   "39",
    "Camera":        "Camera",   # no separate numeric index — cd Camera
    "MAtricks":      "MAtricks",
    "View":          "View",
    "Remote":        "36",
}


@mcp.tool()
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
    client = await get_client()

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


# ============================================================
# Server Startup
# ============================================================


def main():
    """MCP Server entry point."""
    logger.info("Starting grandMA2 MCP Server...")
    logger.info(f"Connecting to grandMA2: {_GMA_HOST}:{_GMA_PORT}")

    # Warn if using factory-default credentials
    if _GMA_USER == "administrator" and _GMA_PASSWORD == "admin":
        logger.warning(
            "Using factory-default credentials (administrator/admin). "
            "Set GMA_USER and GMA_PASSWORD environment variables for "
            "network deployments."
        )

    # Start server using stdio transport
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
