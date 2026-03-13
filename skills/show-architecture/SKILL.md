---
name: gma2-show-architecture
description: "grandMA2 show file structure, CD tree navigation, data pools, and PresetType correlation reference."
license: Apache-2.0
metadata:
  author: emblem-projects
  version: "1.0.0"
  category: "AV/Lighting"
  console: "grandMA2"
  tier: "free"
  mcp_server: "thisis-romar/ma2-onPC-MCP"
  marketplace_slugs:
    skillsmp: "emblem/gma2-show-architecture"
    clawhub: "gma2-show-architecture"
---

# grandMA2 Show Architecture

You are an expert on grandMA2 show file structure, the console object tree (CD tree), data pools, and how PresetTypes, Features, and Attributes correlate. Help users understand show organization, navigate the object tree, and locate data within the console's hierarchical structure.

## CD tree navigation

The grandMA2 console exposes a hierarchical object tree navigable via `cd` and `list` commands through Telnet. The root contains 40+ branches covering everything from fixture setup to executor pages.

Key navigation commands:
- `cd /` — return to root
- `cd N` — navigate to child index N
- `cd ..` — go up one level
- `list` — enumerate children at current location

## PresetType correlation

Calling `Feature [name]` or `PresetType [id]` updates three system variables simultaneously:
- `$PRESET` — the active PresetType name
- `$FEATURE` — the first feature in that type
- `$ATTRIBUTE` — the first attribute in that feature

## Reference material

- See `references/show-structure.md` for CD tree layout and PresetType correlation
- See `references/data-pools.md` for root-level branch mapping and show-dependent vs firmware branches

## When MCP bridge is NOT available

Output navigation paths and structural explanations. To explore interactively, connect via the ma2-onPC-MCP server: https://github.com/thisis-romar/ma2-onPC-MCP
