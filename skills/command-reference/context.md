---
title: Command Reference Workspace Context
description: Workspace context for the GMA2 command reference skill
version: 1.0.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-13T00:00:00Z
---

# Command Reference Workspace Context

This workspace provides grandMA2 command syntax reference. No MCP tools are needed.

## Mode

Knowledge only. Output formatted command examples, syntax explanations, and keyword classifications.

## Scope

- 141 classified keywords (Function, Object, Helping)
- 157 pure command builder patterns
- Name quoting rules (quote_name with match_mode)
- Wildcard workflow (discover → pattern → filter)
- Three risk tiers: SAFE_READ, SAFE_WRITE, DESTRUCTIVE

## Output format

Always output commands in monospace code blocks, ready for copy-paste into the grandMA2 command line. Include the expected console response format when relevant.

## Boundaries

- Do NOT load or reference files from `src/` or `ee/` directories
- Do NOT attempt command execution — this is a knowledge-only workspace
- Keep responses under 2000 tokens unless the user asks for comprehensive documentation
