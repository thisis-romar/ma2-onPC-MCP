---
title: Macro Audit and Fire
description: Safe destructive-macro execution pattern — audit, snapshot, fire, capture, save, restore. Includes build/cleanup pair convention for parametrized object families.
version: 1.0.0
created: 2026-05-13T10:58:00Z
last_updated: 2026-05-13T10:58:00Z
---

# Macro Audit and Fire

Safe pattern for executing any grandMA2 macro that creates, modifies, or deletes console objects. Derived from live execution of Macro 16 (`-Create FT_Pools-`) and v12 (`-Create FT_Pools v12-`) on `19-toronto-2025-09-09-v4`.

---

## The 10-step canonical sequence

### Step 1 — Confirm loaded show (SAFE_READ)

Send `ListVar` → parse `$SHOWFILE` via `list_system_variables()`. **Abort if mismatch** — never fire a macro against an unexpected show.

```python
# Reuse: src/console_state.py → parse_showfile_from_listvar()
```

### Step 2 — Snapshot under a new name (DESTRUCTIVE)

```
SaveShow "<show>-pre-m<N>"    # confirm_destructive=True
```

Naming convention: `<original-show-stem>-pre-m<N>` (e.g. `19-toronto-2025-09-09-v4-pre-m16`).

**Gotcha G1:** `SaveShow "<new>"` renames the show **in memory** — `$SHOWFILE` switches to the new name. It may NOT produce a new `.show.gz` on disk under the renamed name. Verify with `ls` on the shows directory; if absent fall back to `Backup /save` or OS-level file copy.

### Step 3 — Export the macro body (SAFE_READ)

```
Export Macro <N> "<filename>" /overwrite /noconfirm
```

Builder: `src/commands/functions/importexport.py:58` → `export_object()`.

**Gotcha G2:** The XML lands at `<data-root>/macros/<filename>.xml` — NOT `importexport/macros/`. MA2 routes Macro exports to the data-root `macros/` folder, which is also where `import "<filename>"` looks.

### Step 4 — Risk-classify each macroline

Parse the exported XML. Per-line classifier:

| Class | Examples | Gate |
|---|---|---|
| `SAFE_READ` | `list`, `info`, `ListVar` | Always green-light |
| `SAFE_WRITE` | `go`, `at`, `select`, `clear` (no store/delete) | Operator OK |
| `DESTRUCTIVE` | `store`, `delete`, `copy`, `move`, `assign`, `import`, `BlindEdit` toggle | Require Step 2 snapshot |

Present classification table to operator before Step 5.

**Gotcha G7:** `BlindEdit On/Off` looks SAFE but toggles console state — classify as DESTRUCTIVE if it leaves state mutated.

### Step 5 — Fire the macro (DESTRUCTIVE)

```python
# src/telnet_client.py → GMA2TelnetClient  (NOT TelnetClient — import doesn't exist)
async with GMA2TelnetClient(host, port, user, password) as c:
    feedback = await c.send_command_with_response("Go Macro <N>", timeout=10.0)
```

**Gotcha G3:** Use `GMA2TelnetClient`, not `TelnetClient`.

Save full ANSI-stripped stream to `/tmp/macro<N>/feedback.log` before parsing.

### Step 6 — Classify feedback stream

Use `parse_telnet_feedback()` + `FeedbackClass` from `src/rights.py`:

```python
from src.rights import parse_telnet_feedback, FeedbackClass
```

Build side-effect inventory: which Groups / Presets / Worlds / Sequences were created or modified.

**Gotcha G4:** `Echo $VAR` fails in MA2 (expands before executing → UNKNOWN COMMAND). Read variables via `ListVar` only.

### Step 7 — Save result

```
SaveShow "<show>-<feature>"    # confirm_destructive=True
```

Example: `SaveShow "19-toronto-2025-09-09-v4-ft-pools-v12"`.

### Step 8 — Verify save landed on disk

Bash `ls` on shows directory + mtime check. Same G1 gotcha applies.

### Step 9 — Return to baseline show

```
LoadShow "<baseline-show>"    # confirm_destructive=True
ListVar  → confirm $SHOWFILE matches
```

### Step 10 — Document into the transcript

Append a section to `tests/manual/group-audit-transcript.md`:
- Macro body
- Pre-execution state (`$SHOWFILE`, `$SELECTEDEXEC`, `$USERRIGHTS`)
- Full Telnet feedback (line-numbered)
- Per-line classification table
- Side-effect inventory (objects created/modified/deleted)
- Post-state delta

Bump `version` MINOR for new section.

---

## Build/cleanup pair pattern (FT_Pools reference implementation)

When a destructive build macro creates many parametrized objects, ALWAYS ship a paired cleanup macro alongside it.

### Naming convention

| Role | File pattern | `<Macro name>` attribute | Appearance |
|---|---|---|---|
| Build | `-Create <Feature> v<N>-.xml` | matches basename | vivid (e.g. `00cc88`) |
| Cleanup | `-Delete <Feature> v<N>-.xml` | matches basename | red (`cc0044`) |

### Coupling rule

Both files share a **base-config UserVar block** (lines 1-5 by convention, indices 0-4 in the build, 1-5 in the cleanup):

```
$maxFTscan = 30
$ftGroupBase = 1
$poolGroupBase = 11
$presetBase = 11
$worldBase = 11
```

**Edit both files in lockstep** when relocating output slots. Drift causes orphaned objects on cleanup.

### Cleanup properties

- **Linear** — no `Go Macro` jumps, so no line-numbering fragility under future edits
- **Idempotent** — `Delete … Thru … /noconfirm` silently no-ops on empty slots
- **Wide coverage** — default range covers `$maxFTscan` (30) slots per family, so it cleans up any single build run without operator edits
- Cleanup range computed as: `$end = $base + $maxFTscan - 1`

### Live reference implementation

| File | Role |
|---|---|
| `macros/ft-pools/-Create FT_Pools v12-.xml` | Build — 50 macrolines, PT 0-7 universal presets |
| `macros/ft-pools/-Delete FT_Pools v12-.xml` | Cleanup — 22 macrolines, linear, mirrors build base-config |

---

## Gotcha quick-reference

| # | Surprise | Rule |
|---|---|---|
| G1 | `SaveShow "<new>"` renames in memory but may NOT write `.show.gz` to disk | Verify with `ls`, fallback to `Backup /save` |
| G2 | Macro `Export` lands at `<data-root>/macros/`, NOT `importexport/macros/` | Check file at `macros/<filename>.xml` |
| G3 | Telnet class is `GMA2TelnetClient`, NOT `TelnetClient` | Import from `src.telnet_client` |
| G4 | `Echo $VAR` fails (MA2 expands before executing) | Use `ListVar` to read variables |
| G5 | `save_show`, `load_show`, `import_objects`, `export_objects` MCP tool wrappers missing on main | Use `send_raw_command` workaround with `confirm_destructive=True` |
| G6 | Macro 16 hardcodes slot ranges (Groups 1-10 + 11-22, Presets 0.11-0.22, Worlds 11-22) | Run pre-flight `list group / preset / world` before firing on non-19-toronto shows |
| G7 | `BlindEdit On/Off` looks SAFE but toggles console state | Classify as DESTRUCTIVE |

---

## Critical files

| Path | Role |
|---|---|
| `src/commands/functions/importexport.py:58` | `export_object()` builder |
| `src/telnet_client.py` | `GMA2TelnetClient` |
| `src/rights.py` | `parse_telnet_feedback`, `FeedbackClass` |
| `src/console_state.py` | `parse_showfile_from_listvar()` |
| `tests/manual/group-audit-transcript.md` | Audit trail output |
