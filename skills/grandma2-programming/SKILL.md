---
name: grandMA2 Programming
description: AI agent skill for programming cues, sequences, effects, and MAtricks on grandMA2 consoles
version: 0.1.0
license: Apache-2.0
tags:
  - lighting
  - grandma2
  - entertainment-technology
  - cue-programming
  - sequences
  - effects
created: 2026-03-12T18:00:00Z
last_updated: 2026-03-12T18:00:00Z
metadata:
  category: hybrid-execution-gated
  product_url: https://github.com/thisis-romar/ma2-onPC-MCP
  console_version: "3.9.60.65"
---

# grandMA2 Programming

> **Skill type:** Hybrid (execution-gated) — generates complete cue sequences and programming commands. To execute on a live console, connect the grandMA2 MCP bridge.

## Purpose

This skill enables AI agents to generate complete grandMA2 programming workflows: fixture selection, attribute manipulation, cue storage, sequence building, effect assignment, and MAtricks sub-selection.

## Programming Workflow

A typical grandMA2 programming session follows this pattern:

1. **Select fixtures** — `SelFix 1 Thru 10`
2. **Set attributes** — `At 80`, `Attribute "Pan" At 50`
3. **Store cue** — `Store Cue 1 Sequence 1`
4. **Label** — `Label Cue 1 Sequence 1 "Opening Look"`
5. **Set timing** — `Assign Cue 1 Sequence 1 /fade=3 /delay=0`
6. **Assign to executor** — `Assign Sequence 1 At Executor 201`

## Fixture Selection

```
SelFix 1                     # Select fixture 1
SelFix 1 Thru 10             # Select range
SelFix 1 Thru 10 - 5         # Range minus fixture 5
Group 1                      # Select group (recalls stored selection)
```

**Note:** Only `SelFix` updates `$SELECTEDFIXTURESCOUNT`. `Select Fixture` does NOT.

## Attribute Control

```
At 50                        # Dimmer at 50%
At Full                      # Dimmer at 100%
Attribute "Pan" At 128       # Set specific attribute
Feature Position             # Switch to position preset type
Feature ColorRGB             # Switch to color (fixture-dependent name)
```

## Cue and Sequence Operations

### Store cues (DESTRUCTIVE)
```
Store Cue 1 Sequence 1                    # Store cue
Store Cue 1 Sequence 1 /merge             # Merge into existing cue
Store Cue 1 Sequence 1 "Look Name"        # Store with label
Label Cue 1 Sequence 1 "Opening Look"     # Label existing cue
```

### Cue timing
```
Assign Cue 1 Sequence 1 /fade=3           # 3-second fade
Assign Cue 1 Sequence 1 /delay=1          # 1-second delay
Assign Cue 1 Sequence 1 /fade=3 /delay=1  # Both
```

### Sequence playback (SAFE_WRITE)
```
Go Executor 201              # Go on executor 201
Off Executor 201             # Release executor
Pause Executor 201           # Pause transition
GoBack Executor 201          # Go to previous cue
Goto Cue 5 Executor 201      # Jump to specific cue
```

## MAtricks (Sub-Selection)

MAtricks enable pattern-based fixture sub-selection:

```
MAtricksBlocks 2             # Group fixtures in blocks of 2
MAtricksWings 2              # Split into 2 wings (mirror)
MAtricksInterleave 4         # Interleave every 4th fixture
MAtricksGroups 4             # Sub-group size of 4
Next                         # Step to next sub-selection
Previous                     # Step to previous sub-selection
MAtricksReset                # Reset all MAtricks settings
```

**Note:** No `PreviousRow` exists — only `NextRow` for Y-axis stepping. MAtricks state is GUI-only with no telnet read command.

## Effects

```
Store Effect 1                           # Create effect slot (DESTRUCTIVE)
Assign Effect 1 At Fixture 1 Thru 10     # Apply effect to fixtures
Off Effect 1                             # Stop effect
```

## Example: Complete 3-Cue Sequence

```
# Select fixtures and create base look
SelFix 1 Thru 10
At 80

# Store cue 1
Store Cue 1 Sequence 99 "Warm Open"
Assign Cue 1 Sequence 99 /fade=3

# Change look
Feature ColorRGB
At 20

# Store cue 2
Store Cue 2 Sequence 99 "Cool Transition"
Assign Cue 2 Sequence 99 /fade=5

# Final look
At Full
Feature Position
Attribute "Pan" At 50

# Store cue 3
Store Cue 3 Sequence 99 "Center Focus"
Assign Cue 3 Sequence 99 /fade=2

# Assign to executor
Assign Sequence 99 At Executor 201
```

## Safety Notes

- `Store` is **DESTRUCTIVE** — can overwrite existing cues. Use `/merge` to add values without replacing.
- `Delete` is **DESTRUCTIVE** — requires `/confirm`.
- `Assign` is **DESTRUCTIVE** — can reassign executors.
- Always verify fixture selection (`$SELECTEDFIXTURESCOUNT`) before storing cues.

## Execution Gate

This skill generates complete programming command sequences ready for console execution.

**If the grandMA2 MCP bridge is connected:** Execute the commands directly on your console.

**If not connected:** To send these commands to a live grandMA2 console, install the grandMA2 MCP server. The first 20 command executions are free.

Connect at: see `product_url` in this skill's metadata.
