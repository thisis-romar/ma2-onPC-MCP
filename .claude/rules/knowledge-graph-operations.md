---
title: Knowledge Graph Developer Conventions
description: Freshness rules, staleness mapping, graph lifecycle, and safety constraints for src/knowledge_graph/
version: 1.1.0
created: 2026-04-08T09:01:44Z
last_updated: 2026-04-10T02:53:59Z
---

# Knowledge Graph Developer Conventions

> Loaded when working on src/knowledge_graph/, src/agent/policy.py, src/agent/planner.py, or src/agent/executor.py.

---

## When to use the graph

- **Goal enrichment**: `PlanningQueries.enrich_goal()` resolves entity names to graph nodes, warns on missing entities, and suggests related objects.
- **Plan validation**: `PlanningQueries.validate_plan_dependencies()` checks that all entities referenced in a plan exist in the graph.
- **Executor availability**: `PlanningQueries.check_executor_available()` warns when assigning to an occupied executor slot.
- **RAG expansion**: `graph_rag_query()` enriches search results with graph neighbor context.
- **Freshness gating**: `PolicyEngine._check_graph_freshness()` warns when DESTRUCTIVE steps reference stale entities.

---

## Freshness rules

- After a DESTRUCTIVE step, call `store.mark_type_stale(node_type)` for affected types.
- Before using graph data in DESTRUCTIVE operations, check `store.is_fresh(node_id, cutoff)`.
- Freshness cutoff is 5 minutes by default (policy.py Rule 9).
- **Never cache graph results** for DESTRUCTIVE decisions — always re-query.
- Stale nodes are refreshed on the next `sync_snapshot()` call (next hydration cycle).

---

## Staleness mapping (executor.py)

When the executor marks nodes stale after a DESTRUCTIVE step, it uses a tool-name-to-node-type mapping:

| Tool pattern | Node types marked stale |
|-------------|------------------------|
| `store_*`, `delete_*` (cue-related) | `CUE`, `SEQUENCE` |
| `assign_*`, `release_*` (executor-related) | `EXECUTOR`, `SEQUENCE` |
| `patch_*`, `unpatch_*` (fixture-related) | `FIXTURE`, `FIXTURE_TYPE` |
| `store_*` (group/preset-related) | `GROUP`, `PRESET` |
| Unknown DESTRUCTIVE tool | ALL node types (safe fallback) |

---

## Graph store lifecycle

1. `GraphStore(":memory:")` — created during `AgentRuntime.__init__` or `Orchestrator.__init__`
2. `store.initialize()` — creates tables, enables WAL mode
3. `sync_snapshot(store, snapshot)` — incremental delta sync from `ConsoleStateSnapshot`
4. Query/traverse/enrich — used by planner, policy, executor, GraphRAG
5. `store.close()` — cleanup on shutdown

---

## Incremental delta sync

`sync_snapshot()` uses incremental delta sync (not full-clear rebuild):

1. **Upsert phase**: all nodes and edges from the snapshot are upserted (insert or update)
2. **Prune phase**: nodes and edges not seen during this cycle are deleted
3. **INSTANCE_OF edges**: fixture→fixture_type edges are created via name prefix matching

This keeps the graph readable during sync and avoids destroying state that concurrent readers depend on. The returned `counts` dict includes `pruned_nodes` and `pruned_edges` alongside `nodes` and `edges`.

---

## What NOT to do

- Do not add graph features that **block** execution — graph rules are advisory only.
- Do not generate Telnet traffic to populate the graph — use `sync_snapshot()` only.
- Do not mix real embeddings with graph queries — they are separate retrieval paths.
- Do not store DESTRUCTIVE decisions in the graph — it's a read model, not an audit log.
- Do not assume graph data is fresh — always check `is_fresh()` before DESTRUCTIVE ops.
- Do not hardcode `db_path` — always pass as parameter or use `:memory:`.
