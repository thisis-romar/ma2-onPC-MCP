---
name: grandMA2 Networking
description: AI agent skill for configuring grandMA2 network protocols — Art-Net, sACN, MA-Net2, and DMX assignments
version: 0.1.0
license: Apache-2.0
tags:
  - lighting
  - grandma2
  - entertainment-technology
  - networking
  - artnet
  - sacn
created: 2026-03-12T18:00:00Z
last_updated: 2026-03-12T18:00:00Z
metadata:
  category: instruction-only
  product_url: https://github.com/thisis-romar/ma2-onPC-MCP
  console_version: "3.9.60.65"
---

# grandMA2 Networking

> **Skill type:** Instruction-only — provides standalone reference value without requiring the MCP bridge.

## Purpose

This skill enables AI agents to understand and configure grandMA2 network protocol settings: Art-Net universe mapping, sACN configuration, MA-Net2 session management, and DMX port assignments.

## Protocol Overview

grandMA2 supports three primary lighting control protocols:

| Protocol | Use Case | Universe Limit |
|----------|----------|---------------|
| **Art-Net** | Standard IP-based DMX transport | 256 universes |
| **sACN (E1.31)** | Streaming ACN, multicast/unicast | 256 universes |
| **MA-Net2** | Proprietary MA session protocol | MA-Net2 session universes |
| **DMX** | Physical 5-pin DMX ports | Port-dependent |

## New Show Connectivity Hazard

Creating a new show resets network settings. Three flags must be included to preserve connectivity:

| Flag | Preserves |
|------|-----------|
| `/globalsettings` | Telnet login enabled/disabled + MA-Net2 TTL/DSCP |
| `/network` | IP addresses and MA-Net2 network config |
| `/protocols` | Art-Net, sACN, DMX protocol assignments |

**Always use:** `New Show "name" /globalsettings /network /protocols`

Without `/globalsettings`, Telnet resets to "Login Disabled" — severing any remote connection including MCP.

## Network Configuration Paths

Network settings are accessible via Setup → Network Configuration on the console, or via the CD tree for inspection:

- IP configuration: Setup → Console → Global Settings
- Art-Net: Setup → Network Protocols → Art-Net
- sACN: Setup → Network Protocols → sACN
- MA-Net2: Setup → MA Network Control

## Key Concepts

- **Universes** are mapped to protocol outputs (Art-Net/sACN/DMX ports)
- **Sessions** group consoles, NPUs, and onPC stations on the same MA-Net2 network
- **MA-Net2 TTL/DSCP** settings control multicast scope and QoS
- **Merge modes** determine how multiple sources combine on the same universe (HTP, LTP)

## Execution

This skill provides networking reference knowledge for grandMA2. To configure network settings on a live console, connect the grandMA2 MCP server at the product URL listed in this skill's metadata.
