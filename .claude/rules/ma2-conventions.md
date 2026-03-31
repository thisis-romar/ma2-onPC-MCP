---
title: MA2 Console Conventions
description: grandMA2 onPC-specific command conventions, syntax rules, and live-verified behaviours for agent development
version: 1.0.0
created: 2026-03-30T00:00:00Z
last_updated: 2026-03-30T00:00:00Z
---

# MA2 Console Conventions

## New Show — Connectivity Preservation

Always use the default `preserve_connectivity=True` when calling `new_show()`.
Creating a new show without `/globalsettings` **resets Telnet to "Login Disabled"**.

The three flags auto-applied by `preserve_connectivity=True`:

| MA2 flag | What it preserves |
|---|---|
| `/globalsettings` | Telnet login enabled/disabled + MA-Net2 TTL/DSCP |
| `/network` | IP addresses and MA-Net2 network config |
| `/protocols` | Art-Net, sACN, DMX protocol assignments |

Only pass `preserve_connectivity=False` when the user **explicitly** wants a completely clean show AND understands they must manually re-enable Telnet.

## Name Quoting — quote_name()

All label/info/list commands that include a name use `quote_name(name, match_mode)` from `src/commands/helpers.py`.

- **Rule A (default)**: quote if the name contains any MA2 special character (`* @ $ . / ; [ ] ( ) " space`).
- **match_mode="wildcard"**: emits the name raw so `*` acts as a wildcard operator.
- Callers must pass the **raw name**, not a pre-quoted string.

## Wildcard Workflow — discover_object_names

1. Call `discover_object_names("Group")` → returns `names_only` list + `wildcard_tip`
2. Derive a pattern from the names (e.g. `Mac700*`)
3. Pass to `list_objects("group", name="Mac700*", match_mode="wildcard")` → `list group Mac700*`

## MAtricks Command Keywords (live-verified 2026-03-11)

MAtricks are controlled via **direct command keywords** — no `cd` navigation needed.

| Keyword | Syntax | Example |
|---------|--------|---------|
| `MAtricksInterleave` | `[width]`, `+/-`, `Off` | `MAtricksInterleave 4` |
| `MAtricksBlocks` | `[size]`, `[x].[y]`, `+ N/- N`, `Off` | `MAtricksBlocks 2.3` |
| `MAtricksGroups` | `[size]`, `[x].[y]`, `+ N/- N`, `Off` | `MAtricksGroups 4` |
| `MAtricksWings` | `[parts]`, `+/-`, `Off` | `MAtricksWings 2` |
| `MAtricksFilter` | `[num]`, `"name"`, `+/-`, `Off` | `MAtricksFilter "OddID"` |
| `MAtricksReset` | (no args) | `MAtricksReset` |

- `Interleave` is a synonym for `MAtricksInterleave`.
- **No `PreviousRow`** — only `NextRow` exists for Y-axis stepping.
- **No telnet command reads current MAtricks state** — only visible in GUI.

## Appearance Colors (live-verified 2026-03-11)

MA2 appearance commands use **0-100 percentage scale** for RGB and HSB.

| Mode | Parameters | Range |
|------|-----------|-------|
| RGB | `/r=R /g=G /b=B` | 0-100 each |
| HSB | `/h=H /s=S /br=BR` | hue 0-360, sat/bright 0-100 |
| Hex | `/color=RRGGBB` | 6-digit hex, no `#` |

XML format: `<Appearance Color="RRGGBB" />` embeds inside any pool object element.

## Import `/path=` Option (live-verified 2026-03-13)

MA2 Import/Export commands accept `/path=` for a custom directory. **Critical constraint**: path must use **forward slashes** and **no spaces** (use Windows 8.3 short names).

**8.3 short paths for this system:**

| Short path | Resolves to |
|------------|-------------|
| `C:/ProgramData/MALIGH~1/grandma/gma2_V_3.9.60/IMPORT~1/` | `importexport/` |
| `C:/ProgramData/MALIGH~1/grandma/gma2_V_3.9.60/IMPORT~1/filters` | `importexport/filters/` |
| `C:/ProgramData/MALIGH~1/grandma/gma2_V_3.9.60/macros/` | `macros/` |

## MA2 Data Directory Organization

```
macros/
  archive/        — iteration history, exports, duplicates
  utilities/      — Delete Group, Import-Type-Selector, Preset-Type-Selector
  stock/          — MA2 stock macros

importexport/
  filters/        — 168 filter library XMLs (filter_003..filter_170)
  imports/        — user import files
  exports/        — exported objects
```

## Macro Store Group Timing (live-verified 2026-03-13)

| Pattern | Result |
|---------|--------|
| `FixtureType X.M.1 Thru` (own line) → SetUserVar → `Store Group N /o` (later) | **WORKS** |
| `ClearAll ; FixtureType X.M.1 Thru` (one line) + `Store Group` (next) | **FAILS** — 1 subfixture |

When adding features to a working macro, insert new lines around existing logic — do not modify lines that perform critical Store operations.

## grandMA2 System Variables

Access via `list_system_variables()` (all 26) or `get_variable(action="echo", var_name="NAME")` (one).

**`Echo $VARNAME` does NOT work** — use `ListVar` instead.
**`SelFix`** (not `Select`) updates `$SELECTEDFIXTURESCOUNT`.
**`$SELECTEDEXEC` format:** `page.page.exec` (e.g. `1.1.201`).

Key variables: `$SHOWFILE`, `$USER`, `$USERRIGHTS`, `$SELECTEDEXEC`, `$SELECTEDEXECCUE`, `$SELECTEDFIXTURESCOUNT`, `$FADERPAGE`, `$VERSION`.

## PresetType / Feature / CD-Tree Correlation (live-verified 2026-03-10)

Calling `Feature [name]` or `PresetType [id]` updates `$PRESET`, `$FEATURE`, `$ATTRIBUTE` simultaneously.

| PresetType | ID | CD path | $PRESET |
|---|---|---|---|
| Dimmer | 1 | cd 10.2.1 | DIMMER |
| Position | 2 | cd 10.2.2 | POSITION |
| Color | 4 | cd 10.2.4 | COLOR |

## CD Tree Root Location

The root prompt name is **show-dependent** — do not hardcode `"Fixture"`.
Navigation code must detect the actual root dynamically (`cd /` then read prompt).

## Strategic Scan

Fast 4-phase re-scan completes in ~24 min vs 138 min full scan.

```bash
PYTHONUNBUFFERED=1 python -u scripts/strategic_scan.py [--output scan_output_new.json]
```

Show-dependent branches: cd 1, 10.3, 18, 22, 25, 30, 38, 39.
Firmware branches (stable across shows): cd 2-9, 15-16, 20, 23, 27, 36, 41-42.
