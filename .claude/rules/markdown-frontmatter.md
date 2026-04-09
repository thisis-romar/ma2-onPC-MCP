---
title: Markdown Front Matter Rules
description: Required YAML front matter fields and conventions for all .md files in this repo
version: 1.3.0
created: 2026-03-29T21:44:45Z
last_updated: 2026-04-09T16:10:25Z
---

# Markdown Front Matter Rules

All `.md` files in this repository **must** include YAML front matter (`---` fences) at the top.

## Required fields

| Field | Format | Description |
|-------|--------|-------------|
| `title` | string | Document title (matches the `# H1` heading) |
| `description` | string | One-line summary of the document's purpose |
| `version` | semver | `MAJOR.MINOR.PATCH` — bump PATCH for fixes, MINOR for new content, MAJOR for restructures |
| `created` | ISO 8601 | `YYYY-MM-DDTHH:MM:SSZ` — set once when the file is created, never changed |
| `last_updated` | ISO 8601 | `YYYY-MM-DDTHH:MM:SSZ` — update every time the file content changes |

## Rules

1. **New `.md` files** — add front matter before writing any content.
2. **Editing existing `.md` files** — update `last_updated`. Bump `version` for non-trivial changes.
3. **Do not** backfill `created` dates — use the actual date the file was created.

## Timestamp sourcing

Use `get_current_time` from the MCP time server (`.mcp.json`) for all `created` / `last_updated` values. If the time server is unavailable, fall back to the system clock:

```bash
date -u +%Y-%m-%dT%H:%M:%SZ
```

## Version discipline

A full audit (2026-04-09) of all 65 `.md` files across 188 commits found:

| Issue | CLAUDE.md | README.md | SECURITY.md | Total |
|-------|-----------|-----------|-------------|-------|
| Missing bumps | 0 | 4 | 0 | **4** |
| Overbumps | 0 | 0 | 1 | **1** |
| Skipped versions | 1 | 0 | 0 | **1** |
| Regressions | 1 | 0 | 0 | **1** |

Overall discipline score: **87.8%** (30 correct / 37 scored transitions).

**To prevent recurrence:**

4. **Every commit that touches a `.md` file must bump its version** — no exceptions. If in doubt, bump PATCH.
5. **PATCH** = fixing numbers, typos, broken links, count corrections. **MINOR** = new sections, new content, new tables. **MAJOR** = structural reorganization of the document.
6. **Never skip version numbers** — increment by exactly 1 (e.g. `3.15.0 → 3.16.0`, not `3.15.0 → 3.18.0`).
7. **Never downgrade a version** — if the current version is `4.0.0`, the next version must be `≥ 4.0.1`.

## Automated enforcement

These rules are enforced by two hook layers:

**Git pre-commit hook** (`.githooks/pre-commit` → `scripts/validate_md_versions.py`):
- Blocks commits when staged `.md` content changes without a `version` bump
- Blocks commits when `last_updated` is stale (content changed, timestamp unchanged)
- Blocks version regressions (new < old)
- Warns on skipped versions (increment > 1)
- Only validates files actually staged — no cross-file cascading

**Claude Code PostToolUse hook** (`.claude/settings.json` → `.githooks/md-version-reminder.sh`):
- Fires on every `Edit`/`Write` call matching `.md` files
- Outputs advisory reminder to bump `version` and `last_updated`
- Non-blocking (always exits 0)

**Audit tool** (`scripts/audit_md_version_history.py`):
- Walks full git history for all `.md` files
- Classifies each transition: correct_bump, missing_bump, overbump, underbump, skip, regression
- Produces per-file scorecards and overall discipline score

## Two-track versioning

This project uses **independent version tracks** (industry best practice):

| Track | What it versions | Source of truth | Examples |
|-------|-----------------|-----------------|----------|
| **Release version** | The software package | `pyproject.toml` | 3.35.3 |
| **Document versions** | Each `.md` file independently | Front matter `version:` | CLAUDE.md 4.17.0, README.md 3.36.0 |

Document versions evolve independently of the release version. CLAUDE.md at 4.17.0 while pyproject.toml is at 3.35.3 is correct — they track different things.

Release version must stay synced across: `pyproject.toml`, `src/__init__.py`, `LICENSE`, README badge. The pre-commit hook enforces this.

## Template

```yaml
---
title: Document Title
description: Brief purpose of this document
version: 1.0.0
created: YYYY-MM-DDTHH:MM:SSZ
last_updated: YYYY-MM-DDTHH:MM:SSZ
---
```
