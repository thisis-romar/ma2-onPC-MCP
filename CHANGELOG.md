---
title: Changelog
description: All notable changes to GrandPA2-Buddy, organized by version
version: 2.0.0
created: 2026-04-06T15:55:55Z
last_updated: 2026-04-06T16:10:00Z
---

# Changelog

All notable changes to this project are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Fork origin:** This project is forked from [`chienchuanw/ma2-controller`](https://github.com/chienchuanw/ma2-controller).
> The first commit in this repository (`87ee57d`) begins at tool 78 — the original 77 tools were inherited from the upstream.

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
- **Phase 4 — DAG Checkpoint Persistence**
  - `step_checkpoints` table in `WorkflowMemory` for crash recovery
  - `checkpoint_fn` callback in `StepExecutor` persists after every step
  - `resume_run()` in `AgentRuntime` reconstructs and resumes interrupted runs
- **Phase 5 — Bridge Activation**
  - Fixed dependency name↔UUID conversion in bulk converters
  - `execute_subtasks_via_agent()` bridges System A plans to System B executor
  - `_run_via_agent_bridge()` optional backend in Orchestrator
- **Phase 6 — Tool Routing Improvements**
  - Hybrid retrieval via Reciprocal Rank Fusion (RRF) in `suggest_tool_for_task`
  - `filter_risk_tier` and `filter_license_tier` metadata filter parameters
  - `rerank_tools()` second-stage body scorer
  - Enriched taxonomy descriptors (risk_tier, param_names, action_verbs, command_modules)
  - Skills `applicable_context` connected to tool routing (returns `related_skills`)
- **Audit Response**
  - 6 new task decomposition rules: effect, chaser, macro, timecode, import, view/layout (8→14)
  - `_validate_license_tiers()` startup warning for unmapped destructive tools
  - Skill deprecation mechanism (`deprecated` field + `deprecate()`)
  - Pre-filter vector search by `repo_ref` / `kind`
  - Chunk deduplication across `repo_ref`s in query results
  - robots.txt support in web crawler
  - FTS5 rebuild after bulk delete
  - Ruff lint check added to `.githooks/pre-commit`

### Changed
- `instructions=` block updated: 173→197 tools, 9→18 resources, 6→13 prompts
- `suggest_tool_for_task` returns `risk_tier` per suggestion
- `search()` and `list_all()` exclude deprecated skills
- README: Advanced Features table, linked badges, corrected counts

### Fixed
- 10 phantom `TOOL_LICENSE_TIERS` entries removed
- All ruff lint errors resolved
- Version drift: pyproject.toml synced to 3.34.2

### Tests
- 108 new test cases (2885 → 2993 passing, 142 skipped)

---

## [3.33.0] — 2026-04-06

### Added
- IP protection hooks: copyright header check, trade secret language guard, attribution enforcement
- FORKS.md fork documentation

---

## [3.32.0] — 2026-04-04

### Added
- `_check_network_security()` startup guard warns on non-loopback host, bypass vars, factory credentials
- `scripts/lockdown_firewall.sh` restricts TCP 30000 to loopback
- `doc/network-topology.md` deployment diagram

---

## [3.28.0] — 2026-04-04

### Added
- 3-layer MA2 rights enforcement wired into `_handle_errors`
- SECURITY.md, VS Code BSL 1.1 LICENSE settings

### Changed
- Safety System refactored as cohesive 3-layer reference in README

---

## [3.26.0] — 2026-04-04

### Added
- BSL 1.1 license and 3-tier feature gating system (COMMUNITY / PROFESSIONAL / ENTERPRISE)
- `TOOL_LICENSE_TIERS` dict mapping 187 tool function names to license tiers
- `require_tier()`, `get_license_tier()`, `has_tier()` in `src/license.py`
- MD count audit script (`scripts/audit_md_counts.py`) wired into pre-push hook
- Pre-push test hook, pre-commit IP protection hook, stop hook
- TERMS.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md
- Version discipline rules in CLAUDE.md

### Changed
- Project renamed to GrandPA2-Buddy
- `_handle_errors` enforces scope ∩ rights ∩ license tier

---

## [3.25.1] — 2026-04-02

### Added
- Gap-audit sprints 1–7 complete (closing all 19 show-memory gaps)
- BSL 1.1 license file and feature gating system (initial)

---

## [3.25.0] — 2026-04-01

### Added
- Cherry-picked 26 command builders + 5 MCP tools from refactor branch
- Merged `src/agent/` harness + bridge adapter + hardened tool registry
- MCP completions, elicitation, sampling, subscriptions modules
- Configurable MCP transport (stdio/SSE/streamable HTTP)

### Fixed
- K-Means multi-restart + L2-norm normalization
- FTS5 RAG index sync triggers
- Keyword reranker scoring

---

## [3.23.0] — 2026-03-30

### Added
- OpenSpace layer: `SkillImprover`, `DecisionCheckpoint`, `WorkingMemory` v2 compression
- Busking tools: 6 performance builders
- Executor assignment wrappers for priority, MIB, autostart
- `showfile_changed()` detection in agent memory
- Filesystem skills wired into `SkillRegistry` (`.claude/skills/`)
- 11 new `.claude/skills/` instruction modules
- 7 new MCP tools, 4 resources, 4 prompts
- MCP time server integration (`.mcp.json`)
- Dynamic showfile awareness in agent memory

---

## [3.22.0] — 2026-03-29

### Added
- 21 MCP tools (Waves 1–5) closing RAG audit gaps
- `list_agenda_events` tool
- 3 task decomposer rules, 2 WORKER_CATALOG entries
- 8 new skill instruction modules
- Timecode skill

---

## [3.21.0] — 2026-03-28

### Added
- Executor tools, parser improvements
- Demo skill scripts (`scripts/demo_skills.py`, `scripts/demo_skills_live.py`)

### Changed
- Dead code removal across codebase

---

## [3.20.0] — 2026-03-26

### Added
- 3-layer safety model: scope corrections, `check_permission` gate

### Changed
- README architecture diagram audit — 6 fixes

---

## [3.14.0] — 2026-03-25

### Added
- OpenSpace layer: busking tools, executor assignment wrappers
- Full audit pass

---

## [3.13.0] — 2026-03-24

### Added
- Tools 131–137: wildcard resolution, fixture validation
- Full doc audit

---

## [3.10.0] — 2026-03-23

### Added
- Tools 119–130: snapshot write-trackers, 90 new tests
- README refactor

---

## [3.8.0] — 2026-03-22

### Added
- Agentic orchestration layer: tools 110–118
- MA2 native rights enforcement
- Console state hydrator (19 show-memory gaps)
- Agent harness: `AgentRuntime`, `DomainPlanner`, `StepExecutor`, `PolicyEngine`, `Verifier`
- `WorkflowMemory` (SQLite-backed recipes + run history)
- `ExecutionTrace` JSON audit artifacts

---

## [3.1.0] — 2026-03-20

### Added
- MAtricks/filter command builders, vocab keywords
- Scanner efficiency improvements + `discover_filter_attributes` tool

### Changed
- Audit: 90 tools, 1365 tests, 157 builders

---

## [3.0.0] — 2026-03-19

### Added
- RAG pipeline: crawl → chunk → embed → store → retrieve → rerank
- Web crawler for grandMA2 help docs (~1,043 pages)
- MCP SDK source indexing

### Changed
- README refactored with GitHub markdown features

---

## [2.3.0] — 2026-03-18

### Added
- `create_matricks_library` MCP tool and script (tool 87)
- 25-color appearance embedding in MAtricks XML

### Fixed
- RGB 0-100 scale bug

---

## [2.2.0] — 2026-03-17

### Added
- Safety gates and race condition fixes
- ML-based tool categorization: K-Means clustering + auto-labeling (tools 83–86)

---

## [2.1.0] — 2026-03-16

### Added
- `select_feature`, `select_preset_type`, `browse_preset_type` tools (tools 79–82)
- PresetType / Feature / CD-Tree correlation (live-verified)

### Changed
- Full audit: reconcile all docs with 82-tool codebase

---

## [2.0.0] — 2026-03-15

### Added
- `list_system_variables` tool (tool 78)
- Echo action for `get_variable`
- `create_if_missing` option for `navigate_page`
- `manage_variable` list mode + `command_options` vocab
- System variable documentation ($VERSION, $SHOWFILE, $USER, etc.)

> **Note:** This is the first commit in this repository. Tools 1–77 were inherited from the upstream fork [`chienchuanw/ma2-controller`](https://github.com/chienchuanw/ma2-controller).

### Fixed
- ListVar parser and get_variable echo action

---

[3.34.2]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.33.0...v3.34.2
[3.33.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.32.0...v3.33.0
[3.32.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.28.0...v3.32.0
[3.28.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.26.0...v3.28.0
[3.26.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.25.1...v3.26.0
[3.25.1]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.25.0...v3.25.1
[3.25.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.23.0...v3.25.0
[3.23.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.22.0...v3.23.0
[3.22.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.21.0...v3.22.0
[3.21.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.20.0...v3.21.0
[3.20.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.14.0...v3.20.0
[3.14.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.13.0...v3.14.0
[3.13.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.10.0...v3.13.0
[3.10.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.8.0...v3.10.0
[3.8.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.1.0...v3.8.0
[3.1.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.0.0...v3.1.0
[3.0.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v2.3.0...v3.0.0
[2.3.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/thisis-romar/ma2-onPC-MCP/commits/v2.0.0
