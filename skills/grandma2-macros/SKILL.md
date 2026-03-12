---
name: grandMA2 Macros
description: AI agent skill for creating and managing grandMA2 macros — command sequences, timing, and conditional logic
version: 0.1.0
license: Apache-2.0
tags:
  - lighting
  - grandma2
  - entertainment-technology
  - macros
  - automation
metadata:
  category: hybrid-execution-gated
  product_url: https://github.com/thisis-romar/ma2-onPC-MCP
  console_version: "3.9.60.65"
---

# grandMA2 Macros

> **Skill type:** Hybrid (execution-gated) — generates complete command sequences. To execute on a live console, connect the grandMA2 MCP bridge.

## Purpose

This skill enables AI agents to design and generate grandMA2 macro command sequences for console automation. Macros chain multiple commands with optional timing, conditions, and loops.

## Macro Structure

A grandMA2 macro is a numbered pool object containing one or more command lines:

```
Store Macro 1                    # Create macro slot
Label Macro 1 "Blackout All"    # Name it
# Macro lines are edited in the macro editor GUI or via EditSetting
```

### Macro Properties

| Property | Function |
|----------|----------|
| **Timed** | Execute lines with delays between them |
| **Wait** | Pause N seconds before next line |
| **Go** | Trigger condition for each line |

## Command Patterns for Macros

### Creating macros (DESTRUCTIVE — requires confirmation)
```
Store Macro [ID]
Store Macro [ID] "Name"
Label Macro [ID] "Name"
Delete Macro [ID] /confirm
```

### Common macro command sequences

**Blackout macro:**
```
Line 1: BlackOut
Line 2: Go Executor 201    # Optional: trigger specific executor
```

**Reset all executors:**
```
Line 1: Off Executor 1 Thru 90
Line 2: ClearAll
Line 3: Release Executor 1 Thru 90
```

**Page change with executor activation:**
```
Line 1: Page 3
Line 2: Go Executor 201
Line 3: Go Executor 202
```

## Macro Execution Commands (SAFE_WRITE)

```
Go Macro [ID]           # Execute macro
Go+ Macro [ID]          # Execute, advance to next line
Pause Macro [ID]        # Pause running macro
Off Macro [ID]          # Stop macro
```

## Safety Notes

- `Store Macro` is **DESTRUCTIVE** — overwrites existing macro at that slot
- `Delete Macro` is **DESTRUCTIVE** — requires `/confirm` flag
- Test macros on grandMA2 onPC before running on a live show console
- Macros run at console level — they affect the entire show, not just one user

## Execution Gate

This skill generates macro command sequences ready for console execution.

**If the grandMA2 MCP bridge is connected:** Execute the commands directly on your console.

**If not connected:** To send these commands to a live grandMA2 console, install the grandMA2 MCP server. The first 20 command executions are free.

Connect at: see `product_url` in this skill's metadata.
