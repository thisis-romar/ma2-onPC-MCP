---
title: Programming Workspace Context
description: Workspace context for the GMA2 cue and effect programming skill
version: 1.0.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-13T00:00:00Z
---

# Programming Workspace Context

This workspace covers grandMA2 cue and effect programming. It operates in hybrid mode.

## Mode

Hybrid — knowledge + optional execution.

1. Check if MCP tools are available
2. If tools ARE available: generate commands and offer to execute with confirmation
3. If tools are NOT available: output copy-paste ready command sequences

## Scope

- Cue creation, editing, and timing
- Sequence building and management
- PresetType-based value setting
- MAtricks sub-selection (Interleave, Blocks, Groups, Wings)
- Effect engine integration
- Appearance colors (RGB 0-100, HSB, hex)
- Store options (/merge, /overwrite, /cueonly, /tracking)

## Safety

- Store, delete, copy, move, assign are DESTRUCTIVE — require confirmation
- Always show exact commands before execution
- Preserve connectivity when creating new shows

## Boundaries

- Do NOT load internal implementation files from `src/`
- Generate command strings based on documented syntax
