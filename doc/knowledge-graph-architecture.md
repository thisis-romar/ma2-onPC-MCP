---
title: Knowledge Graph Architecture
description: SQLite-backed in-process knowledge graph for MA2 domain entity modeling, traversal, and safety-aware planning
version: 1.0.0
created: 2026-04-08T09:01:44Z
last_updated: 2026-04-08T09:01:44Z
---

# Knowledge Graph Architecture

## Overview

The knowledge graph (`src/knowledge_graph/`) provides an in-process, SQLite-backed graph model of grandMA2 show-file entities and their relationships. It requires zero external dependencies (SQLite is stdlib) and integrates into the agent harness for goal enrichment, plan validation, and freshness tracking.

**Design principle:** The graph is populated from `ConsoleStateSnapshot` hydration — no additional Telnet traffic is generated. All graph features are behind `if graph_store is not None` guards, preserving 100% backward compatibility.

## Module Layout

```
src/knowledge_graph/
  __init__.py        Public API (__all__ with 13 exports), global accessor
  schema.py          NodeType (10), EdgeType (11), node_id(), SCHEMA_SQL
  store.py           GraphStore: CRUD, freshness, bulk ops, WAL mode
  query.py           GraphQuery: BFS, DFS, path finding, neighbor lookup
  sync.py            sync_snapshot(): hydrate graph from ConsoleStateSnapshot
  graph_rag.py       Entity extraction + context expansion for RAG queries
  planning.py        PlanningQueries: goal enrichment, plan validation
```

## Node Types (10)

| Type | Domain Object | Example node_id |
|------|--------------|-----------------|
| `fixture` | Patched fixture instance | `fixture:1` |
| `fixture_type` | Fixture type definition | `fixture_type:3` |
| `group` | Fixture group | `group:1` |
| `sequence` | Sequence (cue list) | `sequence:1` |
| `cue` | Individual cue | `cue:1.3` |
| `executor` | Executor slot | `executor:1.1` |
| `preset` | Stored preset | `preset:4.2` |
| `user` | Console user | `user:administrator` |
| `world` | World (fixture scoping) | `world:1` |
| `filter` | Filter (attribute restriction) | `filter:1` |

## Edge Types (11)

| Type | Direction | Example |
|------|-----------|---------|
| `member_of` | fixture -> group | Fixture 1 is member of Group "Front" |
| `instance_of` | fixture -> fixture_type | Fixture 1 is instance of Mac 700 |
| `patched_to` | fixture -> universe/address | Props: universe, address |
| `assigned_to` | sequence -> executor | Props: page, priority |
| `has_cue` | sequence -> cue | Props: cue_number |
| `controls` | executor -> sequence | Executor controls sequence |
| `uses_preset` | cue -> preset | Props: preset_type |
| `has_role` | user -> rights level | Props: ma2_right, scope_tier |
| `scoped_by` | executor -> world | Executor scoped by world |
| `filtered_by` | executor -> filter | Executor filtered by filter |
| `part_of` | cue_part -> cue | Structural containment |

## Lifecycle

```
ConsoleStateSnapshot hydration
        |
        v
  sync_snapshot(store, snapshot)   <-- populates nodes + edges
        |
        v
  Agent planning / policy / RAG    <-- queries graph
        |
        v
  StepExecutor runs DESTRUCTIVE    <-- marks affected types stale
        |
        v
  Next hydration re-syncs           <-- refreshes stale nodes
```

### Freshness Tracking

Every node carries an `updated_at` ISO timestamp. After a DESTRUCTIVE step, the executor calls `mark_type_stale()` on affected node types, setting `updated_at` to epoch.

**Policy Rule 9** warns when a DESTRUCTIVE plan step references a stale graph entity (>5 min old). This is advisory — it never blocks execution.

**CLAUDE.md rule:** "Do not use graph query results for DESTRUCTIVE operations without verifying freshness — stale graph data may reference deleted console objects."

## Integration Points

| Component | How it uses the graph |
|-----------|----------------------|
| `Orchestrator` | Syncs snapshot into graph after hydration (`orchestrator.py:366`) |
| `DomainPlanner` | Enriches goals with entity context (`planner.py:137-193`) |
| `PolicyEngine` | Rules 7/8/9: entity existence, executor availability, freshness (`policy.py:136-138`) |
| `StepExecutor` | Marks stale after DESTRUCTIVE steps (`executor.py:247-248`) |
| `GraphRAG` | Expands RAG queries with graph neighbors (`tools_enterprise.py:350-351`) |

## Safety Rules

1. Graph features are **advisory only** — they produce warnings, never block execution
2. DESTRUCTIVE steps must verify freshness before acting on graph data
3. The graph store is global (single instance) — designed for single-session MCP usage
4. All SQL is parameterized — no injection surface
5. Graph is populated from read-only snapshot data — no Telnet side effects

## Database Schema

```sql
CREATE TABLE kg_nodes (
    node_id    TEXT PRIMARY KEY,
    node_type  TEXT NOT NULL,
    label      TEXT,
    props      TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL
);

CREATE TABLE kg_edges (
    edge_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id  TEXT NOT NULL REFERENCES kg_nodes(node_id) ON DELETE CASCADE,
    target_id  TEXT NOT NULL REFERENCES kg_nodes(node_id) ON DELETE CASCADE,
    edge_type  TEXT NOT NULL,
    props      TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL,
    UNIQUE(source_id, target_id, edge_type)
);
```

Default storage: `:memory:` (session-scoped, no disk persistence). File-backed mode available via `GraphStore(db_path="path/to/file.db")`.
