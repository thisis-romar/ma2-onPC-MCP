# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
MCP tool tests for set_advanced_timing (P7) and preview_executor_content (P8).
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestSetAdvancedTiming:
    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_fade_path_linear(self, mock_get_client):
        from src.server import set_advanced_timing

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await set_advanced_timing(action="fade_path", path_type="linear")
        data = json.loads(result)

        mock_client.send_command_with_response.assert_called_once_with("FadePath linear")
        assert data["command_sent"] == "FadePath linear"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_out_fade_bare(self, mock_get_client):
        from src.server import set_advanced_timing

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await set_advanced_timing(action="out_fade", value=2.5)
        data = json.loads(result)

        mock_client.send_command_with_response.assert_called_once_with("OutFade 2.5")
        assert data["command_sent"] == "OutFade 2.5"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_out_fade_with_cue_and_sequence(self, mock_get_client):
        from src.server import set_advanced_timing

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await set_advanced_timing(
            action="out_fade", value=1.5, cue_id=5, sequence_id=99
        )
        data = json.loads(result)

        mock_client.send_command_with_response.assert_called_once_with(
            "OutFade 1.5 Cue 5 Sequence 99"
        )
        assert data["command_sent"] == "OutFade 1.5 Cue 5 Sequence 99"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_out_delay(self, mock_get_client):
        from src.server import set_advanced_timing

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await set_advanced_timing(action="out_delay", value=1.0)
        data = json.loads(result)

        mock_client.send_command_with_response.assert_called_once_with("OutDelay 1.0")
        assert data["command_sent"] == "OutDelay 1.0"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_step_fade(self, mock_get_client):
        from src.server import set_advanced_timing

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await set_advanced_timing(action="step_fade", value=0.5)
        data = json.loads(result)

        mock_client.send_command_with_response.assert_called_once_with("StepFade 0.5")
        assert data["command_sent"] == "StepFade 0.5"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_step_in_fade(self, mock_get_client):
        from src.server import set_advanced_timing

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await set_advanced_timing(action="step_in_fade", value=1.0)
        data = json.loads(result)

        mock_client.send_command_with_response.assert_called_once_with("StepInFade 1.0")
        assert data["command_sent"] == "StepInFade 1.0"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_step_out_fade(self, mock_get_client):
        from src.server import set_advanced_timing

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await set_advanced_timing(action="step_out_fade", value=1.0)
        data = json.loads(result)

        mock_client.send_command_with_response.assert_called_once_with("StepOutFade 1.0")
        assert data["command_sent"] == "StepOutFade 1.0"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_invalid_action_blocked(self, mock_get_client):
        from src.server import set_advanced_timing

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = await set_advanced_timing(action="invalid_action")
        data = json.loads(result)

        assert data["blocked"] is True
        mock_client.send_command_with_response.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_fade_path_missing_path_type_blocked(self, mock_get_client):
        from src.server import set_advanced_timing

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = await set_advanced_timing(action="fade_path")
        data = json.loads(result)

        assert data["blocked"] is True
        mock_client.send_command_with_response.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_fade_path_invalid_path_type_blocked(self, mock_get_client):
        from src.server import set_advanced_timing

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = await set_advanced_timing(action="fade_path", path_type="sinusoid")
        data = json.loads(result)

        assert data["blocked"] is True
        mock_client.send_command_with_response.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_out_fade_missing_value_blocked(self, mock_get_client):
        from src.server import set_advanced_timing

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = await set_advanced_timing(action="out_fade")
        data = json.loads(result)

        assert data["blocked"] is True
        mock_client.send_command_with_response.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_raw_response_included(self, mock_get_client):
        from src.server import set_advanced_timing

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Fading")
        mock_get_client.return_value = mock_client

        result = await set_advanced_timing(action="step_fade", value=0.5)
        data = json.loads(result)

        assert data["raw_response"] == "Fading"


class TestPreviewExecutorContent:
    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_preview_bare(self, mock_get_client):
        from src.server import preview_executor_content

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await preview_executor_content(action="preview")
        data = json.loads(result)

        mock_client.send_command_with_response.assert_called_once_with("Preview")
        assert data["command_sent"] == "Preview"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_preview_with_executor(self, mock_get_client):
        from src.server import preview_executor_content

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await preview_executor_content(action="preview", executor_id=5)
        data = json.loads(result)

        mock_client.send_command_with_response.assert_called_once_with("Preview Executor 5")
        assert data["command_sent"] == "Preview Executor 5"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_preview_edit_bare(self, mock_get_client):
        from src.server import preview_executor_content

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await preview_executor_content(action="preview_edit")
        data = json.loads(result)

        mock_client.send_command_with_response.assert_called_once_with("PreviewEdit")
        assert data["command_sent"] == "PreviewEdit"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_preview_edit_with_executor(self, mock_get_client):
        from src.server import preview_executor_content

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await preview_executor_content(action="preview_edit", executor_id=3)
        data = json.loads(result)

        mock_client.send_command_with_response.assert_called_once_with("PreviewEdit Executor 3")
        assert data["command_sent"] == "PreviewEdit Executor 3"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_preview_exec(self, mock_get_client):
        from src.server import preview_executor_content

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await preview_executor_content(action="preview_exec", executor_id=7)
        data = json.loads(result)

        mock_client.send_command_with_response.assert_called_once_with("PreviewExecutor 7")
        assert data["command_sent"] == "PreviewExecutor 7"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_preview_exec_missing_executor_blocked(self, mock_get_client):
        from src.server import preview_executor_content

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = await preview_executor_content(action="preview_exec")
        data = json.loads(result)

        assert data["blocked"] is True
        mock_client.send_command_with_response.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_invalid_action_blocked(self, mock_get_client):
        from src.server import preview_executor_content

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = await preview_executor_content(action="invalid")
        data = json.loads(result)

        assert data["blocked"] is True
        mock_client.send_command_with_response.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_raw_response_included(self, mock_get_client):
        from src.server import preview_executor_content

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Preview active")
        mock_get_client.return_value = mock_client

        result = await preview_executor_content(action="preview", executor_id=1)
        data = json.loads(result)

        assert data["raw_response"] == "Preview active"
