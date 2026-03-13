---
title: MA-Net2 and Telnet Configuration
description: grandMA2 MA-Net2 network setup, Telnet access, and connectivity preservation
version: 1.0.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-13T00:00:00Z
---

# MA-Net2 and Telnet Configuration

## Telnet Access

grandMA2 exposes a Telnet interface on **port 30000** (default) for remote command execution.

### Connection parameters

| Parameter | Default | Environment variable |
|-----------|---------|---------------------|
| Host | `127.0.0.1` | `GMA_HOST` |
| Port | `30000` | `GMA_PORT` |
| Username | `administrator` | `GMA_USER` |
| Password | `admin` | `GMA_PASSWORD` |

### Enabling Telnet

Telnet must be enabled in the console: **Setup → Console → Global Settings → Telnet = "Login Enabled"**

### Safety levels

The MCP server enforces three safety levels via the `GMA_SAFETY_LEVEL` environment variable:

| Level | Allowed commands |
|-------|-----------------|
| `read_only` | Only SAFE_READ (list, info, cd) |
| `standard` | SAFE_READ + SAFE_WRITE (go, at, clear, park) |
| `admin` | All commands including DESTRUCTIVE (with confirmation) |

## Connectivity Preservation

**Critical:** Creating a new show (`new_show`) without preservation flags resets Telnet to "Login Disabled", severing the connection.

The three preservation flags:

| Flag | What it preserves |
|------|-------------------|
| `/globalsettings` | Telnet login enabled/disabled, MA-Net2 TTL/DSCP |
| `/network` | IP addresses, MA-Net2 network configuration |
| `/protocols` | Art-Net, sACN, DMX protocol assignments |

**Always use all three flags** unless the user explicitly wants a completely clean show and understands they must manually re-enable Telnet on the console.

## MA-Net2 Network Architecture

### CD tree paths

| cd path | Content |
|---------|---------|
| cd 5 | NetConfig (5 children, depth 4) |
| cd 3 | Settings (6 children, includes network-related settings) |

### Network system variables

| Variable | Example | Updated by |
|----------|---------|------------|
| `$HOSTIP` | `127.0.0.1` | Network configuration |
| `$HOSTNAME` | `WINDELL-6OKD21F` | Station name setting |
| `$HOSTSTATUS` | `Master 1` | Session role |
| `$HOSTSUBTYPE` | `onPC` | Hardware detection |
| `$OS` | `WINDOWS` | Operating system |

### Session roles

- **Standalone** — single console, no network session
- **Master N** — session master (N = session number)
- **Slave** — follows a master console
- **NPU** — Network Processing Unit (dedicated DMX output)

## Telnet Command Injection Prevention

The safety gate rejects any command containing line breaks (`\r`, `\n`). This prevents command injection through multi-line payloads. All commands must be single-line strings.
