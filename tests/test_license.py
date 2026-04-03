# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
License Tier Feature Gating Tests

Tests for src/license.py — tier parsing, comparison, checking, and the
@require_tier decorator.  Also validates the TOOL_LICENSE_TIERS map in
src/license_tiers.py.
"""

import json

import pytest

# ============================================================================
# LicenseTier enum
# ============================================================================

class TestLicenseTierEnum:
    """Verify LicenseTier enum values and ordering."""

    def test_community_value(self):
        from src.license import LicenseTier
        assert str(LicenseTier.COMMUNITY) == "community"

    def test_professional_value(self):
        from src.license import LicenseTier
        assert str(LicenseTier.PROFESSIONAL) == "professional"

    def test_enterprise_value(self):
        from src.license import LicenseTier
        assert str(LicenseTier.ENTERPRISE) == "enterprise"

    def test_three_tiers_total(self):
        from src.license import LicenseTier
        assert len(LicenseTier) == 3

    def test_tier_rank_ordering(self):
        from src.license import _TIER_RANK, LicenseTier
        assert _TIER_RANK[LicenseTier.COMMUNITY] < _TIER_RANK[LicenseTier.PROFESSIONAL]
        assert _TIER_RANK[LicenseTier.PROFESSIONAL] < _TIER_RANK[LicenseTier.ENTERPRISE]


# ============================================================================
# get_license_tier
# ============================================================================

class TestGetLicenseTier:
    """Test GMA_LICENSE_TIER env var parsing."""

    def test_default_is_community(self, monkeypatch):
        monkeypatch.delenv("GMA_LICENSE_TIER", raising=False)
        from src.license import LicenseTier, get_license_tier
        assert get_license_tier() == LicenseTier.COMMUNITY

    def test_community_explicit(self, monkeypatch):
        monkeypatch.setenv("GMA_LICENSE_TIER", "community")
        from src.license import LicenseTier, get_license_tier
        assert get_license_tier() == LicenseTier.COMMUNITY

    def test_professional(self, monkeypatch):
        monkeypatch.setenv("GMA_LICENSE_TIER", "professional")
        from src.license import LicenseTier, get_license_tier
        assert get_license_tier() == LicenseTier.PROFESSIONAL

    def test_enterprise(self, monkeypatch):
        monkeypatch.setenv("GMA_LICENSE_TIER", "enterprise")
        from src.license import LicenseTier, get_license_tier
        assert get_license_tier() == LicenseTier.ENTERPRISE

    def test_case_insensitive(self, monkeypatch):
        monkeypatch.setenv("GMA_LICENSE_TIER", "PROFESSIONAL")
        from src.license import LicenseTier, get_license_tier
        assert get_license_tier() == LicenseTier.PROFESSIONAL

    def test_unknown_value_falls_back_to_community(self, monkeypatch):
        monkeypatch.setenv("GMA_LICENSE_TIER", "platinum")
        from src.license import LicenseTier, get_license_tier
        assert get_license_tier() == LicenseTier.COMMUNITY

    def test_whitespace_stripped(self, monkeypatch):
        monkeypatch.setenv("GMA_LICENSE_TIER", "  enterprise  ")
        from src.license import LicenseTier, get_license_tier
        assert get_license_tier() == LicenseTier.ENTERPRISE


# ============================================================================
# has_tier
# ============================================================================

class TestHasTier:
    """Test the has_tier() boolean check."""

    def test_community_has_community(self, monkeypatch):
        monkeypatch.setenv("GMA_LICENSE_TIER", "community")
        monkeypatch.delenv("GMA_LICENSE_BYPASS", raising=False)
        from src.license import LicenseTier, has_tier
        assert has_tier(LicenseTier.COMMUNITY) is True

    def test_community_lacks_professional(self, monkeypatch):
        monkeypatch.setenv("GMA_LICENSE_TIER", "community")
        monkeypatch.delenv("GMA_LICENSE_BYPASS", raising=False)
        from src.license import LicenseTier, has_tier
        assert has_tier(LicenseTier.PROFESSIONAL) is False

    def test_community_lacks_enterprise(self, monkeypatch):
        monkeypatch.setenv("GMA_LICENSE_TIER", "community")
        monkeypatch.delenv("GMA_LICENSE_BYPASS", raising=False)
        from src.license import LicenseTier, has_tier
        assert has_tier(LicenseTier.ENTERPRISE) is False

    def test_professional_has_community(self, monkeypatch):
        monkeypatch.setenv("GMA_LICENSE_TIER", "professional")
        monkeypatch.delenv("GMA_LICENSE_BYPASS", raising=False)
        from src.license import LicenseTier, has_tier
        assert has_tier(LicenseTier.COMMUNITY) is True

    def test_professional_has_professional(self, monkeypatch):
        monkeypatch.setenv("GMA_LICENSE_TIER", "professional")
        monkeypatch.delenv("GMA_LICENSE_BYPASS", raising=False)
        from src.license import LicenseTier, has_tier
        assert has_tier(LicenseTier.PROFESSIONAL) is True

    def test_professional_lacks_enterprise(self, monkeypatch):
        monkeypatch.setenv("GMA_LICENSE_TIER", "professional")
        monkeypatch.delenv("GMA_LICENSE_BYPASS", raising=False)
        from src.license import LicenseTier, has_tier
        assert has_tier(LicenseTier.ENTERPRISE) is False

    def test_enterprise_has_all(self, monkeypatch):
        monkeypatch.setenv("GMA_LICENSE_TIER", "enterprise")
        monkeypatch.delenv("GMA_LICENSE_BYPASS", raising=False)
        from src.license import LicenseTier, has_tier
        assert has_tier(LicenseTier.COMMUNITY) is True
        assert has_tier(LicenseTier.PROFESSIONAL) is True
        assert has_tier(LicenseTier.ENTERPRISE) is True

    def test_string_argument(self, monkeypatch):
        monkeypatch.setenv("GMA_LICENSE_TIER", "professional")
        monkeypatch.delenv("GMA_LICENSE_BYPASS", raising=False)
        from src.license import has_tier
        assert has_tier("professional") is True
        assert has_tier("enterprise") is False

    def test_invalid_string_returns_false(self, monkeypatch):
        monkeypatch.setenv("GMA_LICENSE_TIER", "enterprise")
        monkeypatch.delenv("GMA_LICENSE_BYPASS", raising=False)
        from src.license import has_tier
        assert has_tier("nonexistent") is False

    def test_bypass_grants_all(self, monkeypatch):
        monkeypatch.setenv("GMA_LICENSE_TIER", "community")
        monkeypatch.setenv("GMA_LICENSE_BYPASS", "1")
        from src.license import LicenseTier, has_tier
        assert has_tier(LicenseTier.ENTERPRISE) is True

    def test_bypass_off_does_not_grant(self, monkeypatch):
        monkeypatch.setenv("GMA_LICENSE_TIER", "community")
        monkeypatch.setenv("GMA_LICENSE_BYPASS", "0")
        from src.license import LicenseTier, has_tier
        assert has_tier(LicenseTier.PROFESSIONAL) is False


# ============================================================================
# require_tier decorator
# ============================================================================

class TestRequireTierDecorator:
    """Test the @require_tier async decorator."""

    @pytest.mark.asyncio
    async def test_allows_when_tier_sufficient(self, monkeypatch):
        monkeypatch.setenv("GMA_LICENSE_TIER", "professional")
        monkeypatch.delenv("GMA_LICENSE_BYPASS", raising=False)
        from src.license import LicenseTier, require_tier

        @require_tier(LicenseTier.PROFESSIONAL)
        async def my_tool():
            return "success"

        result = await my_tool()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_blocks_when_tier_insufficient(self, monkeypatch):
        monkeypatch.setenv("GMA_LICENSE_TIER", "community")
        monkeypatch.delenv("GMA_LICENSE_BYPASS", raising=False)
        from src.license import LicenseTier, require_tier

        @require_tier(LicenseTier.PROFESSIONAL)
        async def my_tool():
            return "success"

        result = await my_tool()
        assert result != "success"
        data = json.loads(result)
        assert data["blocked"] is True

    @pytest.mark.asyncio
    async def test_blocked_result_is_valid_json(self, monkeypatch):
        monkeypatch.setenv("GMA_LICENSE_TIER", "community")
        monkeypatch.delenv("GMA_LICENSE_BYPASS", raising=False)
        from src.license import LicenseTier, require_tier

        @require_tier(LicenseTier.ENTERPRISE)
        async def my_tool():
            return "success"

        result = await my_tool()
        data = json.loads(result)
        assert "license_required" in data
        assert data["license_required"] == "enterprise"
        assert "current_tier" in data
        assert data["current_tier"] == "community"

    @pytest.mark.asyncio
    async def test_preserves_function_name(self, monkeypatch):
        monkeypatch.setenv("GMA_LICENSE_TIER", "enterprise")
        from src.license import LicenseTier, require_tier

        @require_tier(LicenseTier.PROFESSIONAL)
        async def store_the_cue():
            return "ok"

        assert store_the_cue.__name__ == "store_the_cue"

    @pytest.mark.asyncio
    async def test_bypass_allows_all(self, monkeypatch):
        monkeypatch.setenv("GMA_LICENSE_TIER", "community")
        monkeypatch.setenv("GMA_LICENSE_BYPASS", "1")
        from src.license import LicenseTier, require_tier

        @require_tier(LicenseTier.ENTERPRISE)
        async def enterprise_tool():
            return "enterprise_ok"

        result = await enterprise_tool()
        assert result == "enterprise_ok"

    @pytest.mark.asyncio
    async def test_error_message_includes_tool_name(self, monkeypatch):
        monkeypatch.setenv("GMA_LICENSE_TIER", "community")
        monkeypatch.delenv("GMA_LICENSE_BYPASS", raising=False)
        from src.license import LicenseTier, require_tier

        @require_tier(LicenseTier.PROFESSIONAL)
        async def my_special_tool():
            return "ok"

        result = await my_special_tool()
        data = json.loads(result)
        assert "my_special_tool" in data["error"]

    @pytest.mark.asyncio
    async def test_enterprise_tier_allows_pro_tool(self, monkeypatch):
        monkeypatch.setenv("GMA_LICENSE_TIER", "enterprise")
        monkeypatch.delenv("GMA_LICENSE_BYPASS", raising=False)
        from src.license import LicenseTier, require_tier

        @require_tier(LicenseTier.PROFESSIONAL)
        async def pro_tool():
            return "pro_ok"

        result = await pro_tool()
        assert result == "pro_ok"


# ============================================================================
# TOOL_LICENSE_TIERS map validation
# ============================================================================

class TestToolLicenseTiers:
    """Validate the TOOL_LICENSE_TIERS mapping."""

    def test_all_values_are_valid_license_tiers(self):
        from src.license import LicenseTier
        from src.license_tiers import TOOL_LICENSE_TIERS
        for tool_name, tier in TOOL_LICENSE_TIERS.items():
            assert isinstance(tier, LicenseTier), (
                f"Tool '{tool_name}' has invalid tier type: {type(tier)}"
            )

    def test_no_community_tools_in_map(self):
        """COMMUNITY tools should NOT be in the map (absence = COMMUNITY)."""
        from src.license import LicenseTier
        from src.license_tiers import TOOL_LICENSE_TIERS
        for tool_name, tier in TOOL_LICENSE_TIERS.items():
            assert tier != LicenseTier.COMMUNITY, (
                f"Tool '{tool_name}' should not be in TOOL_LICENSE_TIERS "
                f"(COMMUNITY is the default for unlisted tools)"
            )

    def test_map_has_professional_tools(self):
        from src.license import LicenseTier
        from src.license_tiers import TOOL_LICENSE_TIERS
        pro_tools = [k for k, v in TOOL_LICENSE_TIERS.items()
                     if v == LicenseTier.PROFESSIONAL]
        assert len(pro_tools) > 50, (
            f"Expected >50 PROFESSIONAL tools, got {len(pro_tools)}"
        )

    def test_map_has_enterprise_tools(self):
        from src.license import LicenseTier
        from src.license_tiers import TOOL_LICENSE_TIERS
        ent_tools = [k for k, v in TOOL_LICENSE_TIERS.items()
                     if v == LicenseTier.ENTERPRISE]
        assert len(ent_tools) > 20, (
            f"Expected >20 ENTERPRISE tools, got {len(ent_tools)}"
        )

    def test_map_is_not_empty(self):
        from src.license_tiers import TOOL_LICENSE_TIERS
        assert len(TOOL_LICENSE_TIERS) > 100
