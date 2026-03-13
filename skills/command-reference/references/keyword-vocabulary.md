---
title: GMA2 Keyword Vocabulary
description: Classification of all 141 grandMA2 telnet keywords by category and risk tier
version: 1.0.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-13T00:00:00Z
---

# GMA2 Keyword Vocabulary

grandMA2 v3.9.60.65 exposes 141 keywords via the Telnet interface. Each keyword is classified by **category** (what it is) and **risk tier** (what it can do).

## Keyword Categories

| Category | Role | Examples |
|----------|------|----------|
| **Function** | Verbs — actions that do something | `Go`, `Store`, `Delete`, `Copy`, `Move`, `Select`, `Clear`, `Park` |
| **Object** | Nouns — things you act on | `Fixture`, `Group`, `Cue`, `Sequence`, `Executor`, `Preset`, `Macro` |
| **Helping** | Prepositions — modify context | `At`, `Thru`, `If`, `And`, `Page`, `Part` |

## Risk Tiers

Every keyword has a risk classification that determines whether a safety confirmation is required.

| Tier | Policy | Examples |
|------|--------|----------|
| `SAFE_READ` | Always allowed — read-only operations | `List`, `Info`, `cd`, `ListVar`, `Echo` |
| `SAFE_WRITE` | Allowed in standard/admin modes — modifies programmer or playback state | `Go`, `At`, `Clear`, `Park`, `SelFix`, `Call`, `Page`, `Feature` |
| `DESTRUCTIVE` | Blocked unless explicitly confirmed — permanently modifies show data | `Delete`, `Store`, `Copy`, `Move`, `Assign`, `Label`, `Import`, `Export`, `Oops` |

## Safety gate behavior

1. The safety gate classifies each command's first token using `classify_token()`
2. `SAFE_READ` commands always pass through
3. `SAFE_WRITE` commands pass in `standard` and `admin` safety modes
4. `DESTRUCTIVE` commands are blocked unless the caller sets `confirm_destructive=True`
5. Line breaks (`\r`, `\n`) in command strings are always rejected (injection prevention)

## Key Function Keywords

| Keyword | Risk Tier | Purpose |
|---------|-----------|---------|
| `Assign` | DESTRUCTIVE | Assign objects to targets |
| `Call` | SAFE_WRITE | Recall presets/cues |
| `Clear` | SAFE_WRITE | Clear programmer state |
| `ClearAll` | SAFE_WRITE | Clear all programmer data |
| `Copy` | DESTRUCTIVE | Duplicate objects |
| `Delete` | DESTRUCTIVE | Remove objects permanently |
| `Edit` | SAFE_WRITE | Open object editor |
| `Empty` | DESTRUCTIVE | Clear executor assignment |
| `Export` | DESTRUCTIVE | Export to XML file |
| `Go` | SAFE_WRITE | Trigger playback |
| `GoBack` | SAFE_WRITE | Reverse playback |
| `Goto` | SAFE_WRITE | Jump to cue |
| `Import` | DESTRUCTIVE | Import from XML file |
| `Info` | SAFE_READ | Query object details |
| `Label` | DESTRUCTIVE | Rename objects |
| `List` | SAFE_READ | Enumerate pool contents |
| `Move` | DESTRUCTIVE | Relocate objects |
| `Oops` | DESTRUCTIVE | Undo last action |
| `Park` | SAFE_WRITE | Lock output values |
| `Pause` | SAFE_WRITE | Pause playback |
| `Remove` | DESTRUCTIVE | Remove content |
| `SelFix` | SAFE_WRITE | Select fixtures (updates $SELECTEDFIXTURESCOUNT) |
| `Store` | DESTRUCTIVE | Save to show data |
| `Unpark` | SAFE_WRITE | Release locked values |

## Key Object Keywords

| Keyword | ID Syntax | Notes |
|---------|-----------|-------|
| `Fixture` | `fixture N` | Physical fixture ID |
| `Channel` | `channel N.sub` | Logical channel with optional sub-ID |
| `Group` | `group N` | Fixture group |
| `Preset` | `preset T.N` | T=PresetType ID, N=slot |
| `Cue` | `cue N` | Cue in active sequence |
| `Sequence` | `sequence N` | Cue sequence |
| `Executor` | `executor N` | Physical executor |
| `Macro` | `macro N` | Macro slot |
| `Layout` | `layout N` | Layout view |
| `DMX` | `dmx U.A` | U=universe, A=address |
| `Page` | `page N` or `page +/-` | Executor page |
| `Effect` | `effect N` | Effect engine slot |
| `Timecode` | `timecode N` | Timecode show |

## MAtricks Keywords

Direct command keywords for MAtricks sub-selection — no `cd` navigation needed:

| Keyword | Syntax | Example |
|---------|--------|---------|
| `MAtricksInterleave` | `[width]`, `[col].[width]`, `+/-`, `Off` | `MAtricksInterleave 4` |
| `MAtricksBlocks` | `[size]`, `[x].[y]`, `+ N/- N`, `Off` | `MAtricksBlocks 2.3` |
| `MAtricksGroups` | `[size]`, `[x].[y]`, `+ N/- N`, `Off` | `MAtricksGroups 4` |
| `MAtricksWings` | `[parts]`, `+/-`, `Off` | `MAtricksWings 2` |
| `MAtricksFilter` | `[num]`, `"name"`, `+/-`, `Off` | `MAtricksFilter "OddID"` |
| `MAtricksReset` | (no args) | `MAtricksReset` |
| `Next` / `Previous` | (no args) | Step through X sub-selection |
| `NextRow` | (no args) | Step through Y sub-selection |
| `All` / `AllRows` | (no args) | Reset X/Y sub-selection |
