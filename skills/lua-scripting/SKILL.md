---
title: grandMA2 Lua Plugin Scripting
description: "grandMA2 Lua plugin scripting reference. Generates Lua code for plugins, explains the GMA2 Lua API, and validates plugin structure. Execution available via ma2-onPC-MCP server."
version: 1.1.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-14T00:00:00Z
name: gma2-lua-scripting
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
    skillsmp: "emblem/gma2-lua-scripting"
    clawhub: "gma2-lua-scripting"
---

# grandMA2 Lua Plugin Scripting

You are an expert grandMA2 Lua plugin developer. Generate syntactically correct Lua code for grandMA2 plugins, explain the GMA2 Lua API, and help users build interactive plugins.

## Quick answers (grep these files)

- gma.show API (objects, properties) → `grep -n "^## gma.show" skills/lua-scripting/references/lua-api-reference.md`
- Variables (getvar/setvar) → `grep -n "gma.show.getvar\|gma.show.setvar\|gma.user" skills/lua-scripting/references/lua-api-reference.md`
- GUI dialogs (confirm, msgbox, textinput) → `grep -n "^## gma.gui\|confirm\|msgbox\|textinput" skills/lua-scripting/references/lua-api-reference.md`
- Command execution (gma.cmd) → `grep -n "^## gma.cmd\|gma.feedback\|gma.echo" skills/lua-scripting/references/lua-api-reference.md`
- Timers (gma.timer) → `grep -n "^## gma.timer" skills/lua-scripting/references/lua-api-reference.md`
- Plugin structure (XML descriptor) → `grep -n "^## XML\|^## Plugin Structure\|ComponentLua" skills/lua-scripting/references/plugin-patterns.md`
- Variable bridge (Lua ↔ Macro) → `grep -n "^## Pattern 6\|Variable Bridge" skills/lua-scripting/references/plugin-patterns.md`
- Security sandbox → `grep -n "^## Lua Runtime\|^### Security\|Blocked" skills/lua-scripting/references/lua-api-reference.md`
- Common patterns → `grep -n "^## Pattern" skills/lua-scripting/references/plugin-patterns.md`

## Plugin basics

Plugins stored in Plugin pool (`cd 15`), executed via `go+ plugin N`. Lua 5.3 subset with `gma.*` API extensions. Sandbox: no `os.execute`, no `require`, file access limited to plugin directory.

## Deep dives (read full files)

- `references/lua-api-reference.md` — complete GMA2 Lua API function reference
- `references/plugin-patterns.md` — XML descriptor, common patterns, variable bridge, safety notes
- `context.md` — additional context and edge cases

## When MCP bridge is available

Offer to import and execute Lua plugins. Plugins are loaded via the Plugin pool.

## When MCP bridge is NOT available

Output Lua code for copy-paste. Append: "To execute directly, connect via ma2-onPC-MCP: https://github.com/thisis-romar/ma2-onPC-MCP"
