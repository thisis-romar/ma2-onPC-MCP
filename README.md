---
title: GrandPA2-Buddy
description: AI agent for grandMA2 lighting consoles — 198 MCP tools via Telnet
version: 3.37.0
created: 2025-11-04T17:05:43Z
last_updated: 2026-04-08T16:37:27Z
---

<p align="center">
  <img src="assets/header.jpeg" alt="GrandPA2-Buddy — grandMA2 Console Agent" width="100%">
</p>

# GrandPA2-Buddy 👨‍🎨

<p align="center">
  <a href="https://github.com/thisis-romar/ma2-onPC-MCP/actions/workflows/test.yml"><img src="https://img.shields.io/github/actions/workflow/status/thisis-romar/ma2-onPC-MCP/test.yml?style=for-the-badge&label=Tests" alt="Tests"></a>
  <a href="https://github.com/thisis-romar/ma2-onPC-MCP/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-BSL_1.1-orange?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/thisis-romar/ma2-onPC-MCP/blob/main/.python-version"><img src="https://img.shields.io/badge/Python-3.12%2B-blue?style=for-the-badge" alt="Python 3.12+"></a>
  <a href="https://github.com/thisis-romar/ma2-onPC-MCP/blob/main/src/server.py"><img src="https://img.shields.io/badge/MCP%20Tools-198-brightgreen?style=for-the-badge" alt="198 MCP Tools"></a>
  <a href="https://github.com/thisis-romar/ma2-onPC-MCP/tree/main/tests"><img src="https://img.shields.io/badge/Tests-3403-brightgreen?style=for-the-badge" alt="3403 Tests"></a>
  <a href="https://github.com/thisis-romar/ma2-onPC-MCP/blob/main/pyproject.toml"><img src="https://img.shields.io/badge/Version-3.35.3-purple?style=for-the-badge" alt="Version 3.35.3"></a>
  <br>
  <a href="https://github.com/thisis-romar/ma2-onPC-MCP/stargazers"><img src="https://img.shields.io/github/stars/thisis-romar/ma2-onPC-MCP?style=for-the-badge" alt="GitHub Stars"></a>
  <a href="https://github.com/thisis-romar/ma2-onPC-MCP/blob/main/uv.lock"><img src="https://img.shields.io/badge/MCP%20SDK-%E2%89%A5%201.21-blue?style=for-the-badge" alt="MCP SDK >= 1.21"></a>
  <a href="https://github.com/thisis-romar/ma2-onPC-MCP/blob/main/pyproject.toml"><img src="https://img.shields.io/badge/Linting-Ruff-brightgreen?style=for-the-badge" alt="Ruff"></a>
</p>

**An Agent Harness — and an embedded Agent core — for grandMA2 lighting consoles.** Exposes 198 grandMA2 commands as [Model Context Protocol](https://modelcontextprotocol.io/) tools so AI assistants (Claude Desktop, VS Code, etc.) can drive a lighting console via Telnet. Wire in an LLM client and the built-in orchestrator, task decomposer, and long-term memory turn it into a fully autonomous lighting agent.

> **License:** This software is licensed under the [Business Source License 1.1](LICENSE). The original repository is [`thisis-romar/ma2-onPC-MCP`](https://github.com/thisis-romar/ma2-onPC-MCP). Change Date: 2028-04-02. After the Change Date, the software converts to Apache License 2.0.

<table>
<tr><td><b>Agent Harness</b></td><td>198 MCP tools covering every grandMA2 operation — playback, programming, user management, show files, busking, and more. Connect any MCP-compatible AI assistant and start controlling the console immediately.</td></tr>
<tr><td><b>Embedded Agent Core</b></td><td>Orchestrator, task decomposer, working + long-term memory, and a skill registry with self-improvement suggestions. Inject a real LLM client and it becomes a fully autonomous lighting agent that plans, executes, remembers, and learns.</td></tr>
<tr><td><b>3-layer permission model</b></td><td>OAuth scope ∩ MA2 native rights ∩ console floor — all three must agree. 198 tools mapped to a minimum <code>MA2Right</code> tier, three risk tiers (<code>SAFE_READ</code> / <code>SAFE_WRITE</code> / <code>DESTRUCTIVE</code>), and line-break injection rejected at the transport layer.</td></tr>
<tr><td><b>A closed learning loop</b></td><td>Every tool call recorded to <code>tool_invocations</code>. SkillImprover surfaces repair suggestions from failure patterns and promotion candidates from high-quality sessions. Skills are versioned playbooks with full lineage tracking.</td></tr>
<tr><td><b>RAG-powered knowledge</b></td><td>Three indexed sources: this repo, ~1,043 grandMA2 help pages, and the MCP SDK. Semantic search via GitHub Models embeddings; falls back to keyword search without an API token.</td></tr>
</table>

[Quick Start](#quick-start) · [Architecture](#architecture) · [198 MCP Tools](#mcp-tools) · [Resources](#mcp-resources) · [Prompts](#mcp-prompts) · [Skills](#agent-skills) · [Safety System](#safety-system) · [RAG Pipeline](#rag-pipeline)

*The name is a play on "grandMA2" — [dedicated to someone special](DEDICATION.md).*

---

## Quick Start

```bash
# 1. Install
git clone https://github.com/thisis-romar/ma2-onPC-MCP && cd ma2-onPC-MCP
uv sync

# 2. Configure
cp .env.template .env        # then edit with your console IP

# 3. Install git hooks (pre-commit: RAG index, pre-push: test suite, stop: git guard)
make install-hooks

# 4. Run
uv run python -m src.server  # starts MCP server (stdio transport)
```

> [!TIP]
> **Semantic search:** Add `GITHUB_MODELS_TOKEN=ghp_...` to `.env`, then run
> `uv run python scripts/rag_ingest.py --provider github` once to rebuild the index with
> real embeddings. The `search_codebase` MCP tool will automatically use semantic ranking
> when the token is present.

## Architecture

```mermaid
graph TD
    H["🤖 Agent Core Layer<br/><code>src/private/server_orchestration_tools.py</code><br/>34 tools (110–144) · orchestrator · skills"] --> A
    A["🎭 MCP Server Layer<br/><code>src/server.py</code><br/>164 tools · safety gate"] --> B
    B["🧭 Navigation Layer<br/><code>src/navigation.py</code><br/>cd · list · scan · set_property"] --> C
    C["🔧 Command Builders<br/><code>src/commands/</code><br/>254 pure functions → strings"] --> D
    D["📡 Telnet Client<br/><code>src/telnet_client.py</code><br/>async · auth · injection prevention"]

    E["📖 Prompt Parser<br/><code>src/prompt_parser.py</code><br/>prompt detection · list parsing"] -.-> B
    F["🛡️ Vocabulary & Safety<br/><code>src/vocab.py</code><br/>158 keywords · risk tiers"] -.-> A
    G["🔍 RAG Pipeline<br/><code>rag/</code><br/>crawl → chunk → embed → query"] -.-> A
    I["🧠 Memory & Planning<br/><code>src/agent_memory.py · src/orchestrator.py</code><br/>WorkingMemory · LTM · TaskDecomposer"] -.-> H
    J["📊 OpenSpace<br/><code>src/telemetry.py · src/skill.py · src/skill_improver.py</code><br/>invocation recorder · skill registry · improvement loop"] -.-> H

    style H fill:#1a1a2e,stroke:#e94560,color:#fff
    style A fill:#1a1a2e,stroke:#e94560,color:#fff
    style B fill:#1a1a2e,stroke:#0f3460,color:#fff
    style C fill:#1a1a2e,stroke:#16213e,color:#fff
    style D fill:#1a1a2e,stroke:#533483,color:#fff
    style E fill:#0f3460,stroke:#0f3460,color:#fff
    style F fill:#0f3460,stroke:#0f3460,color:#fff
    style G fill:#0f3460,stroke:#0f3460,color:#fff
    style I fill:#0f3460,stroke:#0f3460,color:#fff
    style J fill:#0f3460,stroke:#0f3460,color:#fff
```

> All network I/O is isolated in [`telnet_client.py`](src/telnet_client.py). Command builders are pure functions that return strings. The navigation layer orchestrates cd/list workflows with parsed telnet feedback.

### Agent Harness vs. Agent Core

GrandPA2-Buddy is a **layered hybrid** — the boundary is explicit in the code:

| Layer | What it is | Key files |
|-------|-----------|-----------|
| **Bottom 164 tools** | **Agent Harness** — exposes a tool surface to an external AI; the reasoning loop lives in Claude Desktop, VS Code, etc. | [`src/server.py`](src/server.py) |
| **Top 34 tools** | **Embedded Agent Core** — orchestrator, task decomposer, long-term memory, skill registry | [`src/private/server_orchestration_tools.py`](src/private/server_orchestration_tools.py), [`src/orchestrator.py`](src/orchestrator.py) |

The orchestrator accepts a `sub_agent_fn` injection point. Without it, tool calls run in-process. Wire in a Claude API client and GrandPA2-Buddy becomes a fully autonomous agent that plans, executes, remembers, and improves itself.

**Autonomous agent entry points:**
- `run_agent_goal(goal, auto_confirm, dry_run)` — full loop: classify → plan → validate → execute → verify → trace
- `plan_agent_goal(goal)` — dry-run: returns plan + policy warnings without executing
- `resume_run(run_id)` — resume an interrupted run from its last DAG checkpoint

4 workflow templates in [`src/agent/workflows/`](src/agent/workflows/): patch, preset, playback, common.

### Module Overview

| Module | Role |
|--------|------|
| [`src/server.py`](src/server.py) | FastMCP server, 164 interactive tools, safety gate, env config |
| [`src/private/server_orchestration_tools.py`](src/private/server_orchestration_tools.py) | 34 agentic tools (110–144) registered onto FastMCP |
| [`src/orchestrator.py`](src/orchestrator.py) | Multi-agent task runner: hydration, risk-tier isolation, LTM; `_showfile_guard()`, `check_showfile()` for dynamic show change detection |
| [`src/task_decomposer.py`](src/task_decomposer.py) | Natural-language goal → ordered SubTask plan (14 built-in rules + `register_rule()` extensibility) |
| [`src/agent_memory.py`](src/agent_memory.py) | WorkingMemory (ephemeral) + LongTermMemory (SQLite session log) + showfile baseline tracking (`baseline_showfile`, `showfile_changed()`) |
| [`src/console_state.py`](src/console_state.py) | ConsoleStateSnapshot: hydrates 19 show-memory gaps; `parse_showfile_from_listvar()` |
| [`src/pool_name_index.py`](src/pool_name_index.py) | In-memory pool name/ID registry — zero-cost object resolution |
| [`src/rights.py`](src/rights.py) | MA2 native rights enforcement (`_OPERATION_MIN_RIGHT`, `get_session_ma2_right`, `is_permitted`) + telnet feedback classification |
| [`src/auth.py`](src/auth.py) | OAuth 2.1 scope enforcement (`@require_scope`), scope tier resolution, `GMA_AUTH_BYPASS` |
| [`src/credentials.py`](src/credentials.py) | OAuth tier → console user credential resolver |
| [`src/session_manager.py`](src/session_manager.py) | Per-operator Telnet session pool (LRU, keepalive, auto-reconnect) |
| [`src/navigation.py`](src/navigation.py) | cd + list + scan orchestration |
| [`src/prompt_parser.py`](src/prompt_parser.py) | Parse console prompts and `list` tabular output |
| [`src/vocab.py`](src/vocab.py) | 158 keywords, `RiskTier`, `FunctionalDomain`, safety classification |
| [`src/commands/`](src/commands/) | 262 exported command-builder functions, grouped by keyword type |
| [`src/commands/busking.py`](src/commands/busking.py) | 6 busking/performance builders: effect assign, rate/speed, page release, fader zero |
| [`src/categorization/`](src/categorization/) | ML tool categorization: K-Means clustering + auto-labeling |
| [`src/knowledge_graph/`](src/knowledge_graph/) | SQLite-backed knowledge graph: 10 node types, 11 edge types, BFS/DFS traversal, GraphRAG, planning integration, freshness tracking |
| [`src/telemetry.py`](src/telemetry.py) | Per-tool invocation recorder: `tool_invocations` table, latency, risk tier |
| [`src/skill.py`](src/skill.py) | `Skill` dataclass + `SkillRegistry`: versioned playbooks with lineage + filesystem skill fallback (`_load_filesystem_skill`, `_list_filesystem_skills`) |
| [`src/skill_improver.py`](src/skill_improver.py) | `SkillImprover`: repair suggestions + promotion candidates (read-only) |
| [`src/license.py`](src/license.py) | `LicenseTier` enum, `get_license_tier()`, `has_tier()`, `require_tier()` |
| [`src/license_tiers.py`](src/license_tiers.py) | `TOOL_LICENSE_TIERS` dict — maps tool names → `LicenseTier` |
| [`src/agent/`](src/agent/) | Agent harness: runtime, domain planner, step executor, policy, verification, memory, trace |
| [`src/agent/rollback.py`](src/agent/rollback.py) | `RollbackExecutor`: OOPS/DELETE compensation after verification failures |
| [`src/agent_bridge.py`](src/agent_bridge.py) | SubTask↔PlanStep converters + `execute_subtasks_via_agent()` bridge |
| [`src/telnet_client.py`](src/telnet_client.py) | Async Telnet (telnetlib3), auth, send/receive, injection prevention, `CircuitBreaker` |
| [`src/completions.py`](src/completions.py) | MCP Completions — argument autocompletion for tool parameters |
| [`src/context.py`](src/context.py) | Shared asyncio ContextVars for operator identity propagation |
| [`src/elicitation.py`](src/elicitation.py) | Server-initiated user input requests (when MCP client supports it) |
| [`src/sampling.py`](src/sampling.py) | Server-initiated LLM calls via MCP client sampling |
| [`src/subscriptions.py`](src/subscriptions.py) | MCP Resource change notification tracking |
| [`src/tools.py`](src/tools.py) | Global GMA2 telnet client accessor — `get_client()` used by all tools |

### Advanced Features (Phases 1–6)

| Feature | Module | Description |
|---------|--------|-------------|
| **Circuit breaker** | `src/telnet_client.py` | 3-state breaker (CLOSED→OPEN→HALF_OPEN) prevents cascading telnet timeouts |
| **Policy strictness** | `src/agent/policy.py` | `GMA_POLICY_STRICTNESS` env var: WARN (default) or BLOCK mode for policy rules |
| **Rollback executor** | `src/agent/rollback.py` | Post-verification OOPS/DELETE compensation strategies |
| **Progress monitor** | `src/agent/executor.py` | Detects stalled (consecutive failures) and looping (identical outputs) execution |
| **Incremental hydration** | `src/console_state.py` | `pool_types` parameter + `pools_for_gaps()` for selective console hydration |
| **Risk-weighted scoring** | `src/skill_improver.py` | Quality scoring weighted by risk tier (DESTRUCTIVE failures count 3x) |
| **Semantic skill search** | `src/skill.py` | Embedding-based `search_semantic()` via RAG `EmbeddingProvider`, LIKE fallback |
| **DAG checkpoints** | `src/agent/memory.py` | `step_checkpoints` table for crash recovery; `resume_run()` in AgentRuntime |
| **Bridge activation** | `src/agent_bridge.py` | System A (Orchestrator) plans execute through System B (StepExecutor) |
| **Hybrid retrieval** | `src/server.py` | Reciprocal Rank Fusion (RRF) combining keyword + semantic scores |
| **Metadata filters** | `src/server.py` | `filter_risk_tier` + `filter_license_tier` in `suggest_tool_for_task` |
| **Tool body reranking** | `rag/retrieve/rerank.py` | Second-stage `rerank_tools()` scoring against full docstrings |

## Configuration

Create a `.env` file (see [`.env.template`](.env.template)):

```env
# grandMA2 Console
GMA_HOST=192.168.1.100     # grandMA2 console IP (required)
GMA_USER=administrator     # default: administrator
GMA_PASSWORD=admin         # default: admin
GMA_PORT=30000             # default: 30000 (30001 = read-only)
GMA_SAFETY_LEVEL=standard  # standard (default), admin, or read-only
LOG_LEVEL=INFO             # default: INFO

# OAuth & License
GMA_SCOPE=tier:3           # OAuth tier (tier:0–tier:5) or explicit scopes
GMA_AUTH_BYPASS=            # set "1" to bypass scope checks (dev only)
GMA_LICENSE_TIER=community  # community (default), professional, enterprise
GMA_LICENSE_BYPASS=         # set "1" to bypass tier checks (dev only)

# Transport
GMA_TRANSPORT=stdio        # stdio (default), sse, or streamable-http

# RAG Pipeline (optional — pick one provider)
GITHUB_MODELS_TOKEN=                          # GitHub PAT with models:read scope (1536-dim)
OPENROUTER_API_KEY=                           # OpenRouter API key (2048-dim, alternative)
RAG_EMBED_MODEL=openai/text-embedding-3-small # embedding model (GitHub Models default)
RAG_EMBED_DIMENSIONS=1536                     # vector dimensions (1536 GitHub, 2048 OpenRouter)
```

> [!NOTE]
> Get a GitHub PAT with the `models:read` scope at [github.com/settings/tokens](https://github.com/settings/tokens). Alternatively, use [openrouter.ai](https://openrouter.ai/) for the OpenRouter provider.

| Level | Behavior |
|-------|----------|
| `read-only` | Only `SAFE_READ` commands allowed (`list`, `info`, `cd`) |
| `standard` | `SAFE_READ` + `SAFE_WRITE` allowed; `DESTRUCTIVE` requires `confirm_destructive=True` |
| `admin` | All commands allowed without confirmation |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GMA_HOST` | `127.0.0.1` | grandMA2 console IP address |
| `GMA_PORT` | `30000` | Telnet port (30001 = read-only) |
| `GMA_USER` | `administrator` | Console login username |
| `GMA_PASSWORD` | `admin` | Console login password |
| `GMA_SAFETY_LEVEL` | `standard` | `read-only`, `standard`, or `admin` |
| `GMA_TRANSPORT` | `stdio` | MCP transport: `stdio` (Claude Desktop, VS Code), `sse` (web clients), `streamable-http` (HTTP integrations) |
| `GMA_SCOPE` | `tier:3` | OAuth tier (`tier:0`–`tier:5`) or explicit scopes |
| `GMA_LICENSE_TIER` | `community` | `community` (free), `professional`, `enterprise` |
| `GMA_TELEMETRY` | `1` | Set `0` to disable per-tool invocation recording |
| `GMA_POLICY_STRICTNESS` | `warn` | `warn` (default) or `block` — controls policy rule enforcement |
| `GMA_AUTH_BYPASS` | _(unset)_ | Set `1` to bypass OAuth scope checks (dev only) |
| `GMA_RIGHTS_BYPASS` | _(unset)_ | Set `1` to bypass MA2 native rights (dev only) |
| `GMA_LICENSE_BYPASS` | _(unset)_ | Set `1` to bypass license tier checks (dev only) |
| `GITHUB_MODELS_TOKEN` | _(unset)_ | GitHub PAT with `models:read` scope for RAG embeddings (falls back to `GITHUB_TOKEN`) |
| `OPENROUTER_API_KEY` | _(unset)_ | OpenRouter API key for RAG embeddings (2048-dim, alternative to GitHub Models) |
| `LOG_LEVEL` | `INFO` | Python logging level |

## License Tiers

All 198 MCP tools are classified into three license tiers:

| Tier | Cost | Tools | Examples |
|------|------|-------|----------|
| `COMMUNITY` | Free | ~10 | `navigate_console`, `get_object_info`, `playback_action`, `set_intensity` |
| `PROFESSIONAL` | Paid | ~133 | Store/copy/delete, presets, sequences, macros, effects, patch, show mgmt |
| `ENTERPRISE` | Premium | ~54 | RAG search, orchestration, skill system, agent harness, ML categorisation |

| Variable | Default | Effect |
|----------|---------|--------|
| `GMA_LICENSE_TIER` | `community` | Active tier: `community`, `professional`, `enterprise` |
| `GMA_LICENSE_BYPASS` | `0` | Set `1` to bypass tier checks (dev/test only) |

Tools not in the tier map default to COMMUNITY. When a tool's required tier exceeds the active tier, it returns `{"blocked": true, "license_required": "...", "current_tier": "..."}`.

## MCP Tools

The server exposes **198 tools** to MCP clients, grouped into 15 categories plus an agentic orchestration layer:

<details>
<summary><strong>🧭 Navigation & Inspection</strong> — 4 tools</summary>

| Tool | Description |
|------|-------------|
| `navigate_console` | Navigate the console object tree via ChangeDest (cd) |
| `get_console_location` | Query the current console destination without navigating |
| `list_console_destination` | List objects at the current destination with parsed entries |
| `scan_console_indexes` | Batch scan numeric indexes at any tree level |

```
cd /            → go to root
cd ..           → go up one level
cd Group.1      → navigate to Group 1 (dot notation)
cd 5            → navigate by element index
cd "MySeq"      → navigate by name
list            → enumerate objects at current destination
```

**Dot notation:** MA2 uses `[object-type].[object-id]` for object references (e.g., `Group.1`, `Preset.4.1`, `Sequence.3`).

</details>

<details>
<summary><strong>💡 Lighting Control</strong> — 7 tools</summary>

| Tool | Description |
|------|-------------|
| `set_intensity` | Set dimmer level on fixtures, groups, or channels |
| `set_attribute` | Set attribute values (Pan, Tilt, Zoom, etc.) on fixtures/groups |
| `apply_preset` | Apply a stored preset (color, position, gobo, beam, etc.) |
| `clear_programmer` | Clear programmer state (all, selection, active, or sequential) |
| `park_fixture` | Park a fixture/channel at its current or a specified value |
| `unpark_fixture` | Release a park lock on a fixture/channel |
| `fix_locate_fixture` | Fix (park) or Locate selected/specified fixtures at their defaults |

</details>

<details>
<summary><strong>🎯 Programmer / Selection</strong> — 8 tools</summary>

| Tool | Description |
|------|-------------|
| `modify_selection` | Select, deselect, or toggle fixtures in the programmer |
| `adjust_value_relative` | Adjust programmer values relatively (+ or –) |
| `manipulate_selection` | Invert or Align the current fixture selection / programmer values |
| `select_fixtures_by_group` | Select all fixtures in a named group |
| `select_executor` | Set the active executor for subsequent operations (single-selection only; use deselect=True to clear) |
| `select_feature` | Set active Feature context (updates `$PRESET`/`$FEATURE`/`$ATTRIBUTE`) |
| `select_preset_type` | Activate a PresetType context (PresetType 1–9 or by name) |
| `if_filter` | Apply an IfOutput / IfActive filter to limit programmer scope |

</details>

<details>
<summary><strong>▶️ Playback & Executor</strong> — 9 tools</summary>

| Tool | Description |
|------|-------------|
| `execute_sequence` | Legacy sequence playback: go, pause, or goto cue |
| `playback_action` | Full playback: go, go_back, goto, fast_forward, fast_back, def_go, def_go_back, def_pause |
| `control_executor` | Control an executor (go, pause, stop, flash, etc.) |
| `load_cue` | Pre-load the next or previous cue on an executor without firing it |
| `get_executor_status` | Query status of an executor (current cue, level, state) |
| `set_executor_level` | Set the fader level on an executor |
| `navigate_page` | Navigate to a specific page or page +/– |
| `release_executor` | Release (deactivate) an executor |
| `blackout_toggle` | Toggle grandmaster blackout on/off |

</details>

<details>
<summary><strong>playback_action</strong> — parameters &amp; response fields</summary>

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | `str` | One of the actions below |
| `object_type` | `str \| None` | Object type for `go`/`go_back` (e.g. `"executor"`, `"sequence"`) |
| `object_id` | `int \| list[int] \| None` | ID or list of IDs — list produces `N + M + …` syntax |
| `cue_id` | `int \| float \| None` | Required for `"goto"` |
| `end` | `int \| None` | End of range for `go`/`go_back` (builds `thru N`) |
| `cue_mode` | `str \| None` | `"normal"`, `"assert"`, `"xassert"`, or `"release"` |
| `executor` | `int \| list[int] \| None` | Executor ID(s) for `goto`/`fast_forward`/`fast_back` — list produces `N + M + …` |
| `sequence` | `int \| None` | Sequence ID for `goto`/`fast_forward`/`fast_back` |

#### Actions

| Action | Command sent | Notes |
|--------|-------------|-------|
| `"go"` | `go [object_type] [id]` | Fires next cue; `object_id` accepts a list |
| `"go_back"` | `goback [object_type] [id]` | Fires previous cue; `object_id` accepts a list |
| `"goto"` | `goto cue N [executor/sequence]` | Pre-flight validates cue exists; returns `blocked=True` on Error #72 |
| `"fast_forward"` | `>>> [executor N]` | `executor` accepts a list |
| `"fast_back"` | `<<< [executor N]` | `executor` accepts a list |
| `"def_go"` | `defgoforward` | Fires on `$SELECTEDEXEC`; reads state before firing |
| `"def_go_back"` / `"def_goback"` | `defgoback` | Same — `def_goback` is an alias |
| `"def_pause"` | `defgopause` | Same |

#### Response fields

All actions return `command_sent` and `raw_response`.

`def_go`, `def_go_back`, and `def_pause` additionally return:

| Field | Value |
|-------|-------|
| `selected_executor` | Value of `$SELECTEDEXEC` read **before** the command was sent (`null` if unavailable) |
| `selected_cue_before` | Value of `$SELECTEDEXECCUE` read before the command (`null` if unavailable) |

`goto` additionally returns `cue_exists`, `cue_probe_response`, and optionally `executor_probe_response`.

#### Examples

```python
# Fire next cue on executors 1, 2, and 3 simultaneously
playback_action(action="go", object_type="executor", object_id=[1, 2, 3])
# → go executor 1 + 2 + 3

# Fast-forward executors 2 and 4
playback_action(action="fast_forward", executor=[2, 4])
# → >>> executor 2 + 4

# Go back on the selected executor — response tells you which one fired
playback_action(action="def_go_back")
# → {"command_sent": "defgoback", "selected_executor": "5", "selected_cue_before": "3"}
```

</details>

<details>
<summary><strong>select_executor</strong> — parameters &amp; response fields</summary>

**Single-selection only.** MA2 telnet `select executor N` accepts exactly one executor number. There is no list syntax — pass a single `executor_id` integer.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `executor_id` | `int` | required | Executor number (1–999) |
| `page` | `int \| None` | `None` | Page number — produces `select executor page.id` (e.g. `page=2, executor_id=5` → `select executor 2.5`) |
| `deselect` | `bool` | `False` | If `True`, sends bare `select` to clear the current selection (**unverified on grandMA2 telnet** — inspect `raw_response`) |

#### Response fields

| Field | Always present | Description |
|-------|---------------|-------------|
| `command_sent` | ✓ | The exact command sent |
| `raw_response` | ✓ | Raw telnet reply |
| `confirmed_selected_exec` | ✓ | Value of `$SELECTEDEXEC` read after the command (`null` if unavailable) |
| `risk_tier` | ✓ | `"SAFE_WRITE"` |
| `warning` | if mismatch | Present when `confirmed_selected_exec` doesn't match the requested `executor_id` |
| `note` | if deselect | Present when `deselect=True` — warns that bare `select` behaviour is unverified |

#### Page-qualified addressing

When `page` is supplied, MA2 stores `$SELECTEDEXEC` as the executor number only (not the page-qualified form). The confirmation check compares against `executor_id` alone — no spurious warning.

#### Examples

```python
# Select executor 5 and confirm
select_executor(executor_id=5)
# → {"command_sent": "select executor 5", "confirmed_selected_exec": "5"}

# Select executor 5 on page 2
select_executor(executor_id=5, page=2)
# → {"command_sent": "select executor 2.5", "confirmed_selected_exec": "5"}

# Clear the current selection
select_executor(executor_id=1, deselect=True)
# → {"command_sent": "select", "note": "Bare 'select' sent … unverified …"}
```

</details>

<details>
<summary><strong>💾 Programming / Store</strong> — 13 tools</summary>

| Tool | Description |
|------|-------------|
| `create_fixture_group` | Select a range of fixtures and save as a named group |
| `store_current_cue` | Store programmer state into a cue |
| `store_new_preset` | Store programmer state as a new preset |
| `store_object` | Store generic objects — macros, effects, worlds, etc. |
| `store_cue_with_timing` | Store a cue with explicit fade/delay timing |
| `update_cue_data` | Update an existing cue with current programmer values |
| `set_cue_timing` | Edit fade, delay, or trigger timing on an existing cue |
| `set_sequence_property` | Set a property on a sequence (e.g. looping, autoprepare) |
| `assign_cue_trigger` | Assign a trigger type (Go, Follow, Time) to a cue |
| `block_unblock_cue` | Block or Unblock a cue to freeze/restore its tracked values |
| `clone_object` | Clone (duplicate with data) one or more objects to new IDs |
| `remove_from_programmer` | Remove specific fixtures or channels from the programmer |
| `run_macro` | Execute a stored macro by ID |

> [!WARNING]
> Store tools are **DESTRUCTIVE** — they require `confirm_destructive=True`.

</details>

<details>
<summary><strong>⏱️ Timecode & Timer</strong> — 3 tools</summary>

| Tool | Description |
|------|-------------|
| `control_timecode` | Start, stop, or jump a timecode show |
| `control_timer` | Start, stop, or reset a timer |
| `store_timecode_event` | Store an event into a timecode show at the current time |

</details>

<details>
<summary><strong>🔗 Assignment & Layout</strong> — 12 tools</summary>

| Tool | Description |
|------|-------------|
| `assign_object` | Assign objects, functions, fades, or layout positions |
| `assign_executor_property` | Assign any of 22 settable options on an executor (width, priority, autostart, etc.) — page-qualified |
| `get_executor_state` | Read all 32 fields of one executor via `List Executor page.id` (SAFE_READ) |
| `scan_page_executor_layout` | Map executor slot occupancy on a page — required pre-flight before width expansion (SAFE_READ) |
| `discover_fixture_type_attributes` | Discover fixture type attribute names via EditSetup tree navigation (SAFE_READ) |
| `label_or_appearance` | Label or set visual appearance of objects |
| `edit_object` | Edit, cut, or paste objects |
| `cut_paste_object` | Cut an object to clipboard, or paste clipboard content at a location |
| `remove_content` | Remove content from objects — fixtures, effects, preset types |
| `save_recall_view` | Save or recall a screen view configuration |
| `set_executor_priority` | Set playback priority on an executor (super/high/normal/low/htp/swap) |
| `set_node_property` | Set a property on any node via dot-separated tree path (DESTRUCTIVE) |

</details>

<details>
<summary><strong>📁 Show Management</strong> — 7 tools</summary>

| Tool | Description |
|------|-------------|
| `save_show` | Save the current show file to disk |
| `list_shows` | List available show files on the console |
| `load_show` | Load a show file by name |
| `new_show` | Create a new empty show |
| `delete_show` | Delete a show file from disk |
| `export_objects` | Export show objects (groups, presets, macros, etc.) to a file |
| `import_objects` | Import objects from a file into the show |

> [!CAUTION]
> `new_show` without `preserve_connectivity=True` **disables Telnet**, severing the MCP connection.

</details>

<details>
<summary><strong>🔌 Fixture Setup & Patch</strong> — 16 tools</summary>

| Tool | Description |
|------|-------------|
| `list_fixture_types` | List fixture types loaded in the show |
| `list_layers` | List fixture layers in the patch |
| `list_universes` | List configured DMX universes |
| `list_library` | Browse the MA2 fixture library |
| `list_fixtures` | List fixtures currently patched in the show |
| `browse_patch_schedule` | Browse the DMX patch schedule |
| `patch_fixture` | Patch a fixture to a DMX universe and address |
| `unpatch_fixture` | Remove a fixture's DMX patch assignment |
| `set_fixture_type_property` | Set a property on a fixture type |
| `manage_matricks` | Manage MAtricks (fixture matrix) objects |
| `create_matricks_library` | Generate combinatorial MAtricks pool with 25-color coding |
| `store_matricks_preset` | Combined set + store + label MAtricks preset workflow |
| `create_filter_library` | Generate color-coded Filter library with V/VT/E variants |
| `import_fixture_type` | Import a fixture type from the MA2 library |
| `import_fixture_layer` | Import a fixture layer XML file into the show patch |
| `generate_fixture_layer_xml` | Generate a grandMA2 fixture layer XML file for import |

<details>
<summary>Fixture import workflow</summary>

```python
# 1. Generate the XML file
generate_fixture_layer_xml(
    filename="my_dimmers",
    layer_name="Dimmers",
    layer_index=1,
    fixtures=[
        {"fixture_id": 1, "name": "Dim 1", "fixture_type_no": 2,
         "fixture_type_name": "2 Dimmer 00", "dmx_address": 1, "num_channels": 1},
    ],
    showfile="myshow",
)

# 2. Import the fixture type from library
import_fixture_type(
    manufacturer="Martin",
    fixture="Mac700Profile_Extended",
    mode="Extended",
    confirm_destructive=True,
)

# 3. Import the layer
import_fixture_layer(filename="my_dimmers", layer_index=1, confirm_destructive=True)
```

</details>

<details>
<summary>MAtricks combinatorial library</summary>

Generates every combination of Wings × Groups × Blocks × Interleave (5⁴ = 625 items) with a **25-color scheme** embedded directly in the XML:

| Dimension | Controls | Values |
|-----------|----------|--------|
| **Wings** | Hue | Red (0°) · Yellow-Green (72°) · Cyan (144°) · Blue (216°) · Magenta (288°) |
| **Groups** | Brightness | 100% · 80% · 60% · 45% · 30% |
| Blocks | — | 0–4 |
| Interleave | — | 0–4 |

Colors use `<Appearance Color="RRGGBB" />` in the XML — import is instant, no telnet loop required.

```bash
# Full library (625 items)
python -m scripts.create_matricks_library --max-value 4

# Quick test (16 items)
python -m scripts.create_matricks_library --max-value 1

# XML only (no telnet import)
python -m scripts.create_matricks_library --xml-only

# Re-apply colors via telnet (if needed)
python -m scripts.create_matricks_library --color-only
```

</details>

</details>

<details>
<summary><strong>🔎 Info, Queries & Discovery</strong> — 15 tools</summary>

| Tool | Description |
|------|-------------|
| `get_object_info` | Query info on any object (fixture, group, sequence, etc.) |
| `query_object_list` | List cues, groups, presets, attributes, or messages |
| `get_variable` | Get the current value of a console variable |
| `list_system_variables` | List all 26 built-in system variables (`$TIME`, `$SHOWFILE`, etc.) |
| `list_sequence_cues` | List all cues in a sequence with timing and labels |
| `discover_object_names` | Discover named objects in a pool via the cd tree |
| `check_pool_availability` | Check which slots are occupied and free in an object pool |
| `browse_preset_type` | Browse Feature/Attribute/SubAttribute tree for a PresetType |
| `list_preset_pool` | List presets in the Global preset pool by type |
| `browse_effect_library` | Browse the grandMA2 effect library |
| `browse_macro_library` | Browse the grandMA2 macro library |
| `browse_plugin_library` | Browse the grandMA2 plugin library |
| `highlight_fixtures` | Toggle highlight mode for selected fixtures |
| `list_undo_history` | List recent undo history entries |
| `discover_filter_attributes` | Discover show-specific filter attributes from patched fixtures |

</details>

<details>
<summary><strong>⚙️ Console & Utilities</strong> — 8 tools</summary>

| Tool | Description |
|------|-------------|
| `send_raw_command` | Send any MA command directly (safety-gated) |
| `copy_or_move_object` | Copy or move objects between slots (with merge/overwrite) |
| `delete_object` | Delete any object by type and ID |
| `manage_variable` | Set or add to console variables (global or user-scoped) |
| `undo_last_action` | Undo the last console action |
| `toggle_console_mode` | Toggle console modes: blind, highlight, freeze, solo |
| `list_fader_modules` | List connected fader modules and their configuration |
| `list_update_history` | List programming update history |

</details>

<details>
<summary><strong>👤 User Management</strong> — 5 tools</summary>

| Tool | Description |
|------|-------------|
| `list_console_users` | List all user profiles configured on the console |
| `create_console_user` | Create a new user profile with name and password |
| `delete_user` | Delete a user profile |
| `inspect_sessions` | Inspect active Telnet sessions and connected operators |
| `assign_world_to_user_profile` | Assign a world (visibility scope) to a user profile |

> [!NOTE]
> Requires `GMA_SCOPE=gma2:user:manage` (Admin tier). Bootstrap 5 default user accounts
> with `python scripts/bootstrap_console_users.py`.

</details>

<details>
<summary><strong>🤖 ML-Based Tool Discovery</strong> — 4 tools</summary>

| Tool | Description |
|------|-------------|
| `list_tool_categories` | Browse auto-discovered tool categories via K-Means clustering |
| `recluster_tools` | Re-run the full ML pipeline (extract → embed → cluster → label) |
| `get_similar_tools` | Find the most similar tools by Euclidean distance in feature space |
| `suggest_tool_for_task` | Suggest tools for a natural-language task description |

</details>

<details>
<summary><strong>🔍 Codebase Search / RAG</strong> — 1 tool</summary>

| Tool | Description |
|------|-------------|
| `search_codebase` | Semantic search over the indexed codebase and MA2 docs |

</details>

<details>
<summary><strong>🤖 Orchestration & Console State</strong> — 34 tools</summary>

These tools form the **agentic layer** ([`src/private/server_orchestration_tools.py`](src/private/server_orchestration_tools.py)). They enable
multi-step task execution with memory, risk-tier isolation, and zero-telnet state queries
via a `ConsoleStateSnapshot` cache that closes 19 show-memory gaps.

#### Task Orchestration (Tools 110–118)

| Tool | Description |
|------|-------------|
| `decompose_task` | Break a lighting goal into an ordered multi-agent plan (review before execute) |
| `run_task` | Execute a full task with risk-tier isolation, memory, and state hydration |
| `list_agent_sessions` | List recent task sessions from long-term memory |
| `recall_agent_session` | Restore WorkingMemory snapshot from a past session |
| `agent_token_report` | Report token consumption across agent sessions |
| `register_decomposition_rule` | Register a custom task-decomposition rule at runtime |
| `resolve_object_ref` | Resolve a pool object name/ID to a quoted MA2 token (zero telnet) |
| `list_pool_names` | List all names and IDs for a pool type from the in-memory index |
| `hydrate_console_state` | Trigger a fresh ConsoleStateSnapshot hydration |

#### Console State Queries (Tools 119–129)

Read from the cached snapshot — **no telnet round-trips required**.

| Tool | Description |
|------|-------------|
| `get_console_state` | Snapshot summary, age, and staleness warning |
| `get_park_ledger` | All currently parked fixtures |
| `get_filter_state` | Active filter ID and V/VT/E flag settings |
| `get_world_state` | Active world and visibility scope |
| `get_matricks_state` | Write-tracked MAtricks state (interleave, blocks, wings, etc.) |
| `get_programmer_selection` | `$SELECTEDFIXTURESCOUNT`, `$SELECTEDEXEC`, `$SELECTEDEXECCUE` |
| `hydrate_sequences` | Deep-hydrate specific sequence cues and parts |
| `get_sequence_memory` | Sequence properties and CueRecords from the snapshot |
| `assert_selection_count` | Validate fixture selection count against an expected value |
| `assert_preset_exists` | Pre-flight check: verify a preset slot is occupied |
| `get_executor_detail` | Full ExecutorState for a given executor ID |

#### Orchestration Safety & Diagnostics (Tools 131–137)

| Tool | Description |
|------|-------------|
| `diff_console_state` | Compare current snapshot against a caller-supplied baseline; returns changed fields |
| `get_showfile_info` | Return showfile name, version, host status, and active user from snapshot (zero telnet) |
| `watch_system_var` | Poll a grandMA2 system variable until it changes or a timeout is reached |
| `confirm_destructive_steps` | Decompose a goal and return only the DESTRUCTIVE steps for human review |
| `abort_task` | Mark a running session as aborted and return completed/failed step summary |
| `retry_failed_steps` | Reload a past session from LTM and re-run the original goal |
| `assert_fixture_exists` | Two-tier fixture patch validation (snapshot index → live telnet fallback) |

#### OpenSpace Layer — Telemetry, Skills & Improvement (Tools 110–144)

| Tool | Scope | Description |
|------|-------|-------------|
| `get_tool_metrics` | DISCOVER | Latency + error-rate stats for any tool over N days |
| `list_skills` | DISCOVER | Search the skill registry by name, description, or context |
| `get_skill` | DISCOVER | Full detail + lineage chain for a single skill |
| `promote_session_to_skill` | PROGRAMMER_WRITE | Manually promote a completed session to a named, versioned skill |
| `get_improvement_suggestions` | DISCOVER | Repair suggestions (failing tools) + promotion candidates (successful sessions) |
| `approve_skill` | SYSTEM_ADMIN | Human-gate: set `approved=True` on a DESTRUCTIVE-scope skill before agents may use it |
| `assert_showfile_unchanged` | DISCOVER | Verify open show matches hydration baseline — live ListVar vs cached snapshot |

#### Compliance, Patch Validation & Cross-Venue Tools

| Tool | Scope | Description |
|------|-------|-------------|
| `detect_dmx_address_conflicts` | DISCOVER | Scan all universes for overlapping fixture DMX address assignments |
| `get_telemetry_report` | DISCOVER | Export tool invocation telemetry as JSON or markdown audit log |
| `generate_compliance_report` | DISCOVER | SB 132 / safety-audit compliance report from session telemetry |
| `validate_preset_references` | DISCOVER | Scan cue list for references to deleted or missing preset pool entries |
| `list_macro_jump_targets` | DISCOVER | Parse macro lines and extract all jump targets for index-shift planning |
| `check_pool_slot_availability` | DISCOVER | Pre-flight: which pool slots are empty vs. occupied in a range |
| `remap_fixture_ids` | PROGRAMMER_WRITE | Remap fixture references from one ID to another in groups after PSR import |

> [!NOTE]
> Call `hydrate_console_state` before using state-query tools. The snapshot caches values
> that have no direct telnet readback (MAtricks state, park ledger, filter VTE flags, etc.).
> Check freshness with `get_console_state`.

</details>

<details>
<summary><strong>🎛️ Busking &amp; Performance</strong> — 6 tools</summary>

| Tool | Description |
|------|-------------|
| `assign_temp_fader` | Set the temp fader level on the currently selected executor |
| `assign_effect_to_executor` | Bind an effect template to an executor slot (DESTRUCTIVE — requires `confirm_destructive=True`) |
| `modulate_effect` | Set rate (`EffectRate`) or speed (`EffectSpeed`) on active effects |
| `clear_effects_on_page` | Release all effect executors on a page range |
| `normalize_page_faders` | Set all faders on a page to 0 without releasing |
| `classify_show_mode` | Inspect executor assignments and classify show as `busking`, `sequence`, `hybrid`, or `empty` |

</details>

## MCP Resources

Eighteen read-only resources exposable to any MCP client. Use them for zero-telnet context before calling tools.

| URI | Description |
|-----|-------------|
| [`ma2://docs/rights-matrix`](src/server.py) | OAuth scope → MA2Right mapping matrix (JSON) |
| [`ma2://docs/vocab-summary`](src/server.py) | All 158 keywords with RiskTier and category (JSON) |
| [`ma2://docs/tool-taxonomy`](src/server.py) | ML-clustered tool taxonomy — 150 base tools clustered into 14 categories (JSON) |
| [`ma2://docs/responsibility-map`](src/server.py) | Module responsibility map for architectural decisions (Markdown) |
| [`ma2://docs/tool-surface-tiers`](src/server.py) | Tier A/B/C classification for every tool (Markdown) |
| [`ma2://docs/volunteer-guide`](src/server.py) | Plain-language volunteer operator guide: three-tier access model + Sunday preflight |
| [`ma2://docs/sb132-compliance`](src/server.py) | SB 132 / CA Film Tax Credit safety documentation mapped to telemetry fields |
| [`ma2://docs/rdm-workflow`](src/server.py) | RDM discovery, autopatch, and device info best practices |
| [`ma2://docs/lua-scripting`](src/server.py) | grandMA2 Lua 5.2 scripting reference: `gma.*` namespace + common patterns |
| [`ma2://skills/{skill_id}`](src/server.py) | Skill injection payload by ID — returns formatted user message ready for agent injection |
| [`ma2://busking/patterns`](src/server.py) | Best-practice busking patterns: fader model, song macro protocol, live recovery |
| [`ma2://busking/effect-design`](src/server.py) | Effect-to-executor assignment patterns, rate vs speed, MAtricks layering |
| [`ma2://busking/color-design`](src/server.py) | HSB palette strategy, preset numbering, monochromatic constraint, color lock |
| [`ma2://docs/psr-guide`](src/server.py) | PSR (Partial Show Read) workflow guide and best practices |
| [`ma2://docs/effects-reference`](src/server.py) | Effects parameter reference: all 10 effect parameters with ranges |
| [`ma2://docs/timecode-reference`](src/server.py) | Timecode show programming reference: SMPTE, events, tracks |
| [`ma2://docs/macro-reference`](src/server.py) | Macro scripting reference: SetVar, conditionals, jump targets |
| [`ma2://docs/network-session`](src/server.py) | Network session reference: JoinSession, TakeControl, SetIP |

All resources are read-only — no console side-effects.

## MCP Prompts

Thirteen workflow prompts that orchestrate tools into guided multi-step procedures.

| Prompt | Args | Description |
|--------|------|-------------|
| [`preflight_destructive_change`](src/server.py) | `operation`, `target`, `reason` | Safety pre-flight checklist before any DESTRUCTIVE tool call — checks rights, target existence, blind mode, and executor state |
| [`inspect_console`](src/server.py) | `focus` | Guided read-only console state inspection — `full`, `playback`, `fixtures`, `show`, or `rights` |
| [`plan_cue_store`](src/server.py) | `sequence_id`, `cue_number`, `fixture_selection`, `preset_or_values` | Plan a cue store operation with pre-flight and verification steps — does not execute |
| [`diagnose_playback_failure`](src/server.py) | `executor_id`, `symptom` | Structured playback failure diagnosis — returns `fault_class`, `root_cause`, `recommended_actions` |
| [`load_show_safely`](src/server.py) | `show_name` | Safe show loading checklist — prevents accidental Telnet disconnection via missing `/globalsettings` |
| [`bootstrap_rights_users`](src/server.py) | *(none)* | Guided provisioning of the six-tier MA2 rights user accounts |
| [`volunteer_sunday_preflight`](src/server.py) | `show_name`, `campus_name` | SAFE_READ preflight for volunteer operators — GREEN/AMBER/RED show verification before service |
| [`generate_busking_template`](src/server.py) | `target_page`, `fixture_strategy` | Build a complete busking template from current patch — groups, presets, effects, executor layout |
| [`pre_show_health_check`](src/server.py) | `sequence_ids`, `strict` | Full show health audit — showfile, presets, executors, cues, parks, and DMX with scored findings |
| [`adapt_show_to_venue`](src/server.py) | `source_show_description`, `new_venue_notes` | Cross-venue show adaptation — patch comparison, group remapping, preset verification |
| [`migrate_show_via_psr`](src/server.py) | `source_show`, `target_objects` | PSR-based cross-show content migration with slot conflict detection |
| [`program_effect`](src/server.py) | `fixture_group`, `effect_type`, `speed_bpm` | Guided effect programming workflow with fixture selection and parameter setting |
| [`build_timecode_show`](src/server.py) | `sequence_ids`, `smpte_start` | Build a SMPTE timecode show with cue-to-timestamp mapping |

## Agent Skills

Instruction modules ([`.claude/skills/`](.claude/skills/)) that are injected as user messages into agent conversations. They teach agents domain-specific workflows without embedding knowledge in tool docstrings.

| Skill | Description |
|-------|-------------|
| [`ma2-command-rules`](.claude/skills/ma2-command-rules/SKILL.md) | MA2 command construction, object resolution, quoting rules, and safety escalation |
| [`telnet-feedback-triage`](.claude/skills/telnet-feedback-triage/SKILL.md) | Classify and summarise grandMA2 Telnet feedback using the `FeedbackClass` enum |
| [`feedback-investigator`](.claude/skills/feedback-investigator/SKILL.md) | Worker playbook: classify and investigate Telnet feedback failures |
| [`cue-list-auditor`](.claude/skills/cue-list-auditor/SKILL.md) | Worker playbook: audit cue list gaps, labels, timing, and health |
| [`busking-lighting-performance`](.claude/skills/busking-lighting-performance/SKILL.md) | Live busking — fader-per-effect model, executor layout, effect layering, live recovery |
| [`song-macro-page-design`](.claude/skills/song-macro-page-design/SKILL.md) | Song macro pages — first-button protocol, executor column layout, jump target safety |
| [`constrained-color-design`](.claude/skills/constrained-color-design/SKILL.md) | Monochromatic HSB palette design — preset numbering, color lock, song-to-palette mapping |
| [`preset-library-architect`](.claude/skills/preset-library-architect/SKILL.md) | Build full dimmer/position/color/gobo preset pools from raw attribute values |
| [`patch-and-group-builder`](.claude/skills/patch-and-group-builder/SKILL.md) | Patch fixtures, build groups by type/position, and verify selection counts |
| [`chaser-builder`](.claude/skills/chaser-builder/SKILL.md) | Step-based chasers, running lights via MAtricks, strobes — speed/rate/direction control |
| [`cue-tracking-and-timing`](.claude/skills/cue-tracking-and-timing/SKILL.md) | Tracking vs non-tracking, Block/Unblock, MIB, timing layers, trigger types, Update vs Store |
| [`executor-configuration`](.claude/skills/executor-configuration/SKILL.md) | Executor priority, trigger types, fader functions, speed masters, protect options |
| [`show-management-and-psr`](.claude/skills/show-management-and-psr/SKILL.md) | Save/Load/New show (connectivity preservation), PSR workflow, Export/Import XML |
| [`macro-advanced`](.claude/skills/macro-advanced/SKILL.md) | SetVar/SetUserVar, conditionals, CmdDelay, jump targets, XML authoring, Store Group timing |
| [`clone-and-data-transfer`](.claude/skills/clone-and-data-transfer/SKILL.md) | Clone fixture with `/selective`, copy/move pool objects, cue-range copy, cross-show PSR |
| [`effect-programmer`](.claude/skills/effect-programmer/SKILL.md) | Build effects from scratch, layer rate/speed/phase, assign to executors |
| [`world-filter-designer`](.claude/skills/world-filter-designer/SKILL.md) | Create worlds, assign fixtures, configure filter objects, control visibility |
| [`timecode-show-programmer`](.claude/skills/timecode-show-programmer/SKILL.md) | Build timecode shows, assign events to cues, enable/disable tracks |
| [`color-preset-creator`](.claude/skills/color-preset-creator/SKILL.md) | Store universal color presets from RGB values — builds the preset pool |
| [`color-palette-sequence-builder`](.claude/skills/color-palette-sequence-builder/SKILL.md) | Build a cue sequence where each cue references a universal color preset |
| [`hue-palette-creator`](.claude/skills/hue-palette-creator/SKILL.md) | Store 96 universal hue presets (4.101–4.196) using the HSB color model |
| [`hue-sequence-builder`](.claude/skills/hue-sequence-builder/SKILL.md) | Build a 16-cue sequence from an adjacent hue pair — 8 saturation variants per hue |
| [`sequence-executor-assigner`](.claude/skills/sequence-executor-assigner/SKILL.md) | Assign a sequence to a free executor so it appears as a playback fader |
| [`rdm-workflow`](.claude/skills/rdm-workflow/SKILL.md) | RDM discovery → device info → autopatch workflow via MCP |
| [`lua-and-plugins`](.claude/skills/lua-and-plugins/SKILL.md) | Lua 5.2 scripting with `gma.*` namespace, plugin invocation, and reload lifecycle |
| [`psr-show-migration`](.claude/skills/psr-show-migration/SKILL.md) | PSR with pre-flight slot check, fixture ID verification, and post-import diff |
| [`compliance-documentation`](.claude/skills/compliance-documentation/SKILL.md) | Generate SB 132 / insurance audit reports from session telemetry — SAFE_READ only |
| [`volunteer-operations`](.claude/skills/volunteer-operations/SKILL.md) | Three-tier access model, Sunday morning preflight, and incident response for non-programmers |
| [`view-and-layout-designer`](.claude/skills/view-and-layout-designer/SKILL.md) | Custom console views, executor button placement, image assignment, sheet recall |
| [`show-health-check`](.claude/skills/show-health-check/SKILL.md) | Pre-show audit — showfile, presets, executors, cues, parks, DMX. Returns GREEN/AMBER/RED |
| [`busking-template-generator`](.claude/skills/busking-template-generator/SKILL.md) | Build a complete busking template from any patched rig — groups, presets, effects, executor page |
| [`cross-venue-adaptation`](.claude/skills/cross-venue-adaptation/SKILL.md) | Adapt show to a new venue rig — patch comparison, group remapping, preset scope verification |
| [`training-mode`](.claude/skills/training-mode/SKILL.md) | Annotated SAFE_READ console tour for students, church volunteers, and IATSE training programs |
| [`remote-monitoring`](.claude/skills/remote-monitoring/SKILL.md) | Continuous SAFE_READ polling — show change detection, alert conditions, broadcast and architectural protocols |

Skills are loaded on demand via `ma2://skills/{skill_id}` resource or injected by the orchestrator. Use `list_skills` / `get_skill` tools to browse and inspect them at runtime.

## Client Setup

### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "gma2": {
      "command": "uv",
      "args": ["--directory", "/path/to/ma2-onPC-MCP", "run", "python", "-m", "src.server"],
      "env": {
        "GMA_HOST": "192.168.1.100",
        "GMA_USER": "administrator",
        "GMA_PASSWORD": "admin"
      }
    },
    "time": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-time"]
    }
  }
}
```

The `time` server provides accurate ISO 8601 timestamps for markdown front matter — required by [`.claude/rules/markdown-frontmatter.md`](.claude/rules/markdown-frontmatter.md). It is also registered automatically for Claude Code CLI via `.mcp.json` and for VS Code via `vscode-mcp-provider/`.

### VS Code

The `vscode-mcp-provider/` directory contains a VS Code extension that registers the grandMA2 MCP server for AI assistant discovery.

```bash
cd vscode-mcp-provider
npm install && npm run compile
# Then install in VS Code (F5 to debug, or package with vsce)
```

See [`vscode-mcp-provider/README.md`](vscode-mcp-provider/README.md) for full details.

## Safety System

GrandPA2-Buddy enforces a **3-layer permission model** — effective permissions are the intersection of all three layers, so no single layer can expand privileges beyond what the others allow:

```
scope ∩ ma2_rights ∩ console_floor = FINAL AUTHORITY
```

### Layer 1 — OAuth Scope ([`src/auth.py`](src/auth.py))

Every MCP tool is decorated with `@require_scope(OAuthScope.*)`. The OAuth layer maps six cumulative scope tiers to grandMA2 console users, each with a fixed native rights level. Set `GMA_SCOPE` to control which tier the session operates at:

| `GMA_SCOPE` | Console user | MA2 Rights | Permitted operations |
|-------------|-------------|-----------|---------------------|
| `tier:0` | `guest` | None (0) | Read-only — list, info, cd |
| `tier:1` | `operator` | Playback (1) | Go, Flash, Off, timecode |
| `tier:2` | `presets_editor` | Presets (2) | Set attributes, apply/store presets |
| `tier:3` | `programmer` | Program (3) | Store cues, groups, sequences, macros |
| `tier:4` | `tech_director` | Setup (4) | Patch, fixture import, console setup |
| `tier:5` | `administrator` | Admin (5) | User management, show load/delete |

Bootstrap the six console users on a fresh show with `python scripts/bootstrap_console_users.py` (only `Administrator` and `Guest` exist natively).

### Layer 2 — MA2 Native Rights ([`src/rights.py`](src/rights.py))

All 198 tools are mapped in `_OPERATION_MIN_RIGHT` to a minimum `MA2Right` tier (NONE through ADMIN). At runtime, `_handle_errors` derives the session's `MA2Right` from the OAuth scope tier via `get_session_ma2_right()` and calls `is_permitted()` before any Telnet command is sent. A tool whose required right exceeds the session right returns `{"blocked": True, "required_ma2_right": "..."}`.

The `check_permission()` utility provides a unified gate combining scope and rights checks in a single call. The full tool-to-right mapping is published in [`doc/ma2-rights-matrix.json`](doc/ma2-rights-matrix.json).

### Layer 3 — Console Floor (grandMA2 enforcement)

The Telnet session authenticates as a console user whose native rights grandMA2 enforces independently. Commands that exceed that user's rights are rejected with `Error #72` — an irrevocable floor that applies regardless of what Layer 1 or 2 permit.

### Risk Tiers

Every grandMA2 keyword is classified into one of three risk tiers. The `_handle_errors` decorator infers the tier at decoration time for telemetry, and `DESTRUCTIVE` tools require an explicit `confirm_destructive=True` parameter:

| Tier | Description | Examples |
|------|-------------|----------|
| `SAFE_READ` | Read-only queries | `Info`, `List`, `CmdHelp`, `ChangeDest` |
| `SAFE_WRITE` | Reversible state changes | `Go`, `At`, `Clear`, `Park`, `SelFix` |
| `DESTRUCTIVE` | Data mutation or loss | `Delete`, `Store`, `Copy`, `Move`, `Shutdown` |

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `GMA_SCOPE` | `gma2:discover gma2:state:read` | Granted OAuth scopes (space-separated or `tier:N`) |
| `GMA_AUTH_BYPASS` | `0` | Set `1` to bypass scope checks (dev/test only) |
| `GMA_RIGHTS_BYPASS` | `0` | Set `1` to bypass rights checks (dev/test only) |
| `GMA_LICENSE_TIER` | `community` | Active license tier: `community`, `professional`, `enterprise` |
| `GMA_LICENSE_BYPASS` | `0` | Set `1` to bypass tier checks (dev/test only) |

> [!IMPORTANT]
> **Command injection prevention:** Line breaks (`\r`, `\n`) are rejected before any command reaches the console. The telnet client strips them as a defense-in-depth measure.

### Network Hardening

The 3-layer model protects against the AI agent but **not** against direct network access to port 30000. The supported deployment co-locates the MCP server on the same machine as grandMA2 onPC with a host firewall restricting Telnet to loopback:

```bash
# Lock down TCP 30000 to localhost (MA-Net2 multicast unaffected)
sudo bash scripts/lockdown_firewall.sh --apply
```

The server's `_check_network_security()` function warns at startup if `GMA_HOST` is not loopback, any bypass variable is enabled, or factory-default credentials are in use. See [`doc/network-topology.md`](doc/network-topology.md) for the full deployment diagram.

### Keyword Classification

The vocabulary classifies all **158 grandMA2 keywords** into categories:

| Category | Count | Description | Examples |
|----------|-------|-------------|----------|
| `OBJECT` | 56 | Console objects (nouns) | Channel, Fixture, Group, Preset, Executor |
| `FUNCTION` | 89 | Actions (verbs) | Store, Delete, Go, At, Kill, List, Info |
| `HELPING` | 7 | Syntax connectors | And, Thru, Fade, Delay, If |
| `SPECIAL_CHAR` | 6 | Operator symbols | Plus `+`, Minus `-`, Dot `.`, Slash `/` |

<details>
<summary>Object Keyword metadata</summary>

Object Keywords carry additional metadata from live telnet verification:

| Field | Description |
|-------|-------------|
| `context_change` | Whether the keyword changes the `[default]>` prompt context |
| `canonical` | Console-normalized spelling (e.g., `DMX` → `Dmx`) |
| `notes` | Behavior notes from live telnet testing |

Of the 56 Object Keywords: 53 change the default prompt context and 3 don't (`Full`, `Normal`, `Zero` — these set dimmer values). `Channel` and `Default` have `context_change=True`; their notes describe resetting the *default keyword*, not the prompt context.

**Console aliases:**

| Input | Resolves To |
|-------|-------------|
| `DMX` | `Dmx` |
| `DMXUniverse` | `DmxUniverse` |
| `Sound` | `SoundChannel` |
| `RDM` | `RdmFixtureType` |

</details>

<details>
<summary><code>classify_token()</code> example</summary>

```python
from src.vocab import build_v39_spec, classify_token

spec = build_v39_spec()

result = classify_token("Delete", spec)
# result.risk == RiskTier.DESTRUCTIVE
# result.canonical == "Delete"
# result.category == KeywordCategory.FUNCTION

result = classify_token("Channel", spec)
# result.risk == RiskTier.SAFE_WRITE
# result.category == KeywordCategory.OBJECT

result = classify_token("DMX", spec)
# result.canonical == "Dmx"  (alias resolution)
```

</details>

## RAG Pipeline

```mermaid
graph LR
    A[Crawl] --> B[Chunk] --> C[Embed] --> D[Store<br/>SQLite] --> E[Query] --> F[Rerank]

    style A fill:#264653,color:#fff
    style B fill:#2a9d8f,color:#fff
    style C fill:#e9c46a,color:#000
    style D fill:#f4a261,color:#000
    style E fill:#e76f51,color:#fff
    style F fill:#e63946,color:#fff
```

```bash
# Ingest repository with real embeddings
uv run python scripts/rag_ingest.py --provider github -v

# Semantic search
uv run python scripts/rag_query.py "store cue with fade" -v

# Text-only keyword search (no token needed)
uv run python scripts/rag_query.py "store cue with fade"
```

| Provider | Flag | Requires | Dimensions |
|----------|------|----------|------------|
| GitHub Models | `--provider github` | `GITHUB_MODELS_TOKEN` | 1536 |
| OpenRouter | `--provider openrouter` | `OPENROUTER_API_KEY` | 2048 |
| Zero-vector stub | `--provider zero` | Nothing (for testing) | 1536 |
| Auto-detect | *(no flag)* | Uses GitHub if token set, otherwise zero-vector | — |

> [!WARNING]
> GitHub Models (1536-dim) and OpenRouter (2048-dim) embeddings are **incompatible** in the same store. Use `rag_upgrade_embeddings.py --re-embed-all` when switching providers.

<details>
<summary>Pipeline stages</summary>

**Ingest**

| Stage | Module | Description |
|-------|--------|-------------|
| Crawl | [`rag/ingest/crawl_repo.py`](rag/ingest/crawl_repo.py) | Walk repo files, respect ignore patterns |
| Chunk | [`rag/ingest/chunk.py`](rag/ingest/chunk.py) | Split into overlapping token-bounded chunks |
| Extract | [`rag/ingest/extract.py`](rag/ingest/extract.py) | Extract symbol names (functions, classes, headings) |
| Embed | [`rag/ingest/embed.py`](rag/ingest/embed.py) | Generate vectors via GitHub Models or OpenRouter API |
| Store | [`rag/store/sqlite.py`](rag/store/sqlite.py) | Write chunks + vectors to SQLite |

**Retrieve**

| Stage | Module | Description |
|-------|--------|-------------|
| Query | [`rag/retrieve/query.py`](rag/retrieve/query.py) | Embed query, cosine similarity search |
| Rerank | [`rag/retrieve/rerank.py`](rag/retrieve/rerank.py) | Sort and filter results by relevance |

</details>

<details>
<summary>Chunking strategies</summary>

| Language | Strategy | Boundary |
|----------|----------|----------|
| Python | AST-based | Top-level `def`/`class` boundaries via `ast.parse` |
| Markdown | Heading-based | `#` heading lines |
| Other | Line-based | Fixed-size line windows with overlap |

Defaults: max 1200 tokens/chunk, 20-line overlap. Configured in [`rag/config.py`](rag/config.py).

</details>

## Console Navigation

The navigation system combines three layers to discover console state via telnet:

1. **Command builder** (`changedest()`) generates cd strings with MA2 dot notation
2. **Telnet client** sends the command and captures the raw response
3. **Prompt parser** extracts the current location from the response

<details>
<summary>Prompt parsing patterns</summary>

| Pattern | Example | Parsed |
|---------|---------|--------|
| Bracket prompt | `[Group 1]>` | location=`Group 1`, type=`Group`, id=`1` |
| Dot notation | `[Group.1]>` | location=`Group.1`, type=`Group`, id=`1` |
| Compound ID | `[Preset.4.1]>` | location=`Preset.4.1`, type=`Preset`, id=`4.1` |
| Trailing slash | `[Sequence 3]>/` | location=`Sequence 3`, type=`Sequence`, id=`3` |
| Angle bracket | `Root>` | location=`Root`, type=`Root` |

</details>

<details>
<summary>List output parsing</summary>

After cd-ing into a destination, `list` returns tabular output. The parser automatically detects headers and maps columns.

| Field | Description |
|-------|-------------|
| `object_type` | Type name (e.g. `Group`, `UserImage`) |
| `object_id` | Numeric ID within the parent |
| `name` | Display name |
| `columns` | Dict mapping extra header names to values |
| `raw_line` | Full original line for manual inspection |

</details>

## Tree Scanner

[`scripts/scan_tree.py`](scripts/scan_tree.py) recursively walks the grandMA2 object tree via Telnet, building a complete JSON map of every node.

```bash
# Quick scan (depth 4)
uv run python scripts/scan_tree.py --max-depth 4 --output scan_test.json

# Full scan (depth 20)
uv run python scripts/scan_tree.py --max-depth 20 --output scan_full.json

# Resume an interrupted scan
uv run python scripts/scan_tree.py --max-depth 20 --output scan_full.json --resume
```

<details>
<summary>Scanner options</summary>

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | from `.env` | Console IP address |
| `--port` | 30000 | Telnet port |
| `--max-depth` | 20 | Maximum recursion depth |
| `--max-nodes` | 0 | Stop after N nodes (0 = unlimited) |
| `--max-index` | 60 | Fallback index limit |
| `--failures` | 3 | Stop branch after N consecutive missing indexes |
| `--output` | `scan_output.json` | Output JSON file path |
| `--delay` | 0.08 | Seconds between commands |
| `--resume` | false | Resume scan from progress file |

</details>

<details>
<summary>Optimizations & resilience</summary>

**Speed optimizations:**
- Known leaf-type shortcutting — skips cd+list for known leaf types
- Smart gap probing — only fills gaps ≤5 between known IDs
- Duplicate detection — compares raw `list` signatures to skip identical subtrees
- Consecutive empty leaf early exit — stops after 10 empty slots

**Resilience:**
- Auto-reconnect with full path recovery
- Progressive save to JSONL after each root branch
- Resume support across sessions
- Heartbeat logging and branch timeouts

</details>

## Command Builders

The command builder layer ([`src/commands/`](src/commands/)) generates grandMA2 command strings as pure functions — no network I/O. **264 exported functions** (272 exports including 8 constants) covering navigation, selection, playback, values, store, delete, assign, label, and more.

> grandMA2 syntax: `[Function] [Object]` — keywords are **Function** (verbs), **Object** (nouns), or **Helping** (prepositions).

<details>
<summary><strong>Full command builder reference</strong></summary>

### Navigation

| Function | Output |
|----------|--------|
| `changedest("/")` | `cd /` |
| `changedest("..")` | `cd ..` |
| `changedest("Group", 1)` | `cd Group.1` |
| `changedest("Preset", "4.1")` | `cd Preset.4.1` |

### Object Keywords

| Function | Output |
|----------|--------|
| `fixture(34)` | `fixture 34` |
| `group(3)` | `group 3` |
| `preset("color", 5)` | `preset 4.5` |
| `cue(5)` | `cue 5` |
| `sequence(3)` | `sequence 3` |
| `executor(1)` | `executor 1` |
| `dmx(101, universe=2)` | `dmx 2.101` |
| `attribute("Pan")` | `attribute "Pan"` |

### Selection & Clear

| Function | Output |
|----------|--------|
| `select_fixture(1, 10)` | `selfix fixture 1 thru 10` |
| `select_fixture([1, 3, 5])` | `selfix fixture 1 + 3 + 5` |
| `clear()` | `clear` |
| `clear_all()` | `clearall` |

### Store

| Function | Output |
|----------|--------|
| `store("macro", 5)` | `store macro 5` |
| `store_cue(1, merge=True)` | `store cue 1 /merge` |
| `store_preset("dimmer", 3)` | `store preset 1.3` |
| `store_group(1)` | `store group 1` |

### Playback

| Function | Output |
|----------|--------|
| `go("executor", 3)` | `go executor 3` |
| `go_executor(3)` | `go executor 3` |
| `go_back("executor", 3)` | `goback executor 3` |
| `go_back_executor(3)` | `goback executor 3` |
| `goto(3)` | `goto cue 3` |
| `go_sequence(1)` | `go+ sequence 1` |
| `go_macro(2)` | `go macro 2` |
| `on_executor(3)` | `on executor 3` |
| `off_executor(3)` | `off executor 3` |
| `flash_executor(3)` | `flash executor 3` |
| `swop_executor(3)` | `swop executor 3` |
| `solo_executor(3)` | `solo executor 3` |
| `top_executor(3)` | `top executor 3` |
| `stomp_executor(3)` | `stomp executor 3` |
| `release_executor(3)` | `release executor 3` |
| `goto_cue(1, 5)` | `goto cue 5 sequence 1` |
| `pause_sequence(1)` | `pause sequence 1` |
| `goto_timecode(1, "00:01:30:00")` | `goto timecode 1 "00:01:30:00"` |
| `go_fast_forward()` | `>>>` |
| `go_fast_forward(executor=[1, 2, 3])` | `>>> executor 1 + 2 + 3` |
| `go_fast_back()` | `<<<` |
| `go_fast_back(executor=[2, 4])` | `<<< executor 2 + 4` |
| `load_next()` | `loadnext` |
| `load_prev()` | `loadprev` |
| `def_go_forward()` | `defgoforward` |
| `def_go_back()` | `defgoback` |
| `def_go_pause()` | `defgopause` |
| `solo()` | `solo` |
| `blind()` | `blind` |
| `freeze()` | `freeze` |
| `blackout()` | `blackout` |

### At (Values)

| Function | Output |
|----------|--------|
| `at(75)` | `at 75` |
| `at_full()` | `at full` |
| `attribute_at("Pan", 20)` | `attribute "Pan" at 20` |
| `fixture_at(2, 50)` | `fixture 2 at 50` |

### Copy, Move, Delete

| Function | Output |
|----------|--------|
| `copy("group", 1, 5)` | `copy group 1 at 5` |
| `move("group", 5, 9)` | `move group 5 at 9` |
| `delete("cue", 7)` | `delete cue 7` |

### Label & Appearance

| Function | Output |
|----------|--------|
| `label("group", 3, "All Studiocolors")` | `label group 3 "All Studiocolors"` |
| `appearance("preset", "0.1", red=100)` | `appearance preset 0.1 /r=100` |
| `appearance("group", 1, color="FF0000")` | `appearance group 1 /color=FF0000` |

> [!NOTE]
> Appearance RGB uses **0–100** percentage scale (not 0–255). HSB: hue 0–360, sat/bright 0–100.

### Import / Export

| Function | Output |
|----------|--------|
| `export_object("Group", 1, "mygroups")` | `export Group 1 "mygroups"` |
| `import_object("mygroups", "Group", 5)` | `import "mygroups" at Group 5` |

### Variables

| Function | Output |
|----------|--------|
| `set_var("myvar", 42)` | `setvar "myvar" 42` |
| `set_user_var("speed", 100)` | `setuservar "speed" 100` |

</details>

## Project Structure

```
ma2-onPC-MCP/
├── src/
│   ├── server.py                           # FastMCP server startup + 17 resources + 13 prompts
│   ├── tools_community.py                  # 20 COMMUNITY tools (free tier, public)
│   ├── private/                            # Git submodule — paid-tier tools
│   │   ├── tools_professional.py           # 124 PROFESSIONAL tools
│   │   ├── tools_enterprise.py             # 20 ENTERPRISE tools
│   │   └── server_orchestration_tools.py   # 34 ENTERPRISE agentic tools (110–144)
│   │
│   │   # Orchestration & Memory
│   ├── orchestrator.py                     # Multi-agent task runner + session memory
│   ├── task_decomposer.py                  # NL goal → ordered SubTask plan
│   ├── agent_memory.py                     # WorkingMemory + LongTermMemory (SQLite)
│   ├── console_state.py                    # ConsoleStateSnapshot (19-gap hydration)
│   ├── pool_name_index.py                  # Object name/ID registry (zero-cost resolve)
│   ├── telemetry.py                        # Per-tool invocation recorder (tool_invocations table)
│   ├── skill.py                            # Skill dataclass + SkillRegistry (versioned playbooks)
│   ├── skill_improver.py                   # SkillImprover: repair suggestions + promotion candidates
│   │
│   │   # Security & Auth
│   ├── auth.py                             # OAuth 2.1 scope enforcement
│   ├── credentials.py                      # OAuth tier → console credentials
│   ├── rights.py                           # MA2 native rights + telnet feedback
│   ├── session_manager.py                  # Telnet session pool (LRU + keepalive)
│   │
│   │   # Core I/O & Parsing
│   ├── telnet_client.py                    # Async Telnet (telnetlib3, injection prevention)
│   ├── navigation.py                       # cd + list + scan orchestration
│   ├── prompt_parser.py                    # Telnet prompt & tabular list parser
│   ├── vocab.py                            # 158 keywords, risk tiers, functional domains
│   │
│   │   # Command Builders & ML
│   ├── commands/                           # 262 exported command-builder functions
│   │   ├── busking.py                      # Busking/performance builders (6 functions)
│   │   ├── objects/                        # Object keywords (9 modules)
│   │   └── functions/                      # Function keywords (17 modules)
│   └── categorization/                     # ML tool categorization (K-Means)
│
├── rag/                                    # RAG pipeline
│   ├── config.py                           # Pipeline constants (chunk size, top-k, rate limits)
│   ├── types.py                            # Chunk, DocumentRecord, RagHit dataclasses
│   ├── ignore.py                           # File ignore patterns
│   ├── ingest/                             # crawl → chunk → embed → store
│   │   ├── crawl_repo.py                   # Walk repo files, respect ignore patterns
│   │   ├── crawl_web.py                    # Crawl HTML pages (robots.txt aware)
│   │   ├── chunk.py                        # AST/heading/line-based chunking + merge
│   │   ├── extract.py                      # Symbol extraction (functions, classes, headings)
│   │   ├── embed.py                        # GitHub Models, OpenRouter, ZeroVector providers
│   │   └── index.py                        # Orchestrate ingest pipeline
│   ├── retrieve/                           # query → rerank
│   │   ├── query.py                        # Embed query, cosine/text search, graph enrichment
│   │   └── rerank.py                       # Keyword-overlap + tool body reranking
│   ├── store/                              # SQLite vector store (rag.db)
│   │   └── sqlite.py                       # RagStore: upsert, search, FTS5, stats
│   └── utils/                              # Helpers (hash, lang detection, text normalization)
│
├── src/knowledge_graph/                    # Knowledge graph layer
│   ├── schema.py                           # NodeType (10), EdgeType (11), Node/Edge dataclasses
│   ├── store.py                            # GraphStore: SQLite CRUD, freshness, node_count
│   ├── query.py                            # QueryEngine: BFS/DFS, neighbor lookup, multi-hop
│   ├── planning.py                         # PlanningQueries: goal enrichment, plan validation
│   ├── graph_rag.py                        # GraphRAG: entity extraction + graph-augmented retrieval
│   └── sync.py                             # sync_snapshot(): hydrate graph from ConsoleStateSnapshot
│
├── scripts/
│   ├── rag_ingest.py                       # Ingest repo (zero-vector or real embeddings)
│   ├── rag_ingest_web.py                   # Crawl MA2 help docs (daily batches)
│   ├── rag_ingest_mcp_sdk.py               # Ingest MCP SDK source (~110 files)
│   ├── rag_query.py                        # Query RAG store from CLI
│   ├── bootstrap_console_users.py          # Create 5 console user accounts
│   ├── create_matricks_library.py          # MAtricks combinatorial library (625 items)
│   ├── create_filter_library.py            # Filter library XMLs (168 items with VTE)
│   └── strategic_scan.py                   # Fast 4-phase console tree scan (~24 min)
├── tests/                                  # 3353 tests (2026-04-08)
├── doc/                                    # Command builders ref + cd-tree docs
├── vscode-mcp-provider/                    # VS Code MCP extension
└── .claude/                                # Skills (playbooks) + scoped rules
    ├── skills/                             # 34 agent instruction modules
    └── rules/                              # 7 scoped rule files (loaded on demand)
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `mcp>=1.21.0` | Model Context Protocol server framework |
| `python-dotenv>=1.0.0` | Load `.env` configuration |
| `telnetlib3>=2.0.8` | Async Telnet client |
| `beautifulsoup4>=4.12.0` | HTML parsing for RAG web crawler |
| `numpy>=1.26.0` | K-Means clustering for tool categorization |
| `pytest>=9.0.1` | Testing (dev) |
| `pytest-asyncio>=1.3.0` | Async test support (dev) |

Requires **Python ≥ 3.12**.

## Development

```bash
# Run all tests
make test                             # or: python -m pytest -v

# Run a subset
python -m pytest tests/test_vocab.py  # single file
python -m pytest tests/test_rag_*.py  # RAG tests only

# Start MCP server
uv run python -m src.server

# Install git hooks (pre-commit, pre-push, stop hook)
make install-hooks

# Login test
python scripts/main.py
```

### Git Hooks

| Hook | Trigger | Action |
|------|---------|--------|
| `pre-commit` | Every commit | Zero-vector RAG ingest (fast, no API calls) |
| `pre-push` | Every push | Runs `pytest -x -q` — blocks push on test failure |
| `stop-git-check.sh` | Claude Code Stop event | Flags uncommitted/unpushed work |

The stop hook is configured in `.claude/settings.json` (project-level) so all collaborators inherit it automatically.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Connection fails | Verify console IP/port, check Telnet is enabled, check firewall |
| Authentication errors | Confirm username/password, check user exists on console |
| Command not working | Verify syntax against MA2 User Manual, ensure objects exist |
| RAG ingest 401 | Verify `GITHUB_MODELS_TOKEN` has `models:read` scope |
| RAG query empty | Run [`scripts/rag_ingest.py`](scripts/rag_ingest.py) first, check `rag/store/rag.db` exists |

## Acknowledgments

This project is derived from [gma2-mcp](https://github.com/chienchuanw/gma2-mcp) by **chienchuanw**, whose foundation work (Nov–Dec 2025) provided the initial grandMA2 Telnet integration that this project builds upon.

## Documentation

- [CHANGELOG.md](CHANGELOG.md) — version history from v2.0.0 to current
- [CONTRIBUTING.md](CONTRIBUTING.md) — contribution guidelines
- [SECURITY.md](SECURITY.md) — security policy and vulnerability reporting
- [doc/network-topology.md](doc/network-topology.md) — deployment diagram and firewall setup (`sudo bash scripts/lockdown_firewall.sh --apply`)
- [doc/responsibility-map.md](doc/responsibility-map.md) — module responsibility boundaries
- [doc/tool-surface-tiers.md](doc/tool-surface-tiers.md) — tool classification by risk and scope

## License

[Business Source License 1.1](LICENSE)
