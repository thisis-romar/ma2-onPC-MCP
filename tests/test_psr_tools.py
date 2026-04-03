# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
MCP Tool tests for PSR (Partial Show Read) tools.

Tests validate:
- Command strings sent to the console
- JSON response structure
- DESTRUCTIVE gate (confirm_destructive=False blocks execution)
- Scope enforcement is exercised via GMA_AUTH_BYPASS=1 (set by conftest autouse fixture)
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ============================================================================
# prepare_partial_show_read
# ============================================================================


class TestPreparePartialShowRead:
    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_sends_psr_prepare_command(self, mock_get_client):
        from src.server import prepare_partial_show_read

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await prepare_partial_show_read("my_show")

        mock_client.send_command_with_response.assert_called_once_with('PSRPrepare "my_show"')
        data = json.loads(result)
        assert data["command_sent"] == 'PSRPrepare "my_show"'
        assert data["risk_tier"] == "SAFE_WRITE"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_show_name_with_spaces(self, mock_get_client):
        from src.server import prepare_partial_show_read

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await prepare_partial_show_read("venue 2024")
        data = json.loads(result)
        assert data["command_sent"] == 'PSRPrepare "venue 2024"'

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_raw_response_included(self, mock_get_client):
        from src.server import prepare_partial_show_read

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="PSR OK")
        mock_get_client.return_value = mock_client

        result = await prepare_partial_show_read("show")
        data = json.loads(result)
        assert data["raw_response"] == "PSR OK"


# ============================================================================
# list_psr_objects
# ============================================================================


class TestListPsrObjects:
    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_sends_psr_list_command(self, mock_get_client):
        from src.server import list_psr_objects

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Cue 1\nGroup 5")
        mock_get_client.return_value = mock_client

        result = await list_psr_objects("my_show")

        mock_client.send_command_with_response.assert_called_once_with('PSRList "my_show"')
        data = json.loads(result)
        assert data["command_sent"] == 'PSRList "my_show"'
        assert data["risk_tier"] == "SAFE_READ"

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_raw_response_included(self, mock_get_client):
        from src.server import list_psr_objects

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="Cue 1\nGroup 5")
        mock_get_client.return_value = mock_client

        result = await list_psr_objects("my_show")
        data = json.loads(result)
        assert data["raw_response"] == "Cue 1\nGroup 5"


# ============================================================================
# partial_show_read
# ============================================================================


class TestPartialShowRead:
    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_blocked_without_confirm(self, mock_get_client):
        from src.server import partial_show_read

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = await partial_show_read(
            source_show="my_show",
            object_type="Cue",
            confirm_destructive=False,
        )

        data = json.loads(result)
        assert data["blocked"] is True
        assert data["risk_tier"] == "DESTRUCTIVE"
        mock_client.send_command_with_response.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_sends_psr_command_when_confirmed(self, mock_get_client):
        from src.server import partial_show_read

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await partial_show_read(
            source_show="my_show",
            object_type="Cue",
            object_id="1",
            confirm_destructive=True,
        )

        mock_client.send_command_with_response.assert_called_once_with('PSR "my_show" Cue 1')
        data = json.loads(result)
        assert data["command_sent"] == 'PSR "my_show" Cue 1'
        assert data["risk_tier"] == "DESTRUCTIVE"
        assert data["blocked"] is False

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_import_all_objects_of_type(self, mock_get_client):
        from src.server import partial_show_read

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await partial_show_read(
            source_show="my_show",
            object_type="Group",
            confirm_destructive=True,
        )

        data = json.loads(result)
        assert data["command_sent"] == 'PSR "my_show" Group'

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_merge_flag_forwarded(self, mock_get_client):
        from src.server import partial_show_read

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await partial_show_read(
            source_show="my_show",
            object_type="Sequence",
            object_id="1",
            merge=True,
            confirm_destructive=True,
        )

        data = json.loads(result)
        assert data["command_sent"] == 'PSR "my_show" Sequence 1 /merge'

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_no_merge_by_default(self, mock_get_client):
        from src.server import partial_show_read

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await partial_show_read(
            source_show="my_show",
            object_type="Preset",
            object_id="5",
            confirm_destructive=True,
        )

        data = json.loads(result)
        assert "/merge" not in data["command_sent"]

    @pytest.mark.asyncio
    @patch("src.server.get_client")
    async def test_range_string_forwarded(self, mock_get_client):
        from src.server import partial_show_read

        mock_client = MagicMock()
        mock_client.send_command_with_response = AsyncMock(return_value="OK")
        mock_get_client.return_value = mock_client

        result = await partial_show_read(
            source_show="my_show",
            object_type="Preset",
            object_id="1 Thru 5",
            confirm_destructive=True,
        )

        data = json.loads(result)
        assert data["command_sent"] == 'PSR "my_show" Preset 1 Thru 5'


# ============================================================================
# PSR resource and prompt smoke tests
# ============================================================================


class TestPsrResource:
    def test_psr_guide_returns_string(self):
        from src.server import psr_guide

        result = psr_guide()
        assert isinstance(result, str)
        assert "PSR" in result
        # MA2 command keywords table
        assert "PSRPrepare" in result
        assert "PSRList" in result
        assert "SLOT CONFLICT" in result

    def test_psr_guide_mentions_workflow_steps(self):
        from src.server import psr_guide

        result = psr_guide()
        assert "prepare_partial_show_read" in result
        assert "list_psr_objects" in result
        assert "partial_show_read" in result


class TestPsrPrompt:
    def test_dry_run_mode(self):
        from src.server import migrate_show_via_psr

        result = migrate_show_via_psr("src_show", "Cue,Group", dry_run=True)
        assert "DRY RUN" in result
        assert "list_psr_objects" in result
        # Import steps should not include confirm_destructive in dry-run mode
        assert "confirm_destructive=True" not in result

    def test_live_mode(self):
        from src.server import migrate_show_via_psr

        result = migrate_show_via_psr("src_show", "Cue,Group", dry_run=False)
        assert "LIVE IMPORT" in result
        assert "partial_show_read" in result
        assert "confirm_destructive=True" in result

    def test_source_show_name_in_output(self):
        from src.server import migrate_show_via_psr

        result = migrate_show_via_psr("venue_2024", "Macro")
        assert "venue_2024" in result

    def test_empty_target_objects(self):
        from src.server import migrate_show_via_psr

        result = migrate_show_via_psr("show", "")
        assert "none specified" in result

    def test_preflight_steps_always_present(self):
        from src.server import migrate_show_via_psr

        result = migrate_show_via_psr("show", "Cue")
        assert "prepare_partial_show_read" in result
        assert "list_psr_objects" in result
        assert "list_system_variables" in result
