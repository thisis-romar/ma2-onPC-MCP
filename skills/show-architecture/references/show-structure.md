---
title: GMA2 Show Structure
description: CD tree layout, PresetType correlation, and root location behavior
version: 1.0.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-13T00:00:00Z
---

# GMA2 Show Structure

## CD Tree Root Location

The root prompt name is **show-dependent** — do not hardcode a specific name:
- Show `claude_ma2_ctrl`: root is `[Fixture]>`
- Different show loaded: root may be `[Screen]>`

Always use `cd /` then read the prompt to detect the actual root location.

## PresetType / Feature / CD-Tree Correlation

Live-verified on v3.9.60.65 onPC (2026-03-10).

Calling `Feature [name]` or `PresetType [id]` updates `$PRESET`, `$FEATURE`, and `$ATTRIBUTE` simultaneously. Feature names are fixture-dependent.

| PresetType | ID | CD path | $PRESET | $FEATURE (1st) | $ATTRIBUTE (1st) |
|------------|-----|---------|---------|----------------|------------------|
| Dimmer | 1 | cd 10.2.1 | DIMMER | DIMMER | DIM |
| Position | 2 | cd 10.2.2 | POSITION | POSITION | PAN |
| Gobo | 3 | cd 10.2.3 | GOBO | GOBO1 | GOBO1 |
| Color | 4 | cd 10.2.4 | COLOR | COLORRGB | COLORRGB1 |
| Beam | 5 | cd 10.2.5 | BEAM | SHUTTER | SHUTTER |
| Focus | 6 | cd 10.2.6 | FOCUS | FOCUS | FOCUS |
| Control | 7 | cd 10.2.7 | CONTROL | MSPEED | INTENSITYMSPEED |
| Shapers | 8 | cd 10.2.8 | — | fixture-dep | — |
| Video | 9 | cd 10.2.9 | — | fixture-dep | — |

## CD Tree Depth

The tree is navigable 4+ levels deep (verified with `list` at each level):

```
cd 10.2        → 9 PresetTypes
cd 10.2.5      → Beam features: SHUTTER(20), BEAM1(21), EFFECT(22)
cd 10.2.5.1    → Attributes under SHUTTER: SHUTTER(22), STROBE_RATIO(0)
cd 10.2.5.1.1  → SubAttributes of SHUTTER (Shutter, Strobe, Pulse, ...)
```

Note: `cd 10.2.N` uses sequential child index (1=first listed), not the internal library ID.

## System Variables

grandMA2 exposes 26 built-in read-only system variables. Key ones for show structure:

| Variable | Example | Notes |
|----------|---------|-------|
| `$SHOWFILE` | `claude_ma2_ctrl` | Current show name |
| `$VERSION` | `3.9.60.65` | Firmware version |
| `$PRESET` | `GOBO` | Active PresetType |
| `$FEATURE` | `GOBO1` | Active feature |
| `$ATTRIBUTE` | `GOBO1` | Active attribute |
| `$SELECTEDEXEC` | `1.1.201` | Selected executor (page.page.exec) |
| `$SELECTEDEXECCUE` | `NONE` or `1` | Active cue on selected executor |
| `$SELECTEDFIXTURESCOUNT` | `0`–`N` | Only updated by `SelFix` |
| `$FADERPAGE` | `1` | Current fader page |
| `$USER` | `administrator` | Current login |
| `$USERRIGHTS` | `Admin` | Permission level |

Access via:
- `ListVar` — returns all 26 variables
- `ListVar` + filter by name — read one variable

Note: `Echo $VARNAME` does NOT work (MA2 expands the variable before executing).

## Feature/Zoom Caveats

`Feature Color` and `Feature Zoom` error on fixtures that use `ColorRGB`/`Shutter` channel names instead. Use `PresetType [id]` as the reliable alternative.
