---
title: Server Workspace Rules
description: Path-scoped rules for MCP server source code
version: 1.0.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-13T00:00:00Z
---

# Server Workspace Rules

Applies to: `src/**`

When working with MCP server source code:

1. **Verify Telnet connection** before any command execution. Check that `GMA_HOST` and `GMA_PORT` are configured.

2. **Confirm destructive commands** before execution. Any tool calling a DESTRUCTIVE command (`Delete`, `Store`, `Copy`, `Move`, `Assign`, `Label`, `Import`, `Export`) must accept `confirm_destructive: bool = False` and gate on it. Never set `confirm_destructive=True` automatically.

3. **FIFO ordering** for multi-command sequences. Never send commands in parallel — use sequential execution through the Telnet client.

4. **Command builders are pure functions.** They must NOT import from `src.telnet_client`, `src.navigation`, or `src.server`. They return raw grandMA2 command strings only.

5. **Safety gate reference:** Classification is handled by `classify_token(token, spec)` in `src/vocab.py`. Three tiers: SAFE_READ, SAFE_WRITE, DESTRUCTIVE.

6. **Connectivity preservation:** Always use `preserve_connectivity=True` (the default) when calling `new_show()`. Without `/globalsettings`, Telnet resets to "Login Disabled".

7. **Line break injection prevention:** The safety gate rejects any command containing `\r` or `\n`.
