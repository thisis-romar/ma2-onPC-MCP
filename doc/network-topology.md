---
title: Network Topology & Security Hardening
description: Co-located deployment model for securing grandMA2 Telnet via the MCP server gateway
version: 1.0.0
created: 2026-04-04T20:12:50Z
last_updated: 2026-04-04T20:12:50Z
---

# Network Topology & Security Hardening

## The Problem

grandMA2 consoles expose Telnet on TCP port 30000 with no encryption.
Credentials travel as plaintext. Anyone with network access to the port can
issue arbitrary console commands — completely bypassing the MCP server's
OAuth scope, MA2 rights, and license tier enforcement.

The MCP server's 3-layer permission model protects against AI agent
misbehavior. It does **not** protect against direct network access to port
30000.

## The Solution: Co-Located Deployment

The only supported topology places the MCP server on the **same machine** as
grandMA2 onPC, with the host firewall restricting Telnet to loopback:

```
┌──────────────────────────────────────────────────────────────────┐
│  grandMA2 onPC Machine (Windows / Linux)                         │
│                                                                  │
│  ┌────────────┐    localhost:30000    ┌─────────────────────┐    │
│  │ grandMA2   │◄──────────────────────│  MCP Server         │    │
│  │ onPC       │    (Telnet, TCP)      │  (src/server.py)    │    │
│  │            │                       │                     │    │
│  │ Port 30000 │                       │  3-layer gate:      │    │
│  │ (loopback  │                       │  ┌───────────────┐  │    │
│  │  only!)    │                       │  │ OAuth scope    │  │    │
│  └────────────┘                       │  │ MA2 rights     │  │    │
│        │                              │  │ License tier   │  │    │
│        │ MA-Net2 multicast            │  └───────────────┘  │    │
│        │ (UDP, eth0)                  └──────────┬──────────┘    │
│        │                                         │               │
├────────┼─────────────────────────────────────────┼───────────────┤
│   eth0 │                                    stdio│or HTTP        │
│        │                                         │               │
│  ┌─────┴──────────────────────┐         ┌────────┴────────┐     │
│  │ MA-Net2 Network            │         │ LLM Client      │     │
│  │ (Full Size, NPU, MA Node)  │         │ (Claude, etc.)  │     │
│  │                            │         │                 │     │
│  │ UDP multicast:             │         │ stdio: local    │     │
│  │  6454 (Art-Net)            │         │ HTTP:  authed   │     │
│  │  5568 (sACN)               │         └─────────────────┘     │
│  │  MA-Net2 session traffic   │                                  │
│  └────────────────────────────┘                                  │
└──────────────────────────────────────────────────────────────────┘

  ─── Firewall boundary ───
  ✅ TCP 30000 from 127.0.0.1      → ACCEPT (MCP server)
  ❌ TCP 30000 from anything else   → DROP
  ✅ UDP 6454/5568 multicast        → ACCEPT (Art-Net/sACN unaffected)
  ✅ MA-Net2 session UDP            → ACCEPT (console networking unaffected)
```

## Why This Works

| Threat | Mitigation |
|--------|------------|
| AI agent exceeds authorized scope | 3-layer gate: OAuth `@require_scope` + MA2 `is_permitted()` + console Error #72 |
| AI agent issues destructive command without confirmation | `confirm_destructive=True` gate + `DESTRUCTIVE` risk tier |
| AI agent injects commands via line breaks | `\r\n` rejection in `send_raw_command()` |
| Network attacker raw-telnets to port 30000 | **Host firewall** restricts TCP 30000 to loopback |
| Credential sniffing on the wire | Telnet leg never leaves loopback — nothing to sniff |
| Unauthenticated HTTP MCP transport | Warning at startup; stdio transport has no network surface |

## Applying the Firewall

```bash
# Linux (iptables)
sudo bash scripts/lockdown_firewall.sh --apply

# Check status
sudo bash scripts/lockdown_firewall.sh --status

# Remove (if needed)
sudo bash scripts/lockdown_firewall.sh --remove
```

On Windows, the script uses `netsh advfirewall` instead. Rules persist across
reboots on Windows; on Linux, use `iptables-save` to persist.

See `scripts/lockdown_firewall.sh --help` for full usage.

## Startup Warnings

The MCP server checks three conditions at startup and emits warnings:

| Condition | Warning |
|-----------|---------|
| `GMA_HOST` is not `127.0.0.1` / `::1` / `localhost` | Telnet credentials travel in cleartext; port reachable from network |
| `GMA_AUTH_BYPASS=1`, `GMA_RIGHTS_BYPASS=1`, or `GMA_LICENSE_BYPASS=1` | Entire permission layer disabled |
| Factory-default credentials (`administrator` / `admin`) | Change before any network deployment |

These are non-fatal warnings, not hard blocks — the server still starts.
The operator is responsible for acting on them.

## What About Remote LLM Clients?

A remote LLM (Claude via API, etc.) does **not** require the Telnet leg to
be remote. The LLM connects to the MCP server, not to the console:

- **stdio transport** (default): LLM runs on the same machine. No network
  surface at all.
- **HTTP transport** (`sse` / `streamable-http`): LLM connects over the
  network to the MCP server's HTTP endpoint. The MCP server still connects
  to onPC via `localhost:30000`. The HTTP leg should be authenticated and
  TLS-wrapped by a reverse proxy (nginx, caddy) — this is outside the
  project's scope.

The key invariant: **Telnet stays on loopback. Always.**

## MA-Net2 Compatibility

The firewall rules affect only **TCP port 30000** (Telnet). MA-Net2 session
traffic uses UDP multicast on separate ports:

| Protocol | Port | Direction | Firewall impact |
|----------|------|-----------|-----------------|
| Telnet | TCP 30000 | Inbound | **Restricted to loopback** |
| Art-Net | UDP 6454 | Multicast | Unaffected |
| sACN | UDP 5568 | Multicast | Unaffected |
| MA-Net2 session | UDP (various) | Multicast | Unaffected |

An onPC instance can join MA-Net2 sessions with Full Size consoles, NPUs,
and MA Nodes while Telnet is locked to loopback.
