---
title: GMA2 Cue Programming Reference
description: Cue storage, sequence management, and timing commands for grandMA2
version: 1.0.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-13T00:00:00Z
---

# GMA2 Cue Programming Reference

## Cue Storage

### Basic cue store

```
store cue 1                     # Store cue 1 (prompts if exists)
store cue 1 /merge              # Merge into existing cue
store cue 1 /overwrite          # Overwrite existing cue
store cue 1 /noconfirm          # Skip confirmation prompt
```

### Store with sequence

```
store cue 1 sequence 99         # Store to specific sequence
store cue 1 sequence 99 /merge  # Merge into cue in sequence
```

### Store options

| Option | Purpose |
|--------|---------|
| `/merge` | Merge new values into existing cue |
| `/overwrite` | Replace existing cue entirely |
| `/remove` | Remove programmer values from cue |
| `/noconfirm` | Skip confirmation dialog |
| `/cueonly` | Store without tracking |
| `/tracking` | Store with tracking enabled |
| `/source` | Include source info |

## Preset Storage

```
store preset 1.3                # Store dimmer preset slot 3
store preset 2.5                # Store position preset slot 5
store preset 4.1                # Store color preset slot 1
```

PresetType IDs: 1=Dimmer, 2=Position, 3=Gobo, 4=Color, 5=Beam, 6=Focus, 7=Control

## Group Storage

```
store group 1                   # Store current selection as group 1
label group 1 "Front Wash"     # Label the group
```

## Sequence Management

### Playback

```
go executor 1                   # Go on executor 1
goback executor 1               # Go back
goto cue 5                      # Jump to cue 5
goto cue 5 sequence 1           # Jump to cue in specific sequence
pause sequence 1                # Pause sequence
go+ sequence 1                  # Go+ on sequence
```

### Sequence properties

```
assign sequence 1 at executor 6     # Assign sequence to executor
assign fade 3 cue 5                 # Set fade time on cue
assign_delay 2 cue 5                # Set delay time on cue
```

## Timing

### Cue timing

```
assign fade 3 cue 1            # 3-second fade
assign delay 2 cue 1           # 2-second delay before fade
```

### Executor properties

```
assign toggle at executor 101   # Set toggle function
assign flash at executor 102    # Set flash function
```

## Selection Patterns

### Fixture selection

```
selfix fixture 1 thru 10       # Select range
selfix fixture 1 + 3 + 5       # Select individual
group 3                         # Select by group
```

### Value setting

```
at 75                           # Set intensity to 75%
at full                         # Set to 100%
at 0                            # Set to 0%
attribute "Pan" at 50           # Set specific attribute
fixture 2 at 50                 # Set specific fixture
fixture 2 at fixture 3          # Copy from another fixture
```

### Relative values

```
+ 10                            # Increase by 10
- 5                             # Decrease by 5
```

## Complete Programming Workflow Example

```
# 1. Select fixtures
selfix fixture 1 thru 10

# 2. Set dimmer
at 75

# 3. Set position
attribute "Pan" at 50
attribute "Tilt" at 30

# 4. Apply color preset
call preset 4.3

# 5. Store as cue
store cue 1 /merge

# 6. Clear programmer
clearall

# 7. Build next cue
selfix fixture 11 thru 20
at full
store cue 2 /merge
clearall

# 8. Assign to executor
assign sequence 1 at executor 1

# 9. Set cue timing
assign fade 3 cue 1
assign fade 5 cue 2
```
