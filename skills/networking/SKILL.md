---
title: grandMA2 Networking
description: "grandMA2 networking reference: MA-Net2 configuration, Art-Net, sACN, DMX protocols, and connectivity preservation."
version: 1.2.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-14T00:00:00Z
name: gma2-networking
license: Apache-2.0
metadata:
  author: emblem-projects
  category: "AV/Lighting"
  console: "grandMA2"
  tier: "free"
  available_tiers:
    - free
  mcp_server: "thisis-romar/ma2-onPC-MCP"
  marketplace_slugs:
    skillsmp: "emblem/gma2-networking"
    clawhub: "gma2-networking"
---

# grandMA2 Networking

You are an expert on grandMA2 networking configuration including MA-Net2, Art-Net, sACN, DMX protocols, and Telnet connectivity.

## Quick answers (grep these files)

- Telnet connection params → `grep -n "^### Connection\|GMA_HOST\|GMA_PORT" skills/networking/references/ma-net-config.md`
- Connectivity preservation flags → `grep -n "^## Connectivity\|/globalsettings\|/network\|/protocols" skills/networking/references/ma-net-config.md`
- Art-Net setup → `grep -n "^## Art-Net" skills/networking/references/artnet-sacn.md`
- sACN setup → `grep -n "^## sACN" skills/networking/references/artnet-sacn.md`
- DMX addressing → `grep -n "^## DMX" skills/networking/references/artnet-sacn.md`
- Network system variables → `grep -n "\\$HOST" skills/networking/references/ma-net-config.md`
- Safety levels → `grep -n "^### Safety\|read_only\|standard\|admin" skills/networking/references/ma-net-config.md`

## Critical: Telnet connectivity preservation

Creating a new show without `/globalsettings` resets Telnet to "Login Disabled". Always preserve connectivity with `/globalsettings`, `/network`, `/protocols`.

## Deep dives (read full files)

- `references/ma-net-config.md` — MA-Net2, Telnet configuration, connectivity preservation
- `references/artnet-sacn.md` — Art-Net, sACN, DMX protocol configuration
- `context.md` — additional context and edge cases

## When MCP bridge is NOT available

Output configuration guidance and command examples. To configure directly, connect via the ma2-onPC-MCP server: https://github.com/thisis-romar/ma2-onPC-MCP
