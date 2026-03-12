"""
Constants for grandMA2 Command Builder

This module contains all constants used by the command builder,
including preset type mappings, store option classifications,
and filter attribute groupings.
"""

# ============================================================================
# PRESET TYPE MAPPINGS
# ============================================================================
# grandMA2 uses numbers to distinguish preset types.
# These mappings convert human-readable names to numeric IDs.

PRESET_TYPES = {
    "dimmer": 1,
    "position": 2,
    "gobo": 3,
    "color": 4,
    "beam": 5,
    "focus": 6,
    "control": 7,
    "shapers": 8,
    "video": 9,
}


# ============================================================================
# STORE OPTION CLASSIFICATIONS
# ============================================================================
# Store options are classified into three types based on their value format.

# Store options that require no value (flag-only options)
# Usage: /merge, /overwrite, /noconfirm
STORE_FLAG_OPTIONS = {
    "merge",
    "overwrite",
    "remove",
    "noconfirm",
    "quiet",
    "global",
    "selective",
    "universal",
    "auto",
    "trackingshield",
    "embedded",
}

# Store options that require a boolean value
# Usage: /cueonly=true, /tracking=false
STORE_BOOL_OPTIONS = {
    "cueonly",
    "tracking",
    "keepactive",
    "presetfilter",
    "addnewcontent",
    "originalcontent",
    "effects",
    "values",
    "valuetimes",
}

# Store options that require a specific value
# Usage: /source=output, /screen=1
STORE_VALUE_OPTIONS = {
    "source",  # Prog, Output, DmxIn
    "useselection",  # Active, Allforselected, Activeforselected, All, Look
    "screen",  # 1..6
    "x",  # x coordinate
    "y",  # y coordinate
}


# ============================================================================
# FILTER ATTRIBUTE GROUPS BY PRESET TYPE (FIXTURE-DEPENDENT DEFAULTS)
# ============================================================================
# Attribute names grouped by PresetType, live-verified from Export Filter XML
# on grandMA2 onPC v3.9.60.65 (2026-03-11, show: claude_ma2_ctrl).
# These correspond to the AttributeLink names in MA2 Filter XML schema.
#
# WARNING: These are DEFAULTS for Mac 700 Profile Extended + Generic Dimmer.
# Shows with different fixtures (Rogue R1, SL Nitro, Elation Fuze, etc.)
# will have different attributes. Use discover_filter_attributes() MCP tool
# to get accurate values for the current show, then pass them to
# create_filter_library(fixture_attributes=...) for correct filter generation.

FILTER_ATTRIBUTES: dict[str, list[str]] = {
    "dimmer": ["DIM"],
    "position": [
        "PAN", "TILT", "POSITIONBLINK",
        "POSITIONOPTIMISATIONMODE", "POSITIONMSPEED",
    ],
    "gobo": [
        "GOBO1", "GOBO1_POS", "GOBO2",
        "ANIMATIONWHEEL", "ANIMATIONINDEXROTATE",
        "ANIMATIONWHEELINCLINE", "ANIMATIONINDEXROTATEMODE",
    ],
    "color": [
        "COLOR1", "COLOR1WHEELOFFSET", "COLOR1WHEELSELECTBLINK",
        "COLORRGB1", "COLORRGB2", "COLORRGB3",
        "COLORMIXER", "CYANMINIMUM", "MAGENTAMINIMUM", "YELLOWMINIMUM",
    ],
    "beam": [
        "SHUTTER", "IRIS", "PRISMA1",
        "EFFECTINDEXROTATE", "EFFECTWHEEL",
    ],
    "focus": ["FOCUS", "ZOOM"],
    "control": [
        "LAMPCONTROL", "LAMPPOWER", "FIXTUREGLOBALRESET",
        "WHEELMODE", "DUMMY", "INTENSITYMSPEED",
    ],
}

# Color scheme for filter pool appearance (hex RRGGBB, no # prefix).
# Used by create_filter_library to color-code filter categories.
FILTER_COLORS: dict[str, str] = {
    "dimmer":   "FFCC00",  # warm yellow
    "position": "0088FF",  # blue
    "gobo":     "00CC44",  # green
    "color":    "FF00CC",  # magenta
    "beam":     "FF6600",  # orange
    "focus":    "00CCCC",  # cyan
    "control":  "999999",  # grey
    "combo":    "CC44FF",  # purple (multi-type combos)
    "exclude":  "FF3333",  # red (No X filters)
}

# Value/ValueTimes/Effects on/off combinations (excluding all-off).
# Each tuple: (suffix, value, value_timing, effect).
# XML attributes: value="false", value_timing="false", effect="false"
# MA2 omits attributes that are true (the default).
# Live-verified on grandMA2 onPC v3.9.60.65 (2026-03-11).
FILTER_VTE_COMBOS: list[tuple[str, bool, bool, bool]] = [
    ("V",      True,  False, False),
    ("VT",     False, True,  False),
    ("E",      False, False, True),
    ("V+VT",   True,  True,  False),
    ("V+E",    True,  False, True),
    ("VT+E",   False, True,  True),
    ("V+VT+E", True,  True,  True),
]

