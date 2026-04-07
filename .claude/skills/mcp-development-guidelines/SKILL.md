---
title: MCP Development Guidelines
description: Contributor workflow for adding new MCP tools, resources, prompts, command builders, and tests
version: 1.0.0
created: 2026-04-07T15:14:23Z
last_updated: 2026-04-07T15:14:23Z
---

# MCP Development Guidelines

## Adding a new MCP tool

1. Add command builder in `src/commands/` — pure, returns `str`, no I/O.
2. Export from `src/commands/__init__.py`.
3. Register in `src/server.py` with `@mcp.tool()` and `@_handle_errors`.
4. Apply `@require_scope(OAuthScope.X)` — see `doc/ma2-rights-matrix.json`.
5. Add an entry to `_OPERATION_MIN_RIGHT` in `src/rights.py` mapping the tool function name to `MA2Right` tier. This is **required** — `_handle_errors` enforces it at runtime.
6. If DESTRUCTIVE, accept `confirm_destructive: bool = False` and gate on it.
7. Assign a license tier in `src/license_tiers.py` (omit for COMMUNITY / free).
8. Add tests in `tests/test_<feature>.py`.

## Adding a new MCP resource

- Use `@mcp.resource("ma2://category/name")` for static docs or URI-addressable state.
- Use `@mcp.resource("ma2://category/{param}")` for templated dynamic resources.
- Resources must be read-only — no console side-effects.

## Adding a new MCP prompt

- Use `@mcp.prompt()` for user-initiated workflow templates.
- Prompts accept arguments and may reference resources.
- Prompts must not themselves execute destructive operations — they orchestrate tools.

## Command builders

- Pure functions only — no imports from `src.telnet_client`, `src.navigation`, or `src.server`.
- Return raw grandMA2 command strings, e.g. `"Store Cue 1 Sequence 99 /merge"`.
- See `.claude/rules/ma2-conventions.md` for quoting, path, and timing rules.

## Tests

- Unit tests import command builders or vocab directly and assert on returned strings.
- No live console required; live tests are in `tests/test_live_integration.py` (skipped by default).
- Use `@pytest.mark.asyncio` for async tests.
- Current counts (2026-04-04): **3141 tests** (unit + live integration).
