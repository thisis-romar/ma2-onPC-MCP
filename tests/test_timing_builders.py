# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
Unit tests for the 6 advanced timing command builders in src/commands/functions/timing.py.
All tests are pure — no console connection required.
"""

import pytest

from src.commands import (
    fade_path,
    out_delay,
    out_fade,
    step_fade,
    step_in_fade,
    step_out_fade,
)
from src.commands.functions.timing import (
    _VALID_FADE_PATHS,
)
from src.commands.functions.timing import (
    fade_path as _fade_path_direct,
)


class TestFadePath:
    def test_linear(self):
        assert fade_path("linear") == "FadePath linear"

    def test_ease_in(self):
        assert fade_path("easeIn") == "FadePath easeIn"

    def test_ease_out(self):
        assert fade_path("easeOut") == "FadePath easeOut"

    def test_ease_in_out(self):
        assert fade_path("easeInOut") == "FadePath easeInOut"

    def test_step(self):
        assert fade_path("step") == "FadePath step"

    def test_broken_line(self):
        assert fade_path("brokenLine") == "FadePath brokenLine"

    def test_invalid_path_raises(self):
        with pytest.raises(ValueError, match="Unknown fade path"):
            fade_path("sinusoid")

    def test_invalid_path_message_includes_valid(self):
        with pytest.raises(ValueError, match="linear"):
            fade_path("invalid")

    def test_all_valid_paths_are_accepted(self):
        for path in _VALID_FADE_PATHS:
            result = fade_path(path)
            assert result == f"FadePath {path}"

    def test_direct_import_matches_top_level(self):
        assert _fade_path_direct("linear") == fade_path("linear")

    def test_case_sensitive_reject(self):
        with pytest.raises(ValueError):
            fade_path("Linear")

    def test_case_sensitive_reject_ease(self):
        with pytest.raises(ValueError):
            fade_path("easein")


class TestOutFade:
    def test_bare_value(self):
        assert out_fade(2.5) == "OutFade 2.5"

    def test_integer_value(self):
        assert out_fade(3) == "OutFade 3"

    def test_zero(self):
        assert out_fade(0) == "OutFade 0"

    def test_with_cue_id(self):
        assert out_fade(3, cue_id=5) == "OutFade 3 Cue 5"

    def test_with_cue_and_sequence(self):
        assert out_fade(1.5, cue_id=5, sequence_id=99) == "OutFade 1.5 Cue 5 Sequence 99"

    def test_sequence_ignored_without_cue(self):
        # sequence_id is silently ignored when cue_id is not given
        result = out_fade(2.0, sequence_id=10)
        assert "Sequence" not in result
        assert result == "OutFade 2.0"


class TestOutDelay:
    def test_bare_value(self):
        assert out_delay(1.0) == "OutDelay 1.0"

    def test_integer_value(self):
        assert out_delay(2) == "OutDelay 2"

    def test_zero(self):
        assert out_delay(0) == "OutDelay 0"

    def test_with_cue_id(self):
        assert out_delay(0.5, cue_id=3) == "OutDelay 0.5 Cue 3"

    def test_with_cue_and_sequence(self):
        assert out_delay(2, cue_id=3, sequence_id=10) == "OutDelay 2 Cue 3 Sequence 10"

    def test_sequence_ignored_without_cue(self):
        result = out_delay(1.0, sequence_id=5)
        assert "Sequence" not in result
        assert result == "OutDelay 1.0"


class TestStepFade:
    def test_float_value(self):
        assert step_fade(0.5) == "StepFade 0.5"

    def test_integer_value(self):
        assert step_fade(2) == "StepFade 2"

    def test_zero(self):
        assert step_fade(0) == "StepFade 0"

    def test_large_value(self):
        assert step_fade(10) == "StepFade 10"


class TestStepInFade:
    def test_float_value(self):
        assert step_in_fade(1.0) == "StepInFade 1.0"

    def test_integer_value(self):
        assert step_in_fade(3) == "StepInFade 3"

    def test_zero(self):
        assert step_in_fade(0) == "StepInFade 0"


class TestStepOutFade:
    def test_float_value(self):
        assert step_out_fade(1.0) == "StepOutFade 1.0"

    def test_integer_value(self):
        assert step_out_fade(3) == "StepOutFade 3"

    def test_zero(self):
        assert step_out_fade(0) == "StepOutFade 0"


class TestAllTimingBuildersReturnStrings:
    def test_all_return_non_empty_strings(self):
        results = [
            fade_path("linear"),
            out_fade(1),
            out_delay(1),
            step_fade(1),
            step_in_fade(1),
            step_out_fade(1),
        ]
        for r in results:
            assert isinstance(r, str)
            assert len(r) > 0

    def test_no_newlines_in_any_builder(self):
        results = [
            fade_path("linear"),
            out_fade(1),
            out_delay(1),
            step_fade(1),
            step_in_fade(1),
            step_out_fade(1),
        ]
        for r in results:
            assert "\n" not in r
            assert "\r" not in r
