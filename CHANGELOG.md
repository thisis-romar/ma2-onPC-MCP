---
title: Changelog
description: All notable changes to GrandPA2-Buddy, organized by version
version: 3.0.0
created: 2026-04-06T15:55:55Z
last_updated: 2026-04-06T22:09:43Z
---

# Changelog

All notable changes to this project are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Fork origin:** Forked from [`chienchuanw/ma2-controller`](https://github.com/chienchuanw/ma2-controller).
> First commit (`39c6303`) begins at tool 78 — tools 1-77 inherited from upstream.

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
- Skill deprecation mechanism (`deprecated` field)
- Pre-filter vector search by repo_ref/kind
- Chunk deduplication across repo_refs
- robots.txt support in web crawler
- FTS5 rebuild after bulk delete
- Ruff lint check in pre-commit hook
- 10 phantom TOOL_LICENSE_TIERS entries removed

### Fixed
- `instructions=` block: 173→198 tools, 9→18 resources, 6→13 prompts
- Version drift: pyproject.toml synced to 3.34.2

### Tests
- 114 new test cases (2885 → 2999)

---

## [3.34.0] — 2026-04-06

### Changed
- README: Advanced Features (Phases 1-6) table added
- All badges linked to canonical proof surfaces
- Version badge synced 3.26.0 → 3.34.0
- pyproject.toml and src/__init__.py synced to 3.34.0

---

## [3.33.0] — 2026-04-06

### Added
- IP protection pre-commit hooks (7 checks: copyright, trade secrets, attribution)
- FORKS.md fork documentation
- Phase 1 safety hardening (initial commit)

### Fixed
- License tier bypass in test conftest
- 6 failing test mocks

---

## [3.32.0] — 2026-04-04

### Added
- `_check_network_security()` startup guard
- `scripts/lockdown_firewall.sh` (restricts port 30000 to loopback)
- `doc/network-topology.md` deployment diagram

---

## [3.31.1] — 2026-04-04

### Added
- `scripts/audit_md_counts.py` wired into pre-push hook

---

## [3.31.0] — 2026-04-04

### Changed
- Test count 2876 → 3027 in CLAUDE.md and README.md

---

## [3.30.0] — 2026-04-04

### Added
- Version discipline rules from full audit of CLAUDE.md + README.md
- System clock fallback for MCP time server unavailability
- Pre-push test hook, project-level Claude settings, stop hook

### Fixed
- YAML front matter versions and timestamps corrected

---

## [3.29.0] — 2026-04-04

### Changed
- README Safety System refactored as cohesive 3-layer reference

---

## [3.28.0] — 2026-04-04

### Added
- 3-layer MA2 rights enforcement wired into `_handle_errors`
- Hardening rules for new tools in CLAUDE.md

### Fixed
- Ruff I001 import sorting and F401 unused imports

---

## [3.27.0] — 2026-04-04

### Changed
- Safety System section corrected: 2-layer active model documented

---

## [3.26.0] — 2026-04-04

### Added
- BSL 1.1 license and 3-tier feature gating (COMMUNITY/PROFESSIONAL/ENTERPRISE)
- `TOOL_LICENSE_TIERS` mapping 187 tool names to tiers
- `require_tier()`, `get_license_tier()`, `has_tier()` in `src/license.py`
- SECURITY.md, TERMS.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md
- Ruff, MCP SDK, Stars badges

### Changed
- `_handle_errors` enforces scope ∩ rights ∩ license tier
- All source file references in README are clickable links

---

## [3.25.1] — 2026-04-02

### Added
- Gap-audit sprints 1-7 complete (closing all 19 show-memory gaps)
- BSL 1.1 license file (initial)

---

## [3.25.0] — 2026-04-01

### Added
- Cherry-picked 26 command builders + 5 MCP tools from refactor branch
- `src/agent/` harness + bridge adapter + hardened tool registry
- MCP completions, elicitation, sampling, subscriptions modules
- Configurable MCP transport (stdio/SSE/streamable HTTP)

### Fixed
- K-Means multi-restart + L2-norm normalization
- FTS5 RAG index sync triggers
- Keyword reranker scoring
- Orchestrator null-guard, BaseException broadening

---

## [3.23.0] — 2026-03-30

### Added
- OpenSpace layer: SkillImprover, DecisionCheckpoint, WorkingMemory v2 compression
- Filesystem skills wired into SkillRegistry (`.claude/skills/`)
- Dynamic showfile awareness in agent memory
- 11 new skill instruction modules, 7 tools, 4 resources, 4 prompts
- MCP time server integration (`.mcp.json`)
- TERMS, NOTICE, CONTRIBUTING, CODE_OF_CONDUCT

### Fixed
- OpenSpace feedback loop: session_id linkage, singleton isolation

---

## [3.22.0] — 2026-03-29

### Added
- 21 MCP tools (Waves 1-5) closing RAG audit gaps
- `list_agenda_events` tool, 3 new tools, 8 skills
- 3 task decomposer rules, 2 WORKER_CATALOG entries, timecode skill

---

## [3.21.0] — 2026-03-28

### Added
- Executor tools, parser improvements
- Demo skill scripts

### Changed
- Dead code removal across codebase

---

## [3.20.0] — 2026-03-26

### Changed
- README architecture diagram audit — 6 fixes

---

## [3.19.0] — 2026-03-25

### Added
- 3-layer safety model: scope corrections, `check_permission` gate

---

## [3.18.0] — 2026-03-24

### Changed
- Project renamed to GrandPA2-Buddy with retro banner
- DEDICATION.md created (tribute moved from README)

---

## [3.17.0] — 2026-03-24

### Fixed
- All 121 pre-existing Ruff lint violations resolved (unblocked CI)

---

## [3.16.1] — 2026-03-24

### Changed
- uv.lock regenerated for package rename

---

## [3.14.0] — 2026-03-24

### Added
- OpenSpace layer: busking tools, executor assignment wrappers
- DecisionCheckpoint, workflow field, WORKER_CATALOG
- Busking layer: command builders, tools, resources, skill files

### Fixed
- Infinite loop in chunk.py on long-line files
- Kill registered as FUNCTION/SAFE_WRITE in VocabSpec

---

## [3.13.0] — 2026-03-23

### Added
- Tools 131-137: wildcard resolution, fixture validation
- OpenSpace framework comparison audit with gap analysis
- Architecture refactor: responsibility map, tool tiers, skills, resources, prompts

---

## [3.10.0] — 2026-03-23

### Added
- Tools 119-130: snapshot write-trackers, 90 new tests

---

## [3.8.0] — 2026-03-22

### Added
- Agent harness: AgentRuntime, DomainPlanner, StepExecutor, PolicyEngine, Verifier
- Agentic orchestration layer: tools 110-118
- MA2 native rights: MA2Right enum, rights-native auth
- Console state hydrator (19 show-memory gaps)
- 8 new MCP tools (102-109), 14 command builders
- Per-operator Telnet session pool — dual-enforcement
- OAuth 2.1 scope enforcement on all 101 tools
- User management command builders and tools

---

## [3.1.0] — 2026-03-20

### Added
- MAtricks/filter command builders, vocab keywords
- Scanner efficiency improvements + discover_filter_attributes tool
- Agent harness: runtime, planner, executor, policy, verification, memory, traces

### Fixed
- 53 ruff lint errors, CI badge URL

---

## [3.0.0] — 2026-03-19

### Added
- RAG pipeline: crawl → chunk → embed → store → retrieve → rerank
- Web crawler for grandMA2 help docs (~1,043 pages)
- MCP SDK source indexing

### Changed
- README refactored with GitHub markdown features

### Fixed
- RAG: search ranking, dimension validation, schema versioning
- RGB 0-100 scale bug

---

## [2.3.0] — 2026-03-18

### Added
- `create_matricks_library` MCP tool (tool 87)
- 25-color appearance embedding in MAtricks XML

---

## [2.2.0] — 2026-03-17

### Added
- Safety gates and race condition fixes
- ML-based tool categorization: K-Means clustering (tools 83-86)

---

## [2.1.0] — 2026-03-16

### Added
- `select_feature`, `select_preset_type`, `browse_preset_type` tools (79-82)
- PresetType / Feature / CD-Tree correlation (live-verified)

---

## [2.0.0] — 2026-03-15

### Added
- `list_system_variables` tool (tool 78) — first commit in this repository
- Echo action for `get_variable`
- `create_if_missing` for `navigate_page`
- `manage_variable` list mode + `command_options` vocab

### Fixed
- ListVar parser, `new_show` /noconfirm

> **Note:** Tools 1-77 inherited from upstream [`chienchuanw/ma2-controller`](https://github.com/chienchuanw/ma2-controller).

---

[3.35.2]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.35.1...v3.35.2
[3.35.1]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.35.0...v3.35.1
[3.35.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.34.2...v3.35.0
[3.34.2]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.34.0...v3.34.2
[3.34.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.33.0...v3.34.0
[3.33.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.32.0...v3.33.0
[3.32.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.31.1...v3.32.0
[3.31.1]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.31.0...v3.31.1
[3.31.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.30.0...v3.31.0
[3.30.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.29.0...v3.30.0
[3.29.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.28.0...v3.29.0
[3.28.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.27.0...v3.28.0
[3.27.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.26.0...v3.27.0
[3.26.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.25.1...v3.26.0
[3.25.1]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.25.0...v3.25.1
[3.25.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.23.0...v3.25.0
[3.23.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.22.0...v3.23.0
[3.22.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.21.0...v3.22.0
[3.21.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.20.0...v3.21.0
[3.20.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.19.0...v3.20.0
[3.19.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.18.0...v3.19.0
[3.18.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.17.0...v3.18.0
[3.17.0]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.16.1...v3.17.0
[3.16.1]: https://github.com/thisis-romar/ma2-onPC-MCP/compare/v3.14.0...v3.16.1
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
