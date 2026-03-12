---
title: Project Rules
description: Agent conventions, architecture quick-reference, and development rules for ma2-onPC-MCP
version: 4.0.0
created: 2026-03-01T00:00:00Z
last_updated: 2026-03-12T12:00:00Z
---

# Project Rules

## Project Identity

MCP server exposing **90 tools**, **6 resources**, and **5 prompts** so AI assistants can control a grandMA2 lighting console via Telnet.
All network I/O is isolated in `src/telnet_client.py`. Command builders in `src/commands/` are pure functions returning strings — no side effects. The MCP layer in `src/server.py` wires tool calls to telnet via the navigation and safety layers. Resources provide read-only console state; prompts encode MA2 domain workflows.

---

## Architecture Quick Reference

| Module | Role |
|--------|------|
| `src/server.py` | FastMCP server, 90 tools, safety gate, env config, transport selection |
| `src/tools.py` | Shared client infrastructure: `get_client()`, `parse_listvar()`, env config |
| `src/resources.py` | 6 MCP resources — read-only console/show state via `gma2://` URIs |
| `src/prompts.py` | 5 MCP prompts — guided MA2 workflows (color chase, patching, diagnostics) |
| `src/completions.py` | MCP argument autocompletion for prompts and resource templates |
| `src/subscriptions.py` | MCP resource subscription tracking (subscribe/unsubscribe handlers) |
| `src/elicitation.py` | Server-initiated user input — destructive op confirmation schemas |
| `src/sampling.py` | Server-initiated LLM calls — cue suggestions, troubleshooting, Lua gen |
| `src/telnet_client.py` | Async Telnet (telnetlib3), auth, send/receive, injection prevention |
| `src/navigation.py` | cd + list + prompt parsing orchestration |
| `src/prompt_parser.py` | Parse console prompts and `list` tabular output |
| `src/commands/` | 110+ pure command-builder functions, grouped by keyword type |
| `src/commands/helpers.py` | `quote_name()` wildcard spec, `_build_options()` flag assembly |
| `src/vocab.py` | 141 keyword vocab, `KeywordCategory`, `RiskTier`, `classify_token()` |
| `rag/ingest/` | crawl → chunk → embed → store pipeline |
| `rag/retrieve/` | cosine similarity search + rerank |
| `rag/store/sqlite.py` | SQLite vector store (`rag/store/rag.db`) |
| `scripts/rag_ingest.py` | CLI: ingest repo into RAG store |
| `scripts/rag_ingest_web.py` | CLI: crawl MA2 help docs and ingest in daily batches |
| `src/categorization/` | ML-based tool categorization: K-Means clustering + auto-labeling |
| `scripts/categorize_tools.py` | CLI: extract features, embed, cluster, write taxonomy JSON |

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

# Start MCP server with SSE transport (for remote clients)
GMA_TRANSPORT=sse GMA_MCP_PORT=8080 uv run python -m src.server

# Start MCP server with streamable-http transport
GMA_TRANSPORT=streamable-http GMA_MCP_PORT=8080 uv run python -m src.server
```

---

## MCP Resources

6 read-only resources exposed via `gma2://` URIs. No safety gate needed — all SAFE_READ.

| URI | Returns |
|-----|---------|
| `gma2://console/status` | All 26 system variables as JSON |
| `gma2://console/location` | Current cd path + prompt text |
| `gma2://show/fixtures` | Fixture pool listing (navigates to FixtureType, lists, returns to root) |
| `gma2://show/groups` | Group pool listing |
| `gma2://show/sequences` | Sequence pool listing |
| `gma2://show/sequences/{seq_id}/cues` | Cues in a specific sequence (resource template) |

Implementation in `src/resources.py`. Each handler calls `get_client()` → sends telnet commands → parses → returns JSON. Navigation resources `cd /` after reading.

---

## MCP Prompts

5 prompt templates encoding MA2 domain expertise as reusable workflows.

| Prompt ID | Purpose | Parameters |
|-----------|---------|------------|
| `program-color-chase` | Guided color chase programming | `fixture_group`, `color_count` |
| `setup-moving-lights` | Patch + group + focus workflow | `fixture_type`, `start_address`, `count` |
| `troubleshoot-connectivity` | Telnet/network diagnostic steps | none |
| `create-cue-sequence` | Step-by-step cue programming | `sequence_id`, `cue_count` |
| `show-status-report` | Dynamic — fetches live console state | none |

Implementation in `src/prompts.py`. Static prompts return message lists; `show-status-report` is dynamic (calls `get_client()`).

---

## MCP Transport

Default: `stdio`. Configurable via environment variables:

| Env var | Values | Default |
|---------|--------|---------|
| `GMA_TRANSPORT` | `stdio`, `sse`, `streamable-http` | `stdio` |
| `GMA_MCP_PORT` | port number | `8080` |

**Security:** HTTP transports have no built-in auth — use for local network only.

---

## MCP Completions

Argument autocompletion for prompt parameters and resource template URIs.

**Resource templates:** `gma2://show/sequences/{seq_id}/cues` → suggests sequence IDs 1-50.

**Prompt arguments:** Completions for `fixture_group`, `color_count`, `fixture_type`, `start_address`, `count`, `sequence_id`, `cue_count` across all parameterized prompts. Prefix-filtered.

Implementation in `src/completions.py`. Registered via `@mcp.completion()`.

---

## MCP Resource Subscriptions

In-memory subscription tracking for resource URIs. Clients subscribe via `resources/subscribe`; the server tracks active subscriptions and can notify via `notifications/resources/updated`.

Helpers: `has_subscribers(uri)`, `get_subscribed_uris()`, `get_subscription_count(uri)`.

Implementation in `src/subscriptions.py`. Subscriptions are lost on server restart.

---

## MCP Elicitation

Server-initiated user input requests. Schemas use Pydantic models with primitive fields only.

| Schema | Fields | Use case |
|--------|--------|----------|
| `DestructiveConfirmation` | `confirmed: bool` | Gate destructive commands interactively |
| `TargetSelection` | `object_id: str`, `object_name: str` | Ask user to pick a target object |
| `PageSelection` | `page_number: int` | Ask user to select a page |

Helpers: `elicit_destructive_confirmation(session, command, description)` → `bool`, `check_elicitation_support(session)` → `bool`.

Graceful degradation: returns `False`/`None` if client doesn't support elicitation.

Implementation in `src/elicitation.py`.

---

## MCP Sampling

Server-initiated LLM calls via the client's configured model.

| Function | Purpose | Max tokens |
|----------|---------|------------|
| `generate_cue_suggestions()` | Suggest next cues based on console state | 500 |
| `generate_troubleshooting_advice()` | Diagnose errors from command history | 300 |
| `generate_lua_script()` | Generate MA2 Lua scripts from description | 1000 |

Default model preference: intelligence > speed > cost, hints `claude-sonnet-4-6`.

Graceful degradation: returns `None` if client doesn't support sampling.

Implementation in `src/sampling.py`.

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
- Current counts (2026-03-12): **1440 unit tests**, **132 live integration tests**.

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

### MAtricks command keywords (live-verified 2026-03-11)

MAtricks are controlled via **direct command keywords** — no `cd` navigation needed.
The `manage_matricks` tool dispatches to these keywords via an `action` parameter (SAFE_WRITE).

| Keyword | Syntax | Example |
|---------|--------|---------|
| `MAtricksInterleave` | `[width]`, `[col].[width]`, `+/-`, `Off` | `MAtricksInterleave 4` |
| `MAtricksBlocks` | `[size]`, `[x].[y]`, `+ N/- N`, `Off` | `MAtricksBlocks 2.3` |
| `MAtricksGroups` | `[size]`, `[x].[y]`, `+ N/- N`, `Off` | `MAtricksGroups 4` |
| `MAtricksWings` | `[parts]`, `+/-`, `Off` | `MAtricksWings 2` |
| `MAtricksFilter` | `[num]`, `"name"`, `+/-`, `Off` | `MAtricksFilter "OddID"` |
| `MAtricksReset` | (no args) | `MAtricksReset` |
| `MAtricks` | `[id]`, `On/Off/Toggle` | `MAtricks 5` |
| `All` | (no args) | resets Single X sub-selection |
| `AllRows` | (no args) | resets Single Y sub-selection |
| `Next` | (no args) | steps forward through Single X sub-selection |
| `Previous` | (no args) | steps backward through Single X sub-selection |
| `NextRow` | (no args) | steps forward through Single Y (row) sub-selection |

- `Interleave` is a synonym for `MAtricksInterleave`.
- Y-axis settings (Block Y, Group Y) require Interleave to be active first.
- **No `PreviousRow`** — asymmetric; only `NextRow` exists for Y-axis stepping.
- **No telnet command reads current MAtricks state** — state is only visible in the GUI toolbar.
- Pool path: `cd MAtricks` → `UserProfiles/Default 1/MatrixPool`.
- **`store_matricks_preset`** tool: combined set + store + label workflow (DESTRUCTIVE).

### Appearance colors

MA2 appearance commands use **0-100 percentage scale** for RGB and HSB — NOT 0-255.

| Mode | Parameters | Range |
|------|-----------|-------|
| RGB | `/r=R /g=G /b=B` | 0-100 each |
| HSB | `/h=H /s=S /br=BR` | hue 0-360, sat/bright 0-100 |
| Hex | `/color=RRGGBB` | 6-digit hex, no `#` |

**XML format:** `<Appearance Color="RRGGBB" />` embeds inside any pool object element (e.g. `<Matrix>`, `<Group>`). Colors imported via XML appear instantly — no telnet appearance loop needed.

**MAtricks library color scheme:** 25 colors using HSB — Wings sets hue (5 hues evenly spaced: 0°, 72°, 144°, 216°, 288°), Groups sets brightness (100/80/60/45/30). Embedded in XML via `<Appearance Color="hex" />`.

**Filter library color scheme:** 9 categories, each a distinct hex color. Shared constants in `src/commands/constants.py`:

| Category | Hex | Color |
|----------|-----|-------|
| dimmer | `FFCC00` | warm yellow |
| position | `0088FF` | blue |
| gobo | `00CC44` | green |
| color | `FF00CC` | magenta |
| beam | `FF6600` | orange |
| focus | `00CCCC` | cyan |
| control | `999999` | grey |
| combo | `CC44FF` | purple |
| exclude | `FF3333` | red |

Filter attribute groups (`FILTER_ATTRIBUTES` in constants) map 36 attributes across 7 PresetTypes. These are **fixture-dependent defaults** (Mac 700 Profile Extended + Generic Dimmer). For shows with different fixtures, call `discover_filter_attributes()` first, then pass the result to `create_filter_library(fixture_attributes=...)`. Import syntax: `Import "filename" At Filter N`.

**Filter V/VT/E (Value/ValueTimes/Effects) layer toggles** are XML attributes on the `<Filter>` element (live-verified 2026-03-11):

| XML attribute | Store option | Default |
|---|---|---|
| `value="false"` | `/values=false` | `true` (omitted) |
| `value_timing="false"` | `/valuetimes=false` | `true` (omitted) |
| `effect="false"` | `/effects=false` | `true` (omitted) |

MA2 omits attributes that are `true` (default). `FILTER_VTE_COMBOS` in constants defines 7 on/off combinations (excluding all-off). With `include_vte=True`, the `create_filter_library` tool generates 21 base × 7 VTE = 147 variant filters (168 total, slots 3-170).

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
| `$PRESET` | `GOBO` | Read-only; changes when `Feature [name]` or `PresetType [id]` is called |
| `$ATTRIBUTE` | `GOBO1` | Read-only; fixture-dependent; changes with `Feature [name]` |
| `$FEATURE` | `GOBO1` | Read-only; fixture-dependent; change via `Feature [name]` or `PresetType [id]` |
| `$SELECTEDEXEC` | `1.1.1` | `page.page.exec` format |
| `$SELECTEDEXECCUE` | `NONE` or `1` | Active cue on selected executor |
| `$SELECTEDFIXTURESCOUNT` | `0`–`N` | Only updated by `SelFix`, not `Select` |
| `$FADERPAGE` | `1` | Read-only; change via `Page N` (page must exist, or use `create_if_missing`) |
| `$BUTTONPAGE` | `1` | Read-only; change via `Page N` |
| `$CHANNELPAGE` | `1` | Read-only; change via `Page N` |

### PresetType / Feature / CD-Tree Correlation (live-verified 2026-03-10, v3.9.60.65)

Calling `Feature [name]` or `PresetType [id]` updates **all three** of `$PRESET`, `$FEATURE`, `$ATTRIBUTE` simultaneously. Feature names are fixture-dependent.

| PresetType | ID | CD path   | $PRESET  | $FEATURE (1st) | $ATTRIBUTE (1st)  |
|------------|----|-----------|----------|----------------|-------------------|
| Dimmer     | 1  | cd 10.2.1 | DIMMER   | DIMMER         | DIM               |
| Position   | 2  | cd 10.2.2 | POSITION | POSITION       | PAN               |
| Gobo       | 3  | cd 10.2.3 | GOBO     | GOBO1          | GOBO1             |
| Color      | 4  | cd 10.2.4 | COLOR    | COLORRGB       | COLORRGB1         |
| Beam       | 5  | cd 10.2.5 | BEAM     | SHUTTER        | SHUTTER           |
| Focus      | 6  | cd 10.2.6 | FOCUS    | FOCUS          | FOCUS             |
| Control    | 7  | cd 10.2.7 | CONTROL  | MSPEED         | INTENSITYMSPEED   |
| Shapers    | 8  | cd 10.2.8 | —        | fixture-dep    | —                 |
| Video      | 9  | cd 10.2.9 | —        | fixture-dep    | —                 |

**CD tree depth** (verified with `list` at each level — tree is navigable 4+ levels deep):
```
cd 10.2        → 9 PresetTypes
cd 10.2.5      → Beam features: SHUTTER(20), BEAM1(21), EFFECT(22)
cd 10.2.5.1    → Attributes under SHUTTER: SHUTTER(22), STROBE_RATIO(0)
cd 10.2.5.1.1  → SubAttributes of SHUTTER (Shutter, Strobe, Pulse, ...)
```
Note: `cd 10.2.N` uses sequential child index (1=first listed), not the internal library ID.

**`Feature Color` and `Feature Zoom` error** on fixtures that use `ColorRGB`/`Shutter` channel names instead.

### CD Tree Root Location

The root prompt name is **show-dependent** — do not hardcode `"Fixture"`:
- Old show (`claude_ma2_ctrl`): root is `[Fixture]>`
- Different show loaded: root is `[Screen]>`

Navigation code that checks "are we still at root?" must detect the actual root location dynamically (e.g. `cd /` then read the prompt).

### Strategic Scan (`scripts/strategic_scan.py`)

Fast 4-phase re-scan for comparing show files (~24 min vs 138 min full scan):

| Phase | What | Time |
|-------|------|------|
| 1 Root | cd+list every index 1-50 | ~38s |
| 2 Structure | depth 3 all branches, depth 1 UserProfiles | ~15 min |
| 3 Deep | full recursive on cd 10.3, 30, 38 | ~5 min |
| 4 Triage | retry failed edges with 2x delay | ~1 min |

```bash
PYTHONUNBUFFERED=1 python -u scripts/strategic_scan.py [--output scan_output_new.json] [--old-scan scan_output.json]
```

Output is compatible with `print_cd_tree.py --input scan_output_new.json`.

**Key show-dependent branches** (vary between show files):
- cd 1 (Showfile history), cd 10.3 (FixtureTypes), cd 18 (Worlds), cd 19 (Filters)
- cd 22 (Groups), cd 25 (Sequences), cd 30 (ExecutorPages), cd 38 (Layouts), cd 39 (UserProfiles)

**Firmware branches** (stable across shows): cd 2-9, 15-16, 20, 23, 27, 36, 41-42

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
