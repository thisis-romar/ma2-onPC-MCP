---
title: Project Rules
description: Agent conventions, architecture quick-reference, and development rules for ma2-onPC-MCP
version: 3.1.0
created: 2026-03-01T00:00:00Z
last_updated: 2026-03-10T00:00:00Z
---

# Project Rules

## Project Identity

MCP server exposing **78 tools** so AI assistants can control a grandMA2 lighting console via Telnet.
All network I/O is isolated in `src/telnet_client.py`. Command builders in `src/commands/` are pure functions returning strings — no side effects. The MCP layer in `src/server.py` wires tool calls to telnet via the navigation and safety layers.

---

## Architecture Quick Reference

| Module | Role |
|--------|------|
| `src/server.py` | FastMCP server, 78 tools, safety gate, env config |
| `src/telnet_client.py` | Async Telnet (telnetlib3), auth, send/receive, injection prevention |
| `src/navigation.py` | cd + list + prompt parsing orchestration |
| `src/prompt_parser.py` | Parse console prompts and `list` tabular output |
| `src/commands/` | 110+ pure command-builder functions, grouped by keyword type |
| `src/commands/helpers.py` | `quote_name()` wildcard spec, `_build_options()` flag assembly |
| `src/vocab.py` | 148 keyword vocab, `KeywordCategory`, `RiskTier`, `classify_token()` |
| `rag/ingest/` | crawl → chunk → embed → store pipeline |
| `rag/retrieve/` | cosine similarity search + rerank |
| `rag/store/sqlite.py` | SQLite vector store (`rag/store/rag.db`) |
| `scripts/rag_ingest.py` | CLI: ingest repo into RAG store |
| `scripts/rag_ingest_web.py` | CLI: crawl MA2 help docs and ingest in daily batches |

---

## Development Commands

```bash
# Run all tests
make test                         # or: python -m pytest -v
# NOTE: uv run may fail with "trampoline" error on Windows — use python -m as fallback

# Run a subset
python -m pytest tests/test_vocab.py       # single file
python -m pytest tests/test_rag_*.py      # RAG tests only

# Start MCP server
uv run python -m src.server

# Ingest repo (zero-vector, no token needed — runs automatically on every commit)
uv run python scripts/rag_ingest.py --root . --provider zero

# Ingest repo with real semantic embeddings (requires GITHUB_MODELS_TOKEN in .env)
source .env && export GITHUB_MODELS_TOKEN && \
  uv run python scripts/rag_ingest.py --provider github

# Ingest MA2 web docs — first run (crawls + saves cache + embeds)
source .env && export GITHUB_MODELS_TOKEN && \
  PYTHONUNBUFFERED=1 uv run python scripts/rag_ingest_web.py \
  --provider github --cache-crawl

# Ingest MA2 web docs — subsequent days (loads cache, no re-crawl)
source .env && export GITHUB_MODELS_TOKEN && \
  PYTHONUNBUFFERED=1 uv run python scripts/rag_ingest_web.py \
  --provider github --cache-crawl

# Install git hooks (pre-commit auto-updates RAG index on every commit)
make install-hooks
```

---

## Code Conventions

### Adding a new MCP tool

1. Add command builder functions in `src/commands/` — pure, return `str`, no I/O.
2. Export them from `src/commands/__init__.py`.
3. Register the tool in `src/server.py` with `@mcp.tool()` and `@_handle_errors`.
4. If the tool issues a `DESTRUCTIVE` command, accept `confirm_destructive: bool = False` and gate on it.
5. Add tests in `tests/test_<feature>.py` — call builders directly, no telnet needed.

### Command builders

- Pure functions only — no imports from `src.telnet_client`, `src.navigation`, or `src.server`.
- Return raw grandMA2 command strings, e.g. `"Store Cue 1 Sequence 99 /merge"`.
- Use `src/commands/helpers.py` for option flag assembly (`_build_options()`).
- Use `src/commands/constants.py` for `PRESET_TYPES` mapping (e.g. `"color" → 4`).

### Tests

- Unit tests import command builders or vocab directly and assert on returned strings.
- No live console required; live tests are in `tests/test_live_integration.py` and skipped by default.
- Use `@pytest.mark.asyncio` for async tests.
- Current counts (2026-03-10): **1157 unit tests**, **132 live integration tests**.

### New Show — connectivity preservation

Always use the default `preserve_connectivity=True` when calling `new_show()`.
Creating a new show without `/globalsettings` **resets Telnet to "Login Disabled"**, severing the MCP connection.
The three flags auto-applied by `preserve_connectivity=True` are:

| MA2 flag | What it preserves |
|---|---|
| `/globalsettings` | Telnet login enabled/disabled + MA-Net2 TTL/DSCP |
| `/network` | IP addresses and MA-Net2 network config |
| `/protocols` | Art-Net, sACN, DMX protocol assignments |

Only pass `preserve_connectivity=False` when the user **explicitly** wants a completely clean show AND understands they must manually re-enable Telnet in Setup → Console → Global Settings on the console.

### Name quoting — quote_name()

All label/info/list commands that include a name use `quote_name(name, match_mode)` from `src/commands/helpers.py`.

- **Rule A (default)**: quote if the name contains any MA2 special character (`* @ $ . / ; [ ] ( ) " space`). Plain names are emitted bare — no quotes added.
- **match_mode="wildcard"**: emits the name raw so `*` acts as a wildcard operator.
- Callers must pass the **raw name**, not a pre-quoted string (e.g. `"Mac700 Front"` not `'"Mac700 Front"'`).

### Wildcard workflow — discover_object_names

To build a wildcard filter for any object pool:

1. Call `discover_object_names("Group")` → returns `names_only` list + `wildcard_tip`
2. Derive a pattern from the names (e.g. `Mac700*`)
3. Pass to `list_objects("group", name="Mac700*", match_mode="wildcard")` → `list group Mac700*`

The tool navigates to the pool, lists all entries, extracts names, then returns to root (`cd /`).
Works with any keyword (`"Group"`, `"Sequence"`, `"Macro"`, etc.) or numeric cd index.

### grandMA2 System Variables

grandMA2 exposes 26 built-in read-only system variables. Access them via:

- `list_system_variables()` — returns all 26 as `{"$NAME": "value"}` dict
- `get_variable(action="echo", var_name="NAME")` — reads one variable (uses ListVar + filter internally)

**ListVar telnet wire format:**
```
$Global : $VARNAME = VALUE
```
The `_parse_listvar()` helper in `src/server.py` strips the `$Global : ` scope prefix.

**`Echo $VARNAME` does NOT work.** MA2 expands the variable before executing, so
`Echo $TIME` becomes `Echo 19h26m52.284s` → UNKNOWN COMMAND. Always use `ListVar`.

**`SelFix` vs `Select` for `$SELECTEDFIXTURESCOUNT`:**
Only `SelFix N [Thru M]` updates `$SELECTEDFIXTURESCOUNT`. `Select Fixture N` does not.

**`$SELECTEDEXEC` format:** `page.page.exec` (e.g. `1.1.201` for executor 201 on page 1).
Changed by `select executor N` or physical console selection.

**`$SELECTEDEXECCUE`:** `NONE` when no cue is active; cue number (e.g. `1`) when running.
Changes on `Go Executor N`, returns to `NONE` on `Off Executor N`.

**All 26 built-in system variables** (live-verified 2026-03-10, v3.9.60.65 onPC):

| Variable | Example value | Notes |
|----------|--------------|-------|
| `$HOSTSUBTYPE` | `onPC` | |
| `$HOSTTYPE` | `Console` | |
| `$HOSTHARDWARE` | `GMA2` | |
| `$HOSTNAME` | `WINDELL-6OKD21F` | Station name |
| `$HOSTIP` | `127.0.0.1` | |
| `$HOSTSTATUS` | `Master 1` | e.g. `Standalone`, `Master N` |
| `$OS` | `WINDOWS` | |
| `$VERSION` | `3.9.60.65` | Full build version |
| `$TIME` | `19h26m52.284s` | MA2 internal time format |
| `$DATE` | `10.3.2026` | `DD.M.YYYY` |
| `$PATH` | `C:/ProgramData/.../gma2_V_3.9.60` | Software run path |
| `$PLUGINPATH` | `.../plugins` | |
| `$TEMPPATH` | `.../temp` | |
| `$USER` | `administrator` | Current login |
| `$USERPROFILE` | `Default` | |
| `$USERRIGHTS` | `Admin` | |
| `$SHOWFILE` | `claude_ma2_ctrl` | Current show name |
| `$PRESET` | `GOBO` | Last active preset type |
| `$ATTRIBUTE` | `GOBO1` | Current attribute context |
| `$FEATURE` | `GOBO1` | Current feature context |
| `$SELECTEDEXEC` | `1.1.1` | `page.page.exec` format |
| `$SELECTEDEXECCUE` | `NONE` or `1` | Active cue on selected executor |
| `$SELECTEDFIXTURESCOUNT` | `0`–`N` | Only updated by `SelFix`, not `Select` |
| `$FADERPAGE` | `1` | Read-only; change via `Page N` (page must exist, or use `create_if_missing`) |
| `$BUTTONPAGE` | `1` | Read-only; change via `Page N` |
| `$CHANNELPAGE` | `1` | Read-only; change via `Page N` |

---

## Safety Rules

Three tiers enforced before any command reaches the console:

| Tier | Examples | Policy |
|------|----------|--------|
| `SAFE_READ` | `list`, `info`, `cd` | Always allowed |
| `SAFE_WRITE` | `go`, `at`, `clear`, `park` | Allowed in `standard` and `admin` modes |
| `DESTRUCTIVE` | `delete`, `store`, `copy`, `move`, `assign` | Blocked unless `confirm_destructive=True` |

**Rules when writing tools:**

- Any tool calling a `DESTRUCTIVE` command must accept `confirm_destructive: bool = False` and gate on it.
- Never pass `confirm_destructive=True` automatically — the caller must opt in.
- Line breaks (`\r`, `\n`) in command strings are rejected by the safety gate.
- Classification entry point: `classify_token(token, spec)` in `src/vocab.py`.
- **`new_show` without `/globalsettings` disables Telnet** — always keep `preserve_connectivity=True` (the default).

---

## RAG Pipeline

### How it works

```
crawl → chunk → embed → store (SQLite) → query → rerank
```

- Python files: AST-aware chunking. Markdown: heading-based. Everything else: line-based.
- Embeddings: `GitHubModelsProvider` (requires `GITHUB_MODELS_TOKEN`) or `ZeroVectorProvider` (CI/testing stub).
- The `search_codebase` MCP tool queries the store; auto-detects token and falls back to text search when absent.
- Embedding API is rate-limited — 4s inter-request delay and batch_size=32 are the defaults to stay within GitHub Models free tier.

### Pre-commit hook

`make install-hooks` installs `.githooks/pre-commit`, which runs zero-vector ingest on every commit (fast, no API calls). Real-vector rebuild must be run manually.

### Web doc batching

~1,043 grandMA2 help pages, embedded in nightly runs. The `--cache-crawl` flag saves the crawl to `rag/store/web_crawl_cache.json` — subsequent runs skip re-crawling and go straight to embedding. Run the same command each night; hash-based dedup skips already-indexed pages automatically.

---

## Markdown Front Matter

All `.md` files in this repository **must** include YAML front matter (`---` fences) at the top.

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

---

## What NOT To Do

- Do not add network I/O to command builder functions in `src/commands/` — they must stay pure.
- Do not import from `src.server` or `src.navigation` inside `src/commands/`.
- Do not hardcode `GMA_HOST`, `GMA_PORT`, or credentials — always read from env vars.
- Do not run live integration tests without a real grandMA2 console on `GMA_HOST`.
- Do not set `confirm_destructive=True` inside server tool implementations — only the MCP caller may set it.
- Do not commit `rag/store/rag.db` or `rag/store/web_crawl_cache.json` — local artifacts, listed in `.gitignore`.
- Do not edit `src/grandMA2_v3_9_telnet_keyword_vocabulary.json` manually — it is the source-of-truth keyword vocabulary.
- Do not duplicate README.md content here — README is for humans, CLAUDE.md is for the agent.
- Do not call `new_show` with `preserve_connectivity=False` unless the user explicitly accepts that Telnet will be disabled and they will re-enable it manually on the console.
- Do not pass pre-quoted strings to `quote_name()` — pass raw names only (e.g. `"Mac700 Front"`, not `'"Mac700 Front"'`).
