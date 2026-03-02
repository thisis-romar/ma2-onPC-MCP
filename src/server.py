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
    store_preset as build_store_preset,
)
from src.commands import (
    unpark as build_unpark,
)
from src.navigation import get_current_location, list_destination, navigate, scan_indexes, set_property
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
logger = logging.getLogger(__name__)

# Get configuration from environment variables
GMA_HOST = os.getenv("GMA_HOST", "127.0.0.1")
GMA_PORT = int(os.getenv("GMA_PORT", "30000"))
GMA_USER = os.getenv("GMA_USER", "administrator")
GMA_PASSWORD = os.getenv("GMA_PASSWORD", "admin")
GMA_SAFETY_LEVEL = os.getenv("GMA_SAFETY_LEVEL", "standard").lower()

# Build vocab spec once for token classification / safety gating
_vocab_spec = build_v39_spec()

# Create MCP server
mcp = FastMCP(
    name="grandMA2-MCP",
    instructions="""
    This is an MCP server for controlling grandMA2 lighting console.
    You can use the following 28 tools to operate grandMA2:

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
            host=GMA_HOST,
            port=GMA_PORT,
            user=GMA_USER,
            password=GMA_PASSWORD,
        )
        try:
            await _client.connect()
            await _client.login()
            _connected = True
            set_gma2_client(_client)
            logger.info(f"Connected to grandMA2: {GMA_HOST}:{GMA_PORT}")
        except Exception:
            _connected = False
            raise

    return _client


def _handle_errors(func):
    """Decorator that catches exceptions in MCP tools and returns JSON errors."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ConnectionError as e:
            logger.error("Connection error in %s: %s", func.__name__, e)
            return json.dumps({"error": f"Connection failed: {e}"}, indent=2)
        except RuntimeError as e:
            logger.error("Runtime error in %s: %s", func.__name__, e)
            return json.dumps({"error": f"Runtime error: {e}"}, indent=2)
        except Exception as e:
            logger.error("Unexpected error in %s: %s", func.__name__, e, exc_info=True)
            return json.dumps({"error": f"Unexpected error: {e}"}, indent=2)

    return wrapper


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

    # Block destructive commands unless explicitly confirmed or admin mode
    if risk == RiskTier.DESTRUCTIVE and GMA_SAFETY_LEVEL != "admin":
        if not confirm_destructive:
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
        logger.warning(
            "CONFIRMED destructive command: %r (risk=%s, canonical=%s)",
            command, risk.value, resolved.canonical,
        )

    # Block all write commands in read-only mode
    if GMA_SAFETY_LEVEL == "read-only" and risk != RiskTier.SAFE_READ:
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
) -> str:
    """
    Store the current programmer state as a cue.

    Saves whatever is currently in the programmer (selected fixtures +
    active values) into a cue in the specified sequence. This is how
    lighting looks are programmed into a show.

    SAFETY: This is a STORE operation which modifies show data.

    Args:
        cue_number: Cue number to store (required)
        sequence_id: Sequence to store into (omit to use selected executor)
        label: Optional name for the cue
        merge: Merge new values into existing cue (default False)
        overwrite: Replace existing cue completely (default False)

    Returns:
        str: JSON with commands_sent and raw_response.

    Examples:
        - Store cue 5: cue_number=5
        - Store cue 3 named "Opening Look": cue_number=3, label="Opening Look"
        - Merge into cue 1: cue_number=1, merge=True
    """
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

    Args:
        target: What to park (e.g. "fixture 1", "dmx 101", "fixture 1 thru 10")
        value: Optional output value to park at (0-255 for DMX, 0-100 for %)

    Returns:
        str: JSON with command_sent and raw_response.

    Examples:
        - Park fixture 1 at current output: target="fixture 1"
        - Park DMX 101 at 128: target="dmx 101", value=128
        - Park fixture range: target="fixture 1 thru 10"
    """
    client = await get_client()
    cmd = build_park(target, at=value)
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
    }, indent=2)


@mcp.tool()
@_handle_errors
async def unpark_fixture(
    target: str,
) -> str:
    """
    Unpark a previously parked fixture or DMX address.

    Releases the park lock so the output resumes following cues and
    programmer values normally.

    Args:
        target: What to unpark (e.g. "fixture 1", "dmx 101", "fixture 1 thru 10")

    Returns:
        str: JSON with command_sent and raw_response.

    Examples:
        - Unpark fixture 1: target="fixture 1"
        - Unpark DMX 101: target="dmx 101"
    """
    client = await get_client()
    cmd = build_unpark(target)
    raw_response = await client.send_command_with_response(cmd)

    return json.dumps({
        "command_sent": cmd,
        "raw_response": raw_response,
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
) -> str:
    """
    Store the current programmer values as a preset.

    Saves the active fixture values (from the programmer) into a preset
    slot for later recall with apply_preset.

    Preset types: "dimmer" (1), "position" (2), "gobo" (3), "color" (4),
    "beam" (5), "focus" (6), "control" (7), "shapers" (8), "video" (9)

    SAFETY: This is a STORE operation which modifies show data.

    Args:
        preset_type: Preset type name (e.g. "color", "position", "gobo")
        preset_id: Preset number within that type
        merge: Merge into existing preset (default False)
        overwrite: Replace existing preset (default False)

    Returns:
        str: JSON with command_sent and raw_response.

    Examples:
        - Store color preset 5: preset_type="color", preset_id=5
        - Merge into position preset 3: preset_type="position", preset_id=3, merge=True
    """
    client = await get_client()
    cmd = build_store_preset(
        preset_type, preset_id,
        merge=merge, overwrite=overwrite,
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
            }, indent=2)
        cmd = build_goto(
            cue_id, executor=executor, sequence=sequence,
            cue_mode=cue_mode,
        )
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
    Set or add to console variables (global or user-scoped).

    Variables are named values stored on the console that can be used in
    macros and command line expressions.

    Args:
        action: "set" to assign a value, "add" to increment by a value
        scope: "global" for system variables, "user" for user-scoped variables
        var_name: Variable name (e.g. "myvar", "speed", "counter")
        value: Value to set or add. Required for "add", optional for "set"
            (if omitted with set + input_dialog, shows input dialog)
        input_dialog: If True with action="set", shows an input dialog
            on the console for the user to enter a value

    Returns:
        str: JSON with command_sent and raw_response.

    Examples:
        - Set global var: action="set", scope="global", var_name="myvar", value=42
        - Set user var: action="set", scope="user", var_name="speed", value=100
        - Add to global: action="add", scope="global", var_name="counter", value=1
        - Show input dialog: action="set", scope="user", var_name="name", input_dialog=True
    """
    action = action.lower()
    scope = scope.lower()

    if action == "set":
        if scope == "global":
            cmd = build_set_var(var_name, value, input_dialog=input_dialog)
        elif scope == "user":
            cmd = build_set_user_var(var_name, value, input_dialog=input_dialog)
        else:
            return json.dumps({
                "error": f"Unknown scope: {scope}. Use 'global' or 'user'.",
            }, indent=2)
    elif action == "add":
        if value is None:
            return json.dumps({
                "error": "add action requires a value.",
            }, indent=2)
        if scope == "global":
            cmd = build_add_var(var_name, value)
        elif scope == "user":
            cmd = build_add_user_var(var_name, value)
        else:
            return json.dumps({
                "error": f"Unknown scope: {scope}. Use 'global' or 'user'.",
            }, indent=2)
    else:
        return json.dumps({
            "error": f"Unknown action: {action}. Use 'set' or 'add'.",
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
            }, indent=2)
        cmd = build_assign_function(function, target_type, target_id)
    elif mode == "fade":
        if fade_time is None or cue_id is None:
            return json.dumps({
                "error": "fade mode requires fade_time and cue_id.",
            }, indent=2)
        cmd = build_assign_fade(fade_time, cue_id, sequence_id=sequence_id)
    elif mode == "layout":
        if source_type is None or source_id is None or layout_id is None:
            return json.dumps({
                "error": "layout mode requires source_type, source_id, and layout_id.",
            }, indent=2)
        cmd = build_assign_to_layout(
            source_type, source_id, layout_id, x=x, y=y,
        )
    elif mode == "empty":
        if target_type is None or target_id is None:
            return json.dumps({
                "error": "empty mode requires target_type and target_id.",
            }, indent=2)
        cmd = build_assign_function("empty", target_type, target_id)
    elif mode == "temp_fader":
        if target_type is None or target_id is None:
            return json.dumps({
                "error": "temp_fader mode requires target_type and target_id.",
            }, indent=2)
        cmd = build_assign_function("tempfader", target_type, target_id)
    else:
        return json.dumps({
            "error": (
                f"Unknown mode: {mode}. Use 'assign', 'function', 'fade', "
                f"'layout', 'empty', or 'temp_fader'."
            ),
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
            }, indent=2)
        cmd = build_cut(object_type, object_id, end=end)
    elif action == "paste":
        cmd = build_paste(object_type, target_id)
    else:
        return json.dumps({
            "error": f"Unknown action: {action}. Use 'edit', 'cut', or 'paste'.",
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
            }, indent=2)
        cmd = build_remove_fixture(object_id, end=end, if_filter=if_filter)
    elif otype == "effect":
        if object_id is None:
            return json.dumps({
                "error": "effect removal requires object_id.",
            }, indent=2)
        cmd = build_remove_effect(object_id, end=end)
    elif otype == "presettype":
        if object_id is None:
            return json.dumps({
                "error": "presettype removal requires object_id (the preset type name or number).",
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
# Server Startup
# ============================================================


def main():
    """MCP Server entry point."""
    logger.info("Starting grandMA2 MCP Server...")
    logger.info(f"Connecting to grandMA2: {GMA_HOST}:{GMA_PORT}")

    # Start server using stdio transport
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
