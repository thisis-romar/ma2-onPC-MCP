---
title: Branch Evolution Audit Report
description: Full audit of all branch evolution relative to main with timestamps and change progression
version: 1.0.0
created: 2026-03-04T16:30:00Z
last_updated: 2026-03-04T16:30:00Z
---

# Branch Evolution Audit Report

## Context

This audit documents the complete branch lifecycle of the **gma2-mcp-telnet** repository — an MCP server for controlling grandMA2 lighting consoles via Telnet. The report maps every branch's relationship to the default branch (`main`), visualizes change progression with timestamps, and identifies development patterns across 77+ commits spanning 3 months.

---

## 1. Repository Overview

| Metric | Value |
|--------|-------|
| Default branch | `main` |
| Total commits (main) | 77 |
| Total unique branches (all time) | 8 |
| Merged PRs | 3 |
| Active unmerged branches | 3 |
| Fully merged branches | 2 |
| Repository lifespan | 2025-11-30 to 2026-03-04 |
| Contributors | 5 (Chuan/chienchuanw, thisis-romar, Claude, Romar J, copilot-swe-agent) |

---

## 2. Timeline Visualization

```
Nov 30 '25                                              Mar 04 '26
|                                                            |
|  FOUNDATION (chienchuanw)    TRANSITION      RAPID DEVELOPMENT
|  ========================    ==========    ====================
|
|  Nov 30   Dec 02  Dec 06  Dec 08  Dec 25-26  Feb 27  Feb 28  Mar 01  Mar 02  Mar 03
|  14 cmts  4 cmts  11 cmts 9 cmts  3 cmts     8 cmts  10 cmts 16 cmts 8 cmts  2 cmts
|  ██████   ██      █████   ████    █           ████    █████   ████████ ████    █
|
|                                                        ▼ PR#1  ▼ PR#2  ▼ PR#3
|                                                       merged  merged  merged
```

### Commit Density Heatmap

```
2025-11-30  ██████████████  (14)  — Project foundation day
2025-12-02  ████            ( 4)  — Layout/preset keywords
2025-12-03  █               ( 1)  — File refactoring
2025-12-04  █               ( 1)  — Test refactoring
2025-12-06  ███████████     (11)  — Sequence/cue/DMX features
2025-12-08  █████████       ( 9)  — Object model refactor
2025-12-25  █               ( 1)  — Holiday fix
2025-12-26  ██              ( 2)  — Holiday work
2026-02-27  ████████        ( 8)  — Navigation + safety audit
2026-02-28  ██████████      (10)  — Tree scanner + resilience
2026-03-01  ████████████████(16)  — MCP tools + CI (peak day)
2026-03-02  ████████        ( 8)  — RAG pipeline + vocab refactor
2026-03-03  ██              ( 2)  — Copilot README refactor
```

---

## 3. Branch Evolution Map

### All branches relative to `main` (default)

```
main (77 commits) ─────────────────────────────────────────── cff747b (HEAD)
  │                                                              │
  │  MERGED INTO MAIN                                            │
  │  ══════════════                                              │
  │                                                              │
  ├── claude/audit-gma2-safety-NOqSw ──── PR #1 ────────┐       │
  │   (1 commit, merged 2026-02-27)                      │       │
  │   └─ 7032e9b audit: fix security issues              ├──► 9cbf4f8
  │                                                      │       │
  ├── feat/scan-tools-ci ─────────────── PR #2 + #3 ────┐│      │
  │   (20 unique commits, merged 2026-03-01)             ││      │
  │   ├─ PR#2 merged at ca1c734 (5f15c16..b3c20c5)      ├┼──► 2263f4a
  │   └─ PR#3 merged at 2263f4a (7dd0168 CI fix)        ││      │
  │                                                      ││      │
  │  ACTIVE / UNMERGED                                   ││      │
  │  ═════════════════                                   ││      │
  │                                                              │
  ├── claude/gma2-rag-pipeline-E2tuR ─── (3 ahead) ─────────── 4f3a230
  │   Forked from: cff747b (main HEAD)                           │
  │   Created: 2026-03-02                                        │
  │   └─ dc695bd feat: RAG pipeline for dual-source indexing     │
  │   └─ 62fb407 feat: GitHubModelsProvider for embeddings       │
  │   └─ 4f3a230 docs: README with ToC + RAG pipeline docs      │
  │   Files changed: 35 (+2560 / -37)                           │
  │                                                              │
  ├── copilot/refactor-readme-structure ─ (2 ahead) ─────────── 130d5e8
  │   Forked from: cff747b (main HEAD)                           │
  │   Created: 2026-03-03                                        │
  │   └─ e2ba1fd Initial plan                                    │
  │   └─ 130d5e8 refactor: collapsible <details> in README      │
  │   Files changed: 1 (+110 / -50)                             │
  │                                                              │
  ├── feat/console-state-vocab-refactor ─ (5 ahead) ─────────── 692739a
  │   Forked from: cff747b (main HEAD)                           │
  │   Created: 2026-03-02                                        │
  │   └─ 89350b8 fix: PRESET_TYPES numbering                    │
  │   └─ 1038829 feat: live telnet research scripts              │
  │   └─ 4c2f861 refactor: vocabulary with categorized keywords  │
  │   └─ 0f7b72c docs: README for vocab refactor                │
  │   └─ 692739a chore: mcp[cli] dependency + command-builders   │
  │   Files changed: 19 (+1652 / -105)                          │
  │                                                              │
  └── GrandMA2-Telnet-Buddy ──────────── (stale, 0 unique) ──── 46c34c6
      Points to: 46c34c6 (ancestor of main)
      Status: All commits already in main via merges
      Likely: original development branch, now superseded
```

---

## 4. Detailed Branch Profiles

### 4.1 `main` (default branch)

| Property | Value |
|----------|-------|
| Commits | 77 |
| HEAD | `cff747b` — ci: add ruff linting and mypy type checking |
| First commit | `8c79e25` — 2025-11-30 (feat: add store) |
| Latest commit | `cff747b` — 2026-03-01 19:22:01 -0500 |
| Merges received | 3 PRs |

**Development phases on main:**

1. **Foundation** (Nov 30 - Dec 8, 2025) — 40 commits by chienchuanw
   - Command keyword framework (store, fixture, channel, group, etc.)
   - Object model, Telnet client, basic MCP server

2. **Dormancy** (Dec 9, 2025 - Feb 26, 2026) — 3 commits (holiday fixes)

3. **Rapid growth** (Feb 27 - Mar 1, 2026) — 34 commits by thisis-romar + Claude
   - Navigation layer, tree scanner, safety audit
   - MCP expansion (5 → 28 tools), CI/CD, 756 tests

---

### 4.2 `claude/audit-gma2-safety-NOqSw` (MERGED — PR #1)

| Property | Value |
|----------|-------|
| Status | **Merged** into main |
| PR | #1 |
| Merge commit | `9cbf4f8` — 2026-02-27 13:16:48 -0500 |
| Unique commits | 1 |
| Author | Claude (AI) |
| Branch deleted | Yes (remote ref removed) |

**Key commit:**
- `7032e9b` — audit: fix security issues, add vocab safety module, clean dead code

**Impact:** Introduced the safety/vocabulary classification system that gates destructive commands.

---

### 4.3 `feat/scan-tools-ci` (MERGED — PR #2 + PR #3)

| Property | Value |
|----------|-------|
| Status | **Merged** into main (twice) |
| PRs | #2 and #3 |
| Merge commits | `ca1c734` (PR#2), `2263f4a` (PR#3) |
| Unique commits | 20 (at time of merge) |
| Active period | 2026-02-27 → 2026-03-01 |
| Author | thisis-romar |

**Commit progression:**

```
Feb 27  Navigation + list parsing (3 commits)
Feb 28  Tree scanner + resilience + VS Code ext (10 commits)
Mar 01  MCP tools 5→28, integration tests, CI (7 commits)
        ├─ PR#2 merged (ca1c734) with 19 commits
        └─ PR#3 merged (2263f4a) with 1 CI fix commit
```

**Impact:** Largest feature branch. Delivered the tree scanner, all 28 MCP tools, 66 integration tests, and the CI pipeline.

---

### 4.4 `GrandMA2-Telnet-Buddy` (STALE)

| Property | Value |
|----------|-------|
| Status | **Stale** — all commits already in main |
| HEAD | `46c34c6` (ancestor of main HEAD) |
| Unique commits vs main | 0 |
| Last activity | 2026-03-01 15:43:33 |

**Analysis:** This branch points to a commit that is an ancestor of `main`. It appears to have been a parallel tracking branch during active development of `feat/scan-tools-ci`. All its content was absorbed into main via the PR merges. **Candidate for deletion.**

---

### 4.5 `claude/gma2-rag-pipeline-E2tuR` (ACTIVE — unmerged)

| Property | Value |
|----------|-------|
| Status | **Active**, 3 commits ahead of main |
| Fork point | `cff747b` (main HEAD) |
| Created | 2026-03-02 |
| Author | Claude (AI) |
| Files changed | 35 (+2,560 / -37 lines) |

**Unique commits (not in main):**

```
2026-03-02 07:34  dc695bd  feat: add RAG pipeline for dual-source repo indexing and retrieval
2026-03-02 08:28  62fb407  feat: add GitHubModelsProvider for real vector search embeddings
2026-03-02 18:52  4f3a230  docs: refactor README with ToC, collapsible sections, and RAG pipeline docs
```

**Purpose:** Adds a Retrieval-Augmented Generation pipeline for indexing the repository and grandMA2 manual for AI-assisted querying.

---

### 4.6 `copilot/refactor-readme-structure` (ACTIVE — unmerged)

| Property | Value |
|----------|-------|
| Status | **Active**, 2 commits ahead of main |
| Fork point | `cff747b` (main HEAD) |
| Created | 2026-03-03 |
| Author | copilot-swe-agent[bot] |
| Files changed | 1 (+110 / -50 lines) |

**Unique commits (not in main):**

```
2026-03-03 02:22  e2ba1fd  Initial plan
2026-03-03 02:28  130d5e8  refactor README.md: wrap 12 sections in collapsible <details> blocks
```

**Purpose:** AI-agent generated README restructuring with collapsible sections.

---

### 4.7 `feat/console-state-vocab-refactor` (ACTIVE — unmerged)

| Property | Value |
|----------|-------|
| Status | **Active**, 5 commits ahead of main |
| Fork point | `cff747b` (main HEAD) |
| Created | 2026-03-02 |
| Author | thisis-romar |
| Files changed | 19 (+1,652 / -105 lines) |

**Unique commits (not in main):**

```
2026-03-02 18:24  89350b8  fix: correct PRESET_TYPES numbering and server type_map
2026-03-02 18:26  1038829  feat: add live telnet research scripts for console state validation
2026-03-02 18:26  4c2f861  refactor: restructure vocabulary with categorized keywords and Object Keyword metadata
2026-03-02 18:47  0f7b72c  docs: update README for PRESET_TYPES fix, vocab refactor, and research scripts
2026-03-02 18:52  692739a  chore: add mcp[cli] dev dependency, launch config, and command-builders doc
```

**Purpose:** Major vocabulary system refactor with categorized keywords, object metadata, and bug fix for preset types.

---

## 5. Contributor Analysis

| Author | Commits | Period | Role |
|--------|---------|--------|------|
| Chuan (home) / chienchuanw | 43 | Nov-Dec 2025 | Original author — foundation |
| thisis-romar | 31 | Feb-Mar 2026 | Lead developer — MCP tools, scanner, CI |
| Claude (AI) | 8 | Feb-Mar 2026 | Safety audit, RAG pipeline, navigation |
| Romar J | 3 | Feb-Mar 2026 | PR merge commits |
| copilot-swe-agent[bot] | 2 | Mar 2026 | README refactoring |

---

## 6. Merge and PR History

```
PR #1 ── claude/audit-gma2-safety-NOqSw ──► main
         Merged: 2026-02-27 13:16:48
         Commits: 1
         Merge commit: 9cbf4f8

PR #2 ── feat/scan-tools-ci ──────────────► main
         Merged: 2026-03-01 18:45:48
         Commits: 19
         Merge commit: ca1c734

PR #3 ── feat/scan-tools-ci ──────────────► main
         Merged: 2026-03-01 18:48:30
         Commits: 1 (CI fix after PR#2)
         Merge commit: 2263f4a
```

---

## 7. Branch Health Summary

| Branch | Status | Ahead | Behind | Action Recommended |
|--------|--------|-------|--------|--------------------|
| `main` | Default | — | — | — |
| `claude/audit-gma2-safety-NOqSw` | Merged | 0 | 0 | Already deleted |
| `feat/scan-tools-ci` | Merged | 0 | 0 | Delete remote ref |
| `GrandMA2-Telnet-Buddy` | Stale | 0 | 12 | **Delete** — fully absorbed |
| `claude/gma2-rag-pipeline-E2tuR` | Active | 3 | 0 | Review for merge |
| `copilot/refactor-readme-structure` | Active | 2 | 0 | Review for merge |
| `feat/console-state-vocab-refactor` | Active | 5 | 0 | Review for merge |

---

## 8. Key Findings

1. **All active branches fork from the same point** (`cff747b`, current main HEAD). No branch is behind main — there are zero merge conflicts pending from drift.

2. **Two branches are candidates for cleanup:** `GrandMA2-Telnet-Buddy` (stale, 0 unique commits) and `feat/scan-tools-ci` (fully merged).

3. **Three active branches contain meaningful unmerged work** totaling 10 commits and ~4,300 lines of additions.

4. **Development ownership transitioned** from chienchuanw (Nov-Dec 2025) to thisis-romar (Feb-Mar 2026), with AI agents (Claude, Copilot) contributing 10 of 87 total commits (11.5%).

5. **Peak activity day:** 2026-03-01 with 16 commits — the MCP tools expansion and CI setup day.

6. **Shallow clone detected:** The earliest commit (`8c79e25`) is grafted, meaning full history may extend further back.

7. **No release tags exist:** The repository has no semantic versioning or release markers despite having 77 commits and a functioning CI pipeline.
