---
title: Project Rules
description: Agent conventions and standards for the gma2-mcp-telnet repository
version: 1.0.0
created: 2026-03-01T00:00:00Z
last_updated: 2026-03-01T00:00:00Z
---

# Project Rules

## Markdown Front Matter

All `.md` files in this repository **must** include YAML front matter (`---` fences) at the top of the file.

### Required fields

| Field | Format | Description |
|-------|--------|-------------|
| `title` | string | Document title (matches the `# H1` heading) |
| `description` | string | One-line summary of the document's purpose |
| `version` | semver | `MAJOR.MINOR.PATCH` — bump PATCH for fixes, MINOR for new content, MAJOR for restructures |
| `created` | ISO 8601 | `YYYY-MM-DDTHH:MM:SSZ` — set once when the file is created, never changed |
| `last_updated` | ISO 8601 | `YYYY-MM-DDTHH:MM:SSZ` — update every time the file content changes |

### Rules

1. **New `.md` files** — add front matter before writing any content.
2. **Editing existing `.md` files** — update `last_updated` to the current date/time. Bump `version` if the change is non-trivial (typo fixes don't require a bump).
3. **Do not** backfill `created` dates — use the actual date the file was created.
4. **Template:**

```yaml
---
title: Document Title
description: Brief purpose of this document
version: 1.0.0
created: YYYY-MM-DDTHH:MM:SSZ
last_updated: YYYY-MM-DDTHH:MM:SSZ
---
```
