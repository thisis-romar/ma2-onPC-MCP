---
title: GMA2 Effect Engine & MAtricks Reference
description: MAtricks sub-selection and appearance color configuration for grandMA2
version: 1.0.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-13T00:00:00Z
---

# GMA2 Effect Engine & MAtricks Reference

## MAtricks Sub-Selection

MAtricks are controlled via direct command keywords — no `cd` navigation needed. The `manage_matricks` MCP tool dispatches to these keywords.

### Command keywords (live-verified 2026-03-11)

| Keyword | Syntax | Example |
|---------|--------|---------|
| `MAtricksInterleave` | `[width]`, `[col].[width]`, `+/-`, `Off` | `MAtricksInterleave 4` |
| `MAtricksBlocks` | `[size]`, `[x].[y]`, `+ N/- N`, `Off` | `MAtricksBlocks 2.3` |
| `MAtricksGroups` | `[size]`, `[x].[y]`, `+ N/- N`, `Off` | `MAtricksGroups 4` |
| `MAtricksWings` | `[parts]`, `+/-`, `Off` | `MAtricksWings 2` |
| `MAtricksFilter` | `[num]`, `"name"`, `+/-`, `Off` | `MAtricksFilter "OddID"` |
| `MAtricksReset` | (no args) | `MAtricksReset` |
| `MAtricks` | `[id]`, `On/Off/Toggle` | `MAtricks 5` |
| `All` | (no args) | Reset Single X sub-selection |
| `AllRows` | (no args) | Reset Single Y sub-selection |
| `Next` | (no args) | Step forward through Single X |
| `Previous` | (no args) | Step backward through Single X |
| `NextRow` | (no args) | Step forward through Single Y |

### Key notes

- `Interleave` is a synonym for `MAtricksInterleave`
- Y-axis settings (Block Y, Group Y) require Interleave to be active first
- **No `PreviousRow`** — asymmetric; only `NextRow` exists for Y-axis
- **No telnet command reads current MAtricks state** — only visible in GUI toolbar
- Pool path: `cd MAtricks` → `UserProfiles/Default 1/MatrixPool`

### MAtricks workflow example

```
# Select 20 fixtures
selfix fixture 1 thru 20

# Set interleave of 2 (every other fixture)
MAtricksInterleave 2

# Set first group to full
at full
store cue 1 /merge

# Step to next group
Next
at full
store cue 2 /merge

# Reset MAtricks
MAtricksReset
clearall
```

## Appearance Colors

MA2 appearance commands use **0-100 percentage scale** for RGB and HSB — NOT 0-255.

### Color modes

| Mode | Parameters | Range |
|------|-----------|-------|
| RGB | `/r=R /g=G /b=B` | 0-100 each |
| HSB | `/h=H /s=S /br=BR` | hue 0-360, sat/bright 0-100 |
| Hex | `/color=RRGGBB` | 6-digit hex, no `#` |

### Examples

```
appearance group 1 /r=100 /g=0 /b=0      # Red (RGB)
appearance group 1 /h=120 /s=100 /br=100  # Green (HSB)
appearance group 1 /color=0000FF           # Blue (Hex)
```

### XML format

`<Appearance Color="RRGGBB" />` embeds inside any pool object element:

```xml
<Group index="1" name="Front Wash">
  <Appearance Color="FF0000" />
</Group>
```

Colors imported via XML appear instantly — no telnet appearance loop needed.

### Filter library color scheme

9 categories with distinct colors (shared constants):

| Category | Hex | Color |
|----------|-----|-------|
| dimmer | `FFCC00` | warm yellow |
| position | `0088FF` | blue |
| gobo | `00CC44` | green |
| color | `FF00CC` | magenta |
| beam | `FF6600` | orange |
| focus | `00CCCC` | cyan |
| control | `999999` | grey |
| combo | `CC44FF` | purple |
| exclude | `FF3333` | red |

### MAtricks library color scheme

25 colors using HSB:
- **Wings** sets hue (5 hues evenly spaced: 0, 72, 144, 216, 288 degrees)
- **Groups** sets brightness (100/80/60/45/30)
- Embedded in XML via `<Appearance Color="hex" />`
