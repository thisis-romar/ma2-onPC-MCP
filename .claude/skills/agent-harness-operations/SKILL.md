---
title: Agent Harness Operations
description: Agent harness architecture, component flow, and PlanStep interop for src/agent/ development
version: 1.0.0
created: 2026-04-07T15:14:23Z
last_updated: 2026-04-07T15:14:23Z
---

# Agent Harness Operations

## Architecture

The agent harness (`src/agent/`) enables autonomous multi-step execution on top of the existing MCP tools — no changes to command builders, telnet client, or navigation.

```
AgentRuntime (runtime.py)
  -> DomainPlanner (planner.py) -- rule-based goal -> plan
  -> PolicyEngine (policy.py)   -- plan-level governance
  -> StepExecutor (executor.py) -- tool dispatch + retries
  -> Verifier (verification.py) -- post-mutation checks
  -> WorkflowMemory (memory.py) -- SQLite operational memory
  -> ExecutionTrace (trace.py)  -- JSON audit artifacts
```

## MCP Tools

- `run_agent_goal(goal, auto_confirm, dry_run)` — end-to-end execution
- `plan_agent_goal(goal)` — plan only, no execution

## PlanStep Interop

`DomainPlanner` uses its own `PlanStep` model. Use `src/agent_bridge.py` to convert between `PlanStep` and main's `SubTask` for cross-system interop.

## Component Details

| Component | File | Role |
|-----------|------|------|
| `AgentRuntime` | `src/agent/runtime.py` | Goal -> plan -> execute -> verify -> trace |
| `DomainPlanner` | `src/agent/planner.py` | Rule-based domain planner, goal classification |
| `StepExecutor` | `src/agent/executor.py` | Step executor with retries, confirmation flow |
| `PolicyEngine` | `src/agent/policy.py` | Plan-level governance (extends `src/vocab.py` safety) |
| `Verifier` | `src/agent/verification.py` | Post-mutation state verification |
| `WorkflowMemory` | `src/agent/memory.py` | SQLite workflow memory (conventions, recipes, run history) |
| `ExecutionTrace` | `src/agent/trace.py` | Structured JSON execution traces |
| `RunContext/PlanStep/Checkpoint` | `src/agent/state.py` | Data models |
| Workflow templates | `src/agent/workflows/` | patch, preset, playback, common |

## Scoped Rules

For detailed conventions on the OpenSpace layer (telemetry, skills, LTM), see `.claude/rules/openspace-layer.md`.
