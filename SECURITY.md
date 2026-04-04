---
title: Security Policy
description: Vulnerability reporting process for the GrandPA2-Buddy MCP server
version: 1.0.0
created: 2026-04-04T00:00:00Z
last_updated: 2026-04-04T00:00:00Z
---

# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 3.26.x  | Yes       |
| < 3.26  | No        |

## Scope

The following components are in scope for security reports:

- **MCP server** (`src/server.py`, `src/server_orchestration_tools.py`) — tool dispatch, input validation, safety gate
- **Telnet client** (`src/telnet_client.py`) — command injection, authentication, session handling
- **Auth & credentials** (`src/auth.py`, `src/credentials.py`) — OAuth scope enforcement, credential resolution
- **Session manager** (`src/session_manager.py`) — session pool, keepalive, reconnect
- **License enforcement** (`src/license.py`, `src/license_tiers.py`) — tier gating bypass
- **Agent harness** (`src/agent/`) — plan-level governance, policy bypass, privilege escalation

### Out of scope

- grandMA2 onPC application itself (report to MA Lighting)
- MA Lighting network infrastructure
- Third-party dependencies (report upstream)

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

1. Email the maintainer privately at: **thisis.romar+security@gmail.com**
2. Include:
   - Affected component and version
   - Steps to reproduce
   - Impact assessment (what an attacker could do)
   - Suggested fix (if any)
3. You will receive an acknowledgment within **48 hours**.
4. A fix or mitigation will be provided within **14 days** of confirmation.

If the vulnerability is critical (e.g., remote command execution on a live console), we will coordinate disclosure timing with you.

## Disclosure Policy

- **14-day grace period** from confirmed report to public disclosure.
- Credit will be given to the reporter in the release notes unless anonymity is requested.
- We follow coordinated disclosure — please do not publish details before the grace period expires.
