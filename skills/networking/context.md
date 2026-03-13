---
title: Networking Workspace Context
description: Workspace context for the GMA2 networking skill
version: 1.0.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-13T00:00:00Z
---

# Networking Workspace Context

This workspace provides grandMA2 networking configuration reference. No MCP tools are needed.

## Mode

Knowledge only. Output network configuration guidance, protocol explanations, and troubleshooting steps.

## Scope

- MA-Net2 configuration (TTL, DSCP, session management)
- Art-Net and sACN protocol setup
- DMX universe addressing and patching
- Telnet connectivity (port 30000, login, session management)
- Connectivity preservation when creating new shows

## Critical safety

Always warn users about connectivity risks:
- `new_show` without `/globalsettings` disables Telnet login
- Network config changes can sever the active connection

## Boundaries

- Do NOT load or reference files from `src/` or `ee/` directories
- Do NOT attempt command execution — this is a knowledge-only workspace
