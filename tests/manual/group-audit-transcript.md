---
title: Group Audit Transcript — nomad22-may11 + 19-toronto-v4
description: Chronological log of group audit, camera-safety pre-flight, and Macro 16/17 dependency analysis
version: 1.2.0
created: 2026-05-11T16:44:00Z
last_updated: 2026-05-11T19:55:00Z
---

# Group Audit Transcript — `nomad22-may11.show.gz`

Show: `C:\ProgramData\MA Lighting Technologies\grandma\gma2_V_3.9.60\shows\nomad22-may11.show.gz`
Console: grandMA2 onPC v3.9.60.65 @ 127.0.0.1:30000
Session: 2026-05-11 | Operator: administrator

---

## Section 1 — Phase 1: Live Inventory (read-only, `list` / `info` only)

### 1.1 Fixture Patch (35 fixtures)

| FixId | Name | Type | Fixture Type | Patch | Notes |
|---|---|---|---|---|---|
| 1 | DJ-LED - 0 | LED Bar | 6 LED Bar 2 11CH | 1.011 | DJ booth LED bar |
| 20 | RGBBLIND 2 | RGBW blinder | 5 RGBBLINDER BAR | 1.001 | Blinder strip |
| 201 | LASERBAR 1 | Laser bar | 4 LASER BARS 26CH | 2.001 | ⚠ CAMERA HAZARD |
| 202 | LASERBAR 2 | Laser bar | 4 LASER BARS 26CH | 1.027 | ⚠ CAMERA HAZARD |
| 203 | LASERBAR 3 | Laser bar | 4 LASER BARS 26CH | 1.053 | ⚠ CAMERA HAZARD |
| 204 | LASERBAR 4 | Laser bar | 4 LASER BARS 26CH | 1.079 | ⚠ CAMERA HAZARD |
| 205 | LASERBAR 5 | Laser bar | 4 LASER BARS 26CH | 1.105 | ⚠ CAMERA HAZARD |
| 206 | LASERBAR 6 | Laser bar | 4 LASER BARS 26CH | 1.131 | ⚠ CAMERA HAZARD |
| 207 | LASERBAR 7 | Laser bar | 4 LASER BARS 26CH | 1.157 | ⚠ CAMERA HAZARD |
| 208 | LASERBAR 8 | Laser bar | 4 LASER BARS 26CH | 1.183 | ⚠ CAMERA HAZARD |
| 209 | LASERBAR 9 | Laser bar | 4 LASER BARS 26CH | 1.209 | ⚠ CAMERA HAZARD |
| 210 | LASERBAR 10 | Laser bar | 4 LASER BARS 26CH | (-) UNPATCHED | ⚠ CAMERA HAZARD — also unpatched |
| 401 | M.BEAM - 1 | Mover beam | 10 Sharpy Standard | 1.280 | |
| 402 | M.BEAM - 2 | Mover beam | 10 Sharpy Standard | 1.296 | |
| 403 | M.BEAM - 3 | Mover beam | 10 Sharpy Standard | 1.312 | |
| 404 | M.BEAM - 4 | Mover beam | 10 Sharpy Standard | 1.328 | |
| 420 | -Atmos- | Dimmer | 2 Dimmer 00 | 2.356 | CO2 atmosphere machine |
| 801 | LED.Strobe-BAR - 1 | LED RGBW strobe | 3 rgbw-13ch 13CH | 1.448 | ⚠ STROBE CAPABLE |
| 802 | LED.Strobe-BAR - 2 | LED RGBW strobe | 3 rgbw-13ch 13CH | 1.435 | ⚠ STROBE CAPABLE |
| 803 | LED.Strobe-BAR - 3 | LED RGBW strobe | 3 rgbw-13ch 13CH | 1.422 | ⚠ STROBE CAPABLE |
| 804 | LED.Strobe-BAR - 4 | LED RGBW strobe | 3 rgbw-13ch 13CH | 1.409 | ⚠ STROBE CAPABLE |
| 805 | LED.Strobe-BAR - 5 | LED RGBW strobe | 3 rgbw-13ch 13CH | 1.396 | ⚠ STROBE CAPABLE |
| 806 | LED.Strobe-BAR - 6 | LED RGBW strobe | 3 rgbw-13ch 13CH | 1.383 | ⚠ STROBE CAPABLE |
| 807 | LED.Strobe-BAR - 7 | LED RGBW strobe | 3 rgbw-13ch 13CH | 1.357 | ⚠ STROBE CAPABLE |
| 911 | Co2-HL.HR | Dimmer | 2 Dimmer 00 | 1.010 | CO2 high/low |
| 1001 | M.Wash - 1 | Moving wash | 7 movingwash zone | 2.200 | |
| 1002 | M.Wash - 2 | Moving wash | 8 NEW WASH | 2.210 | |
| 1003 | M.Wash - 3 | Moving wash | 8 NEW WASH | 1.253 | |
| 1004 | M.Wash - 4 | Moving wash | 7 movingwash zone | 1.262 | |
| 1005 | M.Wash - 5 | Moving wash | 8 NEW WASH | 1.489 | |
| 1006 | M.Wash - 6 | Moving wash | 8 NEW WASH | 1.271 | |
| 1007 | M.Wash - 7 | Moving wash | 8 NEW WASH | 1.469 | |
| 1008 | M.Wash - 8 | Moving wash | 8 NEW WASH | 1.498 | |
| 1009 | M.Wash - 9 | Moving wash | 8 NEW WASH | 1.235 | |
| 1010 | M.Wash - 10 | Moving wash | 8 NEW WASH | 1.244 | |

**Hazard summary:** 10 laser bars (201–210) + 7 LED strobe bars (801–807) + 2 CO2 dimmers (420, 911) = 19 hazard fixtures out of 35 total.

### 1.2 Group Pool (75 groups)

Raw output from `list group` 2026-05-11:

| Id | Name | Issues observed |
|---|---|---|
| 1 | -#Co2#- | |
| 2 | LED.BAR-STROBE | No ⚠ flag on strobe master |
| 3 | M.WASH | |
| 4 | M.LASER | No ⚠ flag on laser master |
| 5 | M.BEAM | |
| 6 | DS.DJ- BOOTH | Typo in name (trailing space) |
| 21 | LASER MIRROR | |
| 22 | ALL LASERS | Duplicate of / overlapping with grp 4, 29, 37 |
| 24 | 208.1: LASERBAR 8 | Patch-address name; duplicate of grp 290 |
| 25 | 209.1: LASERBAR 9 | Patch-address name; duplicate of grp 306 |
| 26 | 210.1: LASERBAR 10 | Patch-address name; only copy |
| 27 | 20: RGBBLIND 2 | Patch-address name |
| 29 | LASER INSTANCES | Overlapping with grp 4, 22, 37 |
| 37 | LASER MAINS | Overlapping with grp 4, 22, 29 |
| 40 | DJ LEFT | |
| 41 | DJ RIGHT | |
| 49 | Group | UNNAMED |
| 51 | 801: LED.Strobe-BAR - 1 | Patch-id name |
| 52 | 802: LED.Strobe-BAR - 2 | Patch-id name; duplicate name of grp 82 |
| 53 | 803: LED.Strobe-BAR - 3 | Patch-id name |
| 54 | LASER SIM 2 | Unclear purpose |
| 55 | 21: RGBBLIND 1 | Patch-address name; fixture not in patch list |
| 56 | 19: RGBBLIND 1 | Patch-address name; fixture not in patch list |
| 57 | 206.1: LASERBAR 6 | Patch-address name; duplicate of grp 289 |
| 58 | 207.1: LASERBAR 7 | Patch-address name; duplicate of grp 320 |
| 62 | bar left | Lowercase; likely Bar L LED strips |
| 63 | bar right | Lowercase |
| 66 | 804: LED.Strobe-BAR - 4 | Patch-id name |
| 67 | 805: LED.Strobe-BAR - 5 | Patch-id name |
| 70 | 20: RGBBLIND 2 | Patch-address name; duplicate of grp 27 |
| 72 | 203.1: LASERBAR 3 | Patch-address name; duplicate of grp 302 |
| 73 | 204.1: LASERBAR 4 | Patch-address name; duplicate of grp 303 |
| 74 | 205.1: LASERBAR 5 | Patch-address name; duplicate of grp 319 |
| 81 | 806: LED.Strobe-BAR - 6 | Patch-id name |
| 82 | 802: LED.Strobe-BAR - 2 | DUPLICATE NAME of grp 52 |
| 83 | 807: LED.Strobe-BAR - 7 | Patch-id name |
| 87 | 201.1: LASERBAR 1 | Patch-address name; duplicate of grp 300 |
| 88 | 202.1: LASERBAR 2 | Patch-address name; duplicate of grp 301 |
| 103 | WASH | Likely same as grp 3 M.WASH — investigate |
| 117 | C02 | Typo (C02 vs CO2); duplicate of grp 1 |
| 147 | RED | Color channel |
| 148 | GREEN | Color channel |
| 149 | BLUE | Color channel |
| 150 | WHITE | Color channel |
| 151 | MASTER | |
| 152 | 106 Dim 1 | Patch-address name |
| 153 | CLIP 1 | Video/media layer? |
| 154 | CLIP 2 | |
| 155 | CLIP 3 | |
| 156 | CLIP 4 | |
| 157 | SYNC | |
| 158 | MASTER LAYER 2 | |
| 159 | 113 Dim 2 | Patch-address name |
| 160 | 114 Dim 3 | Patch-address name |
| 161 | 115 Dim 4 | Patch-address name |
| 162 | 116 Dim 5 | Patch-address name |
| 163 | 117 Dim 6 | Patch-address name |
| 164 | 118 Dim 7 | Patch-address name |
| 170 | 111 Dim 1 | Patch-address name |
| 208 | RPointe1 | Duplicate of grp 227 |
| 209 | Group | UNNAMED |
| 223 | : M.BEAM.  1 | Extra colon + spaces in name |
| 224 | : M.BEAM.  2 | Extra colon + spaces |
| 225 | : M.BEAM.  3 | Extra colon + spaces |
| 226 | : M.BEAM.  4 | Extra colon + spaces |
| 227 | RPointe1 | Duplicate of grp 208 |
| 229 | rgbw-13ch | Fixture-type-name as group name |
| 289 | 206.1: LASERBAR 6 | Duplicate of grp 57 |
| 290 | 208.1: LASERBAR 8 | Duplicate of grp 24 |
| 300 | 201.1: LASERBAR 1 | Duplicate of grp 87 |
| 301 | 202.1: LASERBAR 2 | Duplicate of grp 88 |
| 302 | 203.1: LASERBAR 3 | Duplicate of grp 72 |
| 303 | 204.1: LASERBAR 4 | Duplicate of grp 73 |
| 306 | 209.1: LASERBAR 9 | Duplicate of grp 25 |
| 319 | 205.1: LASERBAR 5 | Duplicate of grp 74 |
| 320 | 207.1: LASERBAR 7 | Duplicate of grp 58 |

---

## Section 2 — Phase 2: Reconciliation Table

User approved Tier 1 execution. Tier 2 + Tier 3 deferred.

---

## Section 3 — Phase 3: Mutations (Tier 1 — executed 2026-05-11)

### 3.1 Label changes

| Cmd | Result |
|---|---|
| `label group 22 "ALL LASERS - HAZARD"` | OK (initial `!!` rejected as forbidden character; retried with `- HAZARD` suffix) |
| `label group 2 "ALL STROBES - HAZARD"` | OK |
| `label group 4 "LASER SHOW - HAZARD"` | OK |

### 3.2 Sequence releases

| Cmd | Result |
|---|---|
| `off sequence 8` (LASER DISCO BALL) | OK |
| `off sequence 15` (STROBE SHOT) | OK |
| `off sequence 20` (STROBE WHITE) | OK |

### 3.3 Park sequence (initial attempt — by group)

| Cmd | Result | Issue |
|---|---|---|
| `park group 22 at 0` | OK | Group membership unverifiable via telnet (`if selection` modifier ignored on this firmware) |
| `park group 4 at 0` | OK | Risk: group 4 (M.LASER) membership unknown — may include beam movers |
| `park group 2 at 0` | OK | Same risk for group 2 |

### 3.4 Park revision — by canonical fixture range

To eliminate group-membership ambiguity:

| Cmd | Result |
|---|---|
| `unpark group 22` | OK |
| `unpark group 4` | OK |
| `unpark group 2` | OK |
| `park fixture 201 thru 210 at 0` | OK — 10 LASERBAR fixtures locked |
| `park fixture 801 thru 807 at 0` | OK — 7 LED.Strobe-BAR fixtures locked |

### 3.5 Snapshot

`Backup SaveAs "nomad22-may11-pre-scout"` — sent without error but no new file appeared at expected path. MA2 autosave updated `nomad22-may11.show.gz` at 18:43 instead.

---

## Section 4 — Phase 4: Verification

### Verified via telnet:
- `list group` confirms labels updated: groups 2, 4, 22 now read `ALL STROBES - HAZARD`, `LASER SHOW - HAZARD`, `ALL LASERS - HAZARD`.

### Could NOT verify via telnet:
- Park status — `list fixture if parked` and `list fixture /parked` modifiers silently ignored by firmware, return full fixture list regardless.
- Group membership — `list fixture if selection` modifier also ignored.

### Visual verification required (user, on gma2 GUI):
- Fixture sheet shows parked indicator (typically red box / "P" tag) on fixtures 201–210 and 801–807
- Group buttons 2, 4, 22 display updated names
- DMX output to lasers and strobes is at 0 across all parameters

---

## Section 5 — Phase 5: Camera-Safety Pre-flight

**Status:** SAFETY LOCKS ACTIVE (pending visual confirmation)

- [x] Group 22 renamed `ALL LASERS - HAZARD`
- [x] Group 2 renamed `ALL STROBES - HAZARD`
- [x] Group 4 renamed `LASER SHOW - HAZARD`
- [x] Fixtures 201–210 (lasers) parked at 0 by canonical fixture id
- [x] Fixtures 801–807 (strobes) parked at 0 by canonical fixture id
- [x] Sequences 8/15/20 released (`off sequence N`)
- [ ] Visual confirmation by user on gma2 GUI
- [ ] Pre-scout snapshot saved with named filename (user can do this in GUI: Backup → Save Show As → `nomad22-may11-pre-scout`)

### Restore commands (run after scout, before any rehearsal):

```
unpark fixture 201 thru 210
unpark fixture 801 thru 807
```

Note: ~35 sequences contain laser/strobe content (search `LASER`, `LSR`, `STROBE`, `STRB` in the 463-sequence list — see prior tool result). Park lock protects against all of them. Once unparked, all are re-armed.

---

## Section 6 — `19-toronto-2025-09-09-v4.show.gz`

Audit performed 2026-05-11T19:55:00Z via binary parse of show `.backup` file (MA2 `info macro N` does not stream script body over Telnet — it opens a GUI editor). Strings extracted as UTF-16 LE from the proprietary binary.

---

### 6.A — Macro 16 + 17 Dependency Audit

#### Macro 16 — `-Create FT_Pools-` (103 lines)

##### Reconstructed logic (from binary UTF-16 string extraction)

The macro is a full MA2 Lua-style script. Key variables and flow:

| Variable | Value | Purpose |
|---|---|---|
| `$IntGroupPool` | `11` | Starting group pool slot id |
| `$presetPoolNum` | `= $IntGroupPool` (11) | Starting cross-pool preset slot id |
| `$slotOffset` | `0` (incremented) | Running slot counter |
| `$currentHue` | `0` | Hue wheel start (degrees) |
| `$hueStep` | `51` | Hue step per FT (gives ~7 distinct colors before wrap) |
| `$FTiterations` | `$SELECTEDFIXTURESCOUNT - 2` | Outer loop count (fixes firmware off-by-two) |
| `$loopFT` | `0 … $FTiterations` | Outer loop index (one pass per unique FT) |

**Outer loop (one pass per fixture type):**

1. Select: `$fixTypeMajor.$fixTypeMinor.1` (select all fixtures of this FT)
2. Count: `$instanceCount = $SELECTEDFIXTURESCOUNT`
3. Compute slot ids: `$currentGroup`, `$currentPreset`, `$ftGroupSlot` from base + offset
4. **Store group** at `$currentGroup /o`
5. **Store cross-pool preset** at `0.$currentPreset /o` (pool 0 = All presets)
6. **Store group** at `$ftGroupSlot /o`
7. **Store preset** at `$currentPreset /o` (FT-scoped preset pool — determined by FT context)
8. **Appearance** on all four objects: `/h=$currentHue /s=100 /br=100`
9. **Label** lump group as `"FT N.1.1"` (`$fullName`), lump preset as same
10. **Label** lump/slot objects as `"FT N.1.0"` (`$lumpName`)

**Inner loop (one pass per physical instance of that FT):**

For each instance `$fixTypePatch`:
1. Select: `$fixTypeMajor.$fixTypeMinor.$fixTypePatch`
2. **Store group** and **preset** for that instance
3. **Label** as `"FT N.M.K"` (`$presetName`)
4. **Appearance**: `/h=$currentHue /s=60 /br=100` (dimmer saturation for instances vs lump)

**Multi-physical merge loop:**
- Computes `$subsPerPhys` (sub-fixtures per physical body)
- Iterates and calls `$lumpFTGroup /o` (first) then `$lumpFTGroup /merge` (subsequent) to build a "lump" group from all physical bodies

**Advance:** `$loopFT += 1`, `$currentHue += $hueStep`, goto outer loop

##### Macro 16 — object dependency table

| Object type | Ids created | Label pattern | Appearance |
|---|---|---|---|
| Group | 11, 12, … (one "lump" + N instances per FT) | `"FT N.1.1"` (lump), `"FT N.M.K"` (instance) | Hue-cycled (51° steps from 0°), sat 100 (lump) / 60 (instance) |
| Preset pool 0 (All) | 11, 12, … | `"FT N.1.1"` / `"FT N.M.K"` | Same hue |
| Preset (FT-scoped) | 11, 12, … | `"FT N.1.0"` / `"FT N.M.K"` | Same hue |
| Groups (self-Goto) | `1."-Create FT_Pools-".N` | — | Goto target, not a pool object |

**Existing state cross-check:** Groups 11–19 in this show are labeled `FT N.M.K [Preset] <FT-name>`. The `[Preset]` suffix is NOT produced by Macro 16 — it must have been added manually or by a subsequent label pass after a prior macro run.

**Does NOT touch:** Worlds, sequences, executors, fixtures 201–210 or 801–807 (no hazard fixture references), `park`, `blackout`.

---

#### Macro 17 — `Global ALL Preset` (14 lines)

##### Reconstructed logic

A short single-pass script that creates (or rebuilds) one unified cross-pool preset.

| Variable | Value | Purpose |
|---|---|---|
| `$isFirst` | `1` (flag) | First FT creates; subsequent FTs merge |
| `$loopFT` | `0 … $FT_TotalCount` | Loop over fixture types |
| `$FT_TotalCount` | `$SELECTEDFIXTURESCOUNT` | Total FT count |
| Target preset | `0.10` | Cross-pool (pool 0) slot 10 — **fixed id** |

**Steps (14 lines):**

1. `$fixTypeMajor = $loopFT` — set FT index
2. Select: `$fixTypeMajor.1.1` — all fixtures of this FT
3. `[$isFirst >= 1]` → `0.10 /o /global` → `$isFirst = 0` — **create** preset 10 (first FT)
4. `[$isFirst <= 0]` → `0.10 /merge /global` — **merge** into preset 10 (subsequent FTs)
5. `$loopFT += 1` → `Goto "Global ALL Preset".5` — loop
6. `0.10 "Global ALL (FT2+)" /o` — **label** preset 10

##### Macro 17 — object dependency table

| Object type | Id | Label | Verb | Present? (from list macro context) |
|---|---|---|---|---|
| Preset pool 0 (All) | 10 | `"Global ALL (FT2+)"` | create/merge | Unknown — not confirmed via telnet |
| (Self-Goto) | `"Global ALL Preset".5` | — | Goto | Internal reference only |

**Does NOT touch:** Groups, worlds, sequences, executors, fixtures by id, any hazard range.

---

#### Combined: what runs if you call Macro 16 then Macro 17

```
Macro 16 (103 lines):
  For each fixture type in the show:
    Store group (lump + per-instance) at slots 11+
    Store cross-pool presets at slots 11+ in pool 0
    Store FT-scoped presets at slots 11+
    Apply hue-cycled color appearance
    Label: "FT N.M.K" / "FT N.1.0" / "FT N.1.1"

Macro 17 (14 lines):
  Iterate all FTs → merge into a single preset at 0.10
  Label: "Global ALL (FT2+)"
```

Both macros iterate over fixture types. They **require** all fixture types to be selectable (i.e., patched and responding to `select $fixTypeMajor.$fixTypeMinor.1`). They start slots at **11** — any existing content at group/preset slots ≥ 11 will be **overwritten** (`/o` = overwrite).

**If run in the current show state (groups 11–19 already populated):** Macro 16 will overwrite groups/presets 11–19 and create new slots for any FTs beyond the current 9. The `[Preset]` suffix labels on groups 11–19 will be replaced with `"FT N.M.K"`.

---

#### Hazard call-outs

| # | Risk | Detail |
|---|---|---|
| 1 | **Overwrites existing groups 11–19** | Groups 11–19 in this show have custom `[Preset]` labels that Macro 16 will replace. Non-destructive to safety (no park state change) but label work is lost. |
| 2 | **Overwrites cross-pool presets 11+ in pool 0** | Any manually created presets at those slots are silently overwritten (`/o`). |
| 3 | **No hazard-fixture guard** | Macro 16 iterates ALL fixture types. If laser/strobe FTs are patched, it will select and store presets for them — not dangerous per se, but those FTs will get group/preset entries without any `[SFX-FREE]` world filter. |
| 4 | **Macro 17 writes preset `0.10` unconditionally** | Any existing content at cross-pool preset 10 is overwritten on first call. |
| 5 | **No SAFE_READ guard** | Both macros are DESTRUCTIVE (create groups + presets). Do not run without a named backup save first. |

---

#### Group 99 — retraction

An earlier assertion that "Group 99 = Live Test Group" was carried forward from a prior session without a fresh `info group 99` to confirm it. **That claim is retracted.** Group 99's actual state in this show is unconfirmed and must be verified via `info group 99` before being relied upon.
