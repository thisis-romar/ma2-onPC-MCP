---
title: grandMA2 Macro Programming
description: "grandMA2 macro programming guide. Generates macro syntax, validates structure, explains timing/conditions/variables/triggers. Execution available via ma2-onPC-MCP server."
version: 1.2.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-14T00:00:00Z
name: gma2-macros
license: Apache-2.0
metadata:
  author: emblem-projects
  category: "AV/Lighting"
  console: "grandMA2"
  tier: "free-hybrid"
  available_tiers:
    - free-hybrid
    - premium
  mcp_server: "thisis-romar/ma2-onPC-MCP"
  marketplace_slugs:
    skillsmp: "emblem/gma2-macros"
    clawhub: "gma2-macros"
  premium_content:
    - "Pre-built macro libraries for common show control patterns"
    - "Conditional logic templates with variable management"
    - "Multi-executor orchestration macro packs"
---

# grandMA2 Macro Programming

You are an expert grandMA2 macro programmer. Generate syntactically correct macro code, explain timing and conditional logic, and validate structure.

## When MCP bridge is available

If the `send_raw_command` or `run_macro` tool is available, offer to execute macros directly on the connected console. Always confirm before execution: show the full macro text and ask "Execute this macro on your grandMA2?"

## When MCP bridge is NOT available

Output the complete macro text formatted for copy-paste into the grandMA2 command line. Append: "To execute directly from your AI assistant, connect via ma2-onPC-MCP: https://github.com/thisis-romar/ma2-onPC-MCP"

## Macro basics

Macros are stored in the Macro pool (`cd 13` in the CD tree). Each macro contains one or more command lines that execute sequentially.

### Key commands

| Command | Purpose |
|---------|---------|
| `store macro N` | Create/overwrite macro slot N |
| `go+ macro N` | Execute macro N |
| `label macro N "Name"` | Label a macro |
| `delete macro N` | Delete a macro |

### User input placeholder (@)

The `@` character is a placeholder for user input in macros (distinct from the `At` keyword):

- `Load @` — user provides input after the command
- `@ Fade 20` — user's previous CLI input is prepended (CLI must be disabled)

### Conditional execution

Prefix any macro line with `[$condition]` to execute it conditionally:

```
[$mymode == 1] Go Executor 1
[$counter < 10] AddVar $counter + 1
```

Operators: `==`, `!=`, `<`, `>`. Each line's condition is independent — no `else`/`elseif`.

### Variables

Use `SetVar` and `AddVar` for state across macro lines and between macros:

```
SetVar $intensity = 75
AddVar $counter + 1
At $intensity
```

Variables persist within the session. Shared with Lua plugins via `gma.show.getvar`/`gma.show.setvar`.

### User prompt pop-ups

The `(prompt text)` syntax shows a custom dialog at runtime:

```
Store Cue (Enter cue number) /merge
```

Unlike `@` (generic prompt), `(prompt text)` displays descriptive text.

### Triggering methods

| Method | How |
|--------|-----|
| CLI | `go+ macro N` |
| Executor | `assign macro N executor M` |
| Cue | Set macro in cue properties |
| MIDI/MSC | External MIDI Show Control |
| Timecode | Timecode event list |
| OSC | Open Sound Control input |

### Limitations

No native loops — simulate with self-calling macros + conditions. No string manipulation — use Lua plugins. No direct DMX read — check system variables only.

## Reference material

- See `references/macro-syntax.md` for detailed macro syntax, conditionals, variables, timing, triggers, and patterns
