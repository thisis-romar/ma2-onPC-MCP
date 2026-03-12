---
name: grandMA2 Show Architecture
description: AI agent skill for understanding grandMA2 show file structure, CD tree navigation, and pool organization
version: 0.1.0
license: Apache-2.0
tags:
  - lighting
  - grandma2
  - entertainment-technology
  - show-management
created: 2026-03-12T18:00:00Z
last_updated: 2026-03-12T18:00:00Z
metadata:
  category: instruction-only
  product_url: https://github.com/thisis-romar/ma2-onPC-MCP
  console_version: "3.9.60.65"
---

# grandMA2 Show Architecture

> **Skill type:** Instruction-only — provides standalone reference value without requiring the MCP bridge.

## Purpose

This skill enables AI agents to understand and navigate grandMA2 show file internals: the CD tree hierarchy, pool organization, PresetType structure, and show-dependent vs firmware-stable branches.

## CD Tree Overview

grandMA2 organizes show data in a navigable tree accessed via `cd` and `list` commands. The root prompt name is **show-dependent** (e.g., `[Fixture]>` or `[Screen]>`).

### Key Branches

| CD Index | Content | Show-Dependent? |
|----------|---------|----------------|
| cd 1 | Showfile history | Yes |
| cd 10.2 | PresetTypes (9 types) | Partially |
| cd 10.3 | FixtureTypes | Yes |
| cd 18 | Worlds | Yes |
| cd 19 | Filters | Yes |
| cd 22 | Groups | Yes |
| cd 25 | Sequences | Yes |
| cd 30 | ExecutorPages | Yes |
| cd 38 | Layouts | Yes |
| cd 39 | UserProfiles | Yes |
| cd 2–9 | Firmware structures | Stable |
| cd 15–16 | Firmware structures | Stable |

### Navigation Depth

The tree is navigable 4+ levels deep:
```
cd 10.2        → 9 PresetTypes
cd 10.2.5      → Beam features: SHUTTER, BEAM1, EFFECT
cd 10.2.5.1    → Attributes under SHUTTER
cd 10.2.5.1.1  → SubAttributes of SHUTTER
```

Child addressing uses sequential index (1 = first listed), not internal library ID.

## PresetType / Feature Correlation

9 PresetTypes with fixture-dependent feature and attribute names:

| PresetType | ID | $PRESET | $FEATURE (1st) | $ATTRIBUTE (1st) |
|------------|----|---------|-----------------|--------------------|
| Dimmer | 1 | DIMMER | DIMMER | DIM |
| Position | 2 | POSITION | POSITION | PAN |
| Gobo | 3 | GOBO | GOBO1 | GOBO1 |
| Color | 4 | COLOR | COLORRGB | COLORRGB1 |
| Beam | 5 | BEAM | SHUTTER | SHUTTER |
| Focus | 6 | FOCUS | FOCUS | FOCUS |
| Control | 7 | CONTROL | MSPEED | INTENSITYMSPEED |
| Shapers | 8 | — | fixture-dep | — |
| Video | 9 | — | fixture-dep | — |

Calling `Feature [name]` or `PresetType [id]` updates `$PRESET`, `$FEATURE`, and `$ATTRIBUTE` simultaneously.

## Pool Organization

Shows contain numbered pools for each object type: Groups (cd 22), Sequences (cd 25), Macros, Effects, Presets (per PresetType), MAtricks, Filters, Layouts, and more. Each pool entry has an ID, optional name/label, and type-specific properties.

## System Variables

26 built-in read-only system variables accessible via `ListVar`:

| Variable | Example | Notes |
|----------|---------|-------|
| `$SHOWFILE` | `claude_ma2_ctrl` | Current show name |
| `$USER` | `administrator` | Current login |
| `$VERSION` | `3.9.60.65` | Firmware version |
| `$SELECTEDEXEC` | `1.1.201` | page.page.exec format |
| `$FADERPAGE` | `1` | Current fader page |

## Execution

This skill provides structural knowledge for understanding grandMA2 shows. To navigate and inspect a live show file, connect the grandMA2 MCP server at the product URL listed in this skill's metadata.
