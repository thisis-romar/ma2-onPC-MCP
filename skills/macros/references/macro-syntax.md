---
title: GMA2 Macro Syntax Reference
description: Detailed macro syntax, conditionals, variables, timing, triggers, and patterns for grandMA2
version: 1.1.0
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

## Conditional Execution

Macro lines can be conditionally executed using the `[$condition]` prefix. If the condition evaluates to false, the line is skipped.

### Syntax

```
[$variable == value] Command
[$variable != value] Command
[$variable < value] Command
[$variable > value] Command
```

### Operators

| Operator | Meaning |
|----------|---------|
| `==` | Equal to |
| `!=` | Not equal to |
| `<` | Less than |
| `>` | Greater than |

### Examples

```
Line 1: [$mymode == 1] Go Executor 1
Line 2: [$mymode == 2] Go Executor 2
Line 3: [$mymode == 3] Go Executor 3
```

```
Line 1: [$counter < 10] AddVar $counter + 1
Line 2: [$counter < 10] Go+ Macro 5
Line 3: [$counter == 10] SetVar $counter = 0
```

Conditions are evaluated per-line. Each line's condition is independent — there is no `else` or `elseif` construct.

## Variables

User variables persist until explicitly cleared or until the show file changes.

### SetVar — set a variable

```
SetVar $myvar = 100
SetVar "scene_name" = "intro"
```

### AddVar — modify a variable

```
AddVar $counter + 1          # Increment by 1
AddVar $counter - 5          # Decrement by 5
```

### Variable expansion

Variables are expanded inline with `$name` syntax:

```
Line 1: SetVar $intensity = 75
Line 2: SelFix Fixture 1 Thru 5
Line 3: At $intensity
```

### Scope

- User variables are global within the session
- Persist across macro calls
- Reset on show file change
- Shared with Lua plugins via `gma.show.getvar` / `gma.show.setvar`

## User Prompt Pop-ups

The `(prompt text)` syntax displays a pop-up dialog asking the user for input at runtime.

### Syntax

```
Command (Prompt text here)
```

### Examples

```
Line 1: Store Cue (Please enter cue number) /merge
Line 2: Goto Cue (Which cue to go to?)
```

### Difference from @

| Syntax | Behavior |
|--------|----------|
| `@` | Generic input prompt, no custom text |
| `(prompt text)` | Custom pop-up with descriptive text |

Both pause macro execution until the user provides input.

## Triggering Methods

Macros can be triggered from multiple sources:

| Method | Syntax / Setup | Notes |
|--------|---------------|-------|
| CLI | `go+ macro N` | Direct command line execution |
| Executor | `assign macro N executor M` | Button/fader press triggers macro |
| Cue macro field | Set in cue properties | Fires when cue executes |
| MIDI | MIDI Show Control setup | External MIDI trigger |
| MSC | MSC configuration | MIDI Show Control protocol |
| Timecode | Timecode event list | Time-synced execution |
| OSC | OSC input mapping | Open Sound Control trigger |
| Self-calling | `go+ macro N` inside macro N | Loop simulation (see below) |

## Timing

Macro lines execute sequentially with **no inter-line delay** by default.

### Wait command

Insert delays between lines with `Wait`:

```
Line 1: Go Executor 1
Line 2: Wait 2                # Wait 2 seconds
Line 3: Go Executor 2
Line 4: Wait 0.5              # Wait 500ms
Line 5: Go Executor 3
```

## Loop Simulation

grandMA2 macros have no native loop constructs (`for`, `while`). Simulate loops by having a macro call itself.

### Basic loop

```
# Macro 10 — loops until counter reaches 5
Line 1: AddVar $counter + 1
Line 2: SelFix Fixture $counter
Line 3: At Full
Line 4: [$counter < 5] Go+ Macro 10
Line 5: [$counter == 5] SetVar $counter = 0
```

### Infinite loop with delay

```
# Macro 11 — toggles blackout every 2 seconds forever
Line 1: BlackOut
Line 2: Wait 2
Line 3: Go+ Macro 11
```

**Warning:** Infinite self-calling macros with no `Wait` can hang the console. Always include a delay or exit condition.

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

## Limitations

| Limitation | Workaround |
|-----------|------------|
| No native loop/for/while | Self-calling macro + conditional `[$var]` |
| No string manipulation | Use Lua plugins for string operations |
| No direct DMX value read | Check system variables (`$SELECTEDFIXTURESCOUNT`, etc.) |
| No arithmetic expressions | Use `AddVar` for increment/decrement only |
| No subroutine return | Chain macros with `go+ macro N` (fire-and-forget) |
| Line count limit | Split into multiple macros chained together |

For complex logic beyond macro capabilities, use Lua plugins (see `skills/lua-scripting/`).
