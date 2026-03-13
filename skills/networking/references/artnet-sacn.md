---
title: Art-Net, sACN, and DMX Protocols
description: DMX protocol configuration for grandMA2 including Art-Net and sACN
version: 1.0.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-13T00:00:00Z
---

# Art-Net, sACN, and DMX Protocols

## DMX Addressing

grandMA2 uses a universe.address notation for DMX:

| Notation | Meaning |
|----------|---------|
| `dmx 1.1` | Universe 1, address 1 |
| `dmx 2.101` | Universe 2, address 101 |
| `dmxuniverse 1` | Reference universe 1 |

Each universe contains 512 channels (addresses 1-512).

## CD Tree: DMX Protocol Configuration

| cd path | Content |
|---------|---------|
| cd 4 | DMX_Protocols (6 children, depth 3) |
| cd 4.1-6 | Individual protocol configurations |

## Art-Net

Art-Net is an Ethernet protocol for transmitting DMX512 data over IP networks.

### Key concepts

- **Art-Net Universe** — maps to a DMX512 universe
- **Subnet/Net** — hierarchical addressing (Net.Subnet.Universe)
- **Broadcast vs Unicast** — Art-Net supports both modes
- **Port** — default UDP port 6454

### grandMA2 Art-Net setup

1. Navigate to **Setup → Network Protocols → Art-Net**
2. Enable Art-Net output on desired interfaces
3. Map internal DMX universes to Art-Net universes
4. Configure output mode (broadcast/unicast)

## sACN (Streaming ACN / E1.31)

sACN is a standard for streaming DMX data over IP using multicast.

### Key concepts

- **Universe** — maps 1:1 to a DMX512 universe (1-63999)
- **Priority** — 0-200 (default 100), higher priority wins on merge
- **Multicast** — each universe has a dedicated multicast address
- **Synchronization** — sACN supports sync universes for frame-accurate output

### grandMA2 sACN setup

1. Navigate to **Setup → Network Protocols → sACN**
2. Enable sACN output on desired interfaces
3. Map internal DMX universes to sACN universes
4. Set priority level (default 100)

## Protocol Assignment Preservation

When creating a new show, the `/protocols` flag preserves:
- Art-Net universe mappings
- sACN universe mappings
- DMX protocol assignments
- Output interface configuration

Without this flag, all protocol assignments reset to defaults and must be manually reconfigured.

## DMX-Related MCP Tools

| Tool | Purpose |
|------|---------|
| `list_universes` | List configured DMX universes |
| `patch_fixture` | Assign fixture to DMX address |
| `unpatch_fixture` | Remove fixture DMX assignment |
| `browse_patch_schedule` | View current patch |
| `park_fixture` / `unpark_fixture` | Lock/unlock DMX output values |
