---
title: Markdown Front Matter Rules
description: Required YAML front matter fields and conventions for all .md files in this repo
version: 1.1.0
created: 2026-03-29T21:44:45Z
last_updated: 2026-04-04T00:00:00Z
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

## Version discipline

A full audit (2026-04-04) of CLAUDE.md and README.md version histories revealed systemic drift:

| Issue | CLAUDE.md | README.md |
|-------|-----------|-----------|
| Missing bumps (no version change on edit) | 14 | 8 |
| Overbumps (MINOR for PATCH work) | 5 | 4 |
| Underbumps (PATCH for MINOR work) | 1 | 3 |
| Skipped versions (gap in sequence) | 2 | 1 |

**To prevent recurrence:**

4. **Every commit that touches a `.md` file must bump its version** — no exceptions. If in doubt, bump PATCH.
5. **PATCH** = fixing numbers, typos, broken links, count corrections. **MINOR** = new sections, new content, new tables. **MAJOR** = structural reorganization of the document.
6. **Never skip version numbers** — increment by exactly 1 (e.g. `3.15.0 → 3.16.0`, not `3.15.0 → 3.18.0`).
7. **Never downgrade a version** — if the current version is `4.0.0`, the next version must be `≥ 4.0.1`.

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
