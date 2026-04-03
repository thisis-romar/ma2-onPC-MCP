# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
Unit tests for the 6 new P2 playback command builders:
flash_go, flash_on, swop_go, swop_on, manual_xfade, snap_percent.
All tests are pure — no console connection required.
"""

import pytest
from src.commands import (
    flash_go,
    flash_on,
    manual_xfade,
    snap_percent,
    swop_go,
    swop_on,
)
from src.commands.functions.playback import (
    flash_go as _flash_go_direct,
    swop_go as _swop_go_direct,
)


class TestFlashGo:
    def test_bare(self):
        assert flash_go(3) == "FlashGo Executor 3"

    def test_page_qualified(self):
        assert flash_go(5, page=2) == "FlashGo Executor 2.5"

    def test_page_one(self):
        assert flash_go(10, page=1) == "FlashGo Executor 1.10"

    def test_large_id(self):
        assert flash_go(201) == "FlashGo Executor 201"

    def test_no_page_no_dot(self):
        result = flash_go(7)
        assert "." not in result

    def test_direct_import_matches_top_level(self):
        assert _flash_go_direct(3) == flash_go(3)
        assert _flash_go_direct(5, page=2) == flash_go(5, page=2)


class TestFlashOn:
    def test_bare(self):
        assert flash_on(3) == "FlashOn Executor 3"

    def test_page_qualified(self):
        assert flash_on(5, page=2) == "FlashOn Executor 2.5"

    def test_page_one(self):
        assert flash_on(10, page=1) == "FlashOn Executor 1.10"

    def test_large_id(self):
        assert flash_on(201) == "FlashOn Executor 201"

    def test_no_page_no_dot(self):
        result = flash_on(7)
        assert "." not in result


class TestSwopGo:
    def test_bare(self):
        assert swop_go(3) == "SwopGo Executor 3"

    def test_page_qualified(self):
        assert swop_go(5, page=2) == "SwopGo Executor 2.5"

    def test_large_id(self):
        assert swop_go(201) == "SwopGo Executor 201"

    def test_no_page_no_dot(self):
        result = swop_go(4)
        assert "." not in result

    def test_direct_import_matches_top_level(self):
        assert _swop_go_direct(3) == swop_go(3)


class TestSwopOn:
    def test_bare(self):
        assert swop_on(3) == "SwopOn Executor 3"

    def test_page_qualified(self):
        assert swop_on(5, page=2) == "SwopOn Executor 2.5"

    def test_large_id(self):
        assert swop_on(201) == "SwopOn Executor 201"

    def test_no_page_no_dot(self):
        result = swop_on(4)
        assert "." not in result


class TestManualXFade:
    def test_bare_integer(self):
        assert manual_xfade(3, 50) == "ManualXFade Executor 3 50"

    def test_bare_float(self):
        assert manual_xfade(3, 50.5) == "ManualXFade Executor 3 50.5"

    def test_zero_position(self):
        assert manual_xfade(3, 0) == "ManualXFade Executor 3 0"

    def test_full_position(self):
        assert manual_xfade(3, 100) == "ManualXFade Executor 3 100"

    def test_page_qualified(self):
        assert manual_xfade(5, 75, page=2) == "ManualXFade Executor 2.5 75"

    def test_no_page_no_dot(self):
        result = manual_xfade(4, 50)
        assert result.count(".") == 0


class TestSnapPercent:
    def test_integer(self):
        assert snap_percent(50) == "SnapPercent 50"

    def test_zero(self):
        assert snap_percent(0) == "SnapPercent 0"

    def test_full(self):
        assert snap_percent(100) == "SnapPercent 100"

    def test_float(self):
        assert snap_percent(33.3) == "SnapPercent 33.3"

    def test_no_executor_in_output(self):
        result = snap_percent(50)
        assert "Executor" not in result


class TestAllP2BuildersReturnStrings:
    def test_all_return_non_empty_strings(self):
        results = [
            flash_go(1),
            flash_on(1),
            swop_go(1),
            swop_on(1),
            manual_xfade(1, 50),
            snap_percent(50),
        ]
        for r in results:
            assert isinstance(r, str)
            assert len(r) > 0

    def test_no_newlines(self):
        results = [
            flash_go(1),
            flash_on(1),
            swop_go(1),
            swop_on(1),
            manual_xfade(1, 50),
            snap_percent(50),
        ]
        for r in results:
            assert "\n" not in r
            assert "\r" not in r

    def test_page_qualified_variants(self):
        page_results = [
            flash_go(1, page=2),
            flash_on(1, page=2),
            swop_go(1, page=2),
            swop_on(1, page=2),
            manual_xfade(1, 50, page=2),
        ]
        for r in page_results:
            assert "2.1" in r
