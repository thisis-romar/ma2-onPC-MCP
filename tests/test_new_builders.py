"""
Tests for new command builders added in session 2026-03-10:
  solo(), blind(), freeze(), oops(), save_show(), delete_show(), update()
  + extended highlight() with object support
"""

from src.commands.functions.edit import oops
from src.commands.functions.playback import blind, freeze, solo
from src.commands.functions.selection import highlight
from src.commands.functions.store import delete_show, save_show, update

# ============================================================================
# solo() — universal (live-verified: all 16 object types)
# ============================================================================


class TestSolo:
    def test_bare_solo(self):
        assert solo() == "solo"

    def test_solo_executor(self):
        assert solo("executor", 3) == "solo executor 3"

    def test_solo_group(self):
        assert solo("group", 5) == "solo group 5"

    def test_solo_sequence(self):
        assert solo("sequence", 99) == "solo sequence 99"

    def test_solo_fixture(self):
        assert solo("fixture", 10) == "solo fixture 10"

    def test_solo_type_only(self):
        assert solo("group") == "solo group"


# ============================================================================
# blind() — universal (live-verified: all 16 object types)
# ============================================================================


class TestBlind:
    def test_bare_blind(self):
        assert blind() == "blind"

    def test_blind_executor(self):
        assert blind("executor", 3) == "blind executor 3"

    def test_blind_sequence(self):
        assert blind("sequence", 5) == "blind sequence 5"

    def test_blind_type_only(self):
        assert blind("executor") == "blind executor"


# ============================================================================
# freeze() — universal (live-verified: all 16 object types)
# ============================================================================


class TestFreeze:
    def test_bare_freeze(self):
        assert freeze() == "freeze"

    def test_freeze_executor(self):
        assert freeze("executor", 3) == "freeze executor 3"

    def test_freeze_sequence(self):
        assert freeze("sequence", 5) == "freeze sequence 5"

    def test_freeze_fixture(self):
        assert freeze("fixture", 10) == "freeze fixture 10"

    def test_freeze_type_only(self):
        assert freeze("group") == "freeze group"


# ============================================================================
# oops() — universal (live-verified: all 16 object types)
# ============================================================================


class TestOops:
    def test_bare_oops(self):
        assert oops() == "oops"

    def test_oops_cue(self):
        assert oops("cue", 5) == "oops cue 5"

    def test_oops_group(self):
        assert oops("group", 3) == "oops group 3"

    def test_oops_type_only(self):
        assert oops("sequence") == "oops sequence"


# ============================================================================
# save_show() — universal (live-verified: all 16 object types)
# ============================================================================


class TestSaveShow:
    def test_bare_save(self):
        assert save_show() == "saveshow"

    def test_save_with_name(self):
        assert save_show("my_show") == 'saveshow "my_show"'

    def test_save_with_spaces_in_name(self):
        assert save_show("My Show File") == 'saveshow "My Show File"'


# ============================================================================
# delete_show() — universal (live-verified: all 16 object types)
# ============================================================================


class TestDeleteShow:
    def test_delete_show_basic(self):
        assert delete_show("old_show") == 'deleteshow "old_show"'

    def test_delete_show_noconfirm(self):
        assert delete_show("old_show", noconfirm=True) == 'deleteshow "old_show" /noconfirm'


# ============================================================================
# update() — generic, universal (live-verified: all 16 object types)
# Note: update_cue() is the richer cue-specific variant, kept as-is
# ============================================================================


class TestUpdate:
    def test_update_group(self):
        assert update("group", 3) == "update group 3"

    def test_update_preset(self):
        assert update("preset", "1.5") == "update preset 1.5"

    def test_update_sequence(self):
        assert update("sequence", 99) == "update sequence 99"

    def test_update_merge(self):
        assert update("group", 3, merge=True) == "update group 3 /merge"

    def test_update_overwrite(self):
        assert update("sequence", 1, overwrite=True) == "update sequence 1 /overwrite"

    def test_update_cueonly_true(self):
        assert update("cue", 5, cueonly=True) == "update cue 5 /cueonly=true"

    def test_update_cueonly_false(self):
        assert update("cue", 5, cueonly=False) == "update cue 5 /cueonly=false"

    def test_update_no_options(self):
        assert update("macro", 10) == "update macro 10"


# ============================================================================
# highlight() — extended with optional object support
# ============================================================================


class TestHighlightExtended:
    def test_bare_on(self):
        """Existing behaviour preserved."""
        assert highlight() == "highlight on"

    def test_bare_off(self):
        """Existing behaviour preserved."""
        assert highlight(False) == "highlight off"

    def test_highlight_executor(self):
        assert highlight(object_type="executor", object_id=3) == "highlight executor 3"

    def test_highlight_group(self):
        assert highlight(object_type="group", object_id=5) == "highlight group 5"

    def test_highlight_sequence(self):
        assert highlight(object_type="sequence", object_id=99) == "highlight sequence 99"

    def test_highlight_type_only(self):
        assert highlight(object_type="fixture") == "highlight fixture"
