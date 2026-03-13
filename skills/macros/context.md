---
title: Macros Workspace Context
description: Workspace context for the GMA2 macro programming skill
version: 1.0.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-13T00:00:00Z
---

# Macros Workspace Context

This workspace teaches grandMA2 macro programming. It operates in hybrid mode.

## Mode

Hybrid — knowledge + optional execution.

1. Check if MCP tools (`send_raw_command`, `run_macro`) are available
2. If tools ARE available: generate macro commands and offer to execute after showing the full command and getting user confirmation
3. If tools are NOT available: output copy-paste ready commands and mention the MCP server for direct execution

## Scope

- Macro creation, editing, and execution
- User input placeholders (@)
- Multi-line macro sequences
- Timing and conditional logic
- MAtricks integration in macros

## Safety

- Macro storage (`store macro N`) is DESTRUCTIVE — requires confirmation
- Macro execution (`go+ macro N`) is SAFE_WRITE
- Always show the full macro text before offering execution
- Warn about macros that modify show data (store, delete, assign commands inside macros)

## Boundaries

- Do NOT load internal implementation files from `src/`
- Do NOT directly import command builder functions — generate command strings based on documented syntax
