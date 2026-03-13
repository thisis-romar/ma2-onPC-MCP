---
title: GMA2 Command Syntax Guide
description: Complete reference for 157 grandMA2 command builder patterns
version: 1.0.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-13T00:00:00Z
---

# GMA2 Command Syntax Guide

All commands follow the grandMA2 syntax: `[Function] [Object] [Options]`. Keywords are classified as **Function** (verbs), **Object** (nouns), or **Helping** (prepositions).

## Navigation (ChangeDest)

| Command | Output |
|---------|--------|
| `cd /` | Navigate to root |
| `cd ..` | Navigate up one level |
| `cd 5` | Navigate to child index 5 |
| `cd Group` | Navigate to Group pool |
| `cd Group.1` | Navigate to Group 1 |
| `cd Preset.4.1` | Navigate to Color Preset 1 |

## Object Keywords

| Command | Purpose |
|---------|---------|
| `fixture 34` | Select by Fixture ID |
| `channel 11.5` | Select by Channel ID with sub-ID |
| `group 3` | Select a group |
| `preset 2.5` | Apply preset (2=Position, 5=slot) |
| `cue 5` | Reference a cue |
| `cue 5 part 2` | Reference a cue part |
| `sequence 3` | Reference a sequence |
| `executor 1` | Reference an executor |
| `dmx 2.101` | Reference DMX address (universe.address) |
| `dmxuniverse 1` | Reference DMX universe |
| `layout 1` | Reference a layout |
| `attribute "Pan"` | Reference an attribute |
| `feature 1` | Reference a feature |
| `timecode 1` | Reference a timecode show |
| `timer 1` | Reference a timer |

## Selection & Clear

| Command | Purpose |
|---------|---------|
| `selfix fixture 1 thru 10` | Select fixture range |
| `selfix fixture 1 + 3 + 5` | Select individual fixtures |
| `clear` | Clear programmer |
| `clearselection` | Clear selection only |
| `clearactive` | Clear active values |
| `clearall` | Clear everything |

## Store

| Command | Purpose |
|---------|---------|
| `store macro 5` | Store to macro slot 5 |
| `store cue 1 /merge` | Store cue 1 with merge |
| `store preset 1.3` | Store dimmer preset slot 3 |
| `store group 1` | Store current selection as group |

**Store options:** `/merge`, `/overwrite`, `/remove`, `/noconfirm`, `/cueonly`, `/tracking`, `/source`

## Playback

| Command | Purpose |
|---------|---------|
| `go executor 1` | Go on executor 1 |
| `goback executor 1` | Go back on executor 1 |
| `goto cue 5` | Jump to cue 5 |
| `go+ sequence 1` | Go+ on sequence 1 |
| `pause sequence 1` | Pause sequence 1 |
| `goto cue 5 sequence 1` | Jump to cue 5 in sequence 1 |
| `<<<` | Fast back |
| `>>>` | Fast forward |

## At (Values)

`At` functions as both a Function Keyword and a Helping Keyword.

| Command | Purpose |
|---------|---------|
| `at 75` | Set value to 75% |
| `at full` | Set to full (100%) |
| `at 0` | Set to zero |
| `at cue 3` | Set from cue 3 values |
| `at fade 2` | Set fade time 2s |
| `attribute "Pan" at 20` | Set Pan to 20 |
| `fixture 2 at 50` | Set fixture 2 to 50% |
| `fixture 2 at fixture 3` | Copy values from fixture 3 |
| `channel 1 at 75` | Set channel 1 to 75% |
| `group 3 at 50` | Set group 3 to 50% |
| `executor 3 at 50` | Set executor 3 to 50% |

## Copy, Move, Cut, Paste

| Command | Purpose |
|---------|---------|
| `copy group 1 at 5` | Copy group 1 to slot 5 |
| `copy group 1 thru 3 at 11` | Copy range to slot 11 |
| `move group 5 at 9` | Move group 5 to slot 9 |
| `cut preset 4.1` | Cut color preset 1 |
| `paste group 5` | Paste to group 5 |

**Options:** `/overwrite`, `/merge`, `/status`, `/cueonly`, `/noconfirm`

## Delete & Remove

| Command | Purpose |
|---------|---------|
| `delete cue 7` | Delete cue 7 |
| `delete cue 1 thru 5 /noconfirm` | Delete cue range |
| `delete group 3` | Delete group 3 |
| `delete preset 4.5` | Delete color preset 5 |
| `delete fixture 4` | Delete fixture 4 |
| `delete messages` | Clear message center |
| `remove selection` | Remove from programmer |
| `remove presettype "position"` | Remove position data |
| `remove fixture 1 if PresetType 1` | Conditional remove |

## Assign

| Command | Purpose |
|---------|---------|
| `assign sequence 1 at executor 6` | Assign sequence to executor |
| `assign dmx 2.101 at channel 5` | Assign DMX to channel |
| `assign toggle at executor 101` | Assign toggle function |
| `assign fade 3 cue 5` | Set fade time on cue |
| `assign group 1 at layout 1 /x=5 /y=2` | Place on layout |
| `empty executor 1` | Clear executor assignment |

## Label & Appearance

| Command | Purpose |
|---------|---------|
| `label group 3 "All Studiocolors"` | Label a group |
| `label preset 2.1 "Red"` | Label a preset |
| `appearance preset 0.1 /r=100` | Set RGB appearance |
| `appearance group 1 /color=FF0000` | Set hex appearance |

**Appearance scales:** RGB and HSB use 0-100 percentage (NOT 0-255). Hex uses 6-digit `RRGGBB` format.

## Info & List

| Command | Purpose |
|---------|---------|
| `list cue` | List all cues |
| `list group` | List all groups |
| `list preset 4` | List color presets |
| `info cue 1` | Get cue 1 details |
| `info group 3` | Get group 3 details |

## Park & Unpark

| Command | Purpose |
|---------|---------|
| `park fixture 1` | Park fixture output |
| `park dmx 101 at 128` | Park DMX at value |
| `unpark fixture 1` | Release parked fixture |

## Call

| Command | Purpose |
|---------|---------|
| `call preset 2.1` | Call position preset 1 |
| `call cue 3 sequence 1` | Call cue from sequence |

## Variables

| Command | Purpose |
|---------|---------|
| `setvar "myvar" 42` | Set show variable |
| `setuservar "speed" 100` | Set user variable |
| `addvar "counter" 1` | Increment variable |
| `adduservar "counter" 1` | Increment user variable |

## Helping Keywords

| Command | Purpose |
|---------|---------|
| `+ 10` | Relative value up |
| `- 5` | Relative value down |
| `+ fixture 5` | Add to selection |
| `- fixture 3` | Remove from selection |
| `page +` | Next page |
| `page -` | Previous page |
| `and group 1` | AND condition |
| `if PresetType 1` | IF condition |

## Macro Placeholder (@)

The `@` character is a placeholder for user input in macros (distinct from the `At` keyword).

| Command | Purpose |
|---------|---------|
| `Load @` | User input after command |
| `@ Fade 20` | User input before command (CLI must be disabled) |

## PresetType ID Mapping

| Type | ID | Example |
|------|----|---------|
| Dimmer | 1 | `preset 1.3` |
| Position | 2 | `preset 2.5` |
| Gobo | 3 | `preset 3.1` |
| Color | 4 | `preset 4.2` |
| Beam | 5 | `preset 5.1` |
| Focus | 6 | `preset 6.1` |
| Control | 7 | `preset 7.1` |
| Shapers | 8 | `preset 8.1` |
| Video | 9 | `preset 9.1` |
