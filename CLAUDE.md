---
title: Project Rules
description: Thin root conventions for ma2-onPC-MCP — architectural invariants, safety rules, and build commands
version: 4.21.0
created: 2026-03-01T23:37:51Z
last_updated: 2026-06-11T14:00:55Z
---

# Project Rules

## Project Identity

MCP server exposing **207 tools**, **22 resources**, **16 prompts**, and **34 skills** so AI assistants can control a grandMA2 lighting console via Telnet. Includes an **agent harness** (`src/agent/`) for autonomous multi-step execution with planning, policy enforcement, verification, and audit traces.

Central rule: **planner decides → skills carry instructions → subagents execute in isolation → tools take narrow actions → memory stores distilled checkpoints**.

All network I/O is isolated in `src/telnet_client.py`. Command builders in `src/commands/` are pure functions returning strings — no side effects.

---

## Architecture Quick Reference

| Module | Role |
|--------|------|
| `src/server.py` | FastMCP server startup — 22 MCP resources + 16 MCP prompts, orchestrator wiring, re-exports |
| `src/server_core.py` | Shared infrastructure — `mcp` instance, `get_client()`, `_handle_errors`, pool helpers |
| `src/tools_community.py` | 20 COMMUNITY tools (free tier, public repo) |
| `src/tools_graph.py` | 9 ENTERPRISE graph-intelligence tools (SAFE_READ, public repo) — registered in `server.py` |
| `src/private/tools_professional.py` | 124 PROFESSIONAL tools (paid tier, private submodule) |
| `src/private/tools_enterprise.py` | 20 ENTERPRISE tools (premium tier, private submodule) |
| `src/private/server_orchestration_tools.py` | 34 ENTERPRISE agentic tools (private submodule) |
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
| `src/knowledge_graph/` | SQLite-backed knowledge graph: 18 node types (10 console + 4 code + 4 MCP), 20 edge types (11 console + 4 code + 5 MCP), BFS/DFS traversal, GraphRAG, planning integration, freshness tracking |
| `src/knowledge_graph/skill_sync.py` | Sync SkillRegistry → KG SKILL nodes + IMPROVES_UPON lineage + IMPLEMENTS (skill→tool) edges |
| `src/knowledge_graph/mcp_metadata.py` | AST-extract `@mcp.tool/resource/prompt` decorators → `MCPMetadata` dataclass |
| `src/knowledge_graph/resource_sync.py` | Sync MCP tools/resources/prompts → KG nodes + DOCUMENTS/ORCHESTRATES/CATEGORIZED_AS edges |
| `src/knowledge_graph/parsers/` | Python AST symbol extraction (`extractor.py`), graph normalization (`normalizer.py`), repo scanning (`repo_scanner.py`), multi-repo tracking (`repo_registry.py`) |
| `rag/ingest/ingest_skills.py` | Crawl `.claude/skills/` → RAG store (`repo_ref="skills"`) |
| `rag/ingest/ingest_resources.py` | Index MCP resource/prompt docstrings → RAG store (`repo_ref="mcp-resources"`) |
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
| `src/agent/` | Agent harness — see Skill `agent-harness-operations` for details |

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

## Repository Setup (first clone)

`src/private/` is a **git submodule** ([`ma2-onPC-MCP-private.git`](https://github.com/thisis-romar/ma2-onPC-MCP-private)) holding 178 of the 207 tools (PROFESSIONAL + ENTERPRISE + orchestration). A fresh clone has it **empty**. Until you initialize it:

- `scripts/audit_md_counts.py` crashes with `FileNotFoundError: src/private/tools_professional.py` (so the **pre-push hook fails too**).
- Only the 20 COMMUNITY + 9 graph tools load; the documented 207 count does not match disk.

```bash
git submodule update --init src/private   # REQUIRED before running tests / audit / full server
```

Working in the **public/COMMUNITY tree only**? That's a valid mode — but skip the audit script and expect the reduced tool count.

---

## Development Commands

```bash
uv run python -m pytest -v                                    # all tests
uv run python -m pytest tests/test_vocab.py                   # subset
uv run ruff check src/ tests/ rag/                            # lint (enforced by pre-commit hook)
uv run python -m src.server                                   # start MCP server
uv run python scripts/rag_ingest.py --root . --provider zero  # RAG ingest (zero-vector)
make install-hooks                                             # git hooks (pre-commit/pre-push/stop)
uv run python scripts/audit_md_counts.py                      # audit MD counts (runs in pre-push)
uv run python scripts/audit_md_counts.py --fix                # auto-fix stale counts
```

---

## Code Conventions

See Skill **`mcp-development-guidelines`** for contributor workflows (adding tools, resources, prompts, command builders, tests).

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

Three tiers: **COMMUNITY** (free, ~30 tools), **PROFESSIONAL** (paid, ~120), **ENTERPRISE** (premium, ~50). Set `GMA_LICENSE_TIER` env var. See Skill **`license-tier-management`** for implementation details and env vars.

---

## Agent Harness (`src/agent/`)

Autonomous multi-step execution: `AgentRuntime` -> `DomainPlanner` -> `PolicyEngine` -> `StepExecutor` -> `Verifier`. MCP tools: `run_agent_goal()`, `plan_agent_goal()`. See Skill **`agent-harness-operations`** for architecture details.

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
| `.claude/rules/knowledge-graph-operations.md` | KG freshness rules, staleness mapping, lifecycle, safety |

---

## What NOT To Do

- Do not add network I/O to command builders in `src/commands/` — they must stay pure.
- Do not import from `src.server` or `src.navigation` inside `src/commands/`.
- Do not hardcode `GMA_HOST`, `GMA_PORT`, or credentials — always read from env vars.
- Do not set `confirm_destructive=True` inside server tool implementations.
- Do not commit `rag/store/rag.db` or `rag/store/web_crawl_cache.json` — local artifacts.
- Do not commit client/engagement-specific scripts to the tree — keep them in the gitignored `_local/` directory, kept separate from this BSL-licensed product.
- Do not edit `src/grandMA2_v3_9_telnet_keyword_vocabulary.json` manually.
- Do not call `new_show` with `preserve_connectivity=False` unless the user explicitly accepts Telnet will be disabled.
- Do not pass pre-quoted strings to `quote_name()` — pass raw names only.
- Do not call `ToolTelemetry.record_sync()` manually — `@_handle_errors` records automatically.
- Do not call `SkillRegistry.approve()` from tool implementations — only Tool 143 may.
- Do not auto-promote Skills from `SkillImprover` output — promotion is operator-initiated via Tool 141.
- Do not make MCP resources perform console side-effects — resources are read-only context.
- Do not put MA2 operating knowledge into tool docstrings — put it in `.claude/skills/` instead.
- Do not add a new `@mcp.tool()` without adding its entry to `_OPERATION_MIN_RIGHT` in `src/rights.py` — `test_all_207_tools_mapped` will fail.
- Do not set `GMA_AUTH_BYPASS=1`, `GMA_RIGHTS_BYPASS=1`, or `GMA_LICENSE_BYPASS=1` in production — dev/test only.
- Do not use graph query results for DESTRUCTIVE operations without verifying freshness — stale graph data may reference deleted console objects.
- Do not mix embedding dimensions in the same RAG store — GitHub Models (1536-dim), OpenRouter (2048-dim), and Gemini (768-dim) are incompatible; use `rag_upgrade_embeddings.py --re-embed-all` to switch.

