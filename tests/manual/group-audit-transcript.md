---
title: Group Audit Transcript — nomad22-may11 + 19-toronto-v4
description: Chronological log of group audit, camera-safety pre-flight, and Macro 16/17 dependency analysis
version: 1.5.0
created: 2026-05-11T16:44:00Z
last_updated: 2026-05-13T19:16:06Z
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

---

### 6.B — Decision Matrix: Run / Edit / Skip

> Added 2026-05-13. Based on Section 6.A reconstruction + RAG-assisted syntax classification.
> Console state cross-check limited to what was captured in Sections 1–5 (live `list`/`info` queries from 2026-05-11). No additional live queries were issued for this section.

#### Prerequisite: save a named backup

Before running either macro:

```
SaveShow "nomad-main-pre-ft-pools"
```

This is mandatory. Both macros issue `Store … /o` commands that silently overwrite pool content with no undo path.

---

#### Macro 16 — `-Create FT_Pools-`: line classification

| Action category | MA2 command form | Risk tier | Classification | Condition |
|---|---|---|---|---|
| Variable setup | `SetVar $X 0`, `AddVar $Y 1` | SAFE_WRITE | **run** | No pool state change |
| FT selection | `SelFix $M.$N.1`, `SelFix $M.$N.$K` | SAFE_READ | **run** | Read-only selection |
| Loop control | `Goto "-Create FT_Pools-".N` | SAFE_WRITE | **run** | Internal self-goto |
| Count read | `SetVar $instanceCount $SELECTEDFIXTURESCOUNT` | SAFE_READ | **run** | Read system var, no write |
| **Store group (overwrite)** | `Store Group $currentGroup /o` | DESTRUCTIVE | **run after SaveShow** | Overwrites groups 11+; current groups 11–19 have `[Preset]` suffix labels that will be replaced |
| **Store cross-pool preset (overwrite)** | `Store Preset 0.$currentPreset /o` | DESTRUCTIVE | **run after SaveShow** | Overwrites pool-0 presets at slots 11+ |
| **Store FT-scoped preset (overwrite)** | `Store Preset $currentPreset /o` | DESTRUCTIVE | **run after SaveShow** | Overwrites FT-scoped preset pool at slots 11+ |
| Appearance | `Appearance Group/Preset $id /h=H /s=S /br=B` | SAFE_WRITE | **run** | Cosmetic color only; HSB 0–100 scale confirmed |
| Label | `Label Group/Preset $id "$name"` | SAFE_WRITE | **run** | Cosmetic only |

**Verdict for Macro 16: RUN — after `SaveShow`.**

Caveats:
1. Groups 11–19 will be regenerated. The `[Preset]` suffix on existing labels will be replaced with `"FT N.M.K"` / `"FT N.1.1"`.
2. Cross-pool presets (pool 0) at slots 11+ will be overwritten. Verify nothing important occupies those slots in the target show.
3. All patched fixture types are processed without a world-filter guard. If any FT should be excluded (e.g. a hazard-class FT), you must either unpatch it before running or manually delete its generated group/preset afterward.
4. Slot numbering starts at 11 (`$IntGroupPool = 11`). If the target show has more FTs than slots allow (>~90 FTs), slot arithmetic could overflow — unlikely for nomad-main.

---

#### Macro 17 — `Global ALL Preset`: line classification

| Action category | MA2 command form | Risk tier | Classification | Condition |
|---|---|---|---|---|
| Variable setup | `SetVar $isFirst 1`, `SetVar $loopFT 0` | SAFE_WRITE | **run** | — |
| FT selection | `SelFix $fixTypeMajor.1.1` | SAFE_READ | **run** | — |
| **Store preset (first FT, overwrite)** | `Store Preset 0.10 /o /global` | DESTRUCTIVE | **run after checking slot 10** | Overwrites cross-pool preset 0.10 unconditionally; verify target show has nothing critical there |
| **Store preset (subsequent FTs, merge)** | `Store Preset 0.10 /merge /global` | DESTRUCTIVE | **run** | Merges all FTs into the same preset — expected behavior |
| Loop control | `Goto "Global ALL Preset".5` | SAFE_WRITE | **run** | Internal self-goto |
| Label | `Label Preset 0.10 "Global ALL (FT2+)" /o` | SAFE_WRITE | **run** | Cosmetic |

**Verdict for Macro 17: RUN — after confirming cross-pool preset 0.10 is empty or expendable.**

Caveats:
1. Preset `0.10` in the **target show** must be checked before running. In the audit show (`nomad22-may11`), preset 0.10 was not listed among the known presets, so it is likely empty — but this was not confirmed by a direct `info preset 0.10` call.
2. Macro 17 depends implicitly on the fixture-type loop established by Macro 16's context. Run Macro 16 first.

---

#### Transfer procedure (Macros 16 + 17 → `nomad-main.show.gz`)

1. **Confirm target show is loaded.** `list showfile` or check `$SHOWFILE` variable.
2. **Save backup:** `SaveShow "nomad-main-pre-ft-pools"`.
3. **Check slot 0.10:** `list preset 0.10` — confirm empty or expendable.
4. **Check groups 11–19:** `list group 11 thru 19` — document what will be overwritten.
5. **Load macros** if not already present. Macros 16 and 17 must be in the macro pool of the loaded show. If transferring from `19-toronto-v4`, use PSR macro import (see Skill `psr-show-migration`).
6. **Run Macro 16:** `Call Macro 16`. Monitor telnet output for errors. Expected runtime: ~5–15 s depending on FT count.
7. **Run Macro 17:** `Call Macro 17`. Expected runtime: <5 s.
8. **Verify:** `list group 11 thru 20`, `list preset 0.10`, `list preset 0.11 thru 20`. Check labels match expected `FT N.M.K` pattern.
9. **Save:** `SaveShow "nomad-main-ft-pools"`.

---

#### Final run/skip summary

| Macro | Verdict | Pre-condition |
|---|---|---|
| 16 — `-Create FT_Pools-` | **RUN** | `SaveShow` first; accept group 11–19 regeneration |
| 17 — `Global ALL Preset` | **RUN** | Confirm `0.10` is empty/expendable; run after Macro 16 |

---

## Section 6.C — Live Execution Log: Macros 16 + 1 (2026-05-12)

> Added 2026-05-13. Live execution on `19-toronto-2025-09-09-v4.show.gz`. Includes Macro 16 full run, Macro 1 cleanup run, and a cross-show interoperability audit.

### Pre-execution state

| Variable | Value | Source |
|---|---|---|
| `$SHOWFILE` | `19-toronto-2025-09-09-v4` | `ListVar` via Telnet |
| `$USER` | `administrator` | `ListVar` |
| `$USERRIGHTS` | `Admin` | `ListVar` |
| `$SELECTEDEXEC` | `1.1.1` | `ListVar` |
| `$FT_TOTALCOUNT` | 8 (FT majors 1–7 + 1 residual) | Inferred from Macro 16 output |
| Backup created | `19-toronto-pre-macro16.show.gz` | `SaveShow "19-toronto-pre-macro16"` via `send_raw_command` |

> **Note:** `SaveShow "19-toronto-pre-macro16"` both saved and renamed the loaded show. After this command, `$SHOWFILE` became `19-toronto-pre-macro16`. The original file `19-toronto-2025-09-09-v4.show.gz` was preserved (1 backup write). All subsequent work is on the renamed show.

---

### Macro 16 — `-Create FT_Pools-` (103 lines, live execution)

**Method:** `Go Macro 16` via raw Telnet. Custom `stream_for()` reader with `silence_after=6.0s` / `max_seconds=120s` (standard `send_command_with_response` `subsequent_timeout=0.1s` was too short for async macro output).

**Runtime:** ~87 seconds.

**FT iterations observed:** 8 (FT major 1 through 7, plus FT 7 multi-instance pass).

#### Objects created

| Object type | Slots occupied | Count | Naming pattern |
|---|---|---|---|
| Groups (lump, cross-FT) | 1–9 | 9 | `FT N.1.1` (bold lump per FT) |
| Groups (numbered pool) | 11–19 | 9 | `FT N.M.K` with instance suffix |
| Presets (FT-scoped, pool 0) | 0.11–0.19 | 9 | Cross-pool color/position |
| Worlds | 11–19 | 9 | FT-scoped world mask |

**Hue progression (51° step):** FT1=0°, FT2=51°, FT3=102°, FT4=153°, FT5=204°, FT6=255°, FT7=306°.
- Lump group appearance: saturation=100 (vivid)
- Instance group appearance: saturation=60 (pastel)

#### Telnet response summary

All 103 macro lines executed without `ERROR` or `DENIED` feedback. No `Error #72 COMMAND NOT EXECUTED` or `Error #14 OBJECT DOES NOT EXIST` lines observed. Final console response: `BlindEdit Off` confirming line 102 (index 102) executed.

---

### Macro 1 — cleanup (8 lines, live execution)

**Method:** `Go Macro 1` via raw Telnet. Runtime: ~4.4 seconds.

#### Macro body (from `macro_1_inspect.xml`)

| Line (index) | Command | Risk tier | Result |
|---|---|---|---|
| 0 | `Delete Group 11 Thru 22` | DESTRUCTIVE | OK — groups 11–19 deleted (22 was empty, no error) |
| 1 | `Delete Preset 0.11 Thru 0.22` | DESTRUCTIVE | OK — presets 0.11–0.19 deleted |
| 2 | `Delete Group 1 Thru 10` | DESTRUCTIVE | OK — lump groups 1–9 deleted |
| 3 | `Delete World 11 Thru 22` | DESTRUCTIVE | OK — worlds 11–19 deleted |
| 4 | `ClearAll` | SAFE_WRITE | OK |
| 5 | `Off Macro 1."::Auto Create Multi-Pool Objects::"` (disabled) | — | SKIPPED (line disabled) |
| 6 | `Off Macro 1."::Auto Create Multi-Pool(s)::"` | SAFE_WRITE | Error #14 OBJECT DOES NOT EXIST — non-fatal; named target not loaded |
| 7 | `Off Macro 1."::Auto Create Multi-Pool(s)::-1"` | SAFE_WRITE | Error #14 OBJECT DOES NOT EXIST — non-fatal; named target not loaded |

**Post-cleanup verification:** `list group` showed only Group 99 remaining. All slots 1–22 cleared. Presets 0.11–0.22 gone. Error #14 on lines 6–7 is expected: those lines reference alternate macro name variants that don't exist in this show's macro pool — they are guard-off commands for a different show context.

---

### Macro architecture patterns (derived from live execution)

#### Dynamic (reads from console state)

The macro reads the selected fixtures count after filtering by FixtureType 1, then loops through to increment the FT major value and calculate the instance count based on that selection.

Specifically:
- Line 1: `SetUserVar $FTiterations = $SELECTEDFIXTURESCOUNT` — captures the full fixture count into a user variable immediately after selection.
- Line 2: `AddUserVar $FTiterations = -2` — subtracts 2 from the count. This hardcoded −2 correction accounts for the show's architecture: FT1 (index 1) is a system/utility type that the loop skips, and the count includes a fencepost offset. The result is the number of "real" FT iterations the loop will perform.
- Each iteration: `FixtureType $fixTypeMajor.$fixTypeMinor.1 Thru` selects all fixtures of that type, then `SetUserVar $instanceCount = $SELECTEDFIXTURESCOUNT` reads the instance count for that FT from the selection state.

This pattern means the macro is **fully data-driven from the live patch** — it does not hardcode fixture counts or FT counts, only the starting slot index (11) and the −2 correction. Any show with a different fixture architecture will produce different iteration counts from the same macro body.

#### Dual-group model

For each FT, two groups are created at different slot ranges:
- **Lump group** (slot 1–9): all instances of one FT in a single group. Named `FT N.1.1`.
- **Pool groups** (slot 11–19): per-instance groups. Named with instance suffix.

The two ranges are maintained in parallel via `$IntGroupPool` (starts at 11) and the loop counter (starts at 1). This mirrors the MA2 dual-group workflow where the lump group drives intensity and the pool groups drive FT-specific attributes.

#### Create/destroy pair

Macro 16 (`-Create FT_Pools-`) and Macro 1 (`-cleanup macro-`) are designed as a matched bracket pair. Macro 1's delete commands exactly mirror Macro 16's store commands: Groups 1–10 + 11–22, Presets 0.11–0.22, Worlds 11–22. Macro 1 lines 6–7 (`Off Macro 1."::Auto Create Multi-Pool Objects::"`) are safety guards for stopping the create macro if it was running under a different name — they are expected to produce Error #14 in any show where those alternate names don't exist.

#### Self-referencing Goto loop

Macro 16 drives its inner loops via `Go Macro 1."-Create FT_Pools-".N` (1-based line index). The outer FT loop jumps back to line 4 (index 3); the inner instance loop jumps back to line 46 (index 45). This is a purely imperative loop structure — no structured `For/EndFor` construct exists in MA2 macro syntax.

#### Hue-step coloring

The hue step of **51°** divides the 360° color wheel into 7 approximately equal bands (51 × 7 = 357, close to 360). This ensures that 7 distinct FTs receive visually distinct hues. The 8th FT wraps back near 0°. Saturation is intentionally different between lump groups (s=100, vivid) and instance groups (s=60, pastel) to visually distinguish "all of a type" from "a specific instance."

---

### Critical interoperability issues

The following issues were identified during the interoperability audit comparing Macro 16/1 behavior in `19-toronto-2025-09-09-v4` against the target `nomad-main.show.gz` architecture.

#### Hardcoded assumptions (known risks before transfer)

| Assumption | Value | Risk level | Impact if violated |
|---|---|---|---|
| FT major starting index | 1 (loop begins at `$fixTypeMajor = 1`) | HIGH | If nomad-main FT majors don't start at 1 or have gaps, wrong fixtures selected per iteration |
| FT minor index | 1 (`$fixTypeMinor = 1` hardcoded throughout) | HIGH | If any FT uses minor > 1 for the "main" mode, those fixtures will not be selected |
| Patch address | 1 (`.1` appended to every FT selection) | MEDIUM | If patch starts at ≠ 1 for any FT, those fixtures will not be selected |
| Group slots | 1–10 (lump) and 11–22 (pool) | HIGH | If nomad-main already uses these slots for non-FT_Pool content, content will be silently overwritten |
| Preset slots | 0.11–0.22 | HIGH | Same overwrite risk |
| World slots | 11–22 | HIGH | Same overwrite risk |
| −2 correction | `AddUserVar $FTiterations = -2` | MEDIUM | Calibrated to 19-toronto architecture (FT1 = system type, skip). If nomad-main has no system FT or more/fewer skip-types, loop count will be off by that delta |

#### FT major contiguity requirement

Macro 16 increments `$fixTypeMajor` by 1 on each outer loop pass (`AddUserVar $fixTypeMajor = $loopFT` where `$loopFT` steps 1, 2, 3…). This requires FT majors to be **contiguous starting from 1**. Any gap (e.g. FT majors 1, 2, 4 with no 3) will cause the loop to attempt `FixtureType 3.1.1 Thru` on an empty slot — which produces zero fixtures for that iteration and a zero-fixture group/preset/world written to that pool slot.

**Mitigation:** Before firing Macro 16 on nomad-main, run `list fixturetype` and confirm the FT table is contiguous from major 1 to N.

#### Preset 0.10 collision (Macro 17)

Macro 17 stores all FT selections into cross-pool preset **0.10** unconditionally on the first FT iteration (`Store Preset 0.10 /o /global`). The `/o` (overwrite) flag provides no warning. If nomad-main already has content at 0.10, it will be silently replaced.

**Mitigation:** `list preset 0.10` before running Macro 17.

#### Pre-flight checklist (before firing Macros 16+1 on nomad-main)

1. `list fixturetype` — confirm FT majors are contiguous 1..N.
2. `list group 1 thru 10` — confirm lump slots are empty.
3. `list group 11 thru 22` — confirm pool slots are empty or expendable.
4. `list preset 0.10` — confirm slot is empty or expendable (for Macro 17).
5. `list preset 0.11 thru 0.22` — confirm cross-pool preset slots are empty.
6. `list world 11 thru 22` — confirm world slots are empty.

If any check reveals occupied slots that must be preserved, relocate them first or adjust macro start indices (requires macro edit).

#### Capacity bounds

With start slot 11 and the slot increment of +1 per FT, the macro can handle at most **11 FTs** before the pool group slots reach 22 (the apparent upper bound of the Delete range in Macro 1). On `19-toronto-v4`, 7 FT iterations were observed, well within this bound. `nomad-main.show.gz` (5.0 MB vs 25.4 MB for 19-toronto-v4) is a smaller show — fewer FTs are likely.

---

### Nomad-main compatibility assessment

Based on the interoperability audit:

| Criterion | Assessment |
|---|---|
| Show complexity | nomad-main is ~5 MB vs 25.4 MB for 19-toronto — likely ≤ 5 FTs, well within slot capacity |
| FT architecture | Unknown until `list fixturetype` is run — must verify contiguity |
| Slot collision (groups 1–22) | Unknown — must verify via pre-flight checklist |
| Slot collision (presets 0.10–0.22) | Unknown — must verify |
| Slot collision (worlds 11–22) | Unknown — must verify |
| −2 correction calibration | Potentially wrong for nomad-main architecture — verify FT1 is a skip-type or adjust |

**Overall verdict:** Transfer of XML files is low-risk and already planned (Section 11 of the plan). Firing Macro 16 on nomad-main requires completing the 6-step pre-flight checklist above before execution.

---

### 6.D  Macro 16 re-fire — canonical multi-instance reference (2026-05-13)

> Added 2026-05-13. Re-fire of the original Macro 16 on show `19-toronto-v4-pre-refire` after cleanup via Macro 21. Purpose: capture a canonical Telnet stream for Python port validation. Python port committed as `4e1828d` (`scripts/build_ft_pools.py`).

**Header block:**

| Field | Value |
|---|---|
| Show | `19-toronto-v4-pre-refire` |
| Macro fired | `-Create FT_Pools-` (Macro 16, 103 macrolines) |
| Cleanup macro | Macro 21 (`-Delete FT_Pools v12-`, 22 lines, 36 output lines) fired first |
| Build log | `c:\tmp\macro16-refire\build-feedback.log` (599 lines) |
| Cleanup log | `c:\tmp\macro16-refire\cleanup-feedback.log` (36 lines) |

---

#### Cleanup run (Macro 21, pre-build)

Macro 21 is the v12 delete macro. Key differences from Macro 1 used in 6.C: uses `/noconfirm`, covers a wider slot range (`$maxFTscan=30` → deletes Groups 1–30 + 11–40, Presets 0–7.11–40, Worlds 11–40), and wraps all destructive work in `BlindEdit On/Off`.

Notable: `Delete Group 11 Thru 40` fired but returned `WARNING, NO OBJECTS FOUND FOR DELETE` — confirming the pool group range was already clear at run time. All other deletes executed silently (no errors = objects found and deleted).

---

#### FT inventory (from build log — `$instanceCount` per `FixtureType N.1.1 Thru`)

| FT major | `instanceCount` | Lump group | Pool group(s) | Preset(s) | World(s) | Fixture count in world |
|---|---|---|---|---|---|---|
| 1 | 1 | Group 1 | Group 11 | 0.11 | World 11 | 46 |
| 2 | 1 | Group 2 | Group 12 | 0.12 | World 12 | 1 |
| 3 | 1 | Group 3 | Group 13 | 0.13 | World 13 | 6 |
| 4 | 2 | Group 4 (lump) | Groups 14 (pool-lump), 15 (inst1), 16 (inst2) | 0.14, 0.15, 0.16 | Worlds 14 (lump), 15 (inst1), 16 (inst2) | 28 (lump), 4 (inst1), 24 (inst2) |
| 5 | 1 | Group 7 | Group 17 | 0.17 | World 17 | 6 |
| 6 | 1 | Group 8 | Group 18 | 0.18 | World 18 | 4 |
| 7 | 1 | Group 9 | Group 19 | 0.19 | World 19 | 1 |

`$instanceCount` is set from `$SELECTEDFIXTURESCOUNT` immediately after `FixtureType N.1.1 Thru` — it counts physical instances (sub-rig splits), not total fixture count. FT4 has 2 physical instances; all others have 1.

---

#### Single-instance pattern (FT 1, log lines 15–51)

Representative command sequence for any single-instance FT (hue=0° shown; hue increments by 51° each FT):

```
FixtureType 1.1.1 Thru               ← probe: $instanceCount = "1"
Store Group 11 /o                     ← pool group (slot 11)
Attribute 1 Thru At Release
Store Preset 0.11 /o                  ← cross-pool preset
ClearAll ; Preset 0.11                ← recall preset to populate programmer
Store Group 1 /o                      ← lump group (slot 1)
Attribute 1 Thru At Release
Store World 11 /o                     ← world (slot 11), fixture count = 46
Appearance Group 11 /h=0 /s=100 /br=100
Appearance Group 1  /h=0 /s=100 /br=100
Appearance Preset 0.11 /h=0 /s=100 /br=100
Appearance World 11  /h=0 /s=100 /br=100
ClearAll
Label Group 1  "FT 1.1.1" /o
Label Preset 0.11 "FT 1.1.1" /o
Label World 11  "FT 1.1.1" /o
```

Because `instanceCount == 1`, the macro takes the single-instance branch (line 27 → line 29) and skips the inner instance loop. The lump group and pool group receive identical labels `"FT N.1.1"`.

---

#### Multi-instance pattern (FT 4, `instanceCount=2`, log lines 129–479)

FT 4 is the only multi-instance FT in this show. Full sequence:

**Phase 1 — lump objects (store before instance loop):**

```
FixtureType 4.1.1 Thru               ← probe: $instanceCount = "2"
Store Group 14 /o                     ← pool-lump group (slot 14)
Attribute 1 Thru At Release
Store Preset 0.14 /o                  ← cross-pool lump preset
ClearAll ; Preset 0.14
Store Group 4 /o                      ← lump group (slot 4)
Attribute 1 Thru At Release
Store World 14 /o                     ← lump world (28 fixtures)
Appearance Group 14 /h=153 /s=100 /br=100
Appearance Group 4  /h=153 /s=100 /br=100
Appearance Preset 0.14 /h=153 /s=100 /br=100
Appearance World 14  /h=153 /s=100 /br=100
ClearAll
Label Group 4  "FT 4.1.0" /o         ← lump label uses .1.0 suffix
Label Preset 0.14 "FT 4.1.0" /o
Label World 14  "FT 4.1.0" /o
Label Group 14  "FT 4.1.0" /o
```

**Phase 2 — instance loop (inst1 = patch 1, inst2 = patch 2):**

```
-- inst1 (fixTypePatch=1) --
FixtureType 4.1.1
Store Group 15 /o
Attribute 1 Thru At Release
Store Preset 0.15 /o
Label Preset 0.15 "FT 4.1.1" /o
ClearAll ; Preset 0.15
Store Group 5 /o
Attribute 1 Thru At Release
Store World 15 /o                     ← inst1 world (4 fixtures)
Label World 15  "FT 4.1.1" /o
Label Group 5   "FT 4.1.1" /o
Appearance Group 15 /h=153 /s=60 /br=100
Appearance Group 5  /h=153 /s=60 /br=100
Appearance Preset 0.15 /h=153 /s=60 /br=100
Appearance World 15  /h=153 /s=60 /br=100

-- inst2 (fixTypePatch=2) --
FixtureType 4.1.2
Store Group 16 /o
Attribute 1 Thru At Release
Store Preset 0.16 /o
Label Preset 0.16 "FT 4.1.2" /o
ClearAll ; Preset 0.16
Store Group 6 /o
Attribute 1 Thru At Release
Store World 16 /o                     ← inst2 world (24 fixtures)
Label World 16  "FT 4.1.2" /o
Label Group 6   "FT 4.1.2" /o
Appearance Group 16 /h=153 /s=60 /br=100
Appearance Group 6  /h=153 /s=60 /br=100
Appearance Preset 0.16 /h=153 /s=60 /br=100
Appearance World 16  /h=153 /s=60 /br=100
```

**Phase 3 — MAtricks merge loop (`physCount=4`, `inst2Total=24`, `subsPerPhys=6`):**

The merge loop rebuilds the lump group (Group 4) by iterating over each physical body. `physCount` is read from `$SELECTEDFIXTURESCOUNT` after `SelFix Group 5` (inst1 group). `inst2Total` comes from `SelFix Group 6` (inst2 group). `subsPerPhys = inst2Total / physCount = 24 / 4 = 6`.

```
-- physLoop 0 (first physical body) --
ClearAll ; SelFix Group 5 ; MAtricksReset ; MAtricksBlocks 1
Next                                  ← walk inst1 to physical body 0
Store Group 4 /o                      ← first physical: overwrite

ClearAll ; SelFix Group 6 ; MAtricksReset ; MAtricksBlocks 6
Next                                  ← walk inst2 to physical body 0
Store Group 4 /merge

MAtricksReset ; ClearAll ; $physLoop += 1

-- physLoop 1..3 (remaining physical bodies) --
[same pattern but Store Group 4 /merge for inst1 also]
MAtricksBlocks 1  → Next × (physLoop+1) to reach body physLoop
Store Group 4 /merge

MAtricksBlocks 6  → Next × (physLoop+1) to reach body physLoop
Store Group 4 /merge
```

The `Next` counter increases by 1 each physLoop iteration — physLoop 0 calls `Next` once, physLoop 1 calls it twice, etc. This is MA2's only mechanism for indexed MAtricks traversal (no direct index addressing).

---

#### Key findings

1. **World store via preset recall, not FixtureType:** The canonical pattern is `ClearAll ; Preset 0.N ; Store World N /o`. This expands all physical fixtures of the FT into the programmer (46, 1, 6, 28, 6, 4, 1 for FTs 1–7). Using `FixtureType N.1.1 Thru` followed immediately by `Store World` gives only 1 fixture instance — wrong for worlds.

2. **`$instanceCount` semantics:** `FixtureType N.1.1 Thru` followed by `SetUserVar $instanceCount = $SELECTEDFIXTURESCOUNT` returns the number of physical instances (sub-rig splits in the patch), not the total fixture count. FT4 returns 2; all others return 1 in this show.

3. **Multi-instance label convention:** The lump group/preset/world for a multi-instance FT uses the `.1.0` suffix (`"FT N.1.0"`), not `.1.1`. Per-instance objects use `.1.1`, `.1.2`, etc.

4. **MAtricks merge — `physCount` from inst1 group, not FT selection:** `physCount = $SELECTEDFIXTURESCOUNT` is read after `SelFix Group $firstInstFTGroup` (the inst1 lump group), not from the FT selection. For FT4 this yields physCount=4 (4 physical bodies each contributing sub-fixtures to inst1).

5. **No `$SELECTEDFIXTURESCOUNT` from `FixtureType` for world counts:** The world fixture counts (46/1/6/28) are produced by the preset recall path, not by FixtureType selection.

---

#### Python port verification (`scripts/build_ft_pools.py`, commit `4e1828d`)

| Check | Result |
|---|---|
| World fixture counts match canonical | FTs 1–7: 46 / 1 / 6 / 28 / 6 / 4 / 1 — verified |
| FT4 group slots | Group 4 (lump), 5 (inst1), 6 (inst2) — correct |
| FT4 pool group slots | Group 14 (pool-lump), 15 (inst1), 16 (inst2) — correct |
| FT4 world fixture counts | World 14 = 28 (lump), World 15 = 4 (inst1), World 16 = 24 (inst2) — correct |
| MAtricks merge phys params | physCount=4, inst2Total=24, subsPerPhys=6 — matches log |
| Single-instance label | `"FT N.1.1"` on lump and pool group — correct |
| Multi-instance lump label | `"FT N.1.0"` — correct |
| Appearance saturation | Lump s=100 (vivid), instance s=60 (pastel) — correct |
