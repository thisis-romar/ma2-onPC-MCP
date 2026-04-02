"""
MCP tool tests for filter_fixture_selection and extended programmer_operations.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestFilterFixtureSelection:
    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_filter_active(self, mock_get_client):
        from src.server import filter_fixture_selection

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await filter_fixture_selection("active")

        mock_client.send_command_with_response.assert_called_once_with("If Active")
        data = json.loads(result)
        assert data["command_sent"] == "If Active"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_filter_output(self, mock_get_client):
        from src.server import filter_fixture_selection

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await filter_fixture_selection("output")

        mock_client.send_command_with_response.assert_called_once_with("If Output")
        data = json.loads(result)
        assert data["command_sent"] == "If Output"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_filter_programmer(self, mock_get_client):
        from src.server import filter_fixture_selection

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await filter_fixture_selection("programmer")

        mock_client.send_command_with_response.assert_called_once_with("If Programmer")
        data = json.loads(result)
        assert data["command_sent"] == "If Programmer"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_invalid_filter_type_blocked(self, mock_get_client):
        from src.server import filter_fixture_selection

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = await filter_fixture_selection("invalid")

        data = json.loads(result)
        assert data["blocked"] is True
        mock_client.send_command_with_response.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_raw_response_included(self, mock_get_client):
        from src.server import filter_fixture_selection

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="5 fixtures")
        mock_get_client.return_value = mock_client

        result = await filter_fixture_selection("active")
        data = json.loads(result)
        assert data["raw_response"] == "5 fixtures"


class TestProgrammerOperationsExtended:
    """Tests for the 4 new SAFE_WRITE actions added to programmer_operations."""

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_shuffle_selection(self, mock_get_client):
        from src.server import programming_action as programmer_operations

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await programmer_operations(action="shuffle_selection")

        mock_client.send_command_with_response.assert_called_once_with("ShuffleSelection")
        data = json.loads(result)
        assert data["command_sent"] == "ShuffleSelection"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_shuffle_values(self, mock_get_client):
        from src.server import programming_action as programmer_operations

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await programmer_operations(action="shuffle_values")

        mock_client.send_command_with_response.assert_called_once_with("ShuffleValues")
        data = json.loads(result)
        assert data["command_sent"] == "ShuffleValues"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_full_highlight(self, mock_get_client):
        from src.server import programming_action as programmer_operations

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await programmer_operations(action="full_highlight")

        mock_client.send_command_with_response.assert_called_once_with("FullHighlight")
        data = json.loads(result)
        assert data["command_sent"] == "FullHighlight"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_blind_edit(self, mock_get_client):
        from src.server import programming_action as programmer_operations

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await programmer_operations(action="blind_edit")

        mock_client.send_command_with_response.assert_called_once_with("BlindEdit")
        data = json.loads(result)
        assert data["command_sent"] == "BlindEdit"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_new_actions_are_not_destructive(self, mock_get_client):
        """New SAFE_WRITE actions must NOT require confirm_destructive."""
        from src.server import programming_action as programmer_operations

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        for action in ("shuffle_selection", "shuffle_values", "full_highlight", "blind_edit"):
            result = await programmer_operations(action=action, confirm_destructive=False)
            data = json.loads(result)
            assert "blocked" not in data or data.get("blocked") is not True, (
                f"Action '{action}' should not be blocked without confirm_destructive"
            )


class TestResourcesAndPromptsSmoke:
    def test_effects_reference_content(self):
        from src.server import effects_reference

        result = effects_reference()
        assert isinstance(result, str)
        assert "EffectBPM" in result
        assert "phase" in result
        assert "set_effect_param" in result

    def test_timecode_reference_content(self):
        from src.server import timecode_reference

        result = timecode_reference()
        assert isinstance(result, str)
        assert "SMPTE" in result
        assert "HH:MM:SS:FF" in result
        assert "store_timecode_event" in result

    def test_macro_reference_content(self):
        from src.server import macro_reference

        result = macro_reference()
        assert isinstance(result, str)
        assert "SetVar" in result
        assert "EndIf" in result
        assert "macro_condition_line" in result

    def test_program_effect_prompt_dry_run(self):
        from src.server import program_effect

        result = program_effect("5", "dimmer", 120.0)
        assert "120" in result
        assert "dimmer" in result.lower()
        assert "set_effect_param" in result
        assert "Group 5" in result or "group_id='5'" in result or "5" in result

    def test_program_effect_prompt_contains_steps(self):
        from src.server import program_effect

        result = program_effect("All Movers", "position", 60.0)
        assert "Pre-flight" in result
        assert "Store" in result
        assert "Verify" in result

    def test_build_timecode_show_prompt(self):
        from src.server import build_timecode_show

        result = build_timecode_show("1,2,3", "00:00:00:00")
        assert "Sequence 1" in result
        assert "Sequence 2" in result
        assert "Sequence 3" in result
        assert "SMPTE" in result
        assert "00:00:00:00" in result

    def test_build_timecode_show_single_sequence(self):
        from src.server import build_timecode_show

        result = build_timecode_show("5", "00:01:00:00")
        assert "Sequence 5" in result
        assert "00:01:00:00" in result

    def test_build_timecode_show_empty_sequences(self):
        from src.server import build_timecode_show

        result = build_timecode_show("")
        assert "none" in result.lower() or "(none specified)" in result
