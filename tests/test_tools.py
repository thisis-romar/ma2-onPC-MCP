"""
MCP Tools Tests

Tests for high-level MCP tools functionality. These are tools that AI can call.
Uses mocks to simulate Telnet connections and avoid actual network calls.

The MCP tool functions are defined in src/server.py with @mcp.tool() decorators.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestCreateFixtureGroupTool:
    """Tests for the create fixture group MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_create_fixture_group_basic(self, mock_get_client):
        """Test creating a basic fixture group."""
        from src.server import create_fixture_group

        mock_client = MagicMock()
        mock_client.send_command = AsyncMock()
        mock_get_client.return_value = mock_client

        result = await create_fixture_group(start_fixture=1, end_fixture=10, group_id=1)

        calls = mock_client.send_command.call_args_list
        assert len(calls) == 2
        assert calls[0][0][0] == "selfix fixture 1 thru 10"
        assert calls[1][0][0] == "store group 1"

        assert "Group 1" in result
        assert "Fixtures 1" in result
        assert "10" in result

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_create_fixture_group_with_label(self, mock_get_client):
        """Test creating a fixture group with a label."""
        from src.server import create_fixture_group

        mock_client = MagicMock()
        mock_client.send_command = AsyncMock()
        mock_get_client.return_value = mock_client

        await create_fixture_group(
            start_fixture=1, end_fixture=10, group_id=1, group_name="Front Wash"
        )

        calls = mock_client.send_command.call_args_list
        assert len(calls) == 3
        assert calls[0][0][0] == "selfix fixture 1 thru 10"
        assert calls[1][0][0] == "store group 1"
        assert calls[2][0][0] == 'label group 1 "Front Wash"'

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_create_fixture_group_with_custom_name(self, mock_get_client):
        """Test creating a fixture group with a custom name."""
        from src.server import create_fixture_group

        mock_client = MagicMock()
        mock_client.send_command = AsyncMock()
        mock_get_client.return_value = mock_client

        await create_fixture_group(
            start_fixture=1, end_fixture=10, group_id=1, group_name="Front Stage Wash"
        )

        calls = mock_client.send_command.call_args_list
        assert calls[2][0][0] == 'label group 1 "Front Stage Wash"'


class TestExecuteSequenceTool:
    """Tests for the execute sequence MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_execute_sequence_go(self, mock_get_client):
        """Test executing a sequence (go)."""
        from src.server import execute_sequence

        mock_client = MagicMock()
        mock_client.send_command = AsyncMock()
        mock_get_client.return_value = mock_client

        await execute_sequence(sequence_id=1, action="go")

        mock_client.send_command.assert_called_once_with("go+ sequence 1")

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_execute_sequence_pause(self, mock_get_client):
        """Test pausing a sequence."""
        from src.server import execute_sequence

        mock_client = MagicMock()
        mock_client.send_command = AsyncMock()
        mock_get_client.return_value = mock_client

        await execute_sequence(sequence_id=1, action="pause")

        mock_client.send_command.assert_called_once_with("pause sequence 1")

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_execute_sequence_goto(self, mock_get_client):
        """Test jumping to a specific cue."""
        from src.server import execute_sequence

        mock_client = MagicMock()
        mock_client.send_command = AsyncMock()
        mock_get_client.return_value = mock_client

        await execute_sequence(sequence_id=1, action="goto", cue_id=5)

        mock_client.send_command.assert_called_once_with("goto cue 5 sequence 1")


class TestSendRawCommandTool:
    """Tests for the send raw command MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_send_safe_write_command(self, mock_get_client):
        """Test sending a SAFE_WRITE command (selfix) — should be allowed."""
        import json

        from src.server import send_raw_command

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await send_raw_command("selfix fixture 1 thru 10")
        data = json.loads(result)

        mock_client.send_command_with_response.assert_called_once_with(
            "selfix fixture 1 thru 10"
        )
        assert data["command_sent"] == "selfix fixture 1 thru 10"
        assert data["blocked"] is False

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_block_destructive_command(self, mock_get_client):
        """Test that destructive commands are blocked without confirm_destructive."""
        import json

        from src.server import send_raw_command

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = await send_raw_command("delete cue 1 thru 9999")
        data = json.loads(result)

        assert data["blocked"] is True
        assert data["risk_tier"] == "DESTRUCTIVE"
        assert data["command_sent"] is None
        # Client should NOT have been called
        mock_client.send_command_with_response.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_allow_destructive_with_confirm(self, mock_get_client):
        """Test that destructive commands pass with confirm_destructive=True."""
        import json

        from src.server import send_raw_command

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await send_raw_command("store cue 1", confirm_destructive=True)
        data = json.loads(result)

        assert data["blocked"] is False
        assert data["command_sent"] == "store cue 1"
        assert data["risk_tier"] == "DESTRUCTIVE"

    @pytest.mark.asyncio
    async def test_block_command_injection(self):
        """Test that commands with line breaks are rejected."""
        import json

        from src.server import send_raw_command

        result = await send_raw_command("list\r\ndelete cue 1")
        data = json.loads(result)

        assert data["blocked"] is True
        assert "line breaks" in data["error"]
        assert data["command_sent"] is None

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_safe_read_always_allowed(self, mock_get_client):
        """Test that SAFE_READ commands (list, info, cd) are always allowed."""
        import json

        from src.server import send_raw_command

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[Fixture]>")
        mock_get_client.return_value = mock_client

        result = await send_raw_command("list")
        data = json.loads(result)

        assert data["blocked"] is False
        assert data["risk_tier"] == "SAFE_READ"


class TestErrorHandling:
    """Tests for the _handle_errors decorator on MCP tools."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_connection_error_returns_json(self, mock_get_client):
        """Test that ConnectionError is caught and returned as JSON."""
        from src.server import set_intensity

        mock_get_client.side_effect = ConnectionError("Unable to connect to 127.0.0.1:30000")

        result = await set_intensity(target_type="fixture", target_id=1, level=50)
        data = json.loads(result)

        assert "error" in data
        assert "Connection failed" in data["error"]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_runtime_error_returns_json(self, mock_get_client):
        """Test that RuntimeError (e.g. dropped connection) is caught."""
        from src.server import get_object_info

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(
            side_effect=RuntimeError("Connection not established")
        )
        mock_get_client.return_value = mock_client

        result = await get_object_info(object_type="group", object_id=3)
        data = json.loads(result)

        assert "error" in data
        assert "Runtime error" in data["error"]


class TestSetIntensityTool:
    """Tests for the set_intensity MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_fixture_at_50(self, mock_get_client):
        """Test setting a single fixture to 50%."""
        from src.server import set_intensity

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await set_intensity(target_type="fixture", target_id=1, level=50)
        data = json.loads(result)

        assert data["command_sent"] == "fixture 1 at 50"
        mock_client.send_command_with_response.assert_called_once_with("fixture 1 at 50")

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_group_at_full(self, mock_get_client):
        """Test setting a group to full."""
        from src.server import set_intensity

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await set_intensity(target_type="group", target_id=3, level=100)
        data = json.loads(result)

        assert data["command_sent"] == "group 3 at 100"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_channel_range(self, mock_get_client):
        """Test setting a channel range."""
        from src.server import set_intensity

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await set_intensity(
            target_type="channel", target_id=1, level=75, end_id=10
        )
        data = json.loads(result)

        assert data["command_sent"] == "channel 1 thru 10 at 75"

    @pytest.mark.asyncio
    async def test_invalid_target_type(self):
        """Test that an invalid target type returns an error."""
        from src.server import set_intensity

        result = await set_intensity(target_type="lamp", target_id=1, level=50)
        data = json.loads(result)

        assert "error" in data
        assert "lamp" in data["error"]


class TestApplyPresetTool:
    """Tests for the apply_preset MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_apply_color_preset(self, mock_get_client):
        """Test applying a color preset to current selection."""
        from src.server import apply_preset

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await apply_preset(preset_type="color", preset_id=3)
        data = json.loads(result)

        assert data["commands_sent"] == ["call preset 4.3"]
        mock_client.send_command_with_response.assert_called_once_with("call preset 4.3")

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_apply_preset_with_group(self, mock_get_client):
        """Test applying a preset after selecting a group."""
        from src.server import apply_preset

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await apply_preset(preset_type="position", preset_id=1, group_id=2)
        data = json.loads(result)

        calls = mock_client.send_command_with_response.call_args_list
        assert len(calls) == 2
        assert calls[0][0][0] == "group 2"
        assert calls[1][0][0] == "call preset 2.1"
        assert data["commands_sent"] == ["group 2", "call preset 2.1"]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_apply_preset_with_fixture_range(self, mock_get_client):
        """Test applying a preset after selecting a fixture range."""
        from src.server import apply_preset

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await apply_preset(
            preset_type="gobo", preset_id=5, fixture_id=1, fixture_end=10
        )
        json.loads(result)

        calls = mock_client.send_command_with_response.call_args_list
        assert calls[0][0][0] == "selfix fixture 1 thru 10"
        assert calls[1][0][0] == "call preset 3.5"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_apply_preset_numeric_type(self, mock_get_client):
        """Test applying a preset using numeric type string."""
        from src.server import apply_preset

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await apply_preset(preset_type="4", preset_id=2)
        data = json.loads(result)

        assert data["commands_sent"] == ["call preset 4.2"]


class TestStoreCueTool:
    """Tests for the store_current_cue MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_store_basic_cue(self, mock_get_client):
        """Test storing a simple cue."""
        from src.server import store_current_cue

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await store_current_cue(cue_number=5)
        data = json.loads(result)

        assert data["commands_sent"] == ["store cue 5"]
        mock_client.send_command_with_response.assert_called_once_with("store cue 5")

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_store_cue_with_sequence(self, mock_get_client):
        """Test storing a cue into a specific sequence."""
        from src.server import store_current_cue

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await store_current_cue(cue_number=3, sequence_id=2)
        data = json.loads(result)

        assert data["commands_sent"] == ["store cue 3 sequence 2"]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_store_cue_with_label(self, mock_get_client):
        """Test storing a cue with a label."""
        from src.server import store_current_cue

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await store_current_cue(cue_number=3, label="Opening Look")
        json.loads(result)

        calls = mock_client.send_command_with_response.call_args_list
        assert len(calls) == 2
        assert calls[0][0][0] == "store cue 3"
        assert calls[1][0][0] == 'label cue 3 "Opening Look"'

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_store_cue_merge(self, mock_get_client):
        """Test storing a cue with merge option."""
        from src.server import store_current_cue

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await store_current_cue(cue_number=1, merge=True)
        data = json.loads(result)

        assert data["commands_sent"] == ["store cue 1 /merge"]


class TestGetObjectInfoTool:
    """Tests for the get_object_info MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_info_group(self, mock_get_client):
        """Test querying info on a group."""
        from src.server import get_object_info

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Group 3 info")
        mock_get_client.return_value = mock_client

        result = await get_object_info(object_type="group", object_id=3)
        data = json.loads(result)

        assert data["command_sent"] == "info group 3"
        assert data["raw_response"] == "Group 3 info"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_info_preset_dot_notation(self, mock_get_client):
        """Test querying info on a preset with dot notation."""
        from src.server import get_object_info

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Preset info")
        mock_get_client.return_value = mock_client

        result = await get_object_info(object_type="preset", object_id="2.1")
        data = json.loads(result)

        assert data["command_sent"] == "info preset 2.1"


class TestClearProgrammerTool:
    """Tests for the clear_programmer MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_clear_all(self, mock_get_client):
        """Test clearing entire programmer."""
        from src.server import clear_programmer

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await clear_programmer(mode="all")
        data = json.loads(result)

        assert data["command_sent"] == "clearall"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_clear_selection(self, mock_get_client):
        """Test clearing selection only."""
        from src.server import clear_programmer

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await clear_programmer(mode="selection")
        data = json.loads(result)

        assert data["command_sent"] == "clearselection"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_clear_active(self, mock_get_client):
        """Test clearing active values only."""
        from src.server import clear_programmer

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await clear_programmer(mode="active")
        data = json.loads(result)

        assert data["command_sent"] == "clearactive"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_clear_sequential(self, mock_get_client):
        """Test sequential clear mode."""
        from src.server import clear_programmer

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await clear_programmer(mode="clear")
        data = json.loads(result)

        assert data["command_sent"] == "clear"

    @pytest.mark.asyncio
    async def test_clear_invalid_mode(self):
        """Test that an invalid mode returns an error."""
        from src.server import clear_programmer

        result = await clear_programmer(mode="invalid")
        data = json.loads(result)

        assert "error" in data
        assert "invalid" in data["error"]


class TestSetNodePropertyTool:
    """Tests for the set_node_property MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.set_property")
    @patch("src.server.get_client")
    async def test_set_property_basic(self, mock_get_client, mock_set_property):
        """Test setting a property on a node."""
        from src.navigation import SetPropertyResult
        from src.server import set_node_property

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_set_property.return_value = SetPropertyResult(
            path="3.1",
            commands_sent=["cd /", "cd 3", 'assign 1/Telnet="Login Disabled"', "cd /"],
            raw_responses=["[Root]>", "[Settings]>", "Ok", "[Root]>"],
            success=True,
            verified_value="Login Disabled",
        )

        result = await set_node_property(
            path="3.1", property_name="Telnet", value="Login Disabled"
        )
        data = json.loads(result)

        assert data["success"] is True
        assert data["verified_value"] == "Login Disabled"
        assert data["property_name"] == "Telnet"
        assert data["path"] == "3.1"
        mock_set_property.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.server.set_property")
    @patch("src.server.get_client")
    async def test_set_property_failure(self, mock_get_client, mock_set_property):
        """Test property set that fails verification."""
        from src.navigation import SetPropertyResult
        from src.server import set_node_property

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_set_property.return_value = SetPropertyResult(
            path="3.1",
            commands_sent=["cd /", "cd 3", 'assign 1/Telnet="Bad"', "cd /"],
            raw_responses=["[Root]>", "[Settings]>", "Error", "[Root]>"],
            success=False,
            error="Verification failed",
        )

        result = await set_node_property(
            path="3.1", property_name="Telnet", value="Bad"
        )
        data = json.loads(result)

        assert data["success"] is False
        assert data["error"] == "Verification failed"


class TestSetAttributeTool:
    """Tests for the set_attribute MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_set_pan(self, mock_get_client):
        """Test setting Pan attribute."""
        from src.server import set_attribute

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await set_attribute(attribute_name="Pan", value=120)
        data = json.loads(result)

        assert data["commands_sent"] == ['attribute "Pan" at 120']

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_set_attribute_with_group(self, mock_get_client):
        """Test setting attribute after selecting a group."""
        from src.server import set_attribute

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await set_attribute(attribute_name="Tilt", value=50, group_id=2)
        json.loads(result)

        calls = mock_client.send_command_with_response.call_args_list
        assert calls[0][0][0] == "group 2"
        assert calls[1][0][0] == 'attribute "Tilt" at 50'

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_set_attribute_with_fixture_range(self, mock_get_client):
        """Test setting attribute after selecting fixtures."""
        from src.server import set_attribute

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await set_attribute(
            attribute_name="Zoom", value=80, fixture_id=1, fixture_end=10
        )
        json.loads(result)

        calls = mock_client.send_command_with_response.call_args_list
        assert calls[0][0][0] == "selfix fixture 1 thru 10"
        assert calls[1][0][0] == 'attribute "Zoom" at 80'


class TestParkFixtureTool:
    """Tests for the park_fixture and unpark_fixture MCP tools."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_park_fixture(self, mock_get_client):
        """Test parking a fixture."""
        from src.server import park_fixture

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await park_fixture(target="fixture 1")
        data = json.loads(result)

        assert data["command_sent"] == "park fixture 1"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_park_dmx_with_value(self, mock_get_client):
        """Test parking DMX at a specific value."""
        from src.server import park_fixture

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await park_fixture(target="dmx 101", value=128)
        data = json.loads(result)

        assert data["command_sent"] == "park dmx 101 at 128"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_unpark_fixture(self, mock_get_client):
        """Test unparking a fixture."""
        from src.server import unpark_fixture

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await unpark_fixture(target="fixture 1")
        data = json.loads(result)

        assert data["command_sent"] == "unpark fixture 1"


class TestRunMacroTool:
    """Tests for the run_macro MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_run_macro(self, mock_get_client):
        """Test executing a macro."""
        from src.server import run_macro

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await run_macro(macro_id=1)
        data = json.loads(result)

        assert data["command_sent"] == "go macro 1"


class TestDeleteObjectTool:
    """Tests for the delete_object MCP tool."""

    @pytest.mark.asyncio
    async def test_delete_blocked_without_confirm(self):
        """Test that delete is blocked without confirmation."""
        from src.server import delete_object

        result = await delete_object(object_type="cue", object_id=5)
        data = json.loads(result)

        assert data["blocked"] is True
        assert "DESTRUCTIVE" in data["error"]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_delete_cue_with_confirm(self, mock_get_client):
        """Test deleting a cue with confirmation."""
        from src.server import delete_object

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await delete_object(
            object_type="cue", object_id=5, confirm_destructive=True
        )
        data = json.loads(result)

        assert data["blocked"] is False
        assert data["command_sent"] == "delete cue 5 /noconfirm"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_delete_group_with_confirm(self, mock_get_client):
        """Test deleting a generic object type."""
        from src.server import delete_object

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await delete_object(
            object_type="group", object_id=3, confirm_destructive=True
        )
        data = json.loads(result)

        assert data["blocked"] is False
        assert "delete group 3" in data["command_sent"]


class TestCopyOrMoveObjectTool:
    """Tests for the copy_or_move_object MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_copy_group(self, mock_get_client):
        """Test copying a group."""
        from src.server import copy_or_move_object

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await copy_or_move_object(
            action="copy", object_type="group", source_id=1, target_id=5
        )
        data = json.loads(result)

        assert data["command_sent"] == "copy group 1 at 5"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_move_macro(self, mock_get_client):
        """Test moving a macro."""
        from src.server import copy_or_move_object

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await copy_or_move_object(
            action="move", object_type="macro", source_id=3, target_id=10
        )
        data = json.loads(result)

        assert data["command_sent"] == "move macro 3 at 10"

    @pytest.mark.asyncio
    async def test_invalid_action(self):
        """Test that invalid action returns error."""
        from src.server import copy_or_move_object

        result = await copy_or_move_object(
            action="cut", object_type="group", source_id=1, target_id=5
        )
        data = json.loads(result)

        assert "error" in data


class TestStoreNewPresetTool:
    """Tests for the store_new_preset MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_store_color_preset(self, mock_get_client):
        """Test storing a color preset."""
        from src.server import store_new_preset

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await store_new_preset(preset_type="color", preset_id=5)
        data = json.loads(result)

        assert data["command_sent"] == "store preset 4.5"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_store_preset_with_merge(self, mock_get_client):
        """Test storing a preset with merge option."""
        from src.server import store_new_preset

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await store_new_preset(
            preset_type="position", preset_id=3, merge=True
        )
        data = json.loads(result)

        assert data["command_sent"] == "store preset 2.3 /merge"


class TestNavigateConsoleTool:
    """Tests for the navigate_console MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.navigate")
    @patch("src.server.get_client")
    async def test_navigate_to_root(self, mock_get_client, mock_navigate):
        """Test navigating to root."""
        from src.prompt_parser import ConsolePrompt
        from src.server import navigate_console

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_result = MagicMock()
        mock_result.command_sent = "cd /"
        mock_result.raw_response = "[Root]>"
        mock_result.success = True
        mock_result.parsed_prompt = ConsolePrompt(
            raw_response="[Root]>",
            prompt_line="[Root]>",
            location="Root",
            object_type="Root",
            object_id=None,
        )
        mock_navigate.return_value = mock_result

        result = await navigate_console(destination="/")
        data = json.loads(result)

        assert data["command_sent"] == "cd /"
        assert data["success"] is True
        assert data["parsed_prompt"]["location"] == "Root"

    @pytest.mark.asyncio
    @patch("src.server.navigate")
    @patch("src.server.get_client")
    async def test_navigate_with_object_id(self, mock_get_client, mock_navigate):
        """Test navigating with dot notation."""
        from src.prompt_parser import ConsolePrompt
        from src.server import navigate_console

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_result = MagicMock()
        mock_result.command_sent = "cd Group.1"
        mock_result.raw_response = "[Group 1]>"
        mock_result.success = True
        mock_result.parsed_prompt = ConsolePrompt(
            raw_response="[Group 1]>",
            prompt_line="[Group 1]>",
            location="Group 1",
            object_type="Group",
            object_id="1",
        )
        mock_navigate.return_value = mock_result

        result = await navigate_console(destination="Group", object_id=1)
        data = json.loads(result)

        assert data["success"] is True
        assert data["parsed_prompt"]["object_type"] == "Group"
        assert data["parsed_prompt"]["object_id"] == "1"


class TestGetConsoleLocationTool:
    """Tests for the get_console_location MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.get_current_location")
    @patch("src.server.get_client")
    async def test_get_location(self, mock_get_client, mock_get_location):
        """Test querying current location."""
        from src.prompt_parser import ConsolePrompt
        from src.server import get_console_location

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_result = MagicMock()
        mock_result.command_sent = ""
        mock_result.raw_response = "[channel]>"
        mock_result.success = True
        mock_result.parsed_prompt = ConsolePrompt(
            raw_response="[channel]>",
            prompt_line="[channel]>",
            location="channel",
            object_type="channel",
            object_id=None,
        )
        mock_get_location.return_value = mock_result

        result = await get_console_location()
        data = json.loads(result)

        assert data["success"] is True
        assert data["parsed_prompt"]["location"] == "channel"


class TestListConsoleDestinationTool:
    """Tests for the list_console_destination MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.list_destination")
    @patch("src.server.get_client")
    async def test_list_destination(self, mock_get_client, mock_list_dest):
        """Test listing objects at current destination."""
        from src.prompt_parser import ListEntry, ListOutput
        from src.server import list_console_destination

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_result = MagicMock()
        mock_result.command_sent = "list"
        mock_result.raw_response = "Group.1  Front Wash\nGroup.2  Back"
        mock_result.parsed_list = ListOutput(
            raw_response="Group.1  Front Wash\nGroup.2  Back",
            entries=(
                ListEntry(object_type="Group", object_id="1", name="Front Wash"),
                ListEntry(object_type="Group", object_id="2", name="Back"),
            ),
        )
        mock_list_dest.return_value = mock_result

        result = await list_console_destination()
        data = json.loads(result)

        assert data["entry_count"] == 2
        assert data["entries"][0]["object_type"] == "Group"
        assert data["entries"][0]["name"] == "Front Wash"
        assert data["entries"][1]["object_id"] == "2"


# ============================================================
# New Composite Tool Tests
# ============================================================


class TestQueryObjectListTool:
    """Tests for the query_object_list MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_list_cue(self, mock_get_client):
        """Test listing cues."""
        from src.server import query_object_list

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Cue 1\nCue 2")
        mock_get_client.return_value = mock_client

        result = await query_object_list(object_type="cue")
        data = json.loads(result)

        assert data["command_sent"] == "list cue"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_list_cue_with_sequence(self, mock_get_client):
        """Test listing cues in a specific sequence."""
        from src.server import query_object_list

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Cue list")
        mock_get_client.return_value = mock_client

        result = await query_object_list(object_type="cue", sequence_id=2)
        data = json.loads(result)

        assert "sequence 2" in data["command_sent"]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_list_group(self, mock_get_client):
        """Test listing groups."""
        from src.server import query_object_list

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Group list")
        mock_get_client.return_value = mock_client

        result = await query_object_list(object_type="group")
        data = json.loads(result)

        assert data["command_sent"] == "list group"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_list_preset(self, mock_get_client):
        """Test listing presets by type."""
        from src.server import query_object_list

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Preset list")
        mock_get_client.return_value = mock_client

        result = await query_object_list(object_type="preset", preset_type="color")
        data = json.loads(result)

        assert "preset" in data["command_sent"].lower()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_list_attribute(self, mock_get_client):
        """Test listing attributes."""
        from src.server import query_object_list

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Attr list")
        mock_get_client.return_value = mock_client

        result = await query_object_list(object_type="attribute")
        data = json.loads(result)

        assert data["command_sent"] == "list attribute"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_list_messages(self, mock_get_client):
        """Test listing messages."""
        from src.server import query_object_list

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Messages")
        mock_get_client.return_value = mock_client

        result = await query_object_list(object_type="messages")
        data = json.loads(result)

        assert data["command_sent"] == "list messages"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_list_generic(self, mock_get_client):
        """Test listing a generic object type."""
        from src.server import query_object_list

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Seq list")
        mock_get_client.return_value = mock_client

        result = await query_object_list(object_type="sequence")
        data = json.loads(result)

        assert data["command_sent"] == "list sequence"


class TestPlaybackActionTool:
    """Tests for the playback_action MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_go_executor(self, mock_get_client):
        """Test go on executor."""
        from src.server import playback_action

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await playback_action(
            action="go", object_type="executor", object_id=1
        )
        data = json.loads(result)

        assert "go" in data["command_sent"].lower()
        assert "executor" in data["command_sent"].lower()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_go_back(self, mock_get_client):
        """Test go back."""
        from src.server import playback_action

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await playback_action(action="go_back")
        data = json.loads(result)

        assert "goback" in data["command_sent"].lower()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_goto_cue(self, mock_get_client):
        """Test goto specific cue."""
        from src.server import playback_action

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await playback_action(action="goto", cue_id=5)
        data = json.loads(result)

        assert "goto" in data["command_sent"].lower()
        assert "5" in data["command_sent"]

    @pytest.mark.asyncio
    async def test_goto_without_cue_id(self):
        """Test that goto requires cue_id."""
        from src.server import playback_action

        result = await playback_action(action="goto")
        data = json.loads(result)

        assert "error" in data
        assert "cue_id" in data["error"]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_fast_forward(self, mock_get_client):
        """Test fast forward."""
        from src.server import playback_action

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await playback_action(action="fast_forward")
        data = json.loads(result)

        assert data["command_sent"] == ">>>"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_fast_back(self, mock_get_client):
        """Test fast back."""
        from src.server import playback_action

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await playback_action(action="fast_back")
        data = json.loads(result)

        assert data["command_sent"] == "<<<"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_def_go(self, mock_get_client):
        """Test go on selected executor."""
        from src.server import playback_action

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await playback_action(action="def_go")
        data = json.loads(result)

        assert data["command_sent"] == "defgoforward"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_def_pause(self, mock_get_client):
        """Test pause selected executor."""
        from src.server import playback_action

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await playback_action(action="def_pause")
        data = json.loads(result)

        assert data["command_sent"] == "defgopause"

    @pytest.mark.asyncio
    async def test_invalid_action(self):
        """Test that an invalid action returns an error."""
        from src.server import playback_action

        result = await playback_action(action="rewind")
        data = json.loads(result)

        assert "error" in data
        assert "rewind" in data["error"]


class TestManageVariableTool:
    """Tests for the manage_variable MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_set_global_var(self, mock_get_client):
        """Test setting a global variable."""
        from src.server import manage_variable

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await manage_variable(
            action="set", scope="global", var_name="myvar", value=42
        )
        data = json.loads(result)

        assert data["command_sent"] == "setvar myvar = 42"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_set_user_var(self, mock_get_client):
        """Test setting a user variable."""
        from src.server import manage_variable

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await manage_variable(
            action="set", scope="user", var_name="speed", value=100
        )
        data = json.loads(result)

        assert data["command_sent"] == "setuservar speed = 100"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_add_global_var(self, mock_get_client):
        """Test adding to a global variable."""
        from src.server import manage_variable

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await manage_variable(
            action="add", scope="global", var_name="counter", value=1
        )
        data = json.loads(result)

        assert data["command_sent"] == "addvar counter = 1"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_add_user_var(self, mock_get_client):
        """Test adding to a user variable."""
        from src.server import manage_variable

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await manage_variable(
            action="add", scope="user", var_name="counter", value=1
        )
        data = json.loads(result)

        assert data["command_sent"] == "adduservar counter = 1"

    @pytest.mark.asyncio
    async def test_add_without_value(self):
        """Test that add without value returns error."""
        from src.server import manage_variable

        result = await manage_variable(
            action="add", scope="global", var_name="counter"
        )
        data = json.loads(result)

        assert "error" in data

    @pytest.mark.asyncio
    async def test_invalid_action(self):
        """Test that invalid action returns error."""
        from src.server import manage_variable

        result = await manage_variable(
            action="multiply", scope="global", var_name="x", value=2
        )
        data = json.loads(result)

        assert "error" in data

    @pytest.mark.asyncio
    async def test_invalid_scope(self):
        """Test that invalid scope returns error."""
        from src.server import manage_variable

        result = await manage_variable(
            action="set", scope="session", var_name="x", value=1
        )
        data = json.loads(result)

        assert "error" in data


class TestLabelOrAppearanceTool:
    """Tests for the label_or_appearance MCP tool."""

    @pytest.mark.asyncio
    async def test_blocked_without_confirm(self):
        """Test that label/appearance is blocked without confirmation."""
        from src.server import label_or_appearance

        result = await label_or_appearance(
            action="label", object_type="group", object_id=3, name="Test"
        )
        data = json.loads(result)

        assert data["blocked"] is True

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_label_group(self, mock_get_client):
        """Test labeling a group."""
        from src.server import label_or_appearance

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await label_or_appearance(
            action="label", object_type="group", object_id=3,
            name="Front Wash", confirm_destructive=True
        )
        data = json.loads(result)

        assert data["command_sent"] == 'label group 3 "Front Wash"'
        assert data["blocked"] is False

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_label_preset(self, mock_get_client):
        """Test labeling a preset with preset_type."""
        from src.server import label_or_appearance

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await label_or_appearance(
            action="label", object_type="preset", object_id=1,
            preset_type="color", name="Red", confirm_destructive=True
        )
        data = json.loads(result)

        assert "preset" in data["command_sent"].lower()
        assert "Red" in data["command_sent"]

    @pytest.mark.asyncio
    async def test_label_without_name(self):
        """Test that label without name returns error."""
        from src.server import label_or_appearance

        result = await label_or_appearance(
            action="label", object_type="group", object_id=3,
            confirm_destructive=True
        )
        data = json.loads(result)

        assert "error" in data

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_appearance_with_color(self, mock_get_client):
        """Test setting appearance with hex color."""
        from src.server import label_or_appearance

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await label_or_appearance(
            action="appearance", object_type="group", object_id=1,
            color="FF0000", confirm_destructive=True
        )
        data = json.loads(result)

        assert "appearance" in data["command_sent"].lower()
        assert "FF0000" in data["command_sent"]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_appearance_with_rgb(self, mock_get_client):
        """Test setting appearance with RGB components."""
        from src.server import label_or_appearance

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await label_or_appearance(
            action="appearance", object_type="group", object_id=1,
            red=255, green=0, blue=0, confirm_destructive=True
        )
        data = json.loads(result)

        assert "appearance" in data["command_sent"].lower()
        assert "/r=255" in data["command_sent"]


class TestAssignObjectTool:
    """Tests for the assign_object MCP tool."""

    @pytest.mark.asyncio
    async def test_blocked_without_confirm(self):
        """Test that assign is blocked without confirmation."""
        from src.server import assign_object

        result = await assign_object(
            mode="assign", source_type="sequence", source_id=1,
            target_type="executor", target_id=6
        )
        data = json.loads(result)

        assert data["blocked"] is True

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_assign_sequence_to_executor(self, mock_get_client):
        """Test assigning a sequence to an executor."""
        from src.server import assign_object

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await assign_object(
            mode="assign", source_type="sequence", source_id=1,
            target_type="executor", target_id=6, confirm_destructive=True
        )
        data = json.loads(result)

        assert data["blocked"] is False
        assert "assign" in data["command_sent"].lower()
        assert "sequence" in data["command_sent"].lower()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_assign_function(self, mock_get_client):
        """Test assigning a function to an executor."""
        from src.server import assign_object

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await assign_object(
            mode="function", function="Toggle",
            target_type="executor", target_id=101, confirm_destructive=True
        )
        data = json.loads(result)

        assert "toggle" in data["command_sent"].lower()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_assign_fade(self, mock_get_client):
        """Test assigning a fade time to a cue."""
        from src.server import assign_object

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await assign_object(
            mode="fade", fade_time=3, cue_id=5, confirm_destructive=True
        )
        data = json.loads(result)

        assert "fade" in data["command_sent"].lower()
        assert "3" in data["command_sent"]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_assign_to_layout(self, mock_get_client):
        """Test assigning an object to a layout."""
        from src.server import assign_object

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await assign_object(
            mode="layout", source_type="group", source_id=1,
            layout_id=1, x=5, y=2, confirm_destructive=True
        )
        data = json.loads(result)

        assert "layout" in data["command_sent"].lower()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_assign_empty(self, mock_get_client):
        """Test emptying an executor."""
        from src.server import assign_object

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await assign_object(
            mode="empty", target_type="executor", target_id=1,
            confirm_destructive=True
        )
        data = json.loads(result)

        assert "empty" in data["command_sent"].lower()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_assign_temp_fader(self, mock_get_client):
        """Test assigning temp fader to an executor."""
        from src.server import assign_object

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await assign_object(
            mode="temp_fader", target_type="executor", target_id=1,
            confirm_destructive=True
        )
        data = json.loads(result)

        assert "tempfader" in data["command_sent"].lower()

    @pytest.mark.asyncio
    async def test_assign_missing_source(self):
        """Test that assign mode without source returns error."""
        from src.server import assign_object

        result = await assign_object(
            mode="assign", target_type="executor", target_id=1,
            confirm_destructive=True
        )
        data = json.loads(result)

        assert "error" in data

    @pytest.mark.asyncio
    async def test_invalid_mode(self):
        """Test that invalid mode returns error."""
        from src.server import assign_object

        result = await assign_object(
            mode="patch", confirm_destructive=True
        )
        data = json.loads(result)

        assert "error" in data


class TestEditObjectTool:
    """Tests for the edit_object MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_edit_cue(self, mock_get_client):
        """Test editing a cue (SAFE_WRITE, no confirm needed)."""
        from src.server import edit_object

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[Edit Cue]>")
        mock_get_client.return_value = mock_client

        result = await edit_object(action="edit", object_type="cue", object_id=1)
        data = json.loads(result)

        assert data["command_sent"] == "edit cue 1"

    @pytest.mark.asyncio
    async def test_cut_blocked_without_confirm(self):
        """Test that cut is blocked without confirmation."""
        from src.server import edit_object

        result = await edit_object(
            action="cut", object_type="preset", object_id="4.1"
        )
        data = json.loads(result)

        assert data["blocked"] is True

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_cut_with_confirm(self, mock_get_client):
        """Test cutting an object with confirmation."""
        from src.server import edit_object

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await edit_object(
            action="cut", object_type="preset", object_id="4.1",
            confirm_destructive=True
        )
        data = json.loads(result)

        assert data["command_sent"] == "cut preset 4.1"
        assert data["blocked"] is False

    @pytest.mark.asyncio
    async def test_paste_blocked_without_confirm(self):
        """Test that paste is blocked without confirmation."""
        from src.server import edit_object

        result = await edit_object(
            action="paste", object_type="group", target_id=5
        )
        data = json.loads(result)

        assert data["blocked"] is True

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_paste_with_confirm(self, mock_get_client):
        """Test pasting with confirmation."""
        from src.server import edit_object

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await edit_object(
            action="paste", object_type="group", target_id=5,
            confirm_destructive=True
        )
        data = json.loads(result)

        assert "paste" in data["command_sent"].lower()

    @pytest.mark.asyncio
    async def test_invalid_action(self):
        """Test that invalid action returns error."""
        from src.server import edit_object

        result = await edit_object(action="merge", confirm_destructive=True)
        data = json.loads(result)

        assert "error" in data


class TestRemoveContentTool:
    """Tests for the remove_content MCP tool."""

    @pytest.mark.asyncio
    async def test_blocked_without_confirm(self):
        """Test that remove is blocked without confirmation."""
        from src.server import remove_content

        result = await remove_content(object_type="selection")
        data = json.loads(result)

        assert data["blocked"] is True

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_remove_selection(self, mock_get_client):
        """Test removing selection."""
        from src.server import remove_content

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await remove_content(
            object_type="selection", confirm_destructive=True
        )
        data = json.loads(result)

        assert data["command_sent"] == "remove selection"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_remove_fixture(self, mock_get_client):
        """Test removing a fixture."""
        from src.server import remove_content

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await remove_content(
            object_type="fixture", object_id=1, confirm_destructive=True
        )
        data = json.loads(result)

        assert "remove" in data["command_sent"].lower()
        assert "fixture" in data["command_sent"].lower()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_remove_fixture_with_filter(self, mock_get_client):
        """Test removing a fixture with if_filter."""
        from src.server import remove_content

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await remove_content(
            object_type="fixture", object_id=1,
            if_filter="PresetType 1", confirm_destructive=True
        )
        data = json.loads(result)

        assert "if PresetType 1" in data["command_sent"]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_remove_effect(self, mock_get_client):
        """Test removing an effect."""
        from src.server import remove_content

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await remove_content(
            object_type="effect", object_id=1, confirm_destructive=True
        )
        data = json.loads(result)

        assert "remove" in data["command_sent"].lower()
        assert "effect" in data["command_sent"].lower()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_remove_preset_type(self, mock_get_client):
        """Test removing a preset type."""
        from src.server import remove_content

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await remove_content(
            object_type="presettype", object_id="position",
            confirm_destructive=True
        )
        data = json.loads(result)

        assert "remove" in data["command_sent"].lower()
        assert "presettype" in data["command_sent"].lower()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_remove_generic(self, mock_get_client):
        """Test generic remove."""
        from src.server import remove_content

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await remove_content(
            object_type="cue", object_id=1, confirm_destructive=True
        )
        data = json.loads(result)

        assert "remove" in data["command_sent"].lower()


class TestStoreObjectTool:
    """Tests for the store_object MCP tool."""

    @pytest.mark.asyncio
    async def test_blocked_without_confirm(self):
        """Test that store is blocked without confirmation."""
        from src.server import store_object

        result = await store_object(object_type="macro", object_id=5)
        data = json.loads(result)

        assert data["blocked"] is True

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_store_macro(self, mock_get_client):
        """Test storing a macro."""
        from src.server import store_object

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await store_object(
            object_type="macro", object_id=5, confirm_destructive=True
        )
        data = json.loads(result)

        assert data["command_sent"] == "store macro 5"
        assert data["blocked"] is False

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_store_with_name(self, mock_get_client):
        """Test storing with a name."""
        from src.server import store_object

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await store_object(
            object_type="effect", object_id=1, name="Rainbow",
            confirm_destructive=True
        )
        data = json.loads(result)

        assert "effect" in data["command_sent"].lower()
        assert "Rainbow" in data["command_sent"]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_store_with_merge(self, mock_get_client):
        """Test storing with merge option."""
        from src.server import store_object

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await store_object(
            object_type="sequence", object_id=3, merge=True,
            confirm_destructive=True
        )
        data = json.loads(result)

        assert "/merge" in data["command_sent"]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_store_with_overwrite(self, mock_get_client):
        """Test storing with overwrite option."""
        from src.server import store_object

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client

        result = await store_object(
            object_type="sequence", object_id=3, overwrite=True,
            confirm_destructive=True
        )
        data = json.loads(result)

        assert "/overwrite" in data["command_sent"]


class TestSearchCodebaseTool:
    """Tests for the search_codebase MCP tool (tool #29)."""

    @pytest.mark.asyncio
    @patch("pathlib.Path.exists", return_value=False)
    async def test_missing_db_returns_error(self, _mock_exists):
        """Returns an error JSON when the RAG index has not been built."""
        from src.server import search_codebase

        result = await search_codebase(query="navigate")
        data = json.loads(result)

        assert "error" in data
        assert "rag_ingest" in data["error"]

    @pytest.mark.asyncio
    @patch("pathlib.Path.exists", return_value=True)
    @patch("rag.retrieve.query.rag_query")
    async def test_text_search_returns_hits(self, mock_rag_query, _mock_exists):
        """Returns formatted hits from the RAG index using text search."""
        from rag.types import RagHit
        from src.server import search_codebase

        mock_rag_query.return_value = [
            RagHit(
                chunk_id="c1", path="src/navigation.py", kind="source",
                start_line=1, end_line=15, score=1.0, text="def navigate(): ..."
            )
        ]

        result = await search_codebase(query="navigate", top_k=5)
        hits = json.loads(result)

        assert len(hits) == 1
        assert hits[0]["path"] == "src/navigation.py"
        assert hits[0]["kind"] == "source"
        assert hits[0]["lines"] == "1-15"
        assert hits[0]["score"] == 1.0
        assert "navigate" in hits[0]["text"]

    @pytest.mark.asyncio
    @patch("pathlib.Path.exists", return_value=True)
    @patch("rag.retrieve.query.rag_query")
    async def test_kind_filter(self, mock_rag_query, _mock_exists):
        """Filters results to the requested kind."""
        from rag.types import RagHit
        from src.server import search_codebase

        mock_rag_query.return_value = [
            RagHit(chunk_id="c1", path="src/nav.py", kind="source",
                   start_line=1, end_line=5, score=1.0, text="source chunk"),
            RagHit(chunk_id="c2", path="tests/test_nav.py", kind="test",
                   start_line=1, end_line=5, score=1.0, text="test chunk"),
        ]

        result = await search_codebase(query="navigate", kind="source")
        hits = json.loads(result)

        assert len(hits) == 1
        assert hits[0]["kind"] == "source"


# ============================================================
# Tests for New Tools 30–44
# ============================================================


class TestSetExecutorLevelTool:
    """Tests for the set_executor_level MCP tool (tool #30)."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_set_executor_level_basic(self, mock_get_client):
        """Test setting executor level to a valid value."""
        from src.server import set_executor_level

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await set_executor_level(executor_id=1, level=75.0)
        data = json.loads(result)

        assert "command_sent" in data
        assert data["risk_tier"] == "SAFE_WRITE"
        mock_client.send_command_with_response.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_set_executor_level_with_page(self, mock_get_client):
        """Test setting executor level with page qualifier."""
        from src.server import set_executor_level

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await set_executor_level(executor_id=5, level=50.0, page=2)
        data = json.loads(result)

        assert "2" in data["command_sent"]
        assert "5" in data["command_sent"]

    @pytest.mark.asyncio
    async def test_set_executor_level_invalid_level_high(self):
        """Test that level > 100 returns an error."""
        from src.server import set_executor_level

        result = await set_executor_level(executor_id=1, level=101.0)
        data = json.loads(result)

        assert "error" in data

    @pytest.mark.asyncio
    async def test_set_executor_level_invalid_level_negative(self):
        """Test that level < 0 returns an error."""
        from src.server import set_executor_level

        result = await set_executor_level(executor_id=1, level=-1.0)
        data = json.loads(result)

        assert "error" in data

    @pytest.mark.asyncio
    async def test_set_executor_level_invalid_executor_id(self):
        """Test that executor_id < 1 returns an error."""
        from src.server import set_executor_level

        result = await set_executor_level(executor_id=0, level=50.0)
        data = json.loads(result)

        assert "error" in data


class TestNavigatePageTool:
    """Tests for the navigate_page MCP tool (tool #31)."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_navigate_page_goto(self, mock_get_client):
        """Test navigating to an absolute page."""
        from src.server import navigate_page

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await navigate_page(action="goto", page_number=3)
        data = json.loads(result)

        assert data["command_sent"] == "page 3"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_navigate_page_next(self, mock_get_client):
        """Test navigating to the next page."""
        from src.server import navigate_page

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await navigate_page(action="next")
        data = json.loads(result)

        assert "page +" in data["command_sent"]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_navigate_page_previous(self, mock_get_client):
        """Test navigating to the previous page."""
        from src.server import navigate_page

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await navigate_page(action="previous")
        data = json.loads(result)

        assert "page -" in data["command_sent"]

    @pytest.mark.asyncio
    async def test_navigate_page_goto_missing_page_number(self):
        """Test that goto without page_number returns an error."""
        from src.server import navigate_page

        result = await navigate_page(action="goto")
        data = json.loads(result)

        assert "error" in data

    @pytest.mark.asyncio
    async def test_navigate_page_invalid_action(self):
        """Test that invalid action returns an error."""
        from src.server import navigate_page

        result = await navigate_page(action="jump")
        data = json.loads(result)

        assert "error" in data

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_navigate_page_next_with_steps(self, mock_get_client):
        """Test navigating forward by multiple steps."""
        from src.server import navigate_page

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await navigate_page(action="next", steps=3)
        data = json.loads(result)

        assert "3" in data["command_sent"]


class TestModifySelectionTool:
    """Tests for the modify_selection MCP tool (tool #32)."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_modify_selection_add(self, mock_get_client):
        """Test adding a fixture to the selection."""
        from src.server import modify_selection

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await modify_selection(action="add", fixture_ids=[5])
        data = json.loads(result)

        assert "+ 5" in data["command_sent"]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_modify_selection_remove(self, mock_get_client):
        """Test removing a fixture from the selection."""
        from src.server import modify_selection

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await modify_selection(action="remove", fixture_ids=[3])
        data = json.loads(result)

        assert "- 3" in data["command_sent"]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_modify_selection_clear(self, mock_get_client):
        """Test clearing the selection."""
        from src.server import modify_selection

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await modify_selection(action="clear")
        data = json.loads(result)

        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_modify_selection_replace(self, mock_get_client):
        """Test replacing the selection."""
        from src.server import modify_selection

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await modify_selection(action="replace", fixture_ids=[1, 5])
        data = json.loads(result)

        assert "command_sent" in data

    @pytest.mark.asyncio
    async def test_modify_selection_missing_fixtures(self):
        """Test that non-clear action without fixture_ids returns an error."""
        from src.server import modify_selection

        result = await modify_selection(action="add")
        data = json.loads(result)

        assert "error" in data

    @pytest.mark.asyncio
    async def test_modify_selection_invalid_action(self):
        """Test that invalid action returns an error."""
        from src.server import modify_selection

        result = await modify_selection(action="toggle", fixture_ids=[1])
        data = json.loads(result)

        assert "error" in data


class TestAdjustValueRelativeTool:
    """Tests for the adjust_value_relative MCP tool (tool #33)."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_adjust_value_positive_delta(self, mock_get_client):
        """Test nudging a value up by a positive delta."""
        from src.server import adjust_value_relative

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_client.send_command = AsyncMock()
        mock_get_client.return_value = mock_client

        result = await adjust_value_relative(delta=10.0)
        data = json.loads(result)

        assert "at + 10" in data["commands_sent"][-1]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_adjust_value_negative_delta(self, mock_get_client):
        """Test nudging a value down by a negative delta."""
        from src.server import adjust_value_relative

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_client.send_command = AsyncMock()
        mock_get_client.return_value = mock_client

        result = await adjust_value_relative(delta=-5.0)
        data = json.loads(result)

        assert "at - 5" in data["commands_sent"][-1]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_adjust_value_with_fixture_and_attribute(self, mock_get_client):
        """Test nudging with fixture selection and attribute targeting."""
        from src.server import adjust_value_relative

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_client.send_command = AsyncMock()
        mock_get_client.return_value = mock_client

        result = await adjust_value_relative(
            delta=10.0, fixture_ids=[1], attribute_name="Pan"
        )
        data = json.loads(result)

        assert len(data["commands_sent"]) == 3

    @pytest.mark.asyncio
    async def test_adjust_value_zero_delta(self):
        """Test that delta=0 returns an error."""
        from src.server import adjust_value_relative

        result = await adjust_value_relative(delta=0)
        data = json.loads(result)

        assert "error" in data


class TestControlTimecodeTool:
    """Tests for the control_timecode MCP tool (tool #34)."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_control_timecode_start(self, mock_get_client):
        """Test starting a timecode show."""
        from src.server import control_timecode

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await control_timecode(action="start", timecode_id=1)
        data = json.loads(result)

        assert data["command_sent"] == "go timecode 1"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_control_timecode_stop(self, mock_get_client):
        """Test stopping a timecode show."""
        from src.server import control_timecode

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await control_timecode(action="stop", timecode_id=2)
        data = json.loads(result)

        assert data["command_sent"] == "off timecode 2"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_control_timecode_goto(self, mock_get_client):
        """Test jumping to a timecode position."""
        from src.server import control_timecode

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await control_timecode(
            action="goto", timecode_id=1, timecode_position="00:01:30:00"
        )
        data = json.loads(result)

        assert "00:01:30:00" in data["command_sent"]

    @pytest.mark.asyncio
    async def test_control_timecode_goto_missing_position(self):
        """Test that goto without timecode_position returns an error."""
        from src.server import control_timecode

        result = await control_timecode(action="goto", timecode_id=1)
        data = json.loads(result)

        assert "error" in data

    @pytest.mark.asyncio
    async def test_control_timecode_invalid_action(self):
        """Test that invalid action returns an error."""
        from src.server import control_timecode

        result = await control_timecode(action="pause", timecode_id=1)
        data = json.loads(result)

        assert "error" in data


class TestControlTimerTool:
    """Tests for the control_timer MCP tool (tool #35)."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_control_timer_start(self, mock_get_client):
        """Test starting a timer."""
        from src.server import control_timer

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await control_timer(action="start", timer_id=1)
        data = json.loads(result)

        assert data["command_sent"] == "go timer 1"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_control_timer_stop(self, mock_get_client):
        """Test stopping a timer."""
        from src.server import control_timer

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await control_timer(action="stop", timer_id=3)
        data = json.loads(result)

        assert data["command_sent"] == "off timer 3"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_control_timer_reset(self, mock_get_client):
        """Test resetting a timer."""
        from src.server import control_timer

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await control_timer(action="reset", timer_id=2)
        data = json.loads(result)

        assert data["command_sent"] == "goto timer 2"

    @pytest.mark.asyncio
    async def test_control_timer_invalid_id(self):
        """Test that timer_id < 1 returns an error."""
        from src.server import control_timer

        result = await control_timer(action="start", timer_id=0)
        data = json.loads(result)

        assert "error" in data

    @pytest.mark.asyncio
    async def test_control_timer_invalid_action(self):
        """Test that invalid action returns an error."""
        from src.server import control_timer

        result = await control_timer(action="pause", timer_id=1)
        data = json.loads(result)

        assert "error" in data


class TestUndoLastActionTool:
    """Tests for the undo_last_action MCP tool (tool #36)."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_undo_once(self, mock_get_client):
        """Test undoing a single action."""
        from src.server import undo_last_action

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await undo_last_action(count=1)
        data = json.loads(result)

        assert data["count"] == 1
        assert data["commands_sent"] == ["oops"]
        mock_client.send_command_with_response.assert_called_once_with("oops")

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_undo_multiple(self, mock_get_client):
        """Test undoing multiple actions."""
        from src.server import undo_last_action

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await undo_last_action(count=3)
        data = json.loads(result)

        assert data["count"] == 3
        assert len(data["commands_sent"]) == 3
        assert mock_client.send_command_with_response.call_count == 3

    @pytest.mark.asyncio
    async def test_undo_count_too_high(self):
        """Test that count > 20 returns an error."""
        from src.server import undo_last_action

        result = await undo_last_action(count=21)
        data = json.loads(result)

        assert "error" in data

    @pytest.mark.asyncio
    async def test_undo_count_zero(self):
        """Test that count=0 returns an error."""
        from src.server import undo_last_action

        result = await undo_last_action(count=0)
        data = json.loads(result)

        assert "error" in data

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_undo_risk_tier(self, mock_get_client):
        """Test that risk tier is SAFE_WRITE."""
        from src.server import undo_last_action

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await undo_last_action()
        data = json.loads(result)

        assert data["risk_tier"] == "SAFE_WRITE"


class TestToggleConsoleModeTool:
    """Tests for the toggle_console_mode MCP tool (tool #37)."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_toggle_blind(self, mock_get_client):
        """Test toggling blind mode."""
        from src.server import toggle_console_mode

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await toggle_console_mode(mode="blind")
        data = json.loads(result)

        assert data["command_sent"] == "blind"
        assert data["mode"] == "blind"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_toggle_highlight(self, mock_get_client):
        """Test toggling highlight mode."""
        from src.server import toggle_console_mode

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await toggle_console_mode(mode="highlight")
        data = json.loads(result)

        assert data["command_sent"] == "highlight"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_toggle_freeze(self, mock_get_client):
        """Test toggling freeze mode."""
        from src.server import toggle_console_mode

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await toggle_console_mode(mode="freeze")
        data = json.loads(result)

        assert data["command_sent"] == "freeze"

    @pytest.mark.asyncio
    async def test_toggle_invalid_mode(self):
        """Test that invalid mode returns an error."""
        from src.server import toggle_console_mode

        result = await toggle_console_mode(mode="blackout")
        data = json.loads(result)

        assert "error" in data


class TestUpdateCueDataTool:
    """Tests for the update_cue_data MCP tool (tool #38)."""

    @pytest.mark.asyncio
    async def test_blocked_without_confirm(self):
        """Test that update is blocked without confirmation."""
        from src.server import update_cue_data

        result = await update_cue_data()
        data = json.loads(result)

        assert data["blocked"] is True
        assert data["risk_tier"] == "DESTRUCTIVE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_update_active_cue(self, mock_get_client):
        """Test updating the currently active cue."""
        from src.server import update_cue_data

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await update_cue_data(confirm_destructive=True)
        data = json.loads(result)

        assert data["command_sent"] == "update"
        assert data["risk_tier"] == "DESTRUCTIVE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_update_specific_cue(self, mock_get_client):
        """Test updating a specific cue."""
        from src.server import update_cue_data

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await update_cue_data(confirm_destructive=True, cue_id=5.0)
        data = json.loads(result)

        assert "cue 5" in data["command_sent"]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_update_with_merge(self, mock_get_client):
        """Test updating with merge option."""
        from src.server import update_cue_data

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await update_cue_data(
            confirm_destructive=True, cue_id=3.0, merge=True
        )
        data = json.loads(result)

        assert "/merge" in data["command_sent"]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_update_with_sequence_scope(self, mock_get_client):
        """Test updating with sequence scoping."""
        from src.server import update_cue_data

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await update_cue_data(
            confirm_destructive=True, cue_id=2.0, sequence_id=1
        )
        data = json.loads(result)

        assert "sequence 1" in data["command_sent"]


class TestSetCueTimingTool:
    """Tests for the set_cue_timing MCP tool (tool #39)."""

    @pytest.mark.asyncio
    async def test_blocked_without_confirm(self):
        """Test that set_cue_timing is blocked without confirmation."""
        from src.server import set_cue_timing

        result = await set_cue_timing(cue_id=1, fade_time=3.0)
        data = json.loads(result)

        assert data["blocked"] is True

    @pytest.mark.asyncio
    async def test_error_no_times_provided(self):
        """Test that omitting both fade_time and delay_time returns an error."""
        from src.server import set_cue_timing

        result = await set_cue_timing(cue_id=1, confirm_destructive=True)
        data = json.loads(result)

        assert "error" in data

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_set_fade_time_only(self, mock_get_client):
        """Test setting fade time only."""
        from src.server import set_cue_timing

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await set_cue_timing(
            cue_id=3, confirm_destructive=True, fade_time=5.0
        )
        data = json.loads(result)

        assert len(data["commands_sent"]) == 1
        assert "fade" in data["commands_sent"][0]
        assert "3" in data["commands_sent"][0]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_set_delay_time_only(self, mock_get_client):
        """Test setting delay time only."""
        from src.server import set_cue_timing

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await set_cue_timing(
            cue_id=4, confirm_destructive=True, delay_time=2.0
        )
        data = json.loads(result)

        assert len(data["commands_sent"]) == 1
        assert "delay" in data["commands_sent"][0]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_set_both_fade_and_delay(self, mock_get_client):
        """Test setting both fade and delay times."""
        from src.server import set_cue_timing

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await set_cue_timing(
            cue_id=5, confirm_destructive=True, fade_time=3.0, delay_time=1.0
        )
        data = json.loads(result)

        assert len(data["commands_sent"]) == 2
        assert data["risk_tier"] == "DESTRUCTIVE"


class TestSelectFixturesByGroupTool:
    """Tests for the select_fixtures_by_group MCP tool (tool #40)."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_select_group_replace(self, mock_get_client):
        """Test selecting a group (replacing current selection)."""
        from src.server import select_fixtures_by_group

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await select_fixtures_by_group(group_id=2)
        data = json.loads(result)

        assert data["command_sent"] == "group 2"
        assert data["group_id"] == 2

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_select_group_append(self, mock_get_client):
        """Test appending a group to the current selection."""
        from src.server import select_fixtures_by_group

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await select_fixtures_by_group(group_id=3, append=True)
        data = json.loads(result)

        assert data["command_sent"] == "+ group 3"

    @pytest.mark.asyncio
    async def test_select_group_invalid_id(self):
        """Test that group_id < 1 returns an error."""
        from src.server import select_fixtures_by_group

        result = await select_fixtures_by_group(group_id=0)
        data = json.loads(result)

        assert "error" in data

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_select_group_risk_tier(self, mock_get_client):
        """Test that risk tier is SAFE_WRITE."""
        from src.server import select_fixtures_by_group

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await select_fixtures_by_group(group_id=1)
        data = json.loads(result)

        assert data["risk_tier"] == "SAFE_WRITE"


class TestControlExecutorTool:
    """Tests for the control_executor MCP tool (tool #41)."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_control_executor_on(self, mock_get_client):
        """Test turning an executor on."""
        from src.server import control_executor

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await control_executor(action="on", executor_id=5)
        data = json.loads(result)

        assert data["risk_tier"] == "SAFE_WRITE"
        assert "on" in data["command_sent"].lower() or "5" in data["command_sent"]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_control_executor_off(self, mock_get_client):
        """Test turning an executor off."""
        from src.server import control_executor

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await control_executor(action="off", executor_id=5)
        data = json.loads(result)

        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_control_executor_flash(self, mock_get_client):
        """Test flashing an executor."""
        from src.server import control_executor

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await control_executor(action="flash", executor_id=3)
        data = json.loads(result)

        assert "command_sent" in data

    @pytest.mark.asyncio
    async def test_control_executor_set_speed_blocked(self):
        """Test that set_speed is blocked without confirmation."""
        from src.server import control_executor

        result = await control_executor(
            action="set_speed", executor_id=1, speed_value=120.0
        )
        data = json.loads(result)

        assert data["blocked"] is True
        assert data["risk_tier"] == "DESTRUCTIVE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_control_executor_set_speed_confirmed(self, mock_get_client):
        """Test setting executor speed with confirmation."""
        from src.server import control_executor

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await control_executor(
            action="set_speed", executor_id=1, speed_value=120.0,
            confirm_destructive=True
        )
        data = json.loads(result)

        assert "120" in data["command_sent"]
        assert data["risk_tier"] == "DESTRUCTIVE"

    @pytest.mark.asyncio
    async def test_control_executor_invalid_action(self):
        """Test that invalid action returns an error."""
        from src.server import control_executor

        result = await control_executor(action="pause", executor_id=1)
        data = json.loads(result)

        assert "error" in data

    @pytest.mark.asyncio
    async def test_control_executor_invalid_id(self):
        """Test that executor_id < 1 returns an error."""
        from src.server import control_executor

        result = await control_executor(action="on", executor_id=0)
        data = json.loads(result)

        assert "error" in data


class TestGetExecutorStatusTool:
    """Tests for the get_executor_status MCP tool (tool #42)."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_get_status_all_executors(self, mock_get_client):
        """Test listing all executors."""
        from src.server import get_executor_status

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Executor list")
        mock_get_client.return_value = mock_client

        result = await get_executor_status()
        data = json.loads(result)

        assert data["command_sent"] == "list executor"
        assert data["risk_tier"] == "SAFE_READ"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_get_status_specific_executor(self, mock_get_client):
        """Test listing a specific executor."""
        from src.server import get_executor_status

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Executor 5")
        mock_get_client.return_value = mock_client

        result = await get_executor_status(executor_id=5)
        data = json.loads(result)

        assert data["command_sent"] == "list executor 5"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_get_status_with_page(self, mock_get_client):
        """Test listing a page-qualified executor."""
        from src.server import get_executor_status

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Executor 2.5")
        mock_get_client.return_value = mock_client

        result = await get_executor_status(executor_id=5, page=2)
        data = json.loads(result)

        assert data["command_sent"] == "list executor 2.5"


class TestStoreTimecodeEventTool:
    """Tests for the store_timecode_event MCP tool (tool #43)."""

    @pytest.mark.asyncio
    async def test_blocked_without_confirm(self):
        """Test that store_timecode_event is blocked without confirmation."""
        from src.server import store_timecode_event

        result = await store_timecode_event(
            timecode_id=1, cue_id=5.0, sequence_id=1
        )
        data = json.loads(result)

        assert data["blocked"] is True
        assert data["risk_tier"] == "DESTRUCTIVE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_store_timecode_without_position(self, mock_get_client):
        """Test storing a timecode event without a position."""
        from src.server import store_timecode_event

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await store_timecode_event(
            timecode_id=2, cue_id=3.0, sequence_id=1, confirm_destructive=True
        )
        data = json.loads(result)

        assert data["command_sent"] == "store timecode 2"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_store_timecode_with_position(self, mock_get_client):
        """Test storing a timecode event at a specific position."""
        from src.server import store_timecode_event

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await store_timecode_event(
            timecode_id=1, cue_id=5.0, sequence_id=2,
            confirm_destructive=True, timecode_position="00:01:00:00"
        )
        data = json.loads(result)

        assert "assign timecode 1" in data["command_sent"]
        assert "00:01:00:00" in data["command_sent"]
        assert "sequence 2" in data["command_sent"]


class TestSetSequencePropertyTool:
    """Tests for the set_sequence_property MCP tool (tool #44)."""

    @pytest.mark.asyncio
    async def test_blocked_without_confirm(self):
        """Test that set_sequence_property is blocked without confirmation."""
        from src.server import set_sequence_property

        result = await set_sequence_property(
            sequence_id=1, property_name="loop", value="on"
        )
        data = json.loads(result)

        assert data["blocked"] is True
        assert data["risk_tier"] == "DESTRUCTIVE"

    @pytest.mark.asyncio
    @patch("src.server.set_property", new_callable=AsyncMock)
    @patch("src.server.get_client")
    async def test_set_loop_property(self, mock_get_client, mock_set_property):
        """Test setting the loop property on a sequence."""
        from src.server import set_sequence_property

        mock_set_property.return_value = {"ok": True}

        result = await set_sequence_property(
            sequence_id=1, property_name="loop", value="on",
            confirm_destructive=True
        )
        data = json.loads(result)

        assert data["sequence_id"] == 1
        assert data["property"] == "loop"
        assert data["value"] == "on"
        assert data["risk_tier"] == "DESTRUCTIVE"
        mock_set_property.assert_called_once_with(
            path="sequence 1", prop="loop", value="on"
        )

    @pytest.mark.asyncio
    @patch("src.server.set_property", new_callable=AsyncMock)
    @patch("src.server.get_client")
    async def test_set_tracking_property(self, mock_get_client, mock_set_property):
        """Test setting the tracking property on a sequence."""
        from src.server import set_sequence_property

        mock_set_property.return_value = {"ok": True}

        result = await set_sequence_property(
            sequence_id=3, property_name="tracking", value="off",
            confirm_destructive=True
        )
        data = json.loads(result)

        assert data["sequence_id"] == 3
        mock_set_property.assert_called_once_with(
            path="sequence 3", prop="tracking", value="off"
        )


# ============================================================
# Tests for New Tools 45-52 -- Quick Start Guide Gap-Fill
# ============================================================


class TestSaveShowTool:
    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_save_show_save(self, mock_get_client):
        from src.server import save_show
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client
        result = await save_show(action="save")
        data = json.loads(result)
        assert data["command_sent"] == "save"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_save_show_saveas(self, mock_get_client):
        from src.server import save_show
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client
        result = await save_show(action="saveas", show_name="my_show")
        data = json.loads(result)
        assert data["command_sent"] == 'saveas "my_show"'

    @pytest.mark.asyncio
    async def test_save_show_saveas_missing_name(self):
        from src.server import save_show
        result = await save_show(action="saveas")
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_save_show_invalid_action(self):
        from src.server import save_show
        result = await save_show(action="delete")
        data = json.loads(result)
        assert "error" in data


class TestStoreCueWithTimingTool:
    @pytest.mark.asyncio
    async def test_store_cue_with_timing_blocked(self):
        from src.server import store_cue_with_timing
        result = await store_cue_with_timing(cue_id=1)
        data = json.loads(result)
        assert data["blocked"] is True
        assert data["risk_tier"] == "DESTRUCTIVE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_store_cue_with_timing_fade(self, mock_get_client):
        from src.server import store_cue_with_timing
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client
        result = await store_cue_with_timing(cue_id=2, confirm_destructive=True, fade_time=15.0)
        data = json.loads(result)
        assert "store cue 2" in data["command_sent"]
        assert "time 15.0" in data["command_sent"]
        assert data["risk_tier"] == "DESTRUCTIVE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_store_cue_with_timing_both_times(self, mock_get_client):
        from src.server import store_cue_with_timing
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client
        result = await store_cue_with_timing(cue_id=3, confirm_destructive=True, fade_time=20.0, out_time=10.0)
        data = json.loads(result)
        assert "time 20.0" in data["command_sent"]
        assert "outtime 10.0" in data["command_sent"]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_store_cue_with_timing_merge(self, mock_get_client):
        from src.server import store_cue_with_timing
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client
        result = await store_cue_with_timing(cue_id=1, confirm_destructive=True, fade_time=5.0, merge=True)
        data = json.loads(result)
        assert "/merge" in data["command_sent"]


class TestSelectExecutorTool:
    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_select_executor_basic(self, mock_get_client):
        from src.server import select_executor
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client
        result = await select_executor(executor_id=3)
        data = json.loads(result)
        assert data["command_sent"] == "select executor 3"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_select_executor_with_page(self, mock_get_client):
        from src.server import select_executor
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client
        result = await select_executor(executor_id=5, page=2)
        data = json.loads(result)
        assert data["command_sent"] == "select executor 2.5"


class TestRemoveFromProgrammerTool:
    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_remove_channel(self, mock_get_client):
        from src.server import remove_from_programmer
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client
        result = await remove_from_programmer(object_type="channel", object_id=5)
        data = json.loads(result)
        assert data["command_sent"] == "off channel 5"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_remove_channel_range(self, mock_get_client):
        from src.server import remove_from_programmer
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client
        result = await remove_from_programmer(object_type="channel", object_id=1, end_id=10)
        data = json.loads(result)
        assert data["command_sent"] == "off channel 1 thru 10"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_remove_fixture(self, mock_get_client):
        from src.server import remove_from_programmer
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client
        result = await remove_from_programmer(object_type="fixture", object_id=111)
        data = json.loads(result)
        assert data["command_sent"] == "off fixture 111"

    @pytest.mark.asyncio
    async def test_remove_invalid_type(self):
        from src.server import remove_from_programmer
        result = await remove_from_programmer(object_type="preset", object_id=1)
        data = json.loads(result)
        assert "error" in data


class TestAssignCueTriggerTool:
    @pytest.mark.asyncio
    async def test_assign_cue_trigger_blocked(self):
        from src.server import assign_cue_trigger
        result = await assign_cue_trigger(cue_id=3, sequence_id=1, trigger_type="follow")
        data = json.loads(result)
        assert data["blocked"] is True
        assert data["risk_tier"] == "DESTRUCTIVE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_assign_cue_trigger_follow(self, mock_get_client):
        from src.server import assign_cue_trigger
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client
        result = await assign_cue_trigger(cue_id=3, sequence_id=1, trigger_type="follow", confirm_destructive=True)
        data = json.loads(result)
        assert data["command_sent"] == "assign trigger follow cue 3 sequence 1"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_assign_cue_trigger_bpm(self, mock_get_client):
        from src.server import assign_cue_trigger
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client
        result = await assign_cue_trigger(cue_id=4, sequence_id=2, trigger_type="bpm", trigger_value=120.0, confirm_destructive=True)
        data = json.loads(result)
        assert data["command_sent"] == "assign trigger bpm 120.0 cue 4 sequence 2"

    @pytest.mark.asyncio
    async def test_assign_cue_trigger_bpm_missing_value(self):
        from src.server import assign_cue_trigger
        result = await assign_cue_trigger(cue_id=1, sequence_id=1, trigger_type="bpm", confirm_destructive=True)
        data = json.loads(result)
        assert "error" in data


class TestAssignExecutorPropertyTool:
    @pytest.mark.asyncio
    async def test_assign_executor_property_blocked(self):
        from src.server import assign_executor_property
        result = await assign_executor_property(property_name="width", executor_id=1, value=2)
        data = json.loads(result)
        assert data["blocked"] is True

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_assign_executor_width(self, mock_get_client):
        from src.server import assign_executor_property
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client
        result = await assign_executor_property(property_name="width", executor_id=1, value=2, confirm_destructive=True)
        data = json.loads(result)
        assert data["command_sent"] == "assign executor 1 /width=2"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_assign_sequence_priority(self, mock_get_client):
        from src.server import assign_executor_property
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client
        result = await assign_executor_property(property_name="priority", sequence_id=1, value="high", confirm_destructive=True)
        data = json.loads(result)
        assert data["command_sent"] == "assign priority high sequence 1"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_assign_executor_rate(self, mock_get_client):
        from src.server import assign_executor_property
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client
        result = await assign_executor_property(property_name="rate", executor_id=3, confirm_destructive=True)
        data = json.loads(result)
        assert data["command_sent"] == "assign rate executor 3"


class TestIfFilterTool:
    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_if_filter_active(self, mock_get_client):
        from src.server import if_filter
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client
        result = await if_filter(filter_type="active")
        data = json.loads(result)
        assert data["command_sent"] == "if"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_if_filter_fixture(self, mock_get_client):
        from src.server import if_filter
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client
        result = await if_filter(filter_type="fixture", fixture_id=5)
        data = json.loads(result)
        assert data["command_sent"] == "if fixture 5"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_if_filter_attribute(self, mock_get_client):
        from src.server import if_filter
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client
        result = await if_filter(filter_type="attribute", fixture_id=5, attribute_name="Pan")
        data = json.loads(result)
        assert data["command_sent"] == 'if fixture 5 attribute "Pan"'

    @pytest.mark.asyncio
    async def test_if_filter_invalid_type(self):
        from src.server import if_filter
        result = await if_filter(filter_type="group")
        data = json.loads(result)
        assert "error" in data


class TestSaveRecallViewTool:
    @pytest.mark.asyncio
    async def test_save_recall_view_store_blocked(self):
        from src.server import save_recall_view
        result = await save_recall_view(action="store", view_id=1)
        data = json.loads(result)
        assert data["blocked"] is True
        assert data["risk_tier"] == "DESTRUCTIVE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_save_recall_view_store(self, mock_get_client):
        from src.server import save_recall_view
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client
        result = await save_recall_view(action="store", view_id=1, screen_id=2, confirm_destructive=True)
        data = json.loads(result)
        assert data["command_sent"] == "store ViewButton 2.1"
        assert data["risk_tier"] == "DESTRUCTIVE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_save_recall_view_recall(self, mock_get_client):
        from src.server import save_recall_view
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client
        result = await save_recall_view(action="recall", view_id=3)
        data = json.loads(result)
        assert data["command_sent"] == "ViewButton 1.3"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_save_recall_view_label(self, mock_get_client):
        from src.server import save_recall_view
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client
        result = await save_recall_view(action="label", view_id=2, view_name="My View")
        data = json.loads(result)
        assert data["command_sent"] == 'label ViewButton 1.2 "My View"'

    @pytest.mark.asyncio
    async def test_save_recall_view_invalid_view_id(self):
        from src.server import save_recall_view
        result = await save_recall_view(action="recall", view_id=11)
        data = json.loads(result)
        assert "error" in data



    # ============================================================
    # Tests for Tools 53-54 -- Import / Export
    # ============================================================


class TestExportObjectsTool:
    @pytest.mark.asyncio
    async def test_export_blocked(self):
        from src.server import export_objects
        result = await export_objects(object_type="Group", object_id="1", filename="test")
        data = json.loads(result)
        assert data["blocked"] is True
        assert data["risk_tier"] == "DESTRUCTIVE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_export_basic(self, mock_get_client):
        from src.server import export_objects
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client
        result = await export_objects(object_type="Group", object_id="1", filename="my_groups", confirm_destructive=True)
        data = json.loads(result)
        assert data["command_sent"] == 'export Group 1 "my_groups" /noconfirm'
        assert data["risk_tier"] == "DESTRUCTIVE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_export_range(self, mock_get_client):
        from src.server import export_objects
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client
        result = await export_objects(object_type="Macro", object_id="1 thru 5", filename="macros", confirm_destructive=True)
        data = json.loads(result)
        assert data["command_sent"] == 'export Macro 1 thru 5 "macros" /noconfirm'

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_export_preset(self, mock_get_client):
        from src.server import export_objects
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client
        result = await export_objects(object_type="Preset", object_id="1.3", filename="dim3", confirm_destructive=True)
        data = json.loads(result)
        assert data["command_sent"] == 'export Preset 1.3 "dim3" /noconfirm'

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_export_with_style_csv(self, mock_get_client):
        from src.server import export_objects
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client
        result = await export_objects(object_type="Sequence", object_id="1", filename="seqs", style="csv", confirm_destructive=True)
        data = json.loads(result)
        assert "/style=csv" in data["command_sent"]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_export_with_overwrite(self, mock_get_client):
        from src.server import export_objects
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client
        result = await export_objects(object_type="Group", object_id="1", filename="grp", overwrite=True, confirm_destructive=True)
        data = json.loads(result)
        assert "/overwrite" in data["command_sent"]

    @pytest.mark.asyncio
    async def test_export_invalid_type(self):
        from src.server import export_objects
        result = await export_objects(object_type="Banana", object_id="1", filename="test", confirm_destructive=True)
        data = json.loads(result)
        assert "error" in data
        assert "Banana" in data["error"]

    @pytest.mark.asyncio
    async def test_export_invalid_style(self):
        from src.server import export_objects
        result = await export_objects(object_type="Group", object_id="1", filename="test", style="pdf", confirm_destructive=True)
        data = json.loads(result)
        assert "error" in data
        assert "style" in data["error"]


class TestImportObjectsTool:
    @pytest.mark.asyncio
    async def test_import_blocked(self):
        from src.server import import_objects
        result = await import_objects(filename="my_groups", destination_type="Group")
        data = json.loads(result)
        assert data["blocked"] is True
        assert data["risk_tier"] == "DESTRUCTIVE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_import_basic(self, mock_get_client):
        from src.server import import_objects
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="1 object(s) imported.")
        mock_get_client.return_value = mock_client
        result = await import_objects(filename="my_groups", destination_type="Group", destination_id="99", confirm_destructive=True)
        data = json.loads(result)
        assert data["command_sent"] == 'import "my_groups" at Group 99 /noconfirm'
        assert data["risk_tier"] == "DESTRUCTIVE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_import_no_id(self, mock_get_client):
        from src.server import import_objects
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client
        result = await import_objects(filename="macros", destination_type="Macro", confirm_destructive=True)
        data = json.loads(result)
        assert data["command_sent"] == 'import "macros" at Macro /noconfirm'

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_import_preset(self, mock_get_client):
        from src.server import import_objects
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client
        result = await import_objects(filename="preset_dimmer", destination_type="Preset", destination_id="1.99", confirm_destructive=True)
        data = json.loads(result)
        assert data["command_sent"] == 'import "preset_dimmer" at Preset 1.99 /noconfirm'

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_import_matricks(self, mock_get_client):
        from src.server import import_objects
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client
        result = await import_objects(filename="matricks_test", destination_type="MAtricks", destination_id="99", confirm_destructive=True)
        data = json.loads(result)
        assert data["command_sent"] == 'import "matricks_test" at MAtricks 99 /noconfirm'

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_import_with_quiet(self, mock_get_client):
        from src.server import import_objects
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Ok")
        mock_get_client.return_value = mock_client
        result = await import_objects(filename="show_backup", destination_type="Group", destination_id="10", quiet=True, confirm_destructive=True)
        data = json.loads(result)
        assert "/quiet" in data["command_sent"]

    @pytest.mark.asyncio
    async def test_import_invalid_type(self):
        from src.server import import_objects
        result = await import_objects(filename="test", destination_type="Banana", confirm_destructive=True)
        data = json.loads(result)
        assert "error" in data
        assert "Banana" in data["error"]

    @pytest.mark.asyncio
    async def test_import_screen_rejected(self):
        from src.server import import_objects
        result = await import_objects(filename="screen_test", destination_type="Screen", confirm_destructive=True)
        data = json.loads(result)
        assert "error" in data
