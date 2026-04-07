---
title: Full Builder / Tool / Skill / Resource / RAG Manual Gap Audit
description: Coverage gaps between command builders, MCP tools, skills, prompts, resources, and MA2 help documentation
version: 1.8.1
created: 2026-04-02T09:07:54Z
last_updated: 2026-04-07T19:09:40Z
---

# Full Builder / Tool / Skill / Resource / RAG Manual Gap Audit

## Scope

The project exposes 191 MCP tools, 222 command builders, 34 skills, 13 resources, and 10 prompts. The RAG manual indexes 1,043 grandMA2 help pages. This document identifies four categories of coverage gaps and assigns a priority rating to each so they can be addressed incrementally.

**No Python source changes are made in this pass.** Follow-on PRs address each priority bucket.

---

## Category 1 — Vocab Keywords with No Builder

Keyword appears in `src/vocab.py` but no pure command builder function exists in `src/commands/`.

### 1.1 Playback / Execution (9 gaps → **COMPLETE** ✓)

| Priority | Keyword | Domain | Builder | Status |
|----------|---------|--------|---------|--------|
| P2 | `FlashGo` | playback_control | `flash_go(executor_id, page)` | ✓ Sprint 4 — wired in `control_executor` |
| P2 | `FlashOn` | playback_control | `flash_on(executor_id, page)` | ✓ Sprint 4 — wired in `control_executor` |
| P2 | `SwopGo` | playback_control | `swop_go(executor_id, page)` | ✓ Sprint 4 — wired in `control_executor` |
| P2 | `SwopOn` | playback_control | `swop_on(executor_id, page)` | ✓ Sprint 4 — wired in `control_executor` |
| P2 | `ManualXFade` | timing_effects | `manual_xfade(executor_id, value, page)` | ✓ Sprint 4 — wired in `control_executor` |
| P7 | `SnapPercent` | timing_effects | `snap_percent(value)` | ✓ Sprint 4 — wired in `set_advanced_timing` |
| P2 | `LoadNext` | playback_control | `load_next(executor, sequence)` | ✓ Pre-existing — wired in `load_cue` tool |
| P2 | `LoadPrev` | playback_control | `load_prev(executor, sequence)` | ✓ Pre-existing — wired in `load_cue` tool |
| P2 | `DefGoPause` | playback_control | `def_go_pause()` | ✓ Pre-existing — wired in `go_executor` tool |

### 1.2 Selection / Filtering (8 gaps → **COMPLETE** ✓)

All 8 builders added to `selection.py` in Sprint 2 (P4); wired in `filter_fixture_selection` and `programming_action` tools.

### 1.3 Preview Mode (3 gaps → **COMPLETE** ✓)

All 3 builders added to `selection.py` in Sprint 3 (P8); wired in `preview_executor_content` tool.

### 1.4 Advanced Timing (5 gaps → **COMPLETE** ✓)

All 6 builders added to `src/commands/functions/timing.py` in Sprint 3 (P7); wired in `set_advanced_timing` tool.

### 1.5 Effect Parameters (6 gaps → **COMPLETE** ✓)

`set_effect_parameter()` in `system.py` covers all effect keywords via a single composite builder:
- Pre-existing: `bpm`, `hz`, `high`, `low`, `phase`, `width`, `attack`, `decay`
- Sprint 4 addition: `delay`, `fade` (added to `_EFFECT_PARAM_KEYWORDS` frozenset)

No separate `effects.py` module needed — the composite builder pattern is sufficient.

### 1.6 Object Editing (2 gaps)

| Priority | Keyword | Domain | Suggested Builder | Module |
|----------|---------|--------|-------------------|--------|
| P4 | `CircularCopy` | object_manipulation | `circular_copy(object_type, src, dest, count)` | `store.py` |
| P4 | `RemoveIndividuals` | object_manipulation | `remove_individuals(object_type, id)` | `edit.py` |

### 1.7 PSR — Partial Show Read (3 gaps → **COMPLETE** ✓)

| Priority | Keyword | Domain | Builder | Status |
|----------|---------|--------|---------|--------|
| **P1** | `PSR` | data_query | `psr(source_show, object_type, id_range)` | ✓ Sprint 1 — wired in `partial_show_read` tool |
| **P1** | `PSRList` | data_query | `psr_list(source_show)` | ✓ Sprint 1 — wired in `list_psr_objects` tool |
| **P1** | `PSRPrepare` | data_query | `psr_prepare(source_show)` | ✓ Sprint 1 — wired in `partial_show_read` tool |

### 1.8 Network / Session (9 gaps → **COMPLETE** ✓)

| Priority | Keyword | Domain | Builder | Status |
|----------|---------|--------|---------|--------|
| P9 | `JoinSession` | network_session | `join_session(session_name)` | ✓ Sprint 7 |
| P9 | `LeaveSession` | network_session | `leave_session()` | ✓ Sprint 7 |
| P9 | `EndSession` | network_session | `end_session()` | ✓ Sprint 7 |
| P9 | `InviteStation` | network_session | `invite_station(station_id)` | ✓ Sprint 7 |
| P9 | `DisconnectStation` | network_session | `disconnect_station(station_id)` | ✓ Sprint 7 |
| P9 | `TakeControl` | network_session | `take_control()` | ✓ Sprint 7 |
| P9 | `DropControl` | network_session | `drop_control()` | ✓ Sprint 7 |
| P9 | `SetIP` | network_session | `set_ip(interface, address)` | ✓ Sprint 7 |
| P9 | `SetHostname` | network_session | `set_hostname(name)` | ✓ Sprint 7 |

### 1.9 System Admin (6 gaps → **COMPLETE** ✓)

| Priority | Keyword | Domain | Builder | Module | Status |
|----------|---------|--------|---------|--------|--------|
| P10 | `CrashLogCopy` | system_admin | `crash_log_copy(dest)` | `system.py` | ✓ Sprint 7 |
| P10 | `CrashLogDelete` | system_admin | `crash_log_delete()` | `system.py` | ✓ Sprint 7 |
| P10 | `CrashLogList` | system_admin | `crash_log_list()` | `system.py` | ✓ Sprint 7 |
| P10 | `UpdateFirmware` | system_admin | `update_firmware(path)` | `system.py` | ✓ Sprint 7 |
| P10 | `UpdateSoftware` | system_admin | `update_software(path)` | `system.py` | ✓ Sprint 7 |
| P10 | `BlackScreen` | system_admin | `black_screen()` — distinct from `blackout()` | `system.py` | ✓ Sprint 3 |

### 1.10 RDM (2 gaps)

| Priority | Keyword | Domain | Suggested Builder | Module |
|----------|---------|--------|-------------------|--------|
| P9 | `RdmFixtureType` | rdm | `rdm_fixture_type(uid)` | `rdm.py` |
| P9 | `RdmSetParameter` | rdm | `rdm_set_parameter(uid, param_id, value)` | `rdm.py` |

---

## Category 2 — Builders with No MCP Tool

Builder function exists in `src/commands/` but is not wired to any MCP tool in `src/server.py`.

| Priority | Builder | Module | What it does | Suggested MCP Tool | Status |
|----------|---------|--------|--------------|--------------------|----|
| **P1** | `psr()` / `psr_list()` / `psr_prepare()` | `psr.py` | Partial Show Read operations | `partial_show_read`, `list_psr_objects` | ✓ Sprint 1 |
| P2 | `load_next()` | `playback.py` | `LoadNext` — load next cue without executing | `load_next_cue(executor_id)` | ✓ Pre-existing — `load_cue` tool |
| P2 | `load_prev()` | `playback.py` | `LoadPrev` — load previous cue without executing | `load_prev_cue(executor_id)` | ✓ Pre-existing — `load_cue` tool |
| P2 | `def_go_pause()` | `playback.py` | `DefGoPause` — define the go+pause action | `def_go_pause(executor_id)` | ✓ Pre-existing — `go_executor` tool |
| P2 | `go_fast_back()` / `go_fast_forward()` | `playback.py` | `<<<` / `>>>` fast cue jump | `go_fast(executor_id, direction)` | ✓ Pre-existing — `go_executor` tool |
| P2 | `record_macro()` | `macro.py` | `Record Macro [ID]` — interactive macro recording | `record_macro(macro_id)` | ✓ Sprint 4 — wired in `programming_action` as DESTRUCTIVE action |
| P2 | `macro_condition_line()` | `macro.py` | Macro conditional (If/While/Unless lines) | `add_macro_condition(macro_id, condition)` | ✓ Sprint 6 — builder complete; referenced in `macro-reference` resource; used at skill/agent layer |
| P2 | `macro_with_input_before/after()` | `macro.py` | Interactive macro input placeholders | `add_macro_input_placeholder(macro_id, ...)` | ✓ Sprint 6 — builders complete; used at skill/agent layer |
| P2 | `list_masters()` | `masters.py` | `List Master` — lists all special masters | `list_masters()` | ✓ Pre-existing — `get_special_masters` tool |
| P2 | `send_chat()` | `system.py` | `SendChat` — sends text to console UI chat | `send_console_chat(message)` | ✓ Pre-existing — `send_console_chat` tool |
| P2 | `extract()` | `edit.py` | `Extract` — extracts object to pool | `extract_object(object_type, id)` | ✓ Pre-existing — `programming_action` tool |
| P2 | `flip()` | `selection.py` | `Flip` — flips fixture parameter (Pan/Tilt) | `flip_fixtures()` | ✓ Pre-existing — `programming_action` tool |

---

## Category 3 — Skills with Missing Tool Dependencies

Skills that reference operations with no or insufficient builder/tool coverage.

| Priority | Skill | Missing Coverage | Recommended Fix | Status |
|----------|-------|------------------|-----------------|--------|
| **P1** | `psr-show-migration` | `PSR`, `PSRList`, `PSRPrepare` have zero builder/tool support | Add `psr.py` builders + 2 MCP tools (see Category 1 §1.7) | ✓ Sprint 1 — PSR builders + tools complete |
| **P1** | `show-management-and-psr` | Same PSR gap | Same fix as above | ✓ Sprint 1 — PSR builders + tools complete |
| P2 | `macro-advanced` | `record_macro` builder exists but no MCP tool for interactive recording | Add `record_macro` MCP tool | Open |
| P3 | `effect-programmer` | `EffectAttack`, `EffectDecay`, `EffectPhase`, `EffectWidth` have no builder | Add effect parameter builders to `effects.py` | ✓ Sprint 4 — `set_effect_parameter()` composite builder covers all 10 effect params incl. `delay`/`fade` |
| ✓ | `timecode-show-programmer` | `store_timecode_event` + `control_timecode` exist | Covered — no action needed | ✓ |
| ✓ | `world-filter-designer` | `store_world` + `store_object` for filters exist | Covered — no action needed | ✓ |

---

## Category 4 — Resources with Missing Coverage

The 16 existing resources cover: rights, vocab, tools, busking reference, RDM, Lua, compliance, volunteer guides, PSR guide, timecode reference, macro reference, network session.

| Priority | Missing Resource URI | What's Needed | Status |
|----------|---------------------|---------------|--------|
| **P1** | `ma2://docs/psr-guide` | PSR workflow, slot conflict resolution, fixture ID verification, post-import diff | ✓ Sprint 1 |
| P3 | `ma2://docs/effects-reference` | Effect parameters, forms, shapes, phase/width/attack/decay tables | ✓ Sprint 4/6 — resource exists; `delay`/`fade` params documented in Sprint 6 |
| P5 | `ma2://docs/timecode-reference` | SMPTE timecode show setup, cue triggers, slot management | ✓ Sprint 5 |
| P5 | `ma2://docs/macro-reference` | Macro Lua scripting, conditional structure, jump targets, CmdDelay | ✓ Sprint 5 |
| P9 | `ma2://docs/network-session` | Multi-console session management, TakeControl, IP setup | ✓ Sprint 5 |

---

## Category 5 — MCP Prompts with Missing Coverage

13 prompts exist covering: preflight, inspect, cue store, playback diagnosis, show load, user provisioning, volunteer preflight, busking template, health check, venue adaptation, PSR migration, effect programming, timecode show.

| Priority | Missing Prompt | Gap | Suggested Prompt Arguments | Status |
|----------|---------------|-----|---------------------------|--------|
| **P1** | `migrate_show_via_psr` | PSR migration has a skill but no guided user-facing prompt | `source_show: str`, `target_objects: str`, `dry_run: bool = True` | ✓ Sprint 1 |
| P3 | `program_effect` | Effect programming has a skill but no prompt | `fixture_group: str`, `effect_type: str`, `speed_bpm: float` | ✓ Sprint 5 |
| P5 | `build_timecode_show` | Timecode show has a skill but no prompt | `sequence_ids: list[int]`, `smpte_start: str` | ✓ Sprint 5 |

---

## Priority Summary

| Priority | Gap Type | Count | Recommended Action | Status |
|----------|----------|-------|--------------------|--------|
| **P1** | PSR keywords — no builder AND no MCP tool | 3 keywords + 2 skills + 1 resource + 1 prompt | Create `src/commands/functions/psr.py`; add `partial_show_read` + `list_psr_objects` tools; add `ma2://docs/psr-guide` resource; add `migrate_show_via_psr` prompt | ✓ Sprint 1 — builders + tools + resource + prompt complete |
| P2 | Builders with no MCP tool (wiring gap) | 10 builders | Wire existing builders into new MCP tools in `src/server.py` | ✓ Sprint 4 — all wired (5 pre-existing, 5 new Sprint 4 actions in `control_executor`) |
| P3 | Effect parameter builders missing | 6 keywords + 1 skill + 1 resource | Create `src/commands/functions/effects.py` with 8 builders; add `ma2://docs/effects-reference` resource; add `program_effect` prompt | ✓ Sprint 4/5/6 — composite builder covers all 10 params; `program_effect` prompt ✓ Sprint 5; `effects-reference` resource + `delay`/`fade` docs ✓ Sprint 6 |
| P4 | Selection helpers missing (IfActive/IfOutput/IfProg/ShuffleSelection etc.) | 8 keywords | Add to `src/commands/functions/selection.py` | ✓ Sprint 2 — all 8 added |
| P5 | Missing resources | 3 remaining | Add `@mcp.resource()` entries for timecode, macro, network-session | ✓ Sprint 5 — all 3 added |
| P6 | Missing prompts | 2 remaining | Add `@mcp.prompt()` entries for timecode show and any others identified above | ✓ Sprint 5 — `program_effect` + `build_timecode_show` complete |
| P7 | Advanced timing builders | 5 keywords | Add to `src/commands/functions/store.py` or new `timing.py` | ✓ Sprint 3 — all 6 added to `timing.py`, wired in `set_advanced_timing` tool |
| P8 | Preview mode builders | 3 keywords | Add to `src/commands/functions/selection.py` | ✓ Sprint 3 — all 3 added, wired in `preview_executor_content` tool |
| P9 | Network/session keywords | 9 keywords | Create `src/commands/functions/session.py`; low urgency for Telnet-only use | ✓ Sprint 7 — all 9 builders in `session.py` |
| P10 | System admin (CrashLog, Firmware, BlackScreen) | 6 keywords | Add to `src/commands/functions/system.py`; rarely needed via MCP | ✓ Sprint 7 — all 6 complete (`black_screen` Sprint 3, rest Sprint 7) |

---

## Verification Checklist

- [x] All 4 gap categories documented (vocab→builder, builder→tool, skill→tool, resource/prompt)
- [x] PSR gap flagged as P1 in §1.7, §Category 3, §Category 4, §Category 5, and §Priority Summary
- [x] Priority table present with counts and recommended actions
- [x] Suggested builder function names and target modules provided for every gap
- [x] Skills with full coverage noted as "Covered — no action needed"
- [x] Sprint 1 (P1 PSR): `psr.py` builders + `partial_show_read` + `list_psr_objects` tools + `ma2://docs/psr-guide` resource + `migrate_show_via_psr` prompt — all ✓
- [x] Sprint 2 (P4 selection): 8 selection helpers in `selection.py`, wired in `filter_fixture_selection` + `programming_action` — all ✓
- [x] Sprint 3 (P7+P8+P10-basics): 6 timing builders in `timing.py`, 3 preview builders, `black_screen`, `alert` — all ✓; `set_advanced_timing` + `preview_executor_content` tools added
- [x] Sprint 4 (P2+P3): 6 playback builders (`flash_go/on`, `swop_go/on`, `manual_xfade`, `snap_percent`) + `delay`/`fade` effect params — all ✓; `control_executor` + `set_advanced_timing` extended
- [x] Sprint 5 (P5+P6): `timecode_reference`, `macro_reference`, `resource_network_session` resources + `program_effect` + `build_timecode_show` prompts — all ✓; 30 tests in `tests/test_p5_p6_resources_prompts.py`
- [x] Sprint 6 (P2+P3): `record_macro` wiring confirmed in `programming_action`; `macro_condition_line`/`macro_with_input_before/after` builders closed; `effects-reference` resource updated with `delay`/`fade` params; `set_effect_param` docstring updated — 12 tests in `tests/test_sprint6_effects_macro.py`
- [x] Sprint 7 (P9+P10): 9 session builders in `session.py`; `crash_log_copy/delete/list`, `update_firmware/software` in `system.py`; all wired in both `__init__.py`s; 20 tests in `tests/test_sprint7_session_sysadmin.py`
- [x] **Gap audit complete** — all P1–P10 buckets closed. Remaining vocab gaps (§1.10 RdmFixtureType/RdmSetParameter) are outside the original scope.
