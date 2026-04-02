"""
Unit tests for PSR (Partial Show Read) command builders.

All tests are pure — no console connection required.
"""

import pytest
from src.commands import psr, psr_list, psr_prepare
from src.commands.functions.psr import psr as _psr_direct


# ============================================================================
# psr_prepare
# ============================================================================


class TestPsrPrepare:
    def test_basic(self):
        assert psr_prepare("my_show") == 'PSRPrepare "my_show"'

    def test_show_with_spaces(self):
        assert psr_prepare("venue 2024") == 'PSRPrepare "venue 2024"'

    def test_show_with_underscores(self):
        assert psr_prepare("claude_ma2_ctrl") == 'PSRPrepare "claude_ma2_ctrl"'

    def test_empty_name_produces_empty_quoted(self):
        # Builder does not validate — empty name passes through
        assert psr_prepare("") == 'PSRPrepare ""'


# ============================================================================
# psr_list
# ============================================================================


class TestPsrList:
    def test_basic(self):
        assert psr_list("my_show") == 'PSRList "my_show"'

    def test_show_with_spaces(self):
        assert psr_list("venue 2024") == 'PSRList "venue 2024"'

    def test_show_with_underscores(self):
        assert psr_list("claude_ma2_ctrl") == 'PSRList "claude_ma2_ctrl"'


# ============================================================================
# psr
# ============================================================================


class TestPsr:
    def test_object_type_only(self):
        assert psr("my_show", "Group") == 'PSR "my_show" Group'

    def test_with_integer_id(self):
        assert psr("my_show", "Cue", 1) == 'PSR "my_show" Cue 1'

    def test_with_string_id(self):
        assert psr("my_show", "Sequence", "5") == 'PSR "my_show" Sequence 5'

    def test_with_range_string(self):
        assert psr("my_show", "Preset", "1 Thru 5") == 'PSR "my_show" Preset 1 Thru 5'

    def test_dotted_id(self):
        assert psr("my_show", "Cue", "1.1") == 'PSR "my_show" Cue 1.1'

    def test_merge_flag(self):
        assert psr("my_show", "Sequence", 1, merge=True) == 'PSR "my_show" Sequence 1 /merge'

    def test_merge_flag_no_id(self):
        assert psr("my_show", "Group", merge=True) == 'PSR "my_show" Group /merge'

    def test_no_merge_by_default(self):
        result = psr("my_show", "Cue", 1)
        assert "/merge" not in result

    def test_show_name_with_spaces(self):
        assert psr("venue 2024", "Macro", 3) == 'PSR "venue 2024" Macro 3'

    def test_zero_id(self):
        assert psr("my_show", "Preset", 0) == 'PSR "my_show" Preset 0'

    def test_large_id(self):
        assert psr("my_show", "Cue", 999) == 'PSR "my_show" Cue 999'

    def test_direct_import_matches_top_level(self):
        assert _psr_direct("s", "Group") == psr("s", "Group")

    def test_all_supported_object_types_format_correctly(self):
        object_types = [
            "Cue", "Sequence", "Group", "Preset", "Macro",
            "Effect", "Timecode", "Filter", "View", "Layout",
            "World", "Plugin", "Timer",
        ]
        for obj_type in object_types:
            result = psr("show", obj_type, 1)
            assert result == f'PSR "show" {obj_type} 1', f"Failed for {obj_type}"
