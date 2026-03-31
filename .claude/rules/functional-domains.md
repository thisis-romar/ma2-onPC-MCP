---
title: Functional Domains and Hardkey Reference
description: FunctionalDomain enum values, hardkey chains, MA+key combos, and executor priority levels
version: 1.1.0
created: 2026-03-30T00:00:00Z
last_updated: 2026-03-30T00:00:00Z
---

# Functional Domains and Hardkey Reference

## Functional Domains (`src/vocab.py`)

`FunctionalDomain` StrEnum (10 values) + `KEYWORD_DOMAINS` dict (198 entries).

| Domain | Count | Examples |
|--------|-------|---------|
| `object_manipulation` | 21 | Assign, Label, Appearance, Store, Copy, Delete |
| `playback_control` | 26 | Go, GoBack, Goto, Flash, Kill, Release, Freeze |
| `selection_filtering` | 28 | Select, Clear, If, Park, Highlight, Blind, SelFix |
| `timing_effects` | 37 | Fade, Speed, Rate, Crossfade, EffectBPM, EffectPhase |
| `network_session` | 20 | JoinSession, TakeControl, SetIP, Telnet, RemoteCommand |
| `system_admin` | 25 | Shutdown, SaveShow, NewShow, UpdateFirmware, Blackout |
| `data_query` | 18 | List, Info, Help, Search, ListVar, PSR |
| `variables_scripting` | 7 | SetVar, AddVar, SetUserVar, Call, Macro, Plugin |
| `matricks` | 8 | MAtricks, MAtricksInterleave, MAtricksBlocks, Interleave |
| `rdm` | 8 | RdmAutomatch, RdmAutopatch, RdmSetpatch, RdmUnmatch |

Also: `CD_KEYWORD_DESTINATIONS` (36 entries), `DEFAULT_KEYWORD_STATES` (10 entries).

## Hardkey Chains (physical key multi-press behaviour)

Defined in `src/commands/constants.py` as `HARDKEY_CHAINS` (12 chains).

| Physical Key | 1× | 2× | 3× | Hold/Other |
|---|---|---|---|---|
| **Assign** | `Assign` | `Label` | `Appearance` | — |
| **At** | `At` | `Normal` | — | hold → `Filter` |
| **Help** | `Help` | `CmdHelp` | — | — |
| **Fixture** | `Fixture` | `Selection` | — | — |
| **Full** | `Full` | `FullHighlight` | — | — |
| **Macro** | `Macro` | `Timecode` | `Agenda` | — |
| **Effect** | `Effect` | `Form` | — | — |
| **Blind** | `Blind` | — | — | hold 2s → `BlindEdit` |
| **Backup** | `Backup` | `QuickSave` | — | — |
| **Group** | `Group` | — | — | hold → GroupMasterView |
| **If** | `If` (helping) | — | — | 4× → `If` (function) |
| **Please** | Execute | Activate All | Deactivate All | 4× → Knock In |

## Key MA+key Combinations (selected, 29 total)

| Combo | Keyword | | Combo | Keyword |
|---|---|---|---|---|
| MA+Copy | `Export` | | MA+Move | `Import` |
| MA+Store | `StoreLook` | | MA+Off | `Kill` |
| MA+Clear | `ClearAll` | | MA+Edit | `BlindEdit` |
| MA+Fix | `SelFix` | | MA+Next | `NextRow` |
| MA+Go+ | `DefGoForward` | | MA+Go- | `DefGoBack` |
| MA+Oops | `ListOops` | | MA+B.O. | `BlackScreen` |
| MA+Full | `ToFull` | | MA+Down | `ToZero` |
| MA+Thru | `AllRows` | | MA+Align | `ShuffleSelection` |

## Executor Priority System

Defined in `src/commands/constants.py` as `EXECUTOR_PRIORITIES` (6 levels).

| Rank | Name | cmd_value | Behaviour |
|---|---|---|---|
| 1 | Super | `super` | LTP above ALL playbacks + programmer |
| 2 | Swap | `swap` | LTP > HTP; negative override possible |
| 3 | HTP | `htp` | Highest intensity value wins |
| 4 | High | `high` | High LTP; overrides Normal/Low |
| 5 | Normal | `normal` | LTP default; last triggered wins |
| 6 | Low | `low` | Lowest priority; overridden by everything |

Syntax: `Assign Executor [ID] /priority=[cmd_value]`

### Executor Assign Option Categories

| Category | Options |
|---|---|
| Start | autostomp, autostart, autostop, autofix, restart |
| Protect | ooo, swopprotect, killprotect |
| MIB | mibalways, mibnever, prepos |
| Function | chaser, softltp, wrap, crossfade |
| Timing | triggerisgo, cmddisable, effectspeed, autogo |
| Speed | speed, speedmaster, ratemaster |
| Layout | width |
