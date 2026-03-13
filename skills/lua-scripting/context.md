---
title: Lua Scripting Workspace Context
description: Workspace context for the GMA2 Lua plugin scripting skill
version: 1.0.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-13T00:00:00Z
---

# Lua Scripting Workspace Context

This workspace covers grandMA2 Lua plugin development. It operates in hybrid mode.

## Mode

Hybrid — knowledge + optional execution.

1. Check if MCP tools are available
2. If tools ARE available: generate Lua plugin code and offer to load/execute on the console
3. If tools are NOT available: output complete Lua code for manual loading

## Scope

- GMA2 Lua API functions (gma.show, gma.gui, gma.network, etc.)
- Plugin structure and lifecycle
- UI dialogs (confirmation, text input, progress bars)
- Fixture and channel iteration
- Timer and callback patterns
- Show data access and modification

## Safety

- Lua plugins can execute any grandMA2 command internally
- Warn users about plugins that modify show data
- Always show complete plugin code before offering to load

## Boundaries

- Do NOT load internal implementation files from `src/`
- Generate Lua code based on the documented GMA2 Lua API
- Note: Lua API reference is based on MA2 documentation and community knowledge
