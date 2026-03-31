"""
tests/test_busking_tools.py — Unit tests for busking / performance layer tools.

Tools tested:
  - assign_effect_to_executor
  - assign_sequence_to_executor
  - assign_macro_to_executor
  - assign_executor_function
  - modulate_effect
  - clear_effects_on_page
  - normalize_page_faders
  - classify_show_mode
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── assign_effect_to_executor ────────────────────────────────────────────────


class TestAssignEffectToExecutor:
    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_blocked_without_confirm(self, mock_get_client):
        from src.server import assign_effect_to_executor

        result = await assign_effect_to_executor(effect_id=5, executor_id=12)
        data = json.loads(result)
        assert data["status"] == "blocked"
        assert "confirm_destructive" in data["reason"]
        mock_get_client.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_basic_assignment(self, mock_get_client):
        from src.server import assign_effect_to_executor

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await assign_effect_to_executor(
            effect_id=5, executor_id=12, confirm_destructive=True
        )
        data = json.loads(result)
        assert data["status"] == "ok"
        assert data["command_sent"] == "assign sequence 5 at executor 12"
        assert data["executor_address"] == "12"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_with_page(self, mock_get_client):
        from src.server import assign_effect_to_executor

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="")
        mock_get_client.return_value = mock_client

        result = await assign_effect_to_executor(
            effect_id=3, executor_id=7, page=2, confirm_destructive=True
        )
        data = json.loads(result)
        assert data["command_sent"] == "assign sequence 3 at executor 2.7"
        assert data["executor_address"] == "2.7"


# ── modulate_effect ──────────────────────────────────────────────────────────


class TestModulateEffect:
    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_error_no_rate_or_speed(self, mock_get_client):
        from src.server import modulate_effect

        result = await modulate_effect(executor_id=5)
        data = json.loads(result)
        assert data["status"] == "error"
        mock_get_client.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_error_both_rate_and_speed(self, mock_get_client):
        from src.server import modulate_effect

        result = await modulate_effect(executor_id=5, rate=100.0, speed=128.0)
        data = json.loads(result)
        assert data["status"] == "error"
        mock_get_client.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_rate_command(self, mock_get_client):
        from src.server import modulate_effect

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="")
        mock_get_client.return_value = mock_client

        result = await modulate_effect(executor_id=12, rate=150.0)
        data = json.loads(result)
        assert data["status"] == "ok"
        assert data["command_sent"] == "executor 12 at rate 150.0"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_speed_command(self, mock_get_client):
        from src.server import modulate_effect

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="")
        mock_get_client.return_value = mock_client

        result = await modulate_effect(executor_id=12, speed=128.0)
        data = json.loads(result)
        assert "speed 128.0" in data["command_sent"]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_rate_with_page(self, mock_get_client):
        from src.server import modulate_effect

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="")
        mock_get_client.return_value = mock_client

        result = await modulate_effect(executor_id=3, rate=50.0, page=2)
        data = json.loads(result)
        assert data["command_sent"] == "executor 2.3 at rate 50.0"


# ── clear_effects_on_page ────────────────────────────────────────────────────


class TestClearEffectsOnPage:
    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_releases_range(self, mock_get_client):
        from src.server import clear_effects_on_page

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="")
        mock_get_client.return_value = mock_client

        result = await clear_effects_on_page(page=2, executor_start=1, executor_end=5)
        data = json.loads(result)
        assert data["status"] == "ok"
        assert data["executors_released"] == 5
        assert data["page"] == 2

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_correct_command_format(self, mock_get_client):
        from src.server import clear_effects_on_page

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="")
        mock_get_client.return_value = mock_client

        await clear_effects_on_page(page=3, executor_start=1, executor_end=3)
        calls = [c.args[0] for c in mock_client.send_command_with_response.call_args_list]
        assert "release executor 3.1" in calls
        assert "release executor 3.2" in calls
        assert "release executor 3.3" in calls


# ── assign_sequence_to_executor ─────────────────────────────────────────────


class TestAssignSequenceToExecutor:
    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_blocked_without_confirm(self, mock_get_client):
        from src.server import assign_sequence_to_executor
        result = await assign_sequence_to_executor(sequence_id=1, executor_id=5)
        data = json.loads(result)
        assert data["status"] == "blocked"
        mock_get_client.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_basic_command(self, mock_get_client):
        from src.server import assign_sequence_to_executor
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="")
        mock_get_client.return_value = mock_client
        result = await assign_sequence_to_executor(sequence_id=1, executor_id=5, confirm_destructive=True)
        data = json.loads(result)
        assert data["status"] == "ok"
        assert "sequence 1" in data["command_sent"]
        assert "executor 5" in data["command_sent"]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_with_page(self, mock_get_client):
        from src.server import assign_sequence_to_executor
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="")
        mock_get_client.return_value = mock_client
        result = await assign_sequence_to_executor(sequence_id=3, executor_id=7, page=2, confirm_destructive=True)
        data = json.loads(result)
        assert data["executor_address"] == "2.7"
        assert "executor 2.7" in data["command_sent"]


# ── assign_macro_to_executor ─────────────────────────────────────────────────


class TestAssignMacroToExecutor:
    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_blocked_without_confirm(self, mock_get_client):
        from src.server import assign_macro_to_executor
        result = await assign_macro_to_executor(macro_id=5, executor_id=1)
        data = json.loads(result)
        assert data["status"] == "blocked"
        mock_get_client.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_basic_command(self, mock_get_client):
        from src.server import assign_macro_to_executor
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="")
        mock_get_client.return_value = mock_client
        result = await assign_macro_to_executor(macro_id=5, executor_id=1, confirm_destructive=True)
        data = json.loads(result)
        assert data["status"] == "ok"
        assert "macro 5" in data["command_sent"]
        assert "executor 1" in data["command_sent"]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_with_page(self, mock_get_client):
        from src.server import assign_macro_to_executor
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="")
        mock_get_client.return_value = mock_client
        result = await assign_macro_to_executor(macro_id=5, executor_id=1, page=3, confirm_destructive=True)
        data = json.loads(result)
        assert data["executor_address"] == "3.1"


# ── assign_executor_function ─────────────────────────────────────────────────


class TestAssignExecutorFunction:
    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_blocked_without_confirm(self, mock_get_client):
        from src.server import assign_executor_function
        result = await assign_executor_function("Toggle", executor_id=5)
        data = json.loads(result)
        assert data["status"] == "blocked"
        mock_get_client.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_invalid_function(self, mock_get_client):
        from src.server import assign_executor_function
        result = await assign_executor_function("NotAFunction", executor_id=5, confirm_destructive=True)
        data = json.loads(result)
        assert data["status"] == "error"
        assert "valid_functions" in data
        mock_get_client.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_button_function_toggle(self, mock_get_client):
        from src.server import assign_executor_function
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="")
        mock_get_client.return_value = mock_client
        result = await assign_executor_function("Toggle", executor_id=5, confirm_destructive=True)
        data = json.loads(result)
        assert data["status"] == "ok"
        assert "toggle" in data["command_sent"].lower()
        assert "executor 5" in data["command_sent"].lower()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_fader_function_speed(self, mock_get_client):
        from src.server import assign_executor_function
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="")
        mock_get_client.return_value = mock_client
        result = await assign_executor_function("Speed", executor_id=3, confirm_destructive=True)
        data = json.loads(result)
        assert data["status"] == "ok"
        assert "speed" in data["command_sent"].lower()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_case_insensitive(self, mock_get_client):
        from src.server import assign_executor_function
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="")
        mock_get_client.return_value = mock_client
        # "go" should be accepted even if stored as "Go"
        result = await assign_executor_function("go", executor_id=1, confirm_destructive=True)
        data = json.loads(result)
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_with_page(self, mock_get_client):
        from src.server import assign_executor_function
        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="")
        mock_get_client.return_value = mock_client
        result = await assign_executor_function("Flash", executor_id=4, page=2, confirm_destructive=True)
        data = json.loads(result)
        assert data["executor_address"] == "2.4"


# ── normalize_page_faders ────────────────────────────────────────────────────


class TestNormalizePageFaders:
    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_command_format(self, mock_get_client):
        from src.server import normalize_page_faders

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="")
        mock_get_client.return_value = mock_client

        result = await normalize_page_faders(page=2)
        data = json.loads(result)
        assert data["status"] == "ok"
        assert data["command_sent"] == "executor 2.1 thru 2.90 at 0"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_custom_range(self, mock_get_client):
        from src.server import normalize_page_faders

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="")
        mock_get_client.return_value = mock_client

        result = await normalize_page_faders(page=1, executor_start=5, executor_end=20)
        data = json.loads(result)
        assert data["command_sent"] == "executor 1.5 thru 1.20 at 0"


# ── classify_show_mode ───────────────────────────────────────────────────────


class TestClassifyShowMode:
    def _make_client(self, seq_lines=0, macro_lines=0, exec_lines=0):
        """Build a mock client with responses that produce the given line counts."""
        def _resp(count):
            if count == 0:
                return "NO OBJECTS FOUND"
            return "\n".join(f"Object {i}" for i in range(1, count + 1))

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(
            side_effect=[_resp(seq_lines), _resp(macro_lines), _resp(exec_lines)]
        )
        return mock_client

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_empty_show(self, mock_get_client):
        from src.server import classify_show_mode

        mock_get_client.return_value = self._make_client(0, 0, 0)
        result = await classify_show_mode()
        data = json.loads(result)
        assert data["mode"] == "empty"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_sequence_show(self, mock_get_client):
        from src.server import classify_show_mode

        mock_get_client.return_value = self._make_client(seq_lines=2, exec_lines=1)
        result = await classify_show_mode()
        data = json.loads(result)
        assert data["mode"] == "sequence"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_busking_show(self, mock_get_client):
        from src.server import classify_show_mode

        mock_get_client.return_value = self._make_client(seq_lines=0, exec_lines=6)
        result = await classify_show_mode()
        data = json.loads(result)
        assert data["mode"] == "busking"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_hybrid_show(self, mock_get_client):
        from src.server import classify_show_mode

        mock_get_client.return_value = self._make_client(seq_lines=3, exec_lines=6)
        result = await classify_show_mode()
        data = json.loads(result)
        assert data["mode"] == "hybrid"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_evidence_dict_present(self, mock_get_client):
        from src.server import classify_show_mode

        mock_get_client.return_value = self._make_client(seq_lines=1, macro_lines=5, exec_lines=2)
        result = await classify_show_mode()
        data = json.loads(result)
        assert "evidence" in data
        assert data["evidence"]["sequences"] == 1
        assert data["evidence"]["macros"] == 5
        assert "recommendation" in data
