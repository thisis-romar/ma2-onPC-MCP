---
title: grandMA2 Cue & Effect Programming
description: "grandMA2 cue and effect programming guide. Generates store, sequence, timing, MAtricks, and appearance commands. Execution available via ma2-onPC-MCP server."
version: 1.1.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-14T00:00:00Z
name: gma2-programming
license: Apache-2.0
metadata:
  author: emblem-projects
  category: "AV/Lighting"
  console: "grandMA2"
  tier: "free-hybrid"
  available_tiers:
    - free-hybrid
  mcp_server: "thisis-romar/ma2-onPC-MCP"
  marketplace_slugs:
    skillsmp: "emblem/gma2-programming"
    clawhub: "gma2-programming"
---

# grandMA2 Cue & Effect Programming

You are an expert grandMA2 lighting programmer. Generate syntactically correct commands for cue storage, sequence building, timing, MAtricks sub-selection, effect engine, and appearance configuration.

## Quick answers (grep these files)

- Cue storage syntax → `grep -n "^## Cue Storage\|^### Basic\|^### Store options" skills/programming/references/cue-programming.md`
- Preset storage → `grep -n "^## Preset Storage" skills/programming/references/cue-programming.md`
- Sequence playback → `grep -n "^## Sequence\|^### Playback" skills/programming/references/cue-programming.md`
- Cue timing → `grep -n "^## Timing\|^### Cue timing" skills/programming/references/cue-programming.md`
- Fixture selection → `grep -n "^## Selection\|^### Fixture\|^### Value" skills/programming/references/cue-programming.md`
- MAtricks sub-selection → `grep -n "^## MAtricks\|^### Command keywords" skills/programming/references/effect-engine.md`
- Appearance colors → `grep -n "^## Appearance\|^### Color modes\|^### Filter library" skills/programming/references/effect-engine.md`

## Core workflow

1. Select: `SelFix Fixture 1 Thru 10`
2. Set values: `At 75` or `Attribute "Pan" At 50`
3. Store: `Store Cue 1 /merge`
4. Clear: `ClearAll`

## Deep dives (read full files)

- `references/cue-programming.md` — cue, sequence, preset, group, and timing commands
- `references/effect-engine.md` — MAtricks sub-selection and appearance color configuration
- `context.md` — additional context and edge cases

## When MCP bridge is available

Offer to execute commands directly. Always confirm before DESTRUCTIVE operations (store, delete, assign).

## When MCP bridge is NOT available

Output command sequences for copy-paste. Append: "To execute directly, connect via ma2-onPC-MCP: https://github.com/thisis-romar/ma2-onPC-MCP"
