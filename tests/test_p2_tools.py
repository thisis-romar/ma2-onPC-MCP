"""
MCP tool tests for P2 extensions:
- control_executor new actions: flash_go, flash_on, swop_go, swop_on, manual_xfade
- set_advanced_timing new action: snap_percent
- set_effect_parameter extended: delay and fade params
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestControlExecutorNewActions:
    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_flash_go(self, mock_get_client):
        from src.server import control_executor

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await control_executor(action="flash_go", executor_id=3)
        data = json.loads(result)

        mock_client.send_command_with_response.assert_called_once_with("FlashGo Executor 3")
        assert data["command_sent"] == "FlashGo Executor 3"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_flash_go_page_qualified(self, mock_get_client):
        from src.server import control_executor

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await control_executor(action="flash_go", executor_id=5, page=2)
        data = json.loads(result)

        mock_client.send_command_with_response.assert_called_once_with("FlashGo Executor 2.5")
        assert data["command_sent"] == "FlashGo Executor 2.5"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_flash_on(self, mock_get_client):
        from src.server import control_executor

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await control_executor(action="flash_on", executor_id=4)
        data = json.loads(result)

        mock_client.send_command_with_response.assert_called_once_with("FlashOn Executor 4")
        assert data["command_sent"] == "FlashOn Executor 4"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_swop_go(self, mock_get_client):
        from src.server import control_executor

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await control_executor(action="swop_go", executor_id=7)
        data = json.loads(result)

        mock_client.send_command_with_response.assert_called_once_with("SwopGo Executor 7")
        assert data["command_sent"] == "SwopGo Executor 7"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_swop_on(self, mock_get_client):
        from src.server import control_executor

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await control_executor(action="swop_on", executor_id=8)
        data = json.loads(result)

        mock_client.send_command_with_response.assert_called_once_with("SwopOn Executor 8")
        assert data["command_sent"] == "SwopOn Executor 8"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_manual_xfade(self, mock_get_client):
        from src.server import control_executor

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await control_executor(action="manual_xfade", executor_id=3, speed_value=75.0)
        data = json.loads(result)

        mock_client.send_command_with_response.assert_called_once_with("ManualXFade Executor 3 75.0")
        assert data["command_sent"] == "ManualXFade Executor 3 75.0"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_manual_xfade_missing_value_blocked(self, mock_get_client):
        from src.server import control_executor

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = await control_executor(action="manual_xfade", executor_id=3)
        data = json.loads(result)

        assert data["blocked"] is True
        mock_client.send_command_with_response.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_invalid_action_blocked(self, mock_get_client):
        from src.server import control_executor

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = await control_executor(action="invalid_action", executor_id=1)
        data = json.loads(result)

        assert data["blocked"] is True
        mock_client.send_command_with_response.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_raw_response_included(self, mock_get_client):
        from src.server import control_executor

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="FlashGo OK")
        mock_get_client.return_value = mock_client

        result = await control_executor(action="flash_go", executor_id=1)
        data = json.loads(result)

        assert data["raw_response"] == "FlashGo OK"


class TestSetAdvancedTimingSnapPercent:
    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_snap_percent(self, mock_get_client):
        from src.server import set_advanced_timing

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await set_advanced_timing(action="snap_percent", value=50)
        data = json.loads(result)

        mock_client.send_command_with_response.assert_called_once_with("SnapPercent 50")
        assert data["command_sent"] == "SnapPercent 50"
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_snap_percent_float(self, mock_get_client):
        from src.server import set_advanced_timing

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await set_advanced_timing(action="snap_percent", value=33.3)
        data = json.loads(result)

        mock_client.send_command_with_response.assert_called_once_with("SnapPercent 33.3")

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_snap_percent_missing_value_blocked(self, mock_get_client):
        from src.server import set_advanced_timing

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = await set_advanced_timing(action="snap_percent")
        data = json.loads(result)

        assert data["blocked"] is True
        mock_client.send_command_with_response.assert_not_called()


class TestSetEffectParameterP3Extension:
    def test_effect_delay_accepted(self):
        from src.commands.functions.system import set_effect_parameter

        result = set_effect_parameter("delay", 1.0)
        assert result == "EffectDelay 1.0"

    def test_effect_fade_accepted(self):
        from src.commands.functions.system import set_effect_parameter

        result = set_effect_parameter("fade", 2.5)
        assert result == "EffectFade 2.5"

    def test_effect_delay_case_insensitive(self):
        from src.commands.functions.system import set_effect_parameter

        result = set_effect_parameter("DELAY", 1.0)
        assert result == "EffectDelay 1.0"

    def test_effect_fade_zero(self):
        from src.commands.functions.system import set_effect_parameter

        result = set_effect_parameter("fade", 0)
        assert result == "EffectFade 0"

    def test_previously_valid_params_still_work(self):
        from src.commands.functions.system import set_effect_parameter

        assert set_effect_parameter("bpm", 120) == "EffectBPM 120"
        assert set_effect_parameter("attack", 5) == "EffectAttack 5"
        assert set_effect_parameter("decay", 10) == "EffectDecay 10"
        assert set_effect_parameter("high", 80) == "EffectHigh 80"
        assert set_effect_parameter("low", 20) == "EffectLow 20"

    def test_invalid_param_still_raises(self):
        from src.commands.functions.system import set_effect_parameter
        import pytest

        with pytest.raises(ValueError, match="Unknown effect parameter"):
            set_effect_parameter("speed_foo", 1.0)
