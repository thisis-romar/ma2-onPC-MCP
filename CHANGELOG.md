---
title: Changelog
description: All notable changes to GrandPA2-Buddy, organized by version
version: 5.0.0
created: 2026-04-06T15:55:55Z
last_updated: 2026-04-07T01:34:22Z
---

# Changelog

All notable changes to this project are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Fork origin:** Forked from [`chienchuanw/ma2-controller`](https://github.com/chienchuanw/ma2-controller).
> First commit (`39c6303`) begins at tool 78 — tools 1-77 inherited from upstream.

---

## Table of Contents

- [3.35.3](#3353--2026-04-07) — CLA file, version sync, CHANGELOG commit-SHA links, stale count fixes
- [3.35.2](#3352--2026-04-06) — resume_agent_run tool, DomainPlanner 13 intents
- [3.35.1](#3351--2026-04-06) — README gap fixes (env var table, agent docs, module table)
- [3.35.0](#3350--2026-04-06) — P0-P1 security hardening (history purge, LICENSE sync)
- [3.34.2](#3342--2026-04-06) — Phases 1-6 orchestration enhancements + audit response
- [3.34.0](#3340--2026-04-06) — README audit (badges, Advanced Features table)
- [3.33.0](#3330--2026-04-06) — IP protection hooks, Phase 1 safety hardening
- [3.32.0](#3320--2026-04-04) — Network hardening layer
- [3.31.1](#3311--2026-04-04) — MD count audit script
- [3.31.0](#3310--2026-04-04) — Test count sync
- [3.30.0](#3300--2026-04-04) — Version discipline, hooks, MCP time fallback
- [3.29.0](#3290--2026-04-04) — Safety System refactor
- [3.28.0](#3280--2026-04-04) — MA2 rights enforcement in _handle_errors
- [3.27.0](#3270--2026-04-04) — Safety System correction
- [3.26.0](#3260--2026-04-04) — BSL 1.1 license, feature gating
- [3.25.1](#3251--2026-04-02) — Gap-audit sprints 1-7
- [3.25.0](#3250--2026-04-01) — Agent harness merge, MCP transport
- [3.23.0](#3230--2026-03-30) — OpenSpace layer, 11 skills, 7 tools
- [3.22.0](#3220--2026-03-29) — 21 tools (Waves 1-5), skills
- [3.21.0](#3210--2026-03-28) — Executor tools, demo scripts
- [3.20.0](#3200--2026-03-26) — Architecture diagram audit
- [3.19.0](#3190--2026-03-25) — 3-layer safety model
- [3.18.0](#3180--2026-03-24) — Project rename to GrandPA2-Buddy
- [3.17.0](#3170--2026-03-24) — Ruff lint cleanup (121 violations)
- [3.14.0](#3140--2026-03-24) — OpenSpace layer, busking tools
- [3.13.0](#3130--2026-03-23) — Tools 131-137, OpenSpace audit
- [3.10.0](#3100--2026-03-23) — Tools 119-130
- [3.8.0](#380--2026-03-22) — Agent harness, tools 102-118, OAuth
- [3.1.0](#310--2026-03-20) — MAtricks/filter builders, agent harness
- [3.0.0](#300--2026-03-19) — RAG pipeline, web crawler
- [2.3.0](#230--2026-03-18) — MAtricks library tool
- [2.2.0](#220--2026-03-17) — ML categorization, safety gates
- [2.1.0](#210--2026-03-16) — PresetType/Feature tools
- [2.0.0](#200--2026-03-15) — First commit (tool 78)

---

## [3.35.3] — 2026-04-07

### Added
- CLA.md (Contributor License Agreement) — required before accepting external contributions
- CHANGELOG Table of Contents with one-line descriptions per version
- CHANGELOG compare links using commit SHAs (replaces broken tag-based URLs)

### Fixed
- Version sync: pyproject.toml, src/__init__.py, LICENSE, README badge all at 3.35.3
- README: 197→198 tools in 2 prose locations, 163→164 in 4 locations
- pyproject.toml description: 197→198 MCP tools
- test_rights.py: rename `test_all_197_tools_mapped` → `test_all_198_tools_mapped`

---

## [3.35.2] — 2026-04-06

### Added
- `resume_agent_run` MCP tool (198th tool) — resume interrupted agent runs from DAG checkpoints
- DomainPlanner: 6 new GoalIntent values (EFFECT, CHASER, MACRO, TIMECODE, IMPORT, VIEW_LAYOUT)
- Generic 3-step workflow builder (discover → execute → verify) for new intents
- RAG golden-set quality tests (5 queries with expected top-1 results)
- `doc/server-split-plan.md` — modularization roadmap for server.py
- `test_no_unmapped_destructive_tools` architecture hygiene test

### Changed
- Tool count 197 → 198 across all docs, tests, instructions block
- DomainPlanner intents 7 → 13

---

## [3.35.1] — 2026-04-06

### Added
- Environment Variables table (15 vars) in README
- Agent entry points documented (run_agent_goal, plan_agent_goal, resume_run)
- 6 missing modules added to Module Overview table
- Documentation section with CHANGELOG, CONTRIBUTING, SECURITY links
- Transport explanation (stdio/sse/streamable-http)

---

## [3.35.0] — 2026-04-06

### Fixed
- P0: Sensitive internal docs purged from all git history (filter-branch)
- P0: Commit messages scrubbed of sensitive terms
- P0: LICENSE version synced v3.26.0 → v3.35.2
- P1: All version locations reconciled to 3.35.2
- P1: Pre-commit hook upgraded with LICENSE + README badge version checks

---

## [3.34.2] — 2026-04-06

### Added
- **Phase 1 — Safety Hardening**: CircuitBreaker, PolicyStrictness (WARN/BLOCK), RollbackExecutor
- **Phase 2 — Performance**: Incremental hydration, risk-weighted scoring, ProgressMonitor
- **Phase 3 — Semantic Skill Search**: `search_semantic()` with embedding cosine similarity
- **Phase 4 — DAG Checkpoints**: `step_checkpoints` table, `checkpoint_fn`, `resume_run()`
- **Phase 5 — Bridge Activation**: dependency name↔UUID fix, `execute_subtasks_via_agent()`
- **Phase 6 — Tool Routing**: Hybrid RRF, metadata filters, `rerank_tools()`, enriched taxonomy

### Audit Response
- 6 new task decomposition rules (8→14): effect, chaser, macro, timecode, import, view/layout
- `_validate_license_tiers()` startup warning
- Skill deprecation mechanism, pre-filter vector search, chunk dedup
- robots.txt support, FTS5 rebuild, ruff in pre-commit hook
- 10 phantom TOOL_LICENSE_TIERS entries removed

### Tests
- 114 new test cases (2885 → 2999)

---

## [3.34.0] — 2026-04-06

### Changed
- README: Advanced Features (Phases 1-6) table added
- All badges linked to canonical proof surfaces
- Version badge synced 3.26.0 → 3.34.0

---

## [3.33.0] — 2026-04-06

### Added
- IP protection pre-commit hooks (7 checks)
- FORKS.md fork documentation

### Fixed
- License tier bypass in test conftest
- 6 failing test mocks

---

## [3.32.0] — 2026-04-04

### Added
- `_check_network_security()` startup guard
- `scripts/lockdown_firewall.sh`
- `doc/network-topology.md`

---

## [3.31.1] — 2026-04-04

### Added
- `scripts/audit_md_counts.py` wired into pre-push hook

---

## [3.31.0] — 2026-04-04

### Changed
- Test count 2876 → 3027

---

## [3.30.0] — 2026-04-04

### Added
- Version discipline rules, system clock fallback
- Pre-push test hook, project-level Claude settings, stop hook

---

## [3.29.0] — 2026-04-04

### Changed
- README Safety System refactored as 3-layer reference

---

## [3.28.0] — 2026-04-04

### Added
- 3-layer MA2 rights enforcement wired into `_handle_errors`
- Tool hardening rules in CLAUDE.md

---

## [3.27.0] — 2026-04-04

### Changed
- Safety System section corrected: 2-layer active model

---

## [3.26.0] — 2026-04-04

### Added
- BSL 1.1 license and 3-tier feature gating
- `TOOL_LICENSE_TIERS` (187 entries)
- SECURITY.md, TERMS.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md

---

## [3.25.1] — 2026-04-02

### Added
- Gap-audit sprints 1-7 (all 19 show-memory gaps closed)
- BSL 1.1 license file (initial)

---

## [3.25.0] — 2026-04-01

### Added
- 26 command builders + 5 MCP tools from refactor branch
- `src/agent/` harness + bridge adapter
- MCP completions, elicitation, sampling, subscriptions
- Configurable MCP transport (stdio/SSE/streamable HTTP)

### Fixed
- K-Means, FTS5, keyword reranker, orchestrator null-guard

---

## [3.23.0] — 2026-03-30

### Added
- OpenSpace layer: SkillImprover, DecisionCheckpoint, WorkingMemory v2
- Filesystem skills in SkillRegistry, dynamic showfile awareness
- 11 skills, 7 tools, 4 resources, 4 prompts, MCP time server
- TERMS, NOTICE, CONTRIBUTING, CODE_OF_CONDUCT

---

## [3.22.0] — 2026-03-29

### Added
- 21 MCP tools (Waves 1-5), 3 decomposer rules, 8 skills

---

## [3.21.0] — 2026-03-28

### Added
- Executor tools, parser improvements, demo scripts

---

## [3.20.0] — 2026-03-26

### Changed
- README architecture diagram audit — 6 fixes

---

## [3.19.0] — 2026-03-25

### Added
- 3-layer safety model: scope corrections, check_permission gate

---

## [3.18.0] — 2026-03-24

### Changed
- Project renamed to GrandPA2-Buddy, DEDICATION.md created

---

## [3.17.0] — 2026-03-24

### Fixed
- 121 pre-existing Ruff lint violations resolved

---

## [3.14.0] — 2026-03-24

### Added
- OpenSpace layer: busking tools, executor assignment wrappers
- DecisionCheckpoint, workflow field, WORKER_CATALOG, busking layer

### Fixed
- chunk.py infinite loop on long-line files

---

## [3.13.0] — 2026-03-23

### Added
- Tools 131-137: wildcard resolution, fixture validation
- OpenSpace comparison audit, architecture refactor

---

## [3.10.0] — 2026-03-23

### Added
- Tools 119-130: snapshot write-trackers, 90 new tests

---

## [3.8.0] — 2026-03-22

### Added
- Agent harness: AgentRuntime, DomainPlanner, StepExecutor, PolicyEngine, Verifier
- Orchestration layer: tools 110-118, console state hydrator
- 8 MCP tools (102-109), 14 command builders
- Per-operator Telnet session pool, OAuth 2.1 on all tools

---

## [3.1.0] — 2026-03-20

### Added
- MAtricks/filter command builders, vocab keywords
- Agent harness traces, discover_filter_attributes tool

### Fixed
- 53 ruff lint errors, CI badge URL

---

## [3.0.0] — 2026-03-19

### Added
- RAG pipeline: crawl → chunk → embed → store → retrieve → rerank
- Web crawler for ~1,043 grandMA2 help pages

### Fixed
- RAG search ranking, dimension validation, RGB 0-100 bug

---

## [2.3.0] — 2026-03-18

### Added
- `create_matricks_library` MCP tool (tool 87)
- 25-color appearance embedding in MAtricks XML

---

## [2.2.0] — 2026-03-17

### Added
- ML-based tool categorization: K-Means (tools 83-86)
- Safety gates and race condition fixes

---

## [2.1.0] — 2026-03-16

### Added
- `select_feature`, `select_preset_type`, `browse_preset_type` (79-82)

---

## [2.0.0] — 2026-03-15

### Added
- `list_system_variables` tool (tool 78) — first commit in this repository
- Echo action, `create_if_missing` for navigate_page, manage_variable

> Tools 1-77 inherited from upstream [`chienchuanw/ma2-controller`](https://github.com/chienchuanw/ma2-controller).

---

[3.35.2]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/c725369...ae5bfc4
[3.35.1]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/206a37d...c725369
[3.35.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/c98f7c1...206a37d
[3.34.2]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/f1be496...c98f7c1
[3.34.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/00434a1...f1be496
[3.33.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/42a0d46...00434a1
[3.32.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/824801c...42a0d46
[3.31.1]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/46a8db4...824801c
[3.31.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/60788c6...46a8db4
[3.30.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/01d6032...60788c6
[3.29.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/8709f3f...01d6032
[3.28.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/12c9687...8709f3f
[3.27.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/9012835...12c9687
[3.26.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/516e8fd...9012835
[3.25.1]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/d42e35a...516e8fd
[3.25.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/0789091...d42e35a
[3.23.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/e962595...0789091
[3.22.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/bfa53af...e962595
[3.21.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/97ba5cf...bfa53af
[3.20.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/4739786...97ba5cf
[3.19.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/ab2ca94...4739786
[3.18.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/c291b55...ab2ca94
[3.17.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/21e6dbc...c291b55
[3.14.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/2e9fe20...169a16d
[3.13.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/94174d9...2e9fe20
[3.10.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/bd364f1...94174d9
[3.8.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/2efbf27...bd364f1
[3.1.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/c1db50a...2efbf27
[3.0.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/6650b63...c1db50a
[2.3.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/11a6169...6650b63
[2.2.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/04abbe5...11a6169
[2.1.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/39c6303...04abbe5
[2.0.0]: https://github.com/thisis-romar/ma2-onPC-MCP/commit/39c6303
