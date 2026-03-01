"""
Live Integration Tests — All 28 MCP Tools

Tests every MCP tool against a real grandMA2 console via telnet.
Organized into 8 layers by risk and dependency:

  Layer 0 — SAFE_READ: Pure queries, no side effects
  Layer 1 — Navigation & State: Reversible navigation and variables
  Layer 2 — Selection & Group Creation: Create test fixtures
  Layer 3 — Light Control: Set intensity, attributes, park/unpark
  Layer 4 — Programming: Store cues, presets, objects (DESTRUCTIVE)
  Layer 5 — Copy/Move/Assign: Operate on created objects (DESTRUCTIVE)
  Layer 6 — Playback: Execute sequences and playback actions
  Layer 7 — Cleanup: Delete test objects (DESTRUCTIVE)

Usage:
    # Safe tests only (Layer 0-3, 6):
    uv run pytest tests/test_live_integration.py -m "live and not destructive" -v -s

    # All layers including destructive:
    uv run pytest tests/test_live_integration.py -m live -v -s --destructive

    # Single layer:
    uv run pytest tests/test_live_integration.py -k "Layer0" -v -s
"""

import json

import pytest
import pytest_asyncio

# All tests in this module share a single event loop so the telnet
# client (a module-level singleton) stays on the same loop.
pytestmark = pytest.mark.asyncio(loop_scope="module")

# All tool functions are imported directly from the server module
from src.server import (
    apply_preset,
    assign_object,
    clear_programmer,
    copy_or_move_object,
    create_fixture_group,
    delete_object,
    edit_object,
    execute_sequence,
    get_client,
    get_console_location,
    get_object_info,
    label_or_appearance,
    list_console_destination,
    manage_variable,
    navigate_console,
    park_fixture,
    playback_action,
    query_object_list,
    remove_content,
    scan_console_indexes,
    send_raw_command,
    set_attribute,
    set_intensity,
    store_current_cue,
    store_new_preset,
    store_object,
    unpark_fixture,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def validate_response(
    result: str,
    expected_keys: list[str] | None = None,
    command_contains: str | None = None,
) -> dict:
    """Parse and validate a JSON tool response.

    Args:
        result: Raw string returned by the MCP tool.
        expected_keys: Keys that must be present in the parsed dict.
        command_contains: Substring that ``command_sent`` must contain.

    Returns:
        The parsed dict for further assertions.
    """
    data = json.loads(result)
    print(f"  Response: {json.dumps(data, indent=2)}")

    if expected_keys:
        for key in expected_keys:
            assert key in data, f"Missing key '{key}' in response: {list(data.keys())}"

    # Validate raw_response is not empty when present
    if "raw_response" in data and data.get("blocked") is not True:
        assert data["raw_response"] is not None, "raw_response is None"

    # Validate command_sent contains expected substring
    if command_contains and "command_sent" in data:
        cmd = data["command_sent"]
        assert cmd is not None, "command_sent is None"
        assert command_contains.lower() in cmd.lower(), (
            f"Expected '{command_contains}' in command_sent '{cmd}'"
        )

    return data


def validate_response_list(
    result: str,
    expected_keys: list[str] | None = None,
    commands_contain: str | None = None,
) -> dict:
    """Like validate_response but checks ``commands_sent`` (plural)."""
    data = json.loads(result)
    print(f"  Response: {json.dumps(data, indent=2)}")

    if expected_keys:
        for key in expected_keys:
            assert key in data, f"Missing key '{key}' in response: {list(data.keys())}"

    if "raw_response" in data:
        assert data["raw_response"] is not None, "raw_response is None"

    if commands_contain and "commands_sent" in data:
        cmds = data["commands_sent"]
        assert any(commands_contain.lower() in c.lower() for c in cmds), (
            f"Expected '{commands_contain}' in commands_sent {cmds}"
        )

    return data


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def live_client():
    """Establish a real telnet connection for the entire test module."""
    client = await get_client()
    assert client is not None, "Failed to connect to grandMA2 console"
    assert client._writer is not None, "Telnet writer is None — not connected"
    yield client


# ---------------------------------------------------------------------------
# Layer 0 — SAFE_READ (Foundation, No Risk)
# ---------------------------------------------------------------------------


@pytest.mark.live
class TestLayer0SafeRead:
    """Pure query tests. No preconditions, no side effects."""

    async def test_get_console_location(self, live_client):
        """0.1 — Query current console location."""
        result = await get_console_location()
        data = validate_response(result, ["success", "parsed_prompt"])
        # The first empty-string probe may return an empty response if the
        # console prompt was already consumed by login.  Accept that as valid.
        assert "parsed_prompt" in data

    async def test_list_console_destination(self, live_client):
        """0.2 — List objects at current destination."""
        result = await list_console_destination()
        data = validate_response(result, ["entries", "entry_count"])
        assert data["entry_count"] >= 0

    async def test_scan_console_indexes(self, live_client):
        """0.3 — Scan numeric indexes at root."""
        result = await scan_console_indexes(reset_to="/", max_index=5, stop_after_failures=3)
        data = validate_response(result, ["scanned_count", "results"])
        assert data["scanned_count"] > 0
        for r in data["results"]:
            assert "index" in r
            assert "entries" in r

    async def test_get_object_info_fixture(self, live_client):
        """0.4 — Get info on fixture 1."""
        result = await get_object_info("fixture", 1)
        data = validate_response(result, ["command_sent", "raw_response"])
        assert data["command_sent"] == "info fixture 1"

    async def test_query_list_cue(self, live_client):
        """0.5 — List cues."""
        result = await query_object_list("cue")
        data = validate_response(result, ["command_sent", "raw_response"])
        assert "cue" in data["command_sent"].lower()

    async def test_query_list_group(self, live_client):
        """0.6 — List groups."""
        result = await query_object_list("group")
        data = validate_response(result, ["command_sent", "raw_response"])
        assert "group" in data["command_sent"].lower()

    async def test_query_list_preset(self, live_client):
        """0.7 — List color presets."""
        result = await query_object_list("preset", preset_type="color")
        data = validate_response(result, ["command_sent", "raw_response"])
        assert "preset" in data["command_sent"].lower()

    async def test_query_list_attribute(self, live_client):
        """0.8 — List attributes."""
        result = await query_object_list("attribute")
        data = validate_response(result, ["command_sent", "raw_response"])
        assert "attribute" in data["command_sent"].lower()

    async def test_query_list_messages(self, live_client):
        """0.9 — List messages."""
        result = await query_object_list("messages")
        data = validate_response(result, ["command_sent", "raw_response"])
        assert "message" in data["command_sent"].lower()

    async def test_query_list_generic(self, live_client):
        """0.10 — List sequences (generic)."""
        result = await query_object_list("sequence")
        data = validate_response(result, ["command_sent", "raw_response"])
        assert "sequence" in data["command_sent"].lower()


# ---------------------------------------------------------------------------
# Layer 1 — Navigation & State (SAFE_WRITE, Reversible)
# ---------------------------------------------------------------------------


@pytest.mark.live
class TestLayer1NavigationState:
    """Navigate the tree, reset programmer, set variables. All reversible."""

    async def test_navigate_to_root(self, live_client):
        """1.1 — Navigate to root."""
        result = await navigate_console("/")
        data = validate_response(result, ["success", "parsed_prompt"])
        assert data["success"] is True

    async def test_navigate_to_group(self, live_client):
        """1.2 — Navigate into Group pool."""
        result = await navigate_console("Group")
        data = validate_response(result, ["success", "parsed_prompt"])
        assert data["success"] is True

    async def test_navigate_back(self, live_client):
        """1.3 — Navigate up one level."""
        result = await navigate_console("..")
        data = validate_response(result, ["success", "parsed_prompt"])
        assert data["success"] is True

    async def test_clear_programmer_all(self, live_client):
        """1.4 — Clear entire programmer."""
        result = await clear_programmer("all")
        data = validate_response(result, ["command_sent", "raw_response"])
        assert data["command_sent"] == "clearall"

    async def test_clear_programmer_selection(self, live_client):
        """1.5 — Clear selection only."""
        result = await clear_programmer("selection")
        data = validate_response(result, ["command_sent", "raw_response"])
        assert data["command_sent"] == "clearselection"

    async def test_manage_var_set_global(self, live_client):
        """1.6 — Set a global variable."""
        result = await manage_variable("set", "global", "test_var", 42)
        data = validate_response(result, ["command_sent", "raw_response"])
        assert "setvar" in data["command_sent"].lower()

    async def test_manage_var_set_user(self, live_client):
        """1.7 — Set a user variable."""
        result = await manage_variable("set", "user", "test_var", 99)
        data = validate_response(result, ["command_sent", "raw_response"])
        assert "setuservar" in data["command_sent"].lower()

    async def test_manage_var_add_global(self, live_client):
        """1.8 — Add to a global variable."""
        result = await manage_variable("add", "global", "test_var", 1)
        data = validate_response(result, ["command_sent", "raw_response"])
        assert "addvar" in data["command_sent"].lower()

    async def test_send_raw_safe_read(self, live_client):
        """1.9 — Send a raw SAFE_READ command."""
        result = await send_raw_command("list")
        data = validate_response(result, ["command_sent", "risk_tier", "blocked"])
        assert data["blocked"] is False
        assert data["risk_tier"] == "SAFE_READ"

    async def test_send_raw_safe_write(self, live_client):
        """1.10 — Send a raw SAFE_WRITE command."""
        result = await send_raw_command("clearall")
        data = validate_response(result, ["command_sent", "risk_tier", "blocked"])
        assert data["blocked"] is False
        assert data["risk_tier"] == "SAFE_WRITE"

    async def test_send_raw_destructive_blocked(self, live_client):
        """1.11 — Verify destructive raw command is blocked without confirmation."""
        result = await send_raw_command("delete cue 9999")
        data = validate_response(result, ["blocked"])
        assert data["blocked"] is True


# ---------------------------------------------------------------------------
# Layer 2 — Selection & Group Creation (SAFE_WRITE)
# ---------------------------------------------------------------------------


@pytest.mark.live
class TestLayer2SelectionGroups:
    """Create test fixtures/groups. Depends on Layer 1 (clear programmer first)."""

    async def test_create_fixture_group(self, live_client):
        """2.1 — Create a fixture group (ID 99)."""
        # create_fixture_group returns a plain string, not JSON
        result = await create_fixture_group(1, 4, 99, "Live Test Group")
        print(f"  Response: {result}")
        assert "Group 99" in result
        assert "error" not in result.lower()

    async def test_verify_group_created(self, live_client):
        """2.2 — Verify group 99 was created."""
        result = await get_object_info("group", 99)
        data = validate_response(result, ["command_sent", "raw_response"])
        assert data["raw_response"] is not None


# ---------------------------------------------------------------------------
# Layer 3 — Light Control (SAFE_WRITE, Reversible via clearall)
# ---------------------------------------------------------------------------


@pytest.mark.live
class TestLayer3LightControl:
    """Set intensity, attributes, presets, park/unpark."""

    async def test_set_intensity_fixture(self, live_client):
        """3.1 — Set intensity on fixture 1."""
        result = await set_intensity("fixture", 1, 50)
        data = validate_response(result, ["command_sent", "raw_response"])
        assert "fixture 1" in data["command_sent"].lower()
        assert "50" in data["command_sent"]

    async def test_set_intensity_group(self, live_client):
        """3.2 — Set intensity on group 99."""
        result = await set_intensity("group", 99, 75)
        data = validate_response(result, ["command_sent", "raw_response"])
        assert "group 99" in data["command_sent"].lower()
        assert "75" in data["command_sent"]

    async def test_set_attribute_pan(self, live_client):
        """3.3 — Set Pan attribute on group 99."""
        result = await set_attribute("Pan", 45, group_id=99)
        data = validate_response_list(result, ["commands_sent", "raw_response"])
        assert len(data["commands_sent"]) == 2  # select + attribute

    async def test_apply_preset_color(self, live_client):
        """3.4 — Apply color preset 1 to group 99."""
        result = await apply_preset("color", 1, group_id=99)
        data = validate_response_list(result, ["commands_sent", "raw_response"])
        assert len(data["commands_sent"]) == 2  # select + call

    async def test_park_fixture(self, live_client):
        """3.5 — Park fixture 1."""
        result = await park_fixture("fixture 1")
        data = validate_response(result, ["command_sent", "raw_response"])
        assert "park" in data["command_sent"].lower()
        assert "fixture 1" in data["command_sent"].lower()

    async def test_unpark_fixture(self, live_client):
        """3.6 — Unpark fixture 1."""
        result = await unpark_fixture("fixture 1")
        data = validate_response(result, ["command_sent", "raw_response"])
        assert "unpark" in data["command_sent"].lower()
        assert "fixture 1" in data["command_sent"].lower()

    async def test_clear_after_control(self, live_client):
        """3.7 — Clear programmer after light control tests."""
        result = await clear_programmer("all")
        data = validate_response(result, ["command_sent", "raw_response"])
        assert data["command_sent"] == "clearall"


# ---------------------------------------------------------------------------
# Layer 4 — Programming (DESTRUCTIVE)
# ---------------------------------------------------------------------------


@pytest.mark.live
@pytest.mark.destructive
class TestLayer4Programming:
    """Store cues, presets, objects. Requires programmer state."""

    async def test_setup_programmer(self, live_client):
        """4.1 — Load programmer with fixture intensity."""
        result = await set_intensity("fixture", 1, 80)
        data = validate_response(result, ["command_sent", "raw_response"])
        assert "80" in data["command_sent"]

    async def test_store_current_cue(self, live_client):
        """4.2 — Store programmer into cue 99."""
        result = await store_current_cue(99, label="Live Test Cue")
        data = validate_response_list(result, ["commands_sent", "raw_response"])
        cmds_joined = " ".join(data["commands_sent"]).lower()
        assert "store" in cmds_joined
        assert "cue" in cmds_joined

    async def test_verify_cue_stored(self, live_client):
        """4.3 — Verify cue 99 exists."""
        result = await get_object_info("cue", 99)
        data = validate_response(result, ["command_sent", "raw_response"])
        assert data["raw_response"] is not None

    async def test_store_new_preset(self, live_client):
        """4.4 — Store programmer as dimmer preset 99."""
        # Ensure programmer has content
        await set_intensity("fixture", 1, 80)
        result = await store_new_preset("dimmer", 99)
        data = validate_response(result, ["command_sent", "raw_response"])
        assert "store" in data["command_sent"].lower()
        assert "preset" in data["command_sent"].lower()

    async def test_store_object_macro(self, live_client):
        """4.5 — Store macro 99 with confirmation."""
        result = await store_object("macro", 99, confirm_destructive=True)
        data = validate_response(result, ["command_sent", "raw_response", "blocked"])
        assert data["blocked"] is False
        assert "store" in data["command_sent"].lower()
        assert "macro" in data["command_sent"].lower()

    async def test_store_object_blocked(self, live_client):
        """4.6 — Verify store is blocked without confirmation."""
        result = await store_object("macro", 98)
        data = validate_response(result, ["blocked"])
        assert data["blocked"] is True

    async def test_label_group(self, live_client):
        """4.7 — Label group 99."""
        result = await label_or_appearance(
            "label", "group", 99, name="Relabeled", confirm_destructive=True,
        )
        data = validate_response(result, ["command_sent", "raw_response", "blocked"])
        assert data["blocked"] is False
        assert "label" in data["command_sent"].lower()
        assert "group" in data["command_sent"].lower()

    async def test_appearance_group(self, live_client):
        """4.8 — Set appearance on group 99."""
        result = await label_or_appearance(
            "appearance", "group", 99, red=255, confirm_destructive=True,
        )
        data = validate_response(result, ["command_sent", "raw_response", "blocked"])
        assert data["blocked"] is False
        assert "appearance" in data["command_sent"].lower()

    async def test_edit_cue(self, live_client):
        """4.9 — Edit cue 99 (no destructive confirmation needed)."""
        result = await edit_object("edit", "cue", 99)
        data = validate_response(result, ["command_sent", "raw_response", "blocked"])
        assert data["blocked"] is False
        assert "edit" in data["command_sent"].lower()
        assert "cue" in data["command_sent"].lower()


# ---------------------------------------------------------------------------
# Layer 5 — Copy/Move/Assign (DESTRUCTIVE)
# ---------------------------------------------------------------------------


@pytest.mark.live
@pytest.mark.destructive
class TestLayer5CopyMoveAssign:
    """Operate on objects created in Layer 4."""

    async def test_copy_group(self, live_client):
        """5.1 — Copy group 99 to 98."""
        result = await copy_or_move_object("copy", "group", 99, 98)
        data = validate_response(result, ["command_sent", "raw_response"])
        assert "copy" in data["command_sent"].lower()
        assert "group" in data["command_sent"].lower()

    async def test_assign_seq_to_executor(self, live_client):
        """5.2 — Assign sequence 1 to executor 99."""
        result = await assign_object(
            "assign",
            source_type="sequence", source_id=1,
            target_type="executor", target_id=99,
            confirm_destructive=True,
        )
        data = validate_response(result, ["command_sent", "raw_response", "blocked"])
        assert data["blocked"] is False
        assert "assign" in data["command_sent"].lower()

    async def test_assign_function(self, live_client):
        """5.3 — Assign Toggle function to executor 99."""
        result = await assign_object(
            "function",
            function="Toggle",
            target_type="executor", target_id=99,
            confirm_destructive=True,
        )
        data = validate_response(result, ["command_sent", "raw_response", "blocked"])
        assert data["blocked"] is False
        assert "toggle" in data["command_sent"].lower()

    async def test_assign_fade(self, live_client):
        """5.4 — Assign fade time 3s to cue 99."""
        result = await assign_object(
            "fade",
            fade_time=3, cue_id=99,
            confirm_destructive=True,
        )
        data = validate_response(result, ["command_sent", "raw_response", "blocked"])
        assert data["blocked"] is False
        assert "fade" in data["command_sent"].lower()

    async def test_assign_empty(self, live_client):
        """5.5 — Empty executor 99."""
        result = await assign_object(
            "empty",
            target_type="executor", target_id=99,
            confirm_destructive=True,
        )
        data = validate_response(result, ["command_sent", "raw_response", "blocked"])
        assert data["blocked"] is False

    async def test_assign_blocked(self, live_client):
        """5.6 — Verify assign is blocked without confirmation."""
        result = await assign_object(
            "assign",
            source_type="sequence", source_id=1,
        )
        data = validate_response(result, ["blocked"])
        assert data["blocked"] is True


# ---------------------------------------------------------------------------
# Layer 6 — Playback (SAFE_WRITE, needs sequences/cues)
# ---------------------------------------------------------------------------


@pytest.mark.live
class TestLayer6Playback:
    """Execute sequences and playback actions."""

    async def test_execute_sequence_go(self, live_client):
        """6.1 — Execute sequence 1 (go)."""
        # execute_sequence returns a plain string
        result = await execute_sequence(1, "go")
        print(f"  Response: {result}")
        assert "Executed" in result or "error" not in result.lower()

    async def test_execute_sequence_pause(self, live_client):
        """6.2 — Pause sequence 1."""
        result = await execute_sequence(1, "pause")
        print(f"  Response: {result}")
        assert "Paused" in result or "error" not in result.lower()

    async def test_playback_goto(self, live_client):
        """6.3 — Goto cue 99."""
        result = await playback_action("goto", cue_id=99)
        data = validate_response(result, ["command_sent", "raw_response"])
        assert "goto" in data["command_sent"].lower()

    async def test_playback_go(self, live_client):
        """6.4 — Playback go."""
        result = await playback_action("go")
        data = validate_response(result, ["command_sent", "raw_response"])
        assert "go" in data["command_sent"].lower()

    async def test_playback_go_back(self, live_client):
        """6.5 — Playback go back."""
        result = await playback_action("go_back")
        data = validate_response(result, ["command_sent", "raw_response"])
        assert "goback" in data["command_sent"].lower()

    async def test_playback_fast_forward(self, live_client):
        """6.6 — Playback fast forward."""
        result = await playback_action("fast_forward")
        data = validate_response(result, ["command_sent", "raw_response"])
        assert data["command_sent"] == ">>>"

    async def test_playback_fast_back(self, live_client):
        """6.7 — Playback fast back."""
        result = await playback_action("fast_back")
        data = validate_response(result, ["command_sent", "raw_response"])
        assert data["command_sent"] == "<<<"

    async def test_playback_def_go(self, live_client):
        """6.8 — Default go (go+)."""
        result = await playback_action("def_go")
        data = validate_response(result, ["command_sent", "raw_response"])
        assert "defgoforward" in data["command_sent"].lower()

    async def test_playback_def_pause(self, live_client):
        """6.9 — Default pause."""
        result = await playback_action("def_pause")
        data = validate_response(result, ["command_sent", "raw_response"])
        assert "defgopause" in data["command_sent"].lower()


# ---------------------------------------------------------------------------
# Layer 7 — Cleanup (DESTRUCTIVE)
# ---------------------------------------------------------------------------


@pytest.mark.live
@pytest.mark.destructive
class TestLayer7Cleanup:
    """Remove/delete test objects created in earlier layers. Runs last."""

    async def test_remove_selection(self, live_client):
        """7.1 — Remove current selection."""
        result = await remove_content("selection", confirm_destructive=True)
        data = validate_response(result, ["command_sent", "raw_response", "blocked"])
        assert data["blocked"] is False
        assert "remove" in data["command_sent"].lower()
        assert "selection" in data["command_sent"].lower()

    async def test_remove_fixture(self, live_client):
        """7.2 — Remove fixture 1 with filter."""
        result = await remove_content(
            "fixture", 1, if_filter="PresetType 1", confirm_destructive=True,
        )
        data = validate_response(result, ["command_sent", "raw_response", "blocked"])
        assert data["blocked"] is False
        assert "remove" in data["command_sent"].lower()
        assert "fixture" in data["command_sent"].lower()

    async def test_remove_blocked(self, live_client):
        """7.3 — Verify remove is blocked without confirmation."""
        result = await remove_content("fixture", 1)
        data = validate_response(result, ["blocked"])
        assert data["blocked"] is True

    async def test_edit_cut(self, live_client):
        """7.4 — Cut group 98."""
        result = await edit_object(
            "cut", "group", 98, confirm_destructive=True,
        )
        data = validate_response(result, ["command_sent", "raw_response", "blocked"])
        assert data["blocked"] is False
        assert "cut" in data["command_sent"].lower()
        assert "group" in data["command_sent"].lower()

    async def test_edit_paste(self, live_client):
        """7.5 — Paste into group 97."""
        result = await edit_object(
            "paste", "group", target_id=97, confirm_destructive=True,
        )
        data = validate_response(result, ["command_sent", "raw_response", "blocked"])
        assert data["blocked"] is False
        assert "paste" in data["command_sent"].lower()

    async def test_delete_group_99(self, live_client):
        """7.6 — Delete group 99."""
        result = await delete_object("group", 99, confirm_destructive=True)
        data = validate_response(result, ["command_sent", "raw_response", "blocked"])
        assert data["blocked"] is False

    async def test_delete_group_98(self, live_client):
        """7.7 — Delete group 98."""
        result = await delete_object("group", 98, confirm_destructive=True)
        data = validate_response(result, ["command_sent", "raw_response", "blocked"])
        assert data["blocked"] is False

    async def test_delete_group_97(self, live_client):
        """7.7b — Delete group 97 (paste target)."""
        result = await delete_object("group", 97, confirm_destructive=True)
        data = validate_response(result, ["command_sent", "raw_response", "blocked"])
        assert data["blocked"] is False

    async def test_delete_cue_99(self, live_client):
        """7.8 — Delete cue 99."""
        result = await delete_object("cue", 99, confirm_destructive=True)
        data = validate_response(result, ["command_sent", "raw_response", "blocked"])
        assert data["blocked"] is False

    async def test_delete_macro_99(self, live_client):
        """7.9 — Delete macro 99."""
        result = await delete_object("macro", 99, confirm_destructive=True)
        data = validate_response(result, ["command_sent", "raw_response", "blocked"])
        assert data["blocked"] is False

    async def test_delete_blocked(self, live_client):
        """7.10 — Verify delete is blocked without confirmation."""
        result = await delete_object("group", 1)
        data = validate_response(result, ["blocked"])
        assert data["blocked"] is True

    async def test_final_clearall(self, live_client):
        """7.11 — Final clearall to leave console clean."""
        result = await clear_programmer("all")
        data = validate_response(result, ["command_sent", "raw_response"])
        assert data["command_sent"] == "clearall"
