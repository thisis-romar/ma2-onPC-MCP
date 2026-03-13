---
title: GMA2 Macro Syntax Reference
description: Detailed macro syntax, multi-line patterns, and timing for grandMA2
version: 1.0.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-13T00:00:00Z
---

# GMA2 Macro Syntax Reference

## Macro Storage

Macros are stored in the Macro pool (cd index 13). Each macro slot can contain multiple command lines.

### Creating macros via Telnet

```
store macro 1                    # Create/overwrite macro slot 1
label macro 1 "My Macro"        # Label the macro
```

### Executing macros

```
go+ macro 1                     # Run macro 1
```

### Multi-line macros

Each line in a macro is a separate grandMA2 command. Lines execute sequentially. To create multi-line macros via Telnet, use the `edit macro N` workflow:

1. `store macro 1` — create the slot
2. Edit the macro content through the macro editor
3. Each line is a standard grandMA2 command

## User Input Placeholder (@)

The `@` character in macros prompts for user input at runtime.

### @ at the end

```
Load @
```
When this macro line executes, the console waits for user input. The user types a value and it's appended to `Load`.

### @ at the beginning

```
@ Fade 20
```
The user's previous command line input is prepended. **Note:** CLI must be disabled for this to work correctly.

### Examples

| Macro line | User types | Executed command |
|------------|-----------|-----------------|
| `Load @` | `Show1` | `Load Show1` |
| `Goto Cue @` | `5` | `Goto Cue 5` |
| `@ At 50` | `Fixture 1 Thru 10` | `Fixture 1 Thru 10 At 50` |

## Common Macro Patterns

### Blackout toggle

```
Line 1: BlackOut
```

### Select and set

```
Line 1: SelFix Fixture 1 Thru 10
Line 2: At 75
```

### Store a cue sequence

```
Line 1: SelFix Fixture 1 Thru 10
Line 2: At Full
Line 3: Store Cue 1 /merge
Line 4: ClearAll
Line 5: SelFix Fixture 11 Thru 20
Line 6: At Full
Line 7: Store Cue 2 /merge
Line 8: ClearAll
```

### Playback control

```
Line 1: Go Executor 1
Line 2: Go Executor 2
```

### Variable-based macros

```
Line 1: SetVar "intensity" 75
Line 2: SelFix Fixture 1 Thru 5
Line 3: At $intensity
```

## MAtricks in Macros

MAtricks commands can be used inside macros for complex sub-selection:

```
Line 1: SelFix Fixture 1 Thru 20
Line 2: MAtricksInterleave 2
Line 3: At Full
Line 4: Store Cue 1 /merge
Line 5: Next
Line 6: At Full
Line 7: Store Cue 2 /merge
Line 8: MAtricksReset
Line 9: ClearAll
```

## Safety Considerations

| Command in macro | Risk tier | Notes |
|-----------------|-----------|-------|
| `SelFix`, `At`, `Go`, `Clear` | SAFE_WRITE | Safe for automated use |
| `Store`, `Delete`, `Assign`, `Label` | DESTRUCTIVE | Modifies show data permanently |
| `NewShow` | DESTRUCTIVE | Can sever Telnet connectivity |

Always review macro contents before execution, especially if they contain DESTRUCTIVE commands.
