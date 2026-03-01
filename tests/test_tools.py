"""
MCP Tools Tests

Tests for high-level MCP tools functionality. These are tools that AI can call.
Uses mocks to simulate Telnet connections and avoid actual network calls.

The MCP tool functions are defined in src/server.py with @mcp.tool() decorators.
"""

import json

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


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

        result = await create_fixture_group(
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

        result = await create_fixture_group(
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

        result = await execute_sequence(sequence_id=1, action="go")

        mock_client.send_command.assert_called_once_with("go+ sequence 1")

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_execute_sequence_pause(self, mock_get_client):
        """Test pausing a sequence."""
        from src.server import execute_sequence

        mock_client = MagicMock()
        mock_client.send_command = AsyncMock()
        mock_get_client.return_value = mock_client

        result = await execute_sequence(sequence_id=1, action="pause")

        mock_client.send_command.assert_called_once_with("pause sequence 1")

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_execute_sequence_goto(self, mock_get_client):
        """Test jumping to a specific cue."""
        from src.server import execute_sequence

        mock_client = MagicMock()
        mock_client.send_command = AsyncMock()
        mock_get_client.return_value = mock_client

        result = await execute_sequence(sequence_id=1, action="goto", cue_id=5)

        mock_client.send_command.assert_called_once_with("goto cue 5 sequence 1")


class TestSendRawCommandTool:
    """Tests for the send raw command MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_send_safe_write_command(self, mock_get_client):
        """Test sending a SAFE_WRITE command (selfix) — should be allowed."""
        from src.server import send_raw_command
        import json

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
        from src.server import send_raw_command
        import json

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
        from src.server import send_raw_command
        import json

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
        from src.server import send_raw_command
        import json

        result = await send_raw_command("list\r\ndelete cue 1")
        data = json.loads(result)

        assert data["blocked"] is True
        assert "line breaks" in data["error"]
        assert data["command_sent"] is None

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_safe_read_always_allowed(self, mock_get_client):
        """Test that SAFE_READ commands (list, info, cd) are always allowed."""
        from src.server import send_raw_command
        import json

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

        assert data["commands_sent"] == ["call preset 2.3"]
        mock_client.send_command_with_response.assert_called_once_with("call preset 2.3")

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
        assert calls[1][0][0] == "call preset 3.1"
        assert data["commands_sent"] == ["group 2", "call preset 3.1"]

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
        data = json.loads(result)

        calls = mock_client.send_command_with_response.call_args_list
        assert calls[0][0][0] == "selfix fixture 1 thru 10"
        assert calls[1][0][0] == "call preset 4.5"

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
        data = json.loads(result)

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
        from src.server import set_node_property
        from src.navigation import SetPropertyResult

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
        from src.server import set_node_property
        from src.navigation import SetPropertyResult

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
