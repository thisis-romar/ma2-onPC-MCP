---
name: grandMA2 Command Reference
description: AI agent skill for generating correct grandMA2 console commands — covers 152 keywords, syntax patterns, and safety classifications
version: 0.1.0
license: Apache-2.0
tags:
  - lighting
  - grandma2
  - entertainment-technology
  - console-programming
metadata:
  category: instruction-only
  product_url: https://github.com/thisis-romar/ma2-onPC-MCP
  console_version: "3.9.60.65"
---

# grandMA2 Command Reference

> **Skill type:** Instruction-only — provides standalone reference value without requiring the MCP bridge.

## Purpose

This skill enables AI agents to generate syntactically correct grandMA2 lighting console commands. It covers the full 152-keyword vocabulary with risk-tier classifications, option flag syntax, and common command patterns.

## Keyword Categories

grandMA2 commands are built from three keyword categories:

| Category | Count | Examples |
|----------|-------|---------|
| Object keywords | 56 | `Fixture`, `Group`, `Sequence`, `Cue`, `Executor`, `Macro` |
| Function keywords | 89 | `Store`, `Delete`, `Copy`, `Go`, `Off`, `At`, `List`, `Info` |
| Helping keywords | 7 | `If`, `Thru`, `Please`, `Oops` |

## Safety Tiers

All commands are classified into three risk tiers:

| Tier | Policy | Examples |
|------|--------|---------|
| `SAFE_READ` | Always allowed | `list`, `info`, `cd`, `listvar` |
| `SAFE_WRITE` | Allowed in standard/admin modes | `go`, `at`, `clear`, `park`, `selfix` |
| `DESTRUCTIVE` | Requires explicit confirmation | `delete`, `store`, `copy`, `move`, `assign`, `new_show` |

## Command Syntax Patterns

### Basic: `Function Object [ID] [/options]`
```
Store Cue 1 Sequence 99
Delete Group 5 /confirm
Go Executor 201
```

### Addressing: `Object ID [Thru ID]`
```
Fixture 1 Thru 10
Group 1 + Group 3
Channel 1 Thru 100 - 50
```

### Value assignment: `Object At [Value] [/options]`
```
At 50
At Full
Fixture 1 At 80
```

### Name quoting
Names containing special characters (`* @ $ . / ; [ ] ( ) " space`) must be quoted:
```
Store Group 1 "Mac700 Front"
Label Sequence 1 "Main Show"
```

Plain names (no special characters) are emitted bare — no quotes needed.

## Wildcard Workflow

To filter objects by name pattern:
1. List all objects in a pool to discover names
2. Derive a wildcard pattern (e.g., `Mac700*`)
3. Use the pattern: `list group Mac700*`

The `*` character acts as a wildcard operator when used unquoted.

## Common Pitfalls

- `Echo $VARNAME` does NOT work — MA2 expands the variable before executing. Use `ListVar` to read variables.
- `Select Fixture N` does NOT update `$SELECTEDFIXTURESCOUNT` — only `SelFix N` does.
- `New Show` without `/globalsettings` resets Telnet to "Login Disabled" — always include `/globalsettings /network /protocols` to preserve connectivity.
- `Feature Color` errors on fixtures using `ColorRGB` channel names — use `Feature ColorRGB` instead.

## Execution

This skill generates command strings that can be:
1. **Reviewed manually** and typed into a grandMA2 command line
2. **Executed via the grandMA2 MCP bridge** — connect the MCP server to send commands directly to a console via Telnet

To execute commands on a live console, connect the grandMA2 MCP server at the product URL listed in this skill's metadata.
