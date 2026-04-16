# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Tests for src/commands/__init__.py — package re-exports (BR=67)."""

import src.commands as commands


class TestCommandsExports:
    """Verify the commands package re-exports all expected builders."""

    def test_all_count(self):
        """__all__ should list 262 exports (254 builders + 8 constants)."""
        assert len(commands.__all__) == 262

    def test_known_duplicate_lua_execute(self):
        """lua_execute appears twice in __all__ (known, harmless)."""
        count = commands.__all__.count("lua_execute")
        assert count == 2, "lua_execute duplicate count changed"

    def test_unique_exports_minus_known_dupes(self):
        """Aside from known duplicates, all exports should be unique."""
        known_dupes = {"lua_execute"}
        seen = set()
        unexpected = [
            n for n in commands.__all__
            if n not in known_dupes and (n in seen or seen.add(n))
        ]
        assert unexpected == [], f"Unexpected duplicate exports: {unexpected}"

    # -- Key builder functions exist -----------------------------------------

    def test_build_go_importable(self):
        assert callable(commands.go)

    def test_build_store_importable(self):
        assert callable(commands.store)

    def test_build_delete_importable(self):
        assert callable(commands.delete)

    def test_build_copy_importable(self):
        assert callable(commands.copy)

    def test_build_move_importable(self):
        assert callable(commands.move)

    def test_build_label_importable(self):
        assert callable(commands.label)

    def test_build_list_objects_importable(self):
        assert callable(commands.list_objects)

    def test_build_info_importable(self):
        assert callable(commands.info)

    def test_build_clear_importable(self):
        assert callable(commands.clear)

    def test_build_assign_importable(self):
        assert callable(commands.assign)

    def test_build_park_importable(self):
        assert callable(commands.park)

    def test_build_unpark_importable(self):
        assert callable(commands.unpark)

    # -- Constants re-exported ------------------------------------------------

    def test_preset_types_dict(self):
        assert isinstance(commands.PRESET_TYPES, dict)
        assert commands.PRESET_TYPES["dimmer"] == 1

    def test_ma2right_enum(self):
        assert hasattr(commands.MA2Right, "ADMIN")

    def test_store_flag_options(self):
        assert isinstance(commands.STORE_FLAG_OPTIONS, set)

    def test_store_bool_options(self):
        assert isinstance(commands.STORE_BOOL_OPTIONS, set)

    def test_store_value_options(self):
        assert isinstance(commands.STORE_VALUE_OPTIONS, set)

    # -- Helpers re-exported --------------------------------------------------

    def test_quote_name_importable(self):
        assert callable(commands.quote_name)

    def test_ma2_special_chars_importable(self):
        assert isinstance(commands.MA2_SPECIAL_CHARS, (set, frozenset))

    # -- Every __all__ name is actually importable ----------------------------

    def test_all_names_resolvable(self):
        """Every name in __all__ must be an attribute of the module."""
        missing = [name for name in commands.__all__ if not hasattr(commands, name)]
        assert missing == [], f"Missing attributes: {missing}"
