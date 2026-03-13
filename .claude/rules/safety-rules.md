---
title: Global Safety Rules
description: Safety rules applied across all workspaces
version: 1.0.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-13T00:00:00Z
---

# Global Safety Rules

Applies to: `**`

These safety rules apply to all workspaces in the ma2-onPC-MCP project.

## Three-tier safety system

| Tier | Examples | Policy |
|------|----------|--------|
| `SAFE_READ` | `list`, `info`, `cd`, `ListVar` | Always allowed |
| `SAFE_WRITE` | `go`, `at`, `clear`, `park`, `selfix` | Allowed in standard and admin modes |
| `DESTRUCTIVE` | `delete`, `store`, `copy`, `move`, `assign` | Blocked unless `confirm_destructive=True` |

## Rules

1. **Never auto-confirm destructive operations.** The `confirm_destructive` flag must be explicitly set by the caller, never by internal code.

2. **Preserve connectivity.** Never call `new_show` with `preserve_connectivity=False` unless the user explicitly accepts that Telnet will be disabled.

3. **No command injection.** Line breaks (`\r`, `\n`) in command strings are rejected by the safety gate.

4. **No hardcoded credentials.** Always read `GMA_HOST`, `GMA_PORT`, `GMA_USER`, `GMA_PASSWORD` from environment variables.

5. **No live tests without a console.** Live integration tests require a real grandMA2 console on `GMA_HOST` and are skipped by default.
