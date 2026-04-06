---
title: Server.py Modularization Plan
description: Proposed split of the 12K-line server.py monolith into focused submodules
version: 1.0.0
created: 2026-04-06T21:43:47Z
last_updated: 2026-04-06T21:43:47Z
---

# Server.py Modularization Plan

## Problem

`src/server.py` is 12,095 lines with 164 tool implementations, 18 resources,
13 prompts, plus helpers, configuration, and the MCP server instance. While
internally consistent, the monolith makes navigation, review, and IDE
performance challenging.

## Current Structure (74 sections)

| Lines | Section | Tool Range | Proposed Module |
|-------|---------|-----------|-----------------|
| 1-505 | Imports, env config, logging | — | `src/server.py` (keep) |
| 506-526 | Environment variables | — | `src/server.py` (keep) |
| 527-546 | FastMCP instance + instructions | — | `src/server.py` (keep) |
| 547-676 | Session pool, telemetry, get_client, _handle_errors | — | `src/server_core.py` |
| 677-750 | Private helpers (object probing) | — | `src/server_core.py` |
| 751-1939 | MCP Tools 1-19 | navigate, list, info, playback, intensity, preset | `src/tools_core.py` |
| 1940-2812 | Composite Tools 20-27 | query_object_list, list_vars, playback, variables | `src/tools_composite.py` |
| 2813-2890 | RAG Search | search_codebase | `src/tools_rag.py` |
| 2891-4042 | Tools 30-44 | executor, page, timecode, tempfader, park | `src/tools_extended.py` |
| 4043-4684 | Tools 45-52 | busking, effects, selection, attribute | `src/tools_quickstart.py` |
| 4685-4895 | Tools 53-54 | import, export | `src/tools_importexport.py` |
| 4896-5130 | Tools 74-76 | fixture type import, layer XML | `src/tools_importexport.py` |
| 5131-5272 | Tools 55-56 | fixture/sequence discovery | `src/tools_discovery.py` |
| 5273-5692 | Tools 57-64 | high-impact tier 1 | `src/tools_tier1.py` |
| 5693-6636 | Tools 65-69 | setup & library tier 2 | `src/tools_tier2.py` |
| 6637-6874 | Tools 70-73 | fixture patching | `src/tools_patch.py` |
| 6875-6906 | Wildcard discovery | — | `src/tools_discovery.py` |
| 6907-7190 | Pool availability | — | `src/tools_discovery.py` |
| 7191-7195 | Server startup | — | `src/server.py` (keep) |
| 7196-7574 | ML Categorization 83-86 | recluster, similar, categorize, suggest | `src/tools_categorization.py` |
| 7575-7739 | User Management 98-100 | users, login, sessions | `src/tools_users.py` |
| 7740-7974 | Quick-wins 102-109 | — | `src/tools_extended.py` |
| 7975-10925 | Resources, Prompts, Orchestration wrappers | — | `src/tools_orchestration.py` |
| 10928-11094 | Agent Harness | run_agent_goal, plan_agent_goal, resume_agent_run | `src/tools_agent.py` |
| 11095-11860 | PSR Tools | partial show read | `src/tools_psr.py` |
| 11861-12095 | Startup, security checks, main() | — | `src/server.py` (keep) |

## Shared State (5 singletons)

These must remain accessible to all tool modules:

| Singleton | Current Location | Proposed |
|-----------|-----------------|----------|
| `mcp` (FastMCP instance) | line 527 | `src/server.py` — import in submodules |
| `_session_manager` | line 548 | `src/server_core.py` — export `get_client()` |
| `_telemetry_singleton` | line 552 | `src/server_core.py` — export `_get_telemetry()` |
| `_handle_errors` decorator | line 598 | `src/server_core.py` — export for all tool modules |
| `_vocab_spec` | line 524 | `src/server_core.py` — export for safety classification |

## Split Strategy

**Phase 1 (low risk):** Extract `_handle_errors`, `get_client()`, `_get_telemetry()` into `src/server_core.py`. All tool modules import from there.

**Phase 2 (medium risk):** Move tool implementations into submodules. Each submodule imports `mcp` from `src/server` and registers tools via `@mcp.tool()`. `src/server.py` becomes a thin orchestrator that imports all submodules.

**Phase 3 (medium risk):** Move resources and prompts into `src/server_resources.py` and `src/server_prompts.py`.

## Prerequisites

- All 198 tools must have the same `@mcp.tool() → @require_scope() → @_handle_errors` decorator stacking
- Circular import prevention: submodules import from `server_core`, never from `server`
- Architecture hygiene test must continue to pass after split
- No changes to MCP protocol behavior or tool registration order

## Risk Assessment

- **NOT recommended for a single session** — 12K lines, 198 tools, 74 sections
- Recommend incremental extraction: one module per session, with full test runs
- Start with Phase 1 (`server_core.py`) since it has zero tool registration changes

## Status

**DEFERRED** — documented for future implementation. The monolith works correctly today.
