# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
Unit tests for the 8 new selection/filtering command builders.
All tests are pure — no console connection required.
"""

from src.commands import (
    blind_edit,
    end_if,
    full_highlight,
    if_active,
    if_output,
    if_prog,
    shuffle_selection,
    shuffle_values,
)
from src.commands.functions.selection import (
    blind_edit as _blind_edit_direct,
)
from src.commands.functions.selection import (
    if_active as _if_active_direct,
)


class TestIfActive:
    def test_returns_if_active(self):
        assert if_active() == "If Active"

    def test_no_arguments(self):
        result = if_active()
        assert result == "If Active"

    def test_direct_import_matches_top_level(self):
        assert _if_active_direct() == if_active()


class TestIfOutput:
    def test_returns_if_output(self):
        assert if_output() == "If Output"


class TestIfProg:
    def test_returns_if_programmer(self):
        assert if_prog() == "If Programmer"


class TestEndIf:
    def test_returns_endif(self):
        assert end_if() == "EndIf"


class TestFullHighlight:
    def test_returns_fullhighlight(self):
        assert full_highlight() == "FullHighlight"

    def test_is_not_plain_highlight(self):
        result = full_highlight()
        assert result != "highlight on"
        assert result != "Highlight"


class TestBlindEdit:
    def test_returns_blindedit(self):
        assert blind_edit() == "BlindEdit"

    def test_direct_import_matches_top_level(self):
        assert _blind_edit_direct() == blind_edit()


class TestShuffleSelection:
    def test_returns_shuffleselection(self):
        assert shuffle_selection() == "ShuffleSelection"


class TestShuffleValues:
    def test_returns_shufflevalues(self):
        assert shuffle_values() == "ShuffleValues"


class TestAllBuildersReturnStrings:
    def test_all_return_non_empty_strings(self):
        builders = [
            if_active, if_output, if_prog, end_if,
            full_highlight, blind_edit,
            shuffle_selection, shuffle_values,
        ]
        for builder in builders:
            result = builder()
            assert isinstance(result, str), f"{builder.__name__} did not return str"
            assert len(result) > 0, f"{builder.__name__} returned empty string"

    def test_no_newlines_in_any_builder(self):
        builders = [
            if_active, if_output, if_prog, end_if,
            full_highlight, blind_edit,
            shuffle_selection, shuffle_values,
        ]
        for builder in builders:
            result = builder()
            assert "\n" not in result, f"{builder.__name__} has newline"
            assert "\r" not in result, f"{builder.__name__} has carriage return"
