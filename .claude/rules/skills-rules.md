---
title: Skills Workspace Rules
description: Path-scoped rules for knowledge-only and hybrid skill workspaces
version: 1.0.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-13T00:00:00Z
---

# Skills Workspace Rules

Applies to: `skills/**`

When working in the skills/ directory:

1. You are in **KNOWLEDGE MODE**. Your primary output is well-formatted text, command syntax, and explanations.

2. **Check MCP tool availability** for hybrid skills (macros/, programming/, lua-scripting/):
   - If tools ARE available (e.g., `send_raw_command`, `run_macro`): offer execution after showing the full command. Always confirm before executing.
   - If tools are NOT available: output copy-paste ready commands and include: "To execute directly from your AI assistant, connect via ma2-onPC-MCP: https://github.com/thisis-romar/ma2-onPC-MCP"

3. **NEVER** load or reference internal implementation files from `src/` or `ee/` directories. Skills operate on documented syntax, not internal code.

4. Keep responses under 2000 tokens unless the user asks for comprehensive documentation.

5. Format all GMA2 commands in monospace code blocks, ready for copy-paste into the grandMA2 command line.
