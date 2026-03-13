---
title: grandMA2 Networking
description: "grandMA2 networking reference: MA-Net2 configuration, Art-Net, sACN, DMX protocols, and connectivity preservation."
version: 1.0.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-13T00:00:00Z
name: gma2-networking
license: Apache-2.0
metadata:
  author: emblem-projects
  category: "AV/Lighting"
  console: "grandMA2"
  tier: "free"
  mcp_server: "thisis-romar/ma2-onPC-MCP"
  marketplace_slugs:
    skillsmp: "emblem/gma2-networking"
    clawhub: "gma2-networking"
---

# grandMA2 Networking

You are an expert on grandMA2 networking configuration including MA-Net2, Art-Net, sACN, DMX protocols, and Telnet connectivity. Help users configure network settings, understand protocol assignments, and troubleshoot connectivity issues.

## Critical: Telnet connectivity preservation

Creating a new show without `/globalsettings` **resets Telnet to "Login Disabled"**, severing any MCP or remote connection. Always preserve connectivity when creating new shows by including these flags:

| Flag | What it preserves |
|------|-------------------|
| `/globalsettings` | Telnet login enabled/disabled + MA-Net2 TTL/DSCP |
| `/network` | IP addresses and MA-Net2 network config |
| `/protocols` | Art-Net, sACN, DMX protocol assignments |

## Network-related system variables

| Variable | Example | Notes |
|----------|---------|-------|
| `$HOSTIP` | `127.0.0.1` | Console IP address |
| `$HOSTNAME` | `WINDELL-6OKD21F` | Station name |
| `$HOSTSTATUS` | `Master 1` | e.g., `Standalone`, `Master N` |
| `$HOSTSUBTYPE` | `onPC` | Hardware subtype |
| `$HOSTHARDWARE` | `GMA2` | Hardware platform |

## Reference material

- See `references/ma-net-config.md` for MA-Net2 and Telnet configuration
- See `references/artnet-sacn.md` for DMX protocol concepts

## When MCP bridge is NOT available

Output configuration guidance and command examples. To configure directly, connect via the ma2-onPC-MCP server: https://github.com/thisis-romar/ma2-onPC-MCP
