---
title: Project Rules
description: Thin root conventions for ma2-onPC-MCP — architectural invariants, safety rules, and build commands
version: 4.12.4
created: 2026-03-01T23:37:51Z
last_updated: 2026-04-06T13:39:09Z
---

# Project Rules

## Project Identity

MCP server exposing **197 tools**, **18 resources**, **13 prompts**, and **34 skills** so AI assistants can control a grandMA2 lighting console via Telnet. Includes an **agent harness** (`src/agent/`) for autonomous multi-step execution with planning, policy enforcement, verification, and audit traces.

Central rule: **planner decides → skills carry instructions → subagents execute in isolation → tools take narrow actions → memory stores distilled checkpoints**.

All network I/O is isolated in `src/telnet_client.py`. Command builders in `src/commands/` are pure functions returning strings — no side effects.

---

## Architecture Quick Reference

| Module | Role |
|--------|------|
| `src/server.py` | FastMCP server — 163 tools + 18 MCP resources + 13 MCP prompts, safety gate |
| `src/server_orchestration_tools.py` | Registers 34 agentic tools onto FastMCP |
| `src/telnet_client.py` | Async Telnet (telnetlib3), auth, send/receive, injection prevention |
| `src/session_manager.py` | Per-operator Telnet session pool (LRU, keepalive, auto-reconnect) |
| `src/credentials.py` | OAuth tier → console user credential resolver |
| `src/auth.py` | OAuth 2.1 scope enforcement (`@require_scope`, `@require_ma2_right`) |
| `src/license.py` | BSL 1.1 license tier enforcement (`LicenseTier`, `require_tier`, `has_tier`, `get_license_tier`) |
| `src/license_tiers.py` | `TOOL_LICENSE_TIERS` dict — maps tool function names → `LicenseTier` (COMMUNITY/PROFESSIONAL/ENTERPRISE) |
| `src/navigation.py` | cd + list + prompt parsing orchestration |
| `src/prompt_parser.py` | Parse console prompts and `list` tabular output |
| `src/commands/` | 254 pure command-builder functions (262 exports incl. 8 constants), grouped by keyword type |
| `src/commands/helpers.py` | `quote_name()` wildcard spec, `_build_store_options()` flag assembly |
| `src/vocab.py` | 158 keyword vocab entries (89 function + 56 object + 7 helping + 6 special), `KeywordCategory`, `RiskTier`, `classify_token()` |
| `src/orchestrator.py` | Multi-agent task runner: hydration, risk-tier isolation, LTM; `_showfile_guard()` + `check_showfile()` |
| `src/task_decomposer.py` | Natural-language goal → ordered SubTask plan (rule-based) |
| `src/agent_memory.py` | WorkingMemory (ephemeral) + LongTermMemory (SQLite session log) + DecisionCheckpoint cache; showfile baseline tracking (`baseline_showfile`, `showfile_changed()`) |
| `src/console_state.py` | ConsoleStateSnapshot: hydrates all 19 show-memory gaps; `parse_showfile_from_listvar()` |
| `src/pool_name_index.py` | In-memory pool name/ID registry, zero-cost object resolution |
| `src/rights.py` | MA2 native rights enforcement, FeedbackClass, parse_telnet_feedback |
| `src/telemetry.py` | Per-tool invocation recorder: `tool_invocations` table, latency, risk tier |
| `src/skill.py` | `Skill` dataclass + `SkillRegistry`: versioned playbooks with lineage + filesystem skill fallback (`_load_filesystem_skill`, `_list_filesystem_skills`) |
| `src/skill_improver.py` | `SkillImprover`: repair suggestions + promotion candidates (read-only) |
| `src/tools.py` | Global GMA2 telnet client accessor — `get_client()` used by all tools |
| `src/categorization/` | ML-based tool categorization: K-Means clustering + auto-labeling |
| `rag/` | crawl → chunk → embed → store → retrieve pipeline |
| `.claude/rules/` | Scoped rule files (loaded on demand, not at startup) |
| `.claude/skills/` | Instruction modules (playbooks injected as user messages) |
| `.claude/settings.json` | Project-level Claude Code config — Stop hook (commit/push guard) |
| `.githooks/pre-commit` | RAG zero-vector ingest on every commit |
| `.githooks/pre-push` | Runs `pytest -x -q` before every push |
| `.githooks/stop-git-check.sh` | Stop hook — flags uncommitted/unpushed work when Claude stops |
| `src/agent/runtime.py` | Agent harness: goal → plan → execute → verify → trace |
| `src/agent/planner.py` | Rule-based domain planner, goal classification |
| `src/agent/executor.py` | Step executor with retries, confirmation flow |
| `src/agent/policy.py` | Plan-level governance (extends `src/vocab.py` safety) |
| `src/agent/verification.py` | Post-mutation state verification |
| `src/agent/memory.py` | SQLite workflow memory (conventions, recipes, run history) |
| `src/agent/trace.py` | Structured JSON execution traces |
| `src/agent/state.py` | Data models: RunContext, PlanStep, Checkpoint |
| `src/agent/workflows/` | Workflow templates: patch, preset, playback, common |

**Responsibility map:** see `doc/responsibility-map.md`.
**Tool tier classification:** see `doc/tool-surface-tiers.md`.
**MCP primitive audit:** see `doc/transcript-architecture-audit.md`.

---

## MCP Servers (project-level)

`.mcp.json` at the repo root registers the following servers for Claude Code CLI agents:

| Server | Command | Purpose |
|--------|---------|---------|
| `time` | `npx -y @modelcontextprotocol/server-time` | Accurate timestamps for `.md` front matter |

When writing or editing any `.md` file, call `get_current_time` first and use the returned `datetime` value for `created` / `last_updated` front matter fields.

**Fallback:** If the MCP time server is unavailable (connection refused, tool not found, or `npx` missing), get the current time from the system instead:

```bash
date -u +%Y-%m-%dT%H:%M:%SZ
```

---

## Development Commands

```bash
uv run python -m pytest -v                                    # all tests
uv run python -m pytest tests/test_vocab.py                   # subset
uv run python -m src.server                                   # start MCP server
uv run python scripts/rag_ingest.py --root . --provider zero  # RAG ingest (zero-vector)
make install-hooks                                             # git hooks (pre-commit/pre-push/stop)
uv run python scripts/audit_md_counts.py                      # audit MD counts (runs in pre-push)
uv run python scripts/audit_md_counts.py --fix                # auto-fix stale counts
```

---

## Code Conventions

### Adding a new MCP tool
1. Add command builder in `src/commands/` — pure, returns `str`, no I/O.
2. Export from `src/commands/__init__.py`.
3. Register in `src/server.py` with `@mcp.tool()` and `@_handle_errors`.
4. Apply `@require_scope(OAuthScope.X)` — see `doc/ma2-rights-matrix.json`.
5. Add an entry to `_OPERATION_MIN_RIGHT` in `src/rights.py` mapping the tool function name → `MA2Right` tier. This is **required** — `_handle_errors` enforces it at runtime.
6. If DESTRUCTIVE, accept `confirm_destructive: bool = False` and gate on it.
7. Assign a license tier in `src/license_tiers.py` (omit for COMMUNITY / free).
8. Add tests in `tests/test_<feature>.py`.

### Adding a new MCP resource
- Use `@mcp.resource("ma2://category/name")` for static docs or URI-addressable state.
- Use `@mcp.resource("ma2://category/{param}")` for templated dynamic resources.
- Resources must be read-only — no console side-effects.

### Adding a new MCP prompt
- Use `@mcp.prompt()` for user-initiated workflow templates.
- Prompts accept arguments and may reference resources.
- Prompts must not themselves execute destructive operations — they orchestrate tools.

### Command builders
- Pure functions only — no imports from `src.telnet_client`, `src.navigation`, or `src.server`.
- Return raw grandMA2 command strings, e.g. `"Store Cue 1 Sequence 99 /merge"`.
- See `.claude/rules/ma2-conventions.md` for quoting, path, and timing rules.

### Tests
- Unit tests import command builders or vocab directly and assert on returned strings.
- No live console required; live tests are in `tests/test_live_integration.py` (skipped by default).
- Use `@pytest.mark.asyncio` for async tests.
- Current counts (2026-04-04): **3099 tests** (unit + live integration).

---

## Safety Rules

**3-layer permission model:** `scope ∩ ma2_rights ∩ console_floor = FINAL AUTHORITY`

| Layer | Enforcement | Bypass |
|-------|-------------|--------|
| OAuth scope | `@require_scope` decorator (src/auth.py) | `GMA_AUTH_BYPASS=1` |
| MA2 native rights | `is_permitted()` in `_handle_errors` (src/rights.py) | `GMA_RIGHTS_BYPASS=1` |
| Console floor | grandMA2 Error #72 (passive, irrevocable) | None |

**Risk tiers** enforced before any command reaches the console:

| Tier | Examples | Policy |
|------|----------|--------|
| `SAFE_READ` | `list`, `info`, `cd` | Always allowed |
| `SAFE_WRITE` | `go`, `at`, `clear`, `park` | Allowed in `standard` and `admin` modes |
| `DESTRUCTIVE` | `delete`, `store`, `copy`, `move`, `assign` | Blocked unless `confirm_destructive=True` |

- Any tool calling a `DESTRUCTIVE` command must accept `confirm_destructive: bool = False` and gate on it.
- Never pass `confirm_destructive=True` automatically.
- Line breaks (`\r`, `\n`) in command strings are rejected by the safety gate.
- **`new_show` without `/globalsettings` disables Telnet** — always keep `preserve_connectivity=True`.
- **New tools must be added to `_OPERATION_MIN_RIGHT`** in `src/rights.py` — omission defaults to `MA2Right.NONE` (read-only).

**Network hardening** — the 3-layer model protects against the AI agent, NOT against direct network access to port 30000:

- The MCP server must run **co-located** with grandMA2 onPC (same machine).
- Host firewall must restrict TCP 30000 to loopback: `sudo bash scripts/lockdown_firewall.sh --apply`.
- `_check_network_security()` in `src/server.py` warns at startup if `GMA_HOST` is not loopback, any bypass var is enabled, or factory credentials are in use.
- See `doc/network-topology.md` for the full deployment diagram.

---

## License Tier Feature Gating

All 197 MCP tools are classified into three license tiers:

| Tier | Cost | Tool count | Examples |
|------|------|-----------|---------|
| `COMMUNITY` | Free | ~30 | `navigate_console`, `get_object_info`, `playback_action`, `set_intensity` |
| `PROFESSIONAL` | Paid | ~120 | Store/copy/delete, presets, sequences, macros, effects, patch, show mgmt |
| `ENTERPRISE` | Premium | ~50 | RAG search, orchestration, skill system, agent harness, ML categorisation |

**Environment variables:**

| Var | Default | Effect |
|-----|---------|--------|
| `GMA_LICENSE_TIER` | `community` | Active tier: `community`, `professional`, `enterprise` |
| `GMA_LICENSE_BYPASS` | `0` | Set `1` to bypass tier checks (dev/test only) |

**How it works:** `_handle_errors` in `src/server.py` reads `TOOL_LICENSE_TIERS` (from `src/license_tiers.py`) at decoration time. Tools not in the map default to COMMUNITY. When a tool's tier exceeds the active tier, it returns `{"blocked": True, "license_required": "...", "current_tier": "..."}`.

**Adding a tool's tier:** Add an entry to `TOOL_LICENSE_TIERS` in `src/license_tiers.py`. Omit COMMUNITY tools (they are the default).

---

## Agent Harness (`src/agent/`)

The agent harness enables autonomous multi-step execution on top of the existing MCP tools — no changes to command builders, telnet client, or navigation.

```
AgentRuntime (runtime.py)
  → DomainPlanner (planner.py) — rule-based goal → plan
  → PolicyEngine (policy.py) — plan-level governance
  → StepExecutor (executor.py) — tool dispatch + retries
  → Verifier (verification.py) — post-mutation checks
  → WorkflowMemory (memory.py) — SQLite operational memory
  → ExecutionTrace (trace.py) — JSON audit artifacts
```

MCP tools added: `run_agent_goal(goal, auto_confirm, dry_run)`, `plan_agent_goal(goal)`.

**Note:** `DomainPlanner` uses its own `PlanStep` model. Use `src/agent_bridge.py` (see below) to convert between `PlanStep` and main's `SubTask` for cross-system interop.

---

## Scoped Rules (loaded on demand)

These files are NOT loaded at startup. Reference them explicitly when working on the relevant area:

| File | When to load |
|------|-------------|
| `.claude/rules/ma2-conventions.md` | MA2 commands, quoting, navigation, macros, system vars |
| `.claude/rules/functional-domains.md` | Vocab domains, hardkey chains, executor priorities |
| `.claude/rules/openspace-layer.md` | Telemetry, skills, SkillImprover, LTM compression |
| `.claude/rules/rag-pipeline.md` | RAG ingest scripts, embedding providers, web docs |
| `.claude/rules/markdown-frontmatter.md` | Front matter requirements for new/edited .md files |
| `.claude/rules/content-filter-avoidance.md` | Workarounds for writing LICENSE/legal text files |

---

## What NOT To Do

- Do not add network I/O to command builders in `src/commands/` — they must stay pure.
- Do not import from `src.server` or `src.navigation` inside `src/commands/`.
- Do not hardcode `GMA_HOST`, `GMA_PORT`, or credentials — always read from env vars.
- Do not set `confirm_destructive=True` inside server tool implementations.
- Do not commit `rag/store/rag.db` or `rag/store/web_crawl_cache.json` — local artifacts.
- Do not edit `src/grandMA2_v3_9_telnet_keyword_vocabulary.json` manually.
- Do not call `new_show` with `preserve_connectivity=False` unless the user explicitly accepts Telnet will be disabled.
- Do not pass pre-quoted strings to `quote_name()` — pass raw names only.
- Do not call `ToolTelemetry.record_sync()` manually — `@_handle_errors` records automatically.
- Do not call `SkillRegistry.approve()` from tool implementations — only Tool 143 may.
- Do not auto-promote Skills from `SkillImprover` output — promotion is operator-initiated via Tool 141.
- Do not make MCP resources perform console side-effects — resources are read-only context.
- Do not put MA2 operating knowledge into tool docstrings — put it in `.claude/skills/` instead.
- Do not add a new `@mcp.tool()` without adding its entry to `_OPERATION_MIN_RIGHT` in `src/rights.py` — `test_all_197_tools_mapped` will fail.
- Do not set `GMA_AUTH_BYPASS=1`, `GMA_RIGHTS_BYPASS=1`, or `GMA_LICENSE_BYPASS=1` in production — dev/test only.

