"""
New MCP Tool Tests — swop/top/stomp, load_cue, cut_paste_object,
clone_object, fix_locate_fixture, manipulate_selection, block_unblock_cue.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestControlExecutorExtendedActions:
    """Tests for new swop, top, stomp actions on control_executor."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_control_executor_swop(self, mock_get_client):
        from src.server import control_executor

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await control_executor(action="swop", executor_id=3)
        data = json.loads(result)

        assert data["risk_tier"] == "SAFE_WRITE"
        assert data["command_sent"] == "swop executor 3"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_control_executor_top(self, mock_get_client):
        from src.server import control_executor

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await control_executor(action="top", executor_id=3)
        data = json.loads(result)

        assert data["risk_tier"] == "SAFE_WRITE"
        assert data["command_sent"] == "top executor 3"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_control_executor_stomp(self, mock_get_client):
        from src.server import control_executor

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await control_executor(action="stomp", executor_id=3)
        data = json.loads(result)

        assert data["risk_tier"] == "SAFE_WRITE"
        assert data["command_sent"] == "stomp executor 3"

    @pytest.mark.asyncio
    async def test_control_executor_invalid_action_still_rejected(self):
        from src.server import control_executor

        result = await control_executor(action="pause", executor_id=1)
        data = json.loads(result)
        assert "error" in data


class TestLoadCueTool:
    """Tests for the load_cue MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_load_cue_next_bare(self, mock_get_client):
        from src.server import load_cue

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await load_cue(direction="next")
        data = json.loads(result)

        assert data["command_sent"] == "loadnext"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_load_cue_next_executor(self, mock_get_client):
        from src.server import load_cue

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await load_cue(direction="next", executor_id=5)
        data = json.loads(result)

        assert data["command_sent"] == "loadnext executor 5"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_load_cue_prev_sequence(self, mock_get_client):
        from src.server import load_cue

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await load_cue(direction="prev", sequence_id=3)
        data = json.loads(result)

        assert data["command_sent"] == "loadprev sequence 3"

    @pytest.mark.asyncio
    async def test_load_cue_invalid_direction(self):
        from src.server import load_cue

        result = await load_cue(direction="forward")
        data = json.loads(result)
        assert "error" in data


class TestCutPasteObjectTool:
    """Tests for the cut_paste_object MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_cut_group(self, mock_get_client):
        from src.server import cut_paste_object

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await cut_paste_object(action="cut", object_type="group", object_id=1)
        data = json.loads(result)

        assert data["command_sent"] == "cut group 1"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_paste_to_target(self, mock_get_client):
        from src.server import cut_paste_object

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await cut_paste_object(action="paste", object_type="group", target_id=5)
        data = json.loads(result)

        assert data["command_sent"] == "paste group 5"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_paste_bare(self, mock_get_client):
        from src.server import cut_paste_object

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await cut_paste_object(action="paste")
        data = json.loads(result)

        assert data["command_sent"] == "paste"

    @pytest.mark.asyncio
    async def test_cut_missing_object_type(self):
        from src.server import cut_paste_object

        result = await cut_paste_object(action="cut")
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_invalid_action(self):
        from src.server import cut_paste_object

        result = await cut_paste_object(action="copy")
        data = json.loads(result)
        assert "error" in data


class TestCloneObjectTool:
    """Tests for the clone_object MCP tool (DESTRUCTIVE)."""

    @pytest.mark.asyncio
    async def test_clone_blocked_without_confirmation(self):
        from src.server import clone_object

        result = await clone_object(object_type="fixture", object_id=1, target_id=2)
        data = json.loads(result)

        assert data["blocked"] is True
        assert data["risk_tier"] == "DESTRUCTIVE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_clone_fixture_confirmed(self, mock_get_client):
        from src.server import clone_object

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await clone_object(
            object_type="fixture", object_id=1, target_id=2,
            confirm_destructive=True,
        )
        data = json.loads(result)

        assert data["command_sent"] == "clone fixture 1 at 2"
        assert data["risk_tier"] == "DESTRUCTIVE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_clone_with_range_and_noconfirm(self, mock_get_client):
        from src.server import clone_object

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await clone_object(
            object_type="fixture", object_id=1, target_id=10,
            end=5, noconfirm=True, confirm_destructive=True,
        )
        data = json.loads(result)

        assert data["command_sent"] == "clone fixture 1 thru 5 at 10 /noconfirm"


class TestFixLocateFixtureTool:
    """Tests for the fix_locate_fixture MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_fix_selection(self, mock_get_client):
        from src.server import fix_locate_fixture

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await fix_locate_fixture(action="fix")
        data = json.loads(result)

        assert data["command_sent"] == "fix"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_fix_specific_fixtures(self, mock_get_client):
        from src.server import fix_locate_fixture

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await fix_locate_fixture(action="fix", fixture_ids=[1, 3, 5])
        data = json.loads(result)

        assert data["command_sent"] == "fix fixture 1 + 3 + 5"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_fix_single_with_end(self, mock_get_client):
        from src.server import fix_locate_fixture

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await fix_locate_fixture(action="fix", fixture_ids=[1], end=10)
        data = json.loads(result)

        assert data["command_sent"] == "fix fixture 1 thru 10"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_locate(self, mock_get_client):
        from src.server import fix_locate_fixture

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await fix_locate_fixture(action="locate")
        data = json.loads(result)

        assert data["command_sent"] == "locate"

    @pytest.mark.asyncio
    async def test_invalid_action(self):
        from src.server import fix_locate_fixture

        result = await fix_locate_fixture(action="park")
        data = json.loads(result)
        assert "error" in data


class TestManipulateSelectionTool:
    """Tests for the manipulate_selection MCP tool."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_invert(self, mock_get_client):
        from src.server import manipulate_selection

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await manipulate_selection(action="invert")
        data = json.loads(result)

        assert data["command_sent"] == "invert"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_align(self, mock_get_client):
        from src.server import manipulate_selection

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await manipulate_selection(action="align")
        data = json.loads(result)

        assert data["command_sent"] == "align"

    @pytest.mark.asyncio
    async def test_invalid_action(self):
        from src.server import manipulate_selection

        result = await manipulate_selection(action="sort")
        data = json.loads(result)
        assert "error" in data


class TestBlockUnblockCueTool:
    """Tests for the block_unblock_cue MCP tool (DESTRUCTIVE)."""

    @pytest.mark.asyncio
    async def test_block_blocked_without_confirmation(self):
        from src.server import block_unblock_cue

        result = await block_unblock_cue(action="block", cue_id=5)
        data = json.loads(result)

        assert data["blocked"] is True
        assert data["risk_tier"] == "DESTRUCTIVE"

    @pytest.mark.asyncio
    async def test_unblock_blocked_without_confirmation(self):
        from src.server import block_unblock_cue

        result = await block_unblock_cue(action="unblock", cue_id=5)
        data = json.loads(result)

        assert data["blocked"] is True
        assert data["risk_tier"] == "DESTRUCTIVE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_block_cue_confirmed(self, mock_get_client):
        from src.server import block_unblock_cue

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await block_unblock_cue(
            action="block", cue_id=5, confirm_destructive=True,
        )
        data = json.loads(result)

        assert data["command_sent"] == "block cue 5"
        assert data["risk_tier"] == "DESTRUCTIVE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_unblock_cue_with_sequence(self, mock_get_client):
        from src.server import block_unblock_cue

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await block_unblock_cue(
            action="unblock", cue_id=3, sequence_id=1, confirm_destructive=True,
        )
        data = json.loads(result)

        assert data["command_sent"] == "unblock cue 3 sequence 1"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_block_cue_range(self, mock_get_client):
        from src.server import block_unblock_cue

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="[channel]>")
        mock_get_client.return_value = mock_client

        result = await block_unblock_cue(
            action="block", cue_id=1, end=5, confirm_destructive=True,
        )
        data = json.loads(result)

        assert data["command_sent"] == "block cue 1 thru 5"

    @pytest.mark.asyncio
    async def test_invalid_action(self):
        from src.server import block_unblock_cue

        result = await block_unblock_cue(action="freeze", cue_id=1)
        data = json.loads(result)
        assert "error" in data
