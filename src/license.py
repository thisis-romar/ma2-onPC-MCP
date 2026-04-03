"""
License tier enforcement layer for feature gating.

This module provides license-tier-based authorization for MCP tools,
enabling community/professional/enterprise feature gating.

Mirrors the pattern from src/auth.py (OAuth scope enforcement).

Environment variables:
    GMA_LICENSE_TIER: The active license tier.
                      Values: "community" (default), "professional", "enterprise"
                      Community is always free. Professional and Enterprise
                      require a commercial license from the Licensor.
    GMA_LICENSE_BYPASS: Set to "1" to disable tier checking (dev/test mode).
                        WARNING: never set in production.

Decorator stacking order in src/server.py (critical):
    @mcp.tool()           <- FastMCP registration (outermost)
    @require_scope(...)   <- OAuth scope check (second)
    @_handle_errors       <- error formatting + license tier check (innermost)
    async def tool_fn():  <- actual implementation

When tier is insufficient, returns the same JSON shape as _handle_errors blocks:
    {"blocked": True, "error": "...", "license_required": "...", "current_tier": "..."}
"""

from __future__ import annotations

import functools
import json
import logging
import os
from enum import StrEnum

logger = logging.getLogger(__name__)


# ============================================================================
# License tier definitions
# ============================================================================

class LicenseTier(StrEnum):
    """Three-tier license model for feature gating."""
    COMMUNITY = "community"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


# Numeric rank for tier comparison (higher = more permissive).
_TIER_RANK: dict[LicenseTier, int] = {
    LicenseTier.COMMUNITY: 0,
    LicenseTier.PROFESSIONAL: 1,
    LicenseTier.ENTERPRISE: 2,
}


# ============================================================================
# Tier resolution from environment
# ============================================================================

def get_license_tier() -> LicenseTier:
    """
    Read GMA_LICENSE_TIER env var and return the corresponding LicenseTier.

    Defaults to COMMUNITY if unset or unrecognised.
    """
    raw = os.getenv("GMA_LICENSE_TIER", "community").strip().lower()
    try:
        return LicenseTier(raw)
    except ValueError:
        logger.warning(
            "Unrecognised GMA_LICENSE_TIER=%r, falling back to 'community'", raw,
        )
        return LicenseTier.COMMUNITY


# ============================================================================
# Tier check
# ============================================================================

def has_tier(required: LicenseTier | str) -> bool:
    """Return True if the current license tier is >= the required tier."""
    if os.getenv("GMA_LICENSE_BYPASS", "0") == "1":
        return True
    if isinstance(required, str):
        try:
            required = LicenseTier(required)
        except ValueError:
            return False
    current = get_license_tier()
    return _TIER_RANK[current] >= _TIER_RANK[required]


# ============================================================================
# require_tier decorator
# ============================================================================

def require_tier(tier: LicenseTier):
    """
    Decorator factory: blocks the MCP tool if the license tier is insufficient.

    Returns a JSON-serialised {"blocked": True, ...} string when access is
    denied, consistent with the existing _handle_errors response format.

    Usage (standalone):
        @mcp.tool()
        @require_tier(LicenseTier.PROFESSIONAL)
        @_handle_errors
        async def premium_tool(...):
            ...

    In practice, tier checking is done inside _handle_errors via the
    TOOL_LICENSE_TIERS map, so this decorator is available for explicit
    per-tool overrides if needed.
    """
    tier_str = str(tier)

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if not has_tier(tier):
                current = get_license_tier()
                logger.warning(
                    "LICENSE TIER DENIED: tool=%r requires=%r current=%r",
                    func.__name__, tier_str, str(current),
                )
                return json.dumps({
                    "blocked": True,
                    "error": (
                        f"Tool '{func.__name__}' requires the '{tier_str}' "
                        f"license tier. Current tier: '{current}'."
                    ),
                    "license_required": tier_str,
                    "current_tier": str(current),
                }, indent=2)
            return await func(*args, **kwargs)
        return wrapper
    return decorator
