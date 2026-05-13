# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for src/commands/constants.py — OAuthScope, hardkeys, executor options (BR=49)."""

from src.commands.constants import (
    EXECUTOR_ASSIGN_OPTION_NAMES,
    EXECUTOR_ASSIGN_OPTIONS,
    EXECUTOR_BUTTON_FUNCTIONS,
    EXECUTOR_FADER_FUNCTIONS,
    EXECUTOR_PRIORITIES,
    EXECUTOR_PRIORITY_VALUES,
    FILTER_ATTRIBUTES,
    FILTER_COLORS,
    FILTER_VTE_COMBOS,
    HARDKEY_CHAINS,
    MA2_BOOTSTRAP_USERS,
    MA2_RIGHTS_LEVELS,
    MA2RIGHT_TO_OAUTH_SCOPE,
    MA_KEY_COMBOS,
    OAUTH_TIER_SCOPES,
    PRESET_TYPES,
    STORE_BOOL_OPTIONS,
    STORE_FLAG_OPTIONS,
    STORE_VALUE_OPTIONS,
    MA2Right,
    OAuthScope,
)


class TestOAuthScope:
    """OAuthScope enum tests."""

    def test_has_20_members(self):
        assert len(OAuthScope) == 20

    def test_all_values_start_with_gma2(self):
        for scope in OAuthScope:
            assert scope.value.startswith("gma2:")

    def test_key_scopes_present(self):
        assert OAuthScope.DISCOVER == "gma2:discover"
        assert OAuthScope.PLAYBACK_GO == "gma2:playback:go"
        assert OAuthScope.CUE_STORE == "gma2:cue:store"
        assert OAuthScope.SYSTEM_ADMIN == "gma2:system:admin"


class TestOAuthTierScopes:
    """OAUTH_TIER_SCOPES mapping tests."""

    def test_has_6_tiers(self):
        assert set(OAUTH_TIER_SCOPES.keys()) == {0, 1, 2, 3, 4, 5}

    def test_tier_0_has_discover(self):
        assert OAuthScope.DISCOVER in OAUTH_TIER_SCOPES[0]

    def test_tier_5_has_system_admin(self):
        assert OAuthScope.SYSTEM_ADMIN in OAUTH_TIER_SCOPES[5]

    def test_all_scopes_covered(self):
        """Every OAuthScope member must appear in exactly one tier."""
        all_scopes = set()
        for scopes in OAUTH_TIER_SCOPES.values():
            all_scopes.update(scopes)
        assert all_scopes == set(OAuthScope)


class TestHardkeyChains:
    """HARDKEY_CHAINS and MA_KEY_COMBOS tests."""

    def test_hardkey_chains_non_empty(self):
        assert isinstance(HARDKEY_CHAINS, list)
        assert len(HARDKEY_CHAINS) == 12

    def test_each_chain_has_physical_key(self):
        for chain in HARDKEY_CHAINS:
            assert "physical_key" in chain
            assert "presses" in chain

    def test_ma_key_combos_non_empty(self):
        assert isinstance(MA_KEY_COMBOS, list)
        assert len(MA_KEY_COMBOS) == 29

    def test_each_combo_has_keyword(self):
        for combo in MA_KEY_COMBOS:
            assert "combo" in combo
            assert "keyword" in combo


class TestExecutorPrioritiesAndOptions:
    """Executor priority and assign option constant tests."""

    def test_priority_values_is_frozenset(self):
        assert isinstance(EXECUTOR_PRIORITY_VALUES, frozenset)

    def test_priority_values_content(self):
        expected = {"super", "swap", "htp", "high", "normal", "low"}
        assert expected == EXECUTOR_PRIORITY_VALUES

    def test_assign_option_names_is_frozenset(self):
        assert isinstance(EXECUTOR_ASSIGN_OPTION_NAMES, frozenset)

    def test_assign_option_names_has_priority(self):
        assert "priority" in EXECUTOR_ASSIGN_OPTION_NAMES

    def test_assign_options_list_matches_names(self):
        names_from_list = {o["option"] for o in EXECUTOR_ASSIGN_OPTIONS}
        assert names_from_list == EXECUTOR_ASSIGN_OPTION_NAMES

    def test_executor_button_functions_tuple(self):
        assert isinstance(EXECUTOR_BUTTON_FUNCTIONS, tuple)
        assert "Go" in EXECUTOR_BUTTON_FUNCTIONS

    def test_executor_fader_functions_tuple(self):
        assert isinstance(EXECUTOR_FADER_FUNCTIONS, tuple)
        assert "Master" in EXECUTOR_FADER_FUNCTIONS

    def test_priorities_list_length(self):
        assert len(EXECUTOR_PRIORITIES) == 6


class TestPresetTypes:
    """PRESET_TYPES mapping tests."""

    def test_is_dict(self):
        assert isinstance(PRESET_TYPES, dict)

    def test_has_expected_types(self):
        for name in ("dimmer", "position", "gobo", "color", "beam", "focus", "control"):
            assert name in PRESET_TYPES

    def test_dimmer_is_1(self):
        assert PRESET_TYPES["dimmer"] == 1


class TestStoreOptions:
    """STORE_*_OPTIONS tests."""

    def test_flag_options_is_set(self):
        assert isinstance(STORE_FLAG_OPTIONS, set)
        assert "overwrite" in STORE_FLAG_OPTIONS

    def test_bool_options_is_set(self):
        assert isinstance(STORE_BOOL_OPTIONS, set)
        assert "cueonly" in STORE_BOOL_OPTIONS

    def test_value_options_is_set(self):
        assert isinstance(STORE_VALUE_OPTIONS, set)
        assert "source" in STORE_VALUE_OPTIONS


class TestMA2Right:
    """MA2Right enum tests."""

    def test_has_6_members(self):
        assert len(MA2Right) == 6

    def test_right_to_scope_mapping_complete(self):
        for right in MA2Right:
            assert right in MA2RIGHT_TO_OAUTH_SCOPE


class TestMiscConstants:
    """Other constant type checks."""

    def test_bootstrap_users_list(self):
        assert isinstance(MA2_BOOTSTRAP_USERS, list)
        assert len(MA2_BOOTSTRAP_USERS) == 6

    def test_rights_levels_dict(self):
        assert isinstance(MA2_RIGHTS_LEVELS, dict)
        assert MA2_RIGHTS_LEVELS[5] == "Admin"

    def test_filter_attributes_dict(self):
        assert isinstance(FILTER_ATTRIBUTES, dict)
        assert "dimmer" in FILTER_ATTRIBUTES

    def test_filter_colors_dict(self):
        assert isinstance(FILTER_COLORS, dict)
        assert len(FILTER_COLORS) == 9

    def test_filter_vte_combos_list(self):
        assert isinstance(FILTER_VTE_COMBOS, list)
        assert len(FILTER_VTE_COMBOS) == 7
