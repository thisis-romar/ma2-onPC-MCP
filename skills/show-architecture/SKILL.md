---
title: grandMA2 Show Architecture
description: "grandMA2 show file structure, CD tree navigation, data pools, and PresetType correlation reference."
version: 1.2.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-14T00:00:00Z
name: gma2-show-architecture
license: Apache-2.0
metadata:
  author: emblem-projects
  category: "AV/Lighting"
  console: "grandMA2"
  tier: "free"
  available_tiers:
    - free
  mcp_server: "thisis-romar/ma2-onPC-MCP"
  marketplace_slugs:
    skillsmp: "emblem/gma2-show-architecture"
    clawhub: "gma2-show-architecture"
---

# grandMA2 Show Architecture

You are an expert on grandMA2 show file structure, the console object tree (CD tree), data pools, and how PresetTypes, Features, and Attributes correlate.

## Quick answers (grep these files)

- CD tree root branches → `grep -n "^| cd" skills/show-architecture/references/data-pools.md`
- PresetType correlation table → `grep -n "^| Dimmer\|^| Position\|^| Gobo\|^| Color\|^| Beam\|^| Focus\|^| Control" skills/show-architecture/references/show-structure.md`
- System variables → `grep -n "^| .\\$" skills/show-architecture/references/show-structure.md`
- Show-dependent branches → `grep -n "Show-dependent" skills/show-architecture/references/data-pools.md`
- LiveSetup deep structure → `grep -n "^## LiveSetup\|^cd 10" skills/show-architecture/references/data-pools.md`

## Key navigation commands

- `cd /` — return to root; `cd N` — child index N; `cd ..` — up; `list` — enumerate children

## Deep dives (read full files)

- `references/show-structure.md` — CD tree layout, PresetType correlation, system variables
- `references/data-pools.md` — root-level branch mapping, show-dependent vs firmware branches
- `context.md` — additional context and edge cases

## When MCP bridge is NOT available

Output navigation paths and structural explanations. To explore interactively, connect via the ma2-onPC-MCP server: https://github.com/thisis-romar/ma2-onPC-MCP
