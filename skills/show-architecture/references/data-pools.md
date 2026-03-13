---
title: GMA2 Data Pools
description: Root-level branch mapping of the grandMA2 console object tree
version: 1.0.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-13T00:00:00Z
---

# GMA2 Data Pools

## Root Level Summary (`cd /`)

Live-scanned from grandMA2 onPC v3.9.60.65 (8,293 nodes, 138 min scan).

| cd | Location | Entries | Max Depth | Notes |
|----|----------|---------|-----------|-------|
| 1 | Showfile | 37 | 2 | Show history |
| 2 | TimeConfig | 0 | 1 | LEAF |
| 3 | Settings | 6 | 4 | Console settings |
| 4 | DMX_Protocols | 6 | 3 | Art-Net, sACN config |
| 5 | NetConfig | 5 | 4 | MA-Net2 network |
| 6 | CITPNetConfig | 0 | 1 | LEAF |
| 7 | TrackingSystems | 0 | 1 | LEAF |
| 8 | UserImagePool | 13 | 2 | Custom images |
| 9 | RDM_Data | 2 | 3 | RDM discovery |
| 10 | LiveSetup | 6 | 8 | Fixtures, patch, types |
| 13 | Macros | 0 | 1 | LEAF (empty show) |
| 14 | FlightRecordings | 0 | 1 | LEAF |
| 15 | Plugins | 1 | 2 | Lua plugins |
| 16 | Gels | 13 | 3 | Gel library (144 entries) |
| 17 | Presets | 0 | 1 | LEAF |
| 18 | Worlds | 1 | 2 | Show worlds |
| 19 | Filters | 1 | 2 | Programmer filters |
| 20 | FadePaths | 0 | 1 | LEAF |
| 21 | Programmer | 0 | 1 | LEAF |
| 22 | Groups | 0 | 1 | LEAF (empty show) |
| 23 | Forms | 23 | 4 | Form library |
| 24 | Effects | 0 | 1 | LEAF |
| 25 | Sequences | 0 | 1 | LEAF (empty show) |
| 26 | Timers | 1 | 2 | Timer pool |
| 27 | MasterSections | 0 | 1 | LEAF |
| 30 | ExecutorPages | 2 | 4 | Executor assignments |
| 31 | ChannelPages | 9 | 2 | Channel pages |
| 33 | Songs | 0 | 1 | LEAF |
| 34 | Agendas | 0 | 1 | LEAF |
| 35 | Timecodes | 0 | 1 | LEAF |
| 36 | RemoteTypes | 3 | 2 | Remote input config |
| 37 | DMXSnapshotPool | 0 | 1 | LEAF |
| 38 | Layouts | 1 | 5 | Layout views |
| 39 | UserProfiles | 254 | 5 | User profiles (7,345 nodes) |
| 40 | Users | 3 | 2 | User accounts |
| 41 | PixelMapperContainer | 3 | 2 | Pixel mapping |
| 42 | NDP_Root | 0 | 1 | LEAF |

**Invalid indexes** (Error #72): 12, 28, 29, 32, 44, 45, 47, 48, 49, 50

## Show-Dependent vs Firmware Branches

**Show-dependent** (vary between show files):
- cd 1 (Showfile history)
- cd 10.3 (FixtureTypes)
- cd 13 (Macros)
- cd 18 (Worlds)
- cd 19 (Filters)
- cd 22 (Groups)
- cd 24 (Effects)
- cd 25 (Sequences)
- cd 30 (ExecutorPages)
- cd 38 (Layouts)
- cd 39 (UserProfiles)

**Firmware-stable** (same across shows):
- cd 2-9 (TimeConfig, Settings, DMX, Network, CITP, Tracking, Images, RDM)
- cd 15-16 (Plugins, Gels)
- cd 20 (FadePaths)
- cd 23 (Forms)
- cd 27 (MasterSections)
- cd 36 (RemoteTypes)
- cd 41-42 (PixelMapper, NDP)

## LiveSetup Deep Structure (cd 10)

The LiveSetup branch is the deepest and most complex:

```
cd 10          → LiveSetup (6 children)
cd 10.1        → Stages
cd 10.2        → PresetTypes (9 types, navigable 6 levels deep)
cd 10.3        → FixtureTypes (fixture library, show-dependent)
cd 10.4        → FixtureLayers
cd 10.5        → DMX addresses
cd 10.6        → Patch schedule
```

## MCP Tool → Tree Branch Mapping

| Tool Category | Tree Branch | Verification Path |
|---------------|-------------|-------------------|
| Fixture groups | `cd Group` | `cd Group` → `list` → check group ID |
| Cue storage | `cd Sequence.N` | `cd Sequence.N` → `list` → check cue |
| Presets | `cd PresetType.N` | `cd PresetType.N` → `list` → check slot |
| Executors | `cd Executor` | `cd Executor` → `list` → check assignment |
| Layouts | `cd Layout.N` | `cd Layout.N` → `list` → check objects |
| Macros | `cd Macro` | `cd Macro` → `list` → check macro slot |
| Filters | `cd Filter` | `cd Filter` → `list` → check filter ID |
