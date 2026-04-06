---
title: Changelog
description: All notable changes to GrandPA2-Buddy, organized by version
version: 1.0.0
created: 2026-04-06T15:55:55Z
last_updated: 2026-04-06T15:55:55Z
---

# Changelog

All notable changes to this project are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.34.2] — 2026-04-06

### Added
- **Phase 1 — Safety Hardening**
  - `CircuitBreaker` on telnet client (3-state: CLOSED→OPEN→HALF_OPEN) prevents cascading timeouts
  - `PolicyStrictness` enum (WARN/BLOCK) with `GMA_POLICY_STRICTNESS` env var
  - `RollbackExecutor` with OOPS/DELETE compensation strategies wired into `StepExecutor`

- **Phase 2 — Performance & Intelligence**
  - Incremental console hydration (`pool_types` param + `pools_for_gaps()` helper)
  - Risk-weighted quality scoring in `SkillImprover` (DESTRUCTIVE failures count 3×)
  - `ProgressMonitor` in executor detects stalled (consecutive failures) and looping (identical outputs)

- **Phase 3 — Semantic Skill Search**
  - `search_semantic()` method on `SkillRegistry` using RAG `EmbeddingProvider` cosine similarity
  - Embedding stored automatically on `save()` and `promote_from_session()`
  - Graceful LIKE fallback when no embedding provider configured

- **Phase 4 — DAG Checkpoint Persistence**
  - `step_checkpoints` table in `WorkflowMemory` for crash recovery
  - `checkpoint_fn` callback in `StepExecutor` persists after every step
  - `resume_run()` in `AgentRuntime` reconstructs and resumes interrupted runs

- **Phase 5 — Bridge Activation**
  - Fixed dependency name↔UUID conversion in `plansteps_from_subtasks()` / `subtasks_from_plansteps()`
  - `execute_subtasks_via_agent()` bridges System A plans to System B executor
  - `_run_via_agent_bridge()` optional backend in Orchestrator

- **Phase 6 — Tool Routing Improvements**
  - Hybrid retrieval via Reciprocal Rank Fusion (RRF) in `suggest_tool_for_task`
  - `filter_risk_tier` and `filter_license_tier` metadata filter parameters
  - `rerank_tools()` second-stage body scorer in `rag/retrieve/rerank.py`
  - Enriched taxonomy descriptors (risk_tier, param_names, action_verbs, command_modules)
  - Skills `applicable_context` connected to tool routing (returns `related_skills`)

- **Audit Response**
  - 6 new task decomposition rules: effect, chaser, macro, timecode, import, view/layout (8→14 rules)
  - `_validate_license_tiers()` startup warning for unmapped destructive tools
  - Skill deprecation mechanism (`deprecated` field + `SkillRegistry.deprecate()`)
  - Pre-filter vector search by `repo_ref` / `kind` in `search_by_embedding()`
  - Chunk deduplication across `repo_ref`s in `rag_query()` results
  - robots.txt support in web crawler via `RobotFileParser`
  - FTS5 rebuild after bulk delete in `delete_by_repo_ref()`
  - End-to-end RAG pipeline test (ingest → query round-trip)
  - License tier validation hygiene test (found and removed 10 phantom entries)
  - Cross-system bridge tests (dependency chain + fault propagation)
  - Ruff lint check added to `.githooks/pre-commit`

### Changed
- `instructions=` block in FastMCP updated: 173→197 tools, 9→18 resources, 6→13 prompts
- `suggest_tool_for_task` now returns `risk_tier` per suggestion
- `search()` and `list_all()` on `SkillRegistry` exclude deprecated skills
- `StepExecutor` skips already-completed steps (enables resume)
- README badge version synced from 3.26.0 to 3.34.2
- README: added "Advanced Features (Phases 1–6)" table to architecture section
- README: all badges now link to canonical proof surfaces
- README: project structure test count 2187→3135, skills count 7→34

### Fixed
- 10 phantom entries removed from `TOOL_LICENSE_TIERS` (builder functions, not MCP tools)
- All ruff lint errors resolved (unused imports, quoted annotations, import sorting)
- Version drift: `pyproject.toml` and `src/__init__.py` synced to 3.34.2

### Tests
- 108 new test cases added (2885 → 2993 passing, 142 skipped)
- `test_rag_query.py`: 4 → 14 tests (score ordering, empty DB, embedding fallback, multi-kind, E2E)
- `test_task_decomposer.py`: 56 → 74 tests (6 new workflow rule suites)
- `test_agent_bridge.py`: 25 → 32 tests (dependency resolution, bridge execution, fault propagation)
- `test_agent_executor.py`: 12 → 22 tests (checkpoint callback, resume skip, stall detection)
- `test_skill.py`: 59 → 66 tests (semantic search, embedding storage, migration idempotency)
- `test_skill_improver.py`: 20 → 26 tests (risk-weighted scoring)
- `test_console_state.py`: 44 → 51 tests (pools_for_gaps, GAP_POOL_MAP validation)
- `test_rerank.py`: 15 → 20 tests (rerank_tools body overlap)
- `test_agent_workflow_memory.py`: 13 → 20 tests (step checkpoint CRUD)
- `test_architecture_hygiene.py`: added license tier validation test

---

## [3.26.0] — 2026-04-04

### Added
- BSL 1.1 license and 3-tier feature gating system (COMMUNITY / PROFESSIONAL / ENTERPRISE)
- `TOOL_LICENSE_TIERS` dict mapping 187 tool function names to license tiers
- `require_tier()` decorator, `get_license_tier()`, `has_tier()` in `src/license.py`
- Network hardening: `_check_network_security()` startup guard, `scripts/lockdown_firewall.sh`
- `doc/network-topology.md` deployment diagram
- MD count audit script (`scripts/audit_md_counts.py`) wired into pre-push hook
- Pre-push test hook, pre-commit IP protection hook, stop hook for uncommitted work
- SECURITY.md, TERMS.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md

### Changed
- Project renamed to GrandPA2-Buddy
- All tools gated by license tier (default COMMUNITY for unlisted tools)
- `_handle_errors` decorator enforces scope ∩ rights ∩ license tier

---

## [3.23.0] — 2026-03-30

### Added
- OpenSpace layer: `SkillImprover`, `DecisionCheckpoint`, `WorkingMemory` compression (v2 format)
- Busking tools: 6 performance builders (effect assign, rate/speed, page release, fader zero)
- Executor assignment wrappers for priority, MIB, autostart options
- `showfile_changed()` detection in agent memory
- 11 new `.claude/skills/` instruction modules
- 7 new MCP tools, 4 resources, 4 prompts
- MCP time server integration (`.mcp.json`)

---

## [3.21.0] — 2026-03-28

### Added
- 21 MCP tools (Waves 1–5) closing RAG audit gaps
- `list_agenda_events` tool
- 3 task decomposer rules, 2 WORKER_CATALOG entries
- 8 new skill instruction modules
- Timecode skill

---

## [3.20.0] — 2026-03-26

### Added
- Agent harness: `AgentRuntime`, `DomainPlanner`, `StepExecutor`, `PolicyEngine`, `Verifier`
- `WorkflowMemory` (SQLite-backed recipes + run history)
- `ExecutionTrace` JSON audit artifacts
- Agentic orchestration layer: tools 110–137
- Console state hydrator (19 show-memory gaps)
- Wildcard discovery + fixture validation tools
- MCP completions, elicitation, sampling, subscriptions modules

### Changed
- Orchestrator refactored with `_showfile_guard()`, `_preflight_guard()`
- README rewritten with architecture diagrams

---

## [3.9.0] — 2026-03-20

### Added
- ML-based tool categorization: K-Means clustering + auto-labeling (`src/categorization/`)
- `create_matricks_library` tool with 25-color appearance embedding
- Safety gates and race condition fixes
- RAG pipeline: crawl → chunk → embed → store → retrieve → rerank
- Web crawler for grandMA2 help docs (~1,043 pages)
- MCP SDK source indexing

---

## [3.0.0] — 2026-03-15

### Added
- Initial MCP server with 78 tools covering grandMA2 Telnet operations
- `src/commands/` pure command builders (no I/O)
- `src/telnet_client.py` async Telnet with auth
- `src/vocab.py` keyword vocabulary (158 entries)
- `src/navigation.py` cd/list orchestration
- `src/prompt_parser.py` console prompt and tabular output parser
- OAuth scope enforcement (`@require_scope`)
- Risk tier classification (SAFE_READ / SAFE_WRITE / DESTRUCTIVE)
- System variable access (ListVar, GetVar)
- PresetType / Feature / CD-Tree correlation

---

[3.34.2]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.26.0...v3.34.2
[3.26.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.23.0...v3.26.0
[3.23.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.21.0...v3.23.0
[3.21.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.20.0...v3.21.0
[3.20.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.9.0...v3.20.0
[3.9.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.0.0...v3.9.0
[3.0.0]: https://github.com/thisis-romar/ma2-onPC-MCP/commits/v3.0.0
