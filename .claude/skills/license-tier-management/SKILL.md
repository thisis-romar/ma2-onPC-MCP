---
title: License Tier Management
description: License tier feature gating implementation — tier classification, environment variables, and adding tool tiers
version: 1.0.0
created: 2026-04-07T15:14:23Z
last_updated: 2026-04-07T15:14:23Z
---

# License Tier Management

## Tier Classification

All 198 MCP tools are classified into three license tiers:

| Tier | Cost | Tool count | Examples |
|------|------|-----------|---------|
| `COMMUNITY` | Free | ~30 | `navigate_console`, `get_object_info`, `playback_action`, `set_intensity` |
| `PROFESSIONAL` | Paid | ~120 | Store/copy/delete, presets, sequences, macros, effects, patch, show mgmt |
| `ENTERPRISE` | Premium | ~50 | RAG search, orchestration, skill system, agent harness, ML categorisation |

## Environment Variables

| Var | Default | Effect |
|-----|---------|--------|
| `GMA_LICENSE_TIER` | `community` | Active tier: `community`, `professional`, `enterprise` |
| `GMA_LICENSE_BYPASS` | `0` | Set `1` to bypass tier checks (dev/test only) |

## How It Works

`_handle_errors` in `src/server.py` reads `TOOL_LICENSE_TIERS` (from `src/license_tiers.py`) at decoration time. Tools not in the map default to COMMUNITY. When a tool's tier exceeds the active tier, it returns `{"blocked": True, "license_required": "...", "current_tier": "..."}`.

## Adding a Tool's Tier

Add an entry to `TOOL_LICENSE_TIERS` in `src/license_tiers.py`. Omit COMMUNITY tools (they are the default).
