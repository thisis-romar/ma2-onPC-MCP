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

from src.telnet_client import GMA2TelnetClient
from src.tools import set_gma2_client
from src.commands import (
    select_fixture,
    store_group,
    label_group,
    go_sequence,
    pause_sequence,
    goto_cue,
    fixture_at,
    group_at,
    channel_at,
    attribute_at,
    at,
    at_full,
    at_zero,
    call,
    store_cue as build_store_cue,
    label as build_label,
    info as build_info,
    clear as build_clear,
    clear_all as build_clear_all,
    clear_selection as build_clear_selection,
    clear_active as build_clear_active,
)
from src.navigation import navigate, get_current_location, list_destination, scan_indexes, set_property
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
    You can use the following tools to operate grandMA2:

    1. create_fixture_group - Create a fixture group
       Example: Save fixtures 1 to 10 as group 1 with name "Front Wash"

    2. execute_sequence - Execute sequence operations
       Example: Execute sequence 1, pause sequence 2, jump to cue 5 of sequence 1

    3. send_raw_command - Send raw MA commands
       Example: Send "blackout" or "go+ executor 1.1"

    4. navigate_console - Navigate the console's object tree (ChangeDest/cd)
       Example: cd to "Group.1", go up with "..", return to root with "/"
       Returns raw telnet response + parsed prompt state for exploration.

    5. get_console_location - Query the current console destination
       Returns raw telnet response + parsed prompt state without navigating.

    6. list_console_destination - List objects at the current destination
       After cd-ing into a location, run list to enumerate children.
       Returns parsed entries with object-type, object-id, and element names.

    7. set_node_property - Set a property on a node in the object tree
       Uses dot-separated index paths from the scan tree output.
       Example: path="3.1", property_name="Telnet", value="Login Disabled"

    8. set_intensity - Set dimmer level on fixtures, groups, or channels
       Example: Set fixture 1 to 50%, set group 3 to full

    9. apply_preset - Apply a stored preset (color, position, gobo, etc.)
       Example: Apply color preset 3 to group 2

    10. store_current_cue - Store programmer state into a cue (DESTRUCTIVE)
        Example: Store cue 5 named "Opening Look"

    11. get_object_info - Query info on any console object
        Example: Get info on group 3, sequence 1

    12. clear_programmer - Clear programmer state (all, selection, active)
        Example: Clear all, or just deselect fixtures
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
    if _client is not None and _connected:
        if _client._writer is None:
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
                f"Server is in read-only mode (GMA_SAFETY_LEVEL=read-only). "
                f"Only SAFE_READ commands (list, info, cd) are allowed."
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

    Preset types: "dimmer" (1), "color" (2), "position" (3), "gobo" (4),
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
        "dimmer": "1", "color": "2", "position": "3", "gobo": "4",
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
