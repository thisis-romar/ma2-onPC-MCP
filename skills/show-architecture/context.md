---
title: Show Architecture Workspace Context
description: Workspace context for the GMA2 show architecture skill
version: 1.0.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-13T00:00:00Z
---

# Show Architecture Workspace Context

This workspace provides grandMA2 show file structure and data pool reference. No MCP tools are needed.

## Mode

Knowledge only. Output structural explanations, navigation paths, and data pool descriptions.

## Scope

- CD tree structure (40+ root branches, up to 8 levels deep)
- PresetType / Feature / Attribute correlation (9 types)
- Show-dependent vs firmware-stable branches
- Root location behavior (show-dependent prompt name)
- Strategic scan phases for show comparison

## Output format

Use tree diagrams and navigation path notation (`cd N` → `list`) to illustrate structure. Include the cd index numbers for precise navigation.

## Boundaries

- Do NOT load or reference files from `src/` or `ee/` directories
- Do NOT attempt command execution — this is a knowledge-only workspace
