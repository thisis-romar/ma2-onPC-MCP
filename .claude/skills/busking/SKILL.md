---
title: Busking
description: Combined instruction module for grandMA2 busking — fader-per-effect performance model, executor layout, effect layering, live recovery, and template generation from patch (groups, presets, speed masters, executor page layout)
version: 1.0.0
created: 2026-04-07T15:14:23Z
last_updated: 2026-04-07T15:14:23Z
---

# Busking

## Theory: Fader-Per-Effect Model

In busking mode the LD *performs*, not triggers. Each executor runs one
continuously looping effect. The fader controls master intensity:

- **Fader at 0** → effect runs but outputs nothing (silenced, not released)
- **Fader at 100** → effect runs at full intensity
- **Raise/lower live** → real-time modulation without programmer interaction

This is the opposite of sequence-cue playback. There are no cue steps;
everything is always running, always modulatable.

### Executor Layout Convention

```
Page layout (one page per song + one fixed global page):

[1]  Song loader macro (first-button protocol — see song-macro-page-design skill)
[2]  Strobe / flash effect
[3]  Chase effect (color or position)
[4]  Beam effect (gobos, zoom)
[5]  Ambient wash effect
[6]  Key light effect or special
[7]  Audience blinder effect
[8]  Haze / atmospheric
[9]  Group master — front wash (intensity only)
[10] Group master — back wash (intensity only)
```

Fixed global page (always loaded as second layer):
- Overture / downtime look
- House light control
- Emergency blackout macro
- Stage manager cueing macro

### Rate vs Intensity

| What you want | Tool | Parameter |
|---|---|---|
| Make effect feel slower/faster | `modulate_effect(mode="rate", value=N)` | 50 = half speed, 200 = double |
| Lock effect to BPM | `modulate_effect(mode="speed", value=BPM)` | e.g. 128 for EDM |
| Make effect brighter/dimmer | Push/pull fader via `set_executor_level` | 0–100 |
| Kill effect completely | `clear_effects_on_page(page, start_exec=N, end_exec=N)` | single exec |

Rate is relative (multiplier around whatever the effect's base speed is).
Speed is absolute — it locks the BPM regardless of the effect's programmed rate.
Use rate for feel adjustments; use speed when syncing to a specific BPM track.

### Effect Layering with MAtricks

Layer spatial variation on top of effects without duplicating them:

1. Select the fixture group the effect runs on
2. Apply `MAtricksInterleave 4` (or other split) — divides fixtures into alternating groups
3. Run the effect — MA2 applies the phase offset automatically per MAtricks split
4. Adjust interleave live with `modulate_effect` rate to tighten/loosen the chase

Useful combinations:
- Strobe + Interleave 2 → alternating strobe (odd vs even fixtures)
- Chase + Interleave 4 → 4-way pixel chase
- Beam effect + Groups 2 → two independent beam balls

### Live Recovery Protocol

When show state drifts (levels stuck, wrong color, effect not responding):

```
Step 1: normalize_page_faders(page)
        → silences everything without visual glitch (faders → 0, executors stay active)

Step 2: clear_effects_on_page(page)
        → releases all executors on page (clean slate)

Step 3: Re-trigger song loader (Exec 1 on current page)
        → restores song's base state: color, position, programmer clear

Step 4: Gradually raise effect faders in order
        → 1 fader at a time, verify each effect before adding the next
```

Never: jump straight to step 2 without step 1 — releasing running effects
causes a visible flash if their faders are above zero.

### Safety Rules

- Never call `assign_effect_to_executor` during a live show — always pre-show
- Use `normalize_page_faders` before `clear_effects_on_page` in all recovery paths
- Effects assigned to executors survive `ClearAll` — programmer clear does not kill faders
- Group masters (execs 9-10) override individual effect intensities — always check these
  when an effect seems low/high

---

## Template Generator

**Worker charter:** DESTRUCTIVE — creates groups, presets, sequences, and executor assignments. Always save show before starting. Confirm each phase with operator before executing.

Invoke when asked to: build a busking template, generate a busk rig from patch, auto-generate groups and presets, or set up a festival busking page.

Target users: Busking operators at festivals/clubs, emerging EDM artists, venue operators setting up for unknown visiting acts.

### What This Builds

From a patched rig with fixture types already imported, this skill generates:

1. **Fixture groups** by type (all wash movers, all spots, all beams, all LED bars, all strobes)
2. **Color presets** — 8 universal colors per fixture group: red, orange, yellow, green, cyan, blue, magenta, white
3. **Position presets** — 4 universal positions per mover group: home, down-center, stage-left-top, stage-right-top
4. **Effects** — 3 universal effects per group: slow color chase, medium position wave, fast strobe
5. **Speed masters** — assign speed master 1 to all chase effects
6. **Executor layout** — single page: groups on right wing, effects across main faders

### Phase 0 — Survey (SAFE_READ, always first)

```python
hydrate_console_state()
list_fixtures()           # total fixture count
list_fixture_types()      # what types are in the rig
list_universes()          # which universes are used
list_preset_pool(preset_type="color")     # check if presets already exist
list_preset_pool(preset_type="position")
```

Present summary to operator: "Found [N] fixtures across [M] types. Color pool has [K] existing presets. Proceed?"

### Phase 1 — Group Creation (DESTRUCTIVE)

For each unique fixture type found:
```python
create_fixture_group(
    group_id=<next_available>,  # start from 1 or first empty slot
    fixture_selection="FixtureType [TypeName] 1 Thru",
    confirm_destructive=True
)
label_or_appearance(object_type="group", object_id=N, label="[TypeName] ALL")
```

Use HSB color coding per group type (0-100 percentage scale):
- Wash → blue (hue 240, sat 100, brightness 80)
- Spot → white (hue 0, sat 0, brightness 100)
- Beam → yellow (hue 60, sat 100, brightness 80)
- Strobe → red (hue 0, sat 100, brightness 80)

### Phase 2 — Color Presets (DESTRUCTIVE)

For each group, create 8 universal color presets. RGB values use the 0-100 percentage scale (NOT 0-255):

| Label | R | G | B |
|-------|---|---|---|
| Red | 100 | 0 | 0 |
| Orange | 100 | 40 | 0 |
| Yellow | 100 | 100 | 0 |
| Green | 0 | 100 | 0 |
| Cyan | 0 | 100 | 100 |
| Blue | 0 | 0 | 100 |
| Magenta | 100 | 0 | 100 |
| White | 100 | 100 | 100 |

```python
# Select fixture group first
select_fixtures_by_group(group_id=N)
# Set color attribute (0-100 scale)
set_attribute(attribute="ColorRgb1", value=100)
# Store as universal preset
store_new_preset(preset_type="color", preset_id=<slot>, scope="universal", confirm_destructive=True)
label_or_appearance(object_type="preset", object_id=<slot>, preset_type="color", label="Red")
```

### Phase 3 — Position Presets (DESTRUCTIVE, mover groups only)

Only for fixture groups whose types have Pan and Tilt attributes.

| Label | Pan | Tilt |
|-------|-----|------|
| Home | 50 | 50 |
| DownCenter | 50 | 80 |
| SL Top | 25 | 30 |
| SR Top | 75 | 30 |

```python
select_fixtures_by_group(group_id=N)
set_attribute(attribute="Pan", value=50)
set_attribute(attribute="Tilt", value=50)
store_new_preset(preset_type="position", preset_id=<slot>, scope="universal", confirm_destructive=True)
label_or_appearance(object_type="preset", preset_type="position", object_id=<slot>, label="Home")
```

### Phase 4 — Executor Layout (DESTRUCTIVE)

Assign sequences to executors on a dedicated busking page:

| Exec | Content | Label |
|------|---------|-------|
| 1 | Song loader macro | LOAD |
| 2-5 | Effect sequences per fixture type | FX [Type] |
| 6-8 | Group masters (intensity only) | GRP [N] |
| 9 | Speed master 1 | SPD |
| 10 | Emergency blackout macro | BO |

```python
assign_sequence_to_executor(sequence_id=N, executor_id="[page].[exec]", confirm_destructive=True)
control_special_master(master_type="speed", master_id=1, value=120)  # default 120 BPM
```

### Phase 5 — Verify and Save

```python
get_console_state()           # confirm groups, presets registered
save_show(confirm_destructive=True)   # always save after template build
```

### Operator Confirmation Gates

Pause and confirm with operator before each DESTRUCTIVE phase:

- **Phase 1:** "I will create [N] groups. This will overwrite slots [X-Y]. Proceed?"
- **Phase 2:** "I will create [M] color presets in slots [A-B]. Proceed?"
- **Phase 4:** "I will assign sequences to page [P] executors 1-10. This will overwrite existing assignments. Proceed?"

Never proceed past a confirmation gate without explicit operator approval.

### Allowed Tools

```
SAFE_READ: hydrate_console_state, list_fixtures, list_fixture_types, list_universes, list_preset_pool
DESTRUCTIVE: create_fixture_group, label_or_appearance, set_attribute, store_new_preset,
             store_current_cue, assign_sequence_to_executor, control_special_master, save_show
```
