---
title: "Triage: Make grandpa2-buddy Tooling Run Reliably in Claude Desktop"
description: Root-cause analysis of MCP transport stalls (F1–F5) and a workstream plan (WS1–WS6) to make Desktop a first-class surface
version: 1.0.0
created: 2026-06-11T17:56:22Z
last_updated: 2026-06-11T18:49:43Z
---

# Triage: Make grandpa2-buddy Tooling Run Reliably in Claude Desktop

**Date:** 2026-06-10
**Question:** What would it take to fix the structural stalling so we *don't* have to flee to Claude Code?
**Headline finding:** **4 of the 5 stall causes live in the grandpa2-buddy MCP transport layer — which you own (`C:\Users\romar\ma2-onPC-mcp`).** They are NOT Claude Desktop limitations. Claude Code only "fixes" it because it lets you hand-write a synchronous batch loop; baking that same loop into the MCP makes Desktop work just as well.

---

## 1. Observed failure modes → root cause (evidence from this session)

| # | Symptom (observed) | Root cause | Lives in |
|---|--------------------|------------|----------|
| F1 | Every grandMA2 popup (export dialog, "10 objects exported", SaveShow overwrite) → next call "no result after 4 min" | grandMA2 halts its Telnet command processor while a modal GUI dialog is open. MCP sends, console never returns `[Fixture]>`, MCP read blocks until Desktop's 4-min tool timeout | **MCP transport** (+ MA2 behavior) |
| F2 | PowerShell Telnet batch corrupted 4.432–4.472, MCP went unresponsive | Two clients on one Telnet port (PowerShell + MCP) interleave bytes; the MCP's read framing desyncs | **Operational** (don't dual-connect) + MCP guard |
| F3 | Fixed-sleep batch produced silent failures / `sG` mixed states | Commands sent without waiting for `[Fixture]>` to return (blind-fire) | **The PowerShell bypass** (MCP path likely already synchronous) |
| F4 | Navigated FixtureTypes tree, next turn's `List` ran from root | `cd` destination resets across tool calls separated by wall-clock time | **MCP / console idle** |
| F5 | A hung call freezes the whole Desktop app; later calls also hang | Desktop serializes MCP calls; one blocked call (long 4-min timeout) stalls the queue | **Claude Desktop** — but only *triggered* by F1 |

**Key logic:** F5 is downstream of F1. If the MCP never blocks longer than a few seconds, Desktop never freezes. **Fix the MCP's transport to guarantee bounded response time and the cascade stops.**

---

## 2. Research tasks (confirm diagnoses BEFORE building — ~1–2 hrs, run in Claude Code against the repo)

| ID | Task | Why it matters |
|----|------|----------------|
| **R3 ★** | Inspect the existing **`execute_sequence`** tool in grandpa2-buddy (it was in the deferred tool list but we never used it) | If it already does server-side synchronous looping, **WS3 below is mostly already built** — we just never called it, and reached for PowerShell instead. Highest-value lead. |
| R1 | Read the Telnet transport (where `send_raw_command` reads): does it read-until-prompt or fixed-sleep? What socket timeout? | Determines if F1 fix (WS1) is a 1-line timeout change or a refactor |
| R2 | Confirm `send_raw_command` already reads synchronously | If yes, F3 was purely the PowerShell bypass; the MCP path is sound |
| R4 | Confirm the 4-min timeout is Desktop's vs the MCP's | Either way WS1 helps (MCP returns fast), but tells us if Desktop config tuning is also needed |
| R5 | Check Claude Desktop MCP config for timeout/keepalive knobs | Possible quick mitigation independent of code |

---

## 3. Workstreams to harden the MCP (effort / risk / order)

| WS | Fix | Solves | Effort | Risk |
|----|-----|--------|--------|------|
| **WS1** | **Bounded read + fast-fail.** Short socket read timeout (~5 s); if `[Fixture]>` doesn't return, raise a clean error ("console not responding — check for a modal dialog") instead of hanging | **F1, F5** (4-min freeze → 5-sec error) | 3–5 h | LOW |
| **WS2** | **Auto-`/noconfirm` injection** for dialog-raising keywords (Store, Delete, SaveShow, Label, Remove, Merge, Update, Import), opt-out per call | **F1** (no dialog ever raised) | 2–3 h | LOW-MED |
| **WS3 ★** | **Server-side batch/sequence tool** (or finish/expose `execute_sequence`): one tool call loops N commands, reads-until-prompt after each, aggregates errors, returns a compact summary. Reuses the single persistent socket | **F2, F3** + collapses 200 round-trips → 1 + removes any need for PowerShell Telnet | 6–10 h (or far less if `execute_sequence` exists) | MED |
| WS4 | Single-connection advisory lock (refuse 2nd client with a clear message) | F2 | 2–4 h | LOW |
| WS5 | Atomic navigation tools (semicolon-chained navigate→read→home in one call; re-assert destination) | F4 | 3–5 h | LOW |
| WS6 | Compact batch summaries + structured error lists + optional OpenTelemetry spans | Context bloat; observability | 2–4 h | LOW |

**Build order (max pain-relief first):** WS1 → WS2 → WS3 → WS4 → WS5 → WS6.

---

## 4. Scope options

| Option | Includes | Effort | Result |
|--------|----------|--------|--------|
| **MVP — "stop the stalling"** | WS1 + WS2 + WS3 | **~11–18 h (~2 days)**, less if `execute_sequence` already covers WS3 | Desktop runs 200-preset batches in one call, no 4-min freezes, no PowerShell needed |
| **Full hardening** | WS1–WS6 | **~18–31 h (~3–5 days)** | Production-grade: locks, atomic nav, telemetry, compact output |

---

## 5. Why this is worth doing (not just tonight)

This isn't throwaway remediation — it advances the **grandpa2-buddy / Interlock commercial roadmap**:
- **Desktop reliability = market reach.** Claude Desktop is the mainstream surface; requiring customers to use Claude Code narrows your addressable market. "Runs in Desktop" is a selling point.
- WS3 (batch) + WS1 (fast-fail) + WS6 (telemetry/OTel) are already on your nine-workstream roadmap — this just sequences them by the pain they remove.
- The fast-fail + lock work directly supports the Community/Pro/Enterprise tiering story (robustness as a paid differentiator).

---

## 6. Recommendation

1. **Run R3 first** (assess `execute_sequence`). If it already loops synchronously server-side, you may be ~1 day from MVP, not 2.
2. Build the **MVP trio (WS1 → WS2 → WS3)**. That alone converts Desktop from "stalls every few commands" to "one-call batches."
3. Defer WS4–WS6 to the commercial-hardening sprint.
4. Tonight's show work can still go through Claude Code (faster to ship the persistent-Telnet script by hand) — but **the same synchronous-batch logic, once in the MCP, retires the Claude-Code dependency.**

**Net:** the stalling is a fixable transport-layer gap in your own MCP, not a Claude Desktop ceiling. ~2 focused days makes Desktop a first-class surface for this tooling.
