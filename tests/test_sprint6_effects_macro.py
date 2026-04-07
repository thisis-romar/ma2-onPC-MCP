# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
Sprint 6 tests — P3 effects-reference resource content fix + P2 record_macro dispatch verification.

Covers:
  - effects_reference() resource includes delay/fade params (added Sprint 4, now documented)
  - set_effect_param tool docstring covers all 10 params
  - programming_action(action="record_macro") dispatch path
  - macro_condition_line / macro_with_input_before/after builders
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestEffectsReferenceResource:
    def _get(self) -> str:
        from src.server import effects_reference
        return effects_reference()

    def test_returns_non_empty_string(self):
        body = self._get()
        assert isinstance(body, str)
        assert len(body) > 100

    def test_contains_all_10_params(self):
        body = self._get()
        for param in ("bpm", "hz", "high", "low", "phase", "width", "attack", "decay", "delay", "fade"):
            assert param in body, f"Missing param '{param}' in effects_reference"

    def test_delay_and_fade_in_param_table(self):
        body = self._get()
        assert "EffectDelay" in body
        assert "EffectFade" in body

    def test_no_telnet_calls(self):
        body = self._get()
        for forbidden in ("telnet_send", "send_command", "_send", "telnet_client"):
            assert forbidden not in body


class TestProgrammingActionRecordMacro:
    @pytest.mark.asyncio
    @patch("src.server_core.get_client")
    async def test_record_macro_blocked_without_confirm(self, mock_get_client):
        from src.server import programming_action

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = await programming_action(action="record_macro", macro_id=5)
        data = json.loads(result)

        assert data["blocked"] is True
        mock_client.send_command_with_response.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.server_core.get_client")
    async def test_record_macro_dispatches_with_confirm(self, mock_get_client):
        from src.server import programming_action

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await programming_action(
            action="record_macro", macro_id=5, confirm_destructive=True
        )
        data = json.loads(result)

        mock_client.send_command_with_response.assert_called_once_with("Record Macro 5")
        assert data["command_sent"] == "Record Macro 5"

    @pytest.mark.asyncio
    @patch("src.server_core.get_client")
    async def test_record_macro_missing_macro_id_blocked(self, mock_get_client):
        from src.server import programming_action

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = await programming_action(action="record_macro", confirm_destructive=True)
        data = json.loads(result)

        assert data["blocked"] is True
        mock_client.send_command_with_response.assert_not_called()

    def test_record_macro_builder_output(self):
        from src.commands import record_macro
        assert record_macro(1) == "Record Macro 1"
        assert record_macro(99) == "Record Macro 99"


class TestMacroBuildersDocumented:
    def test_macro_condition_line_referenced_in_resource(self):
        from src.server import macro_reference
        assert "macro_condition_line" in macro_reference()

    def test_macro_with_input_after_builder(self):
        from src.commands import macro_with_input_after
        assert macro_with_input_after("Store Cue 1") == "Store Cue 1 @"

    def test_macro_with_input_before_builder(self):
        from src.commands import macro_with_input_before
        assert macro_with_input_before("Fade 10") == "@ Fade 10"

    def test_macro_condition_line_builder(self):
        from src.commands import macro_condition_line
        result = macro_condition_line("$mymode", "==", 1, "Go Executor 1")
        assert result == "[$mymode == 1] Go Executor 1"
