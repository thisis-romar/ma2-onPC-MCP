# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
Unit tests for the 3 preview mode builders and 2 P10 system builders.
All tests are pure — no console connection required.
"""

from src.commands import (
    alert,
    black_screen,
    preview,
    preview_edit,
    preview_executor,
)
from src.commands.functions.selection import (
    preview as _preview_direct,
)
from src.commands.functions.selection import (
    preview_edit as _preview_edit_direct,
)
from src.commands.functions.selection import (
    preview_executor as _preview_executor_direct,
)
from src.commands.functions.system import (
    alert as _alert_direct,
)
from src.commands.functions.system import (
    black_screen as _black_screen_direct,
)


class TestPreview:
    def test_bare_preview(self):
        assert preview() == "Preview"

    def test_with_executor_id(self):
        assert preview(5) == "Preview Executor 5"

    def test_executor_id_zero(self):
        assert preview(0) == "Preview Executor 0"

    def test_large_executor_id(self):
        assert preview(201) == "Preview Executor 201"

    def test_none_gives_bare(self):
        assert preview(None) == "Preview"

    def test_direct_import_matches_top_level(self):
        assert _preview_direct(5) == preview(5)
        assert _preview_direct() == preview()


class TestPreviewEdit:
    def test_bare_preview_edit(self):
        assert preview_edit() == "PreviewEdit"

    def test_with_executor_id(self):
        assert preview_edit(3) == "PreviewEdit Executor 3"

    def test_executor_id_zero(self):
        assert preview_edit(0) == "PreviewEdit Executor 0"

    def test_none_gives_bare(self):
        assert preview_edit(None) == "PreviewEdit"

    def test_direct_import_matches_top_level(self):
        assert _preview_edit_direct(3) == preview_edit(3)
        assert _preview_edit_direct() == preview_edit()


class TestPreviewExecutor:
    def test_basic(self):
        assert preview_executor(7) == "PreviewExecutor 7"

    def test_id_one(self):
        assert preview_executor(1) == "PreviewExecutor 1"

    def test_large_id(self):
        assert preview_executor(201) == "PreviewExecutor 201"

    def test_direct_import_matches_top_level(self):
        assert _preview_executor_direct(7) == preview_executor(7)


class TestBlackScreen:
    def test_returns_blackscreen(self):
        assert black_screen() == "BlackScreen"

    def test_no_arguments(self):
        result = black_screen()
        assert result == "BlackScreen"

    def test_is_string(self):
        assert isinstance(black_screen(), str)

    def test_direct_import_matches_top_level(self):
        assert _black_screen_direct() == black_screen()


class TestAlert:
    def test_basic_message(self):
        assert alert("hello") == 'Alert "hello"'

    def test_message_with_spaces(self):
        assert alert("Doors open in 5 minutes") == 'Alert "Doors open in 5 minutes"'

    def test_empty_message(self):
        assert alert("") == 'Alert ""'

    def test_direct_import_matches_top_level(self):
        assert _alert_direct("test") == alert("test")


class TestAllPreviewAndSystemBuildersReturnStrings:
    def test_all_return_non_empty_strings(self):
        builders_and_results = [
            preview(),
            preview(1),
            preview_edit(),
            preview_edit(1),
            preview_executor(1),
            black_screen(),
            alert("x"),
        ]
        for r in builders_and_results:
            assert isinstance(r, str)
            assert len(r) > 0

    def test_no_newlines(self):
        results = [
            preview(),
            preview(1),
            preview_edit(),
            preview_edit(1),
            preview_executor(1),
            black_screen(),
            alert("test"),
        ]
        for r in results:
            assert "\n" not in r
            assert "\r" not in r
