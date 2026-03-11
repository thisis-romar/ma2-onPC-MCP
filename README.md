---
title: GMA2 MCP
description: MCP server for controlling grandMA2 lighting consoles via Telnet
version: 2.1.0
created: 2025-02-27T00:00:00Z
last_updated: 2026-03-11T00:00:00Z
---

# GMA2 MCP

[![Tests](https://github.com/thisis-romar/gma2-mcp-telnet/actions/workflows/test.yml/badge.svg)](https://github.com/thisis-romar/gma2-mcp-telnet/actions/workflows/test.yml)

MCP server for controlling grandMA2 lighting consoles via Telnet.

Exposes grandMA2 commands as [Model Context Protocol](https://modelcontextprotocol.io/) tools so that AI assistants (Claude Desktop, etc.) can operate a lighting console programmatically.

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [MCP Tools](#mcp-tools)
- [Client Setup](#client-setup)
- [RAG Pipeline](#rag-pipeline)
- [Console Navigation & Prompt Parsing](#console-navigation-prompt-parsing)
- [Tree Scanner](#tree-scanner)
- [Command Builder Reference](#command-builder-reference)
- [Safety System](#safety-system)
- [Project Structure](#project-structure)
- [Dependencies](#dependencies)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Quick Start

```bash
# 1. Install
git clone https://github.com/thisis-romar/gma2-mcp-telnet && cd gma2-mcp-telnet
uv sync

# 2. Configure
cp .env.template .env        # then edit with your console IP

# 3. Install git hooks (auto-updates RAG index on every commit)
make install-hooks

# 4. Run
uv run python -m src.server  # starts MCP server (stdio transport)
```

> **Optional — semantic search:** Add `GITHUB_MODELS_TOKEN=ghp_...` to `.env`, then run
> `uv run python scripts/rag_ingest.py --provider github` once to rebuild the index with
> real embeddings. The `search_codebase` MCP tool will automatically use semantic ranking
> when the token is present.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  MCP Server Layer              src/server.py             │
│  82 tools across 12 categories                           │
│  Safety gate: classifies commands before sending         │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│  Navigation Layer          src/navigation.py             │
│  navigate(), get_current_location(), list_destination()  │
│  set_property(), scan_indexes()                          │
│  Combines command builder + telnet I/O + prompt parsing  │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│  Command Builder Layer     src/commands/                  │
│  110+ pure functions generating grandMA2 command strings  │
│  helpers.py: quote_name(), _build_options() flag assembly │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│  Telnet Client Layer       src/telnet_client.py           │
│  Async connection, auth, send/receive via telnetlib3      │
│  Input sanitization (strips \r\n to prevent injection)    │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Prompt Parser             src/prompt_parser.py           │
│  parse_prompt() — detect console location from responses  │
│  parse_list_output() — extract entries + column headers   │
│    with automatic header detection and column mapping     │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Vocabulary & Safety       src/vocab.py                   │
│  141 keywords: 56 Object, 78 Function, 7 Helping, 6 Char │
│  KeywordCategory + RiskTier classification via            │
│  classify_token() with Object Keyword context metadata    │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  RAG Pipeline              rag/                           │
│  Ingest: crawl → chunk → embed → store (SQLite)          │
│  Retrieve: query → cosine similarity → rerank            │
│  Providers: GitHubModelsProvider, ZeroVectorProvider      │
└──────────────────────────────────────────────────────────┘
```

All network I/O is isolated in `telnet_client.py`. Command builders are pure functions that return strings. The navigation layer orchestrates cd/list workflows with parsed telnet feedback.

## Configuration

Create a `.env` file (see `.env.template`):

```env
# grandMA2 Console
GMA_HOST=192.168.1.100     # grandMA2 console IP (required)
GMA_USER=administrator     # default: administrator
GMA_PASSWORD=admin         # default: admin
GMA_PORT=30000             # default: 30000 (30001 = read-only)
GMA_SAFETY_LEVEL=standard  # standard (default), admin, or read-only
LOG_LEVEL=INFO             # default: INFO

# RAG Pipeline (optional)
GITHUB_MODELS_TOKEN=                          # GitHub PAT with models:read scope
RAG_EMBED_MODEL=openai/text-embedding-3-small # embedding model
RAG_EMBED_DIMENSIONS=1536                     # vector dimensions
```

Get a GitHub PAT with the `models:read` scope at [github.com/settings/tokens](https://github.com/settings/tokens). See [GitHub Docs — Managing personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).

| Level | Behavior |
|-------|----------|
| `read-only` | Only SAFE_READ commands allowed (list, info, cd) |
| `standard` | SAFE_READ + SAFE_WRITE allowed; DESTRUCTIVE requires `confirm_destructive=True` |
| `admin` | All commands allowed without confirmation |

## MCP Tools

The server exposes **82 tools** to MCP clients, grouped by category:

<details>
<summary><strong>Navigation & Inspection (4 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `navigate_console` | Navigate the console object tree via ChangeDest (cd) |
| `get_console_location` | Query the current console destination without navigating |
| `list_console_destination` | List objects at the current destination with parsed entries |
| `scan_console_indexes` | Batch scan numeric indexes at any tree level |

```
cd /            → go to root
cd ..           → go up one level
cd Group.1      → navigate to Group 1 (dot notation)
cd 5            → navigate by element index
cd "MySeq"      → navigate by name
list            → enumerate objects at current destination
```

**Workflow:** Use `navigate_console` to cd into a location, then `list_console_destination` to enumerate children. Both return JSON with raw telnet responses and parsed structure (object-type, object-id, element name).

**Dot notation:** MA2 uses `[object-type].[object-id]` for object references (e.g., `Group.1`, `Preset.4.1`, `Sequence.3`).

</details>

<details>
<summary><strong>Lighting Control (6 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `set_intensity` | Set dimmer level on fixtures, groups, or channels |
| `set_attribute` | Set attribute values (Pan, Tilt, Zoom, etc.) on fixtures/groups |
| `apply_preset` | Apply a stored preset (color, position, gobo, beam, etc.) |
| `clear_programmer` | Clear programmer state (all, selection, active, or sequential) |
| `park_fixture` | Park a fixture/channel at its current or a specified value |
| `unpark_fixture` | Release a park lock on a fixture/channel |

</details>

<details>
<summary><strong>Programmer / Selection (7 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `modify_selection` | Select, deselect, or toggle fixtures in the programmer |
| `adjust_value_relative` | Adjust programmer values relatively (+ or –) |
| `select_fixtures_by_group` | Select all fixtures in a named group |
| `select_executor` | Set the active executor for subsequent operations |
| `select_feature` | Set active Feature context (updates $PRESET/$FEATURE/$ATTRIBUTE) |
| `select_preset_type` | Activate a PresetType context (PresetType 1-9 or by name) |
| `if_filter` | Apply an IfOutput / IfActive filter to limit programmer scope |

</details>

<details>
<summary><strong>Playback & Executor (8 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `execute_sequence` | Legacy sequence playback: go, pause, or goto cue |
| `playback_action` | Full playback control: go, go_back, goto, fast_forward, fast_back, def_go, def_pause |
| `control_executor` | Control an executor (go, pause, stop, flash, etc.) |
| `get_executor_status` | Query status of an executor (current cue, level, state) |
| `set_executor_level` | Set the fader level on an executor |
| `navigate_page` | Navigate to a specific page or page +/– |
| `release_executor` | Release (deactivate) an executor |
| `blackout_toggle` | Toggle grandmaster blackout on/off |

</details>

<details>
<summary><strong>Programming / Store (11 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `create_fixture_group` | Select a range of fixtures and save as a named group |
| `store_current_cue` | Store programmer state into a cue (**DESTRUCTIVE**) |
| `store_new_preset` | Store programmer state as a new preset (**DESTRUCTIVE**) |
| `store_object` | Store generic objects — macros, effects, worlds, etc. (**DESTRUCTIVE**) |
| `store_cue_with_timing` | Store a cue with explicit fade/delay timing (**DESTRUCTIVE**) |
| `update_cue_data` | Update an existing cue with current programmer values |
| `set_cue_timing` | Edit fade, delay, or trigger timing on an existing cue |
| `set_sequence_property` | Set a property on a sequence (e.g. looping, autoprepare) |
| `assign_cue_trigger` | Assign a trigger type (Go, Follow, Time) to a cue |
| `remove_from_programmer` | Remove specific fixtures or channels from the programmer |
| `run_macro` | Execute a stored macro by ID |

</details>

<details>
<summary><strong>Timecode & Timer (3 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `control_timecode` | Start, stop, or jump a timecode show |
| `control_timer` | Start, stop, or reset a timer |
| `store_timecode_event` | Store an event into a timecode show at the current time |

</details>

<details>
<summary><strong>Assignment & Layout (6 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `assign_object` | Assign objects, functions, fades, or layout positions (**DESTRUCTIVE**) |
| `assign_executor_property` | Set a property on an executor (e.g. name, page, size) |
| `label_or_appearance` | Label or set visual appearance of objects (**DESTRUCTIVE**) |
| `edit_object` | Edit, cut, or paste objects (cut/paste **DESTRUCTIVE**) |
| `remove_content` | Remove content from objects — fixtures, effects, preset types (**DESTRUCTIVE**) |
| `save_recall_view` | Save or recall a screen view configuration |

</details>

<details>
<summary><strong>Show Management (6 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `save_show` | Save the current show file to disk |
| `list_shows` | List available show files on the console |
| `load_show` | Load a show file by name (**DESTRUCTIVE**) |
| `new_show` | Create a new empty show (**DESTRUCTIVE**) |
| `export_objects` | Export show objects (groups, presets, macros, etc.) to a file |
| `import_objects` | Import objects from a file into the show (**DESTRUCTIVE**) |

</details>

<details>
<summary><strong>Fixture Setup & Patch (13 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `list_fixture_types` | List fixture types loaded in the show |
| `list_layers` | List fixture layers in the patch |
| `list_universes` | List configured DMX universes |
| `list_library` | Browse the MA2 fixture library |
| `list_fixtures` | List fixtures currently patched in the show |
| `browse_patch_schedule` | Browse the DMX patch schedule (fixture → universe → address) |
| `patch_fixture` | Patch a fixture to a DMX universe and address |
| `unpatch_fixture` | Remove a fixture's DMX patch assignment |
| `set_fixture_type_property` | Set a property on a fixture type |
| `manage_matricks` | Manage MAtricks (fixture matrix) objects |
| `import_fixture_type` | Import a fixture type from the MA2 library (**DESTRUCTIVE**) |
| `import_fixture_layer` | Import a fixture layer XML file into the show patch (**DESTRUCTIVE**) |
| `generate_fixture_layer_xml` | Generate a grandMA2 fixture layer XML file for import |

**Fixture import workflow:**
```python
# 1. Generate the XML file
generate_fixture_layer_xml(
    filename="my_dimmers",
    layer_name="Dimmers",
    layer_index=1,
    fixtures=[
        {"fixture_id": 1, "name": "Dim 1", "fixture_type_no": 2,
         "fixture_type_name": "2 Dimmer 00", "dmx_address": 1, "num_channels": 1},
        # ... more fixtures
    ],
    showfile="myshow",
)

# 2. Import the fixture type from library
import_fixture_type(
    manufacturer="Martin",
    fixture="Mac700Profile_Extended",
    mode="Extended",
    confirm_destructive=True,
)

# 3. Import the layer
import_fixture_layer(filename="my_dimmers", layer_index=1, confirm_destructive=True)
```

</details>

<details>
<summary><strong>Info, Queries & Discovery (11 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `get_object_info` | Query info on any object (fixture, group, sequence, etc.) |
| `query_object_list` | List cues, groups, presets, attributes, or messages from the show |
| `get_variable` | Get the current value of a console variable |
| `list_system_variables` | List all 26 built-in system variables ($TIME, $SHOWFILE, etc.) |
| `list_sequence_cues` | List all cues in a sequence with timing and labels |
| `discover_object_names` | Discover named objects in a pool via the cd tree |
| `browse_preset_type` | Browse Feature/Attribute/SubAttribute tree for a PresetType (cd 10.2.N) |
| `list_preset_pool` | List presets in the Global preset pool by type (cd 17 tree) |
| `highlight_fixtures` | Toggle highlight mode for selected fixtures |
| `set_node_property` | Set a property on any node via dot-separated tree path |
| `list_undo_history` | List recent undo history entries |

</details>

<details>
<summary><strong>Console & Utilities (6 tools)</strong></summary>

| Tool | Description |
|------|-------------|
| `send_raw_command` | Send any MA command directly (safety-gated) |
| `copy_or_move_object` | Copy or move objects between slots (with merge/overwrite options) |
| `delete_object` | Delete any object by type and ID (**DESTRUCTIVE**) |
| `manage_variable` | Set or add to console variables (global or user-scoped) |
| `undo_last_action` | Undo the last console action |
| `toggle_console_mode` | Toggle console modes: blind, highlight, freeze, solo |

</details>

<details>
<summary><strong>Codebase Search / RAG (1 tool)</strong></summary>

| Tool | Description |
|------|-------------|
| `search_codebase` | Semantic search over the indexed codebase and MA2 docs |

</details>

## Client Setup

### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "gma2": {
      "command": "uv",
      "args": ["--directory", "/path/to/gma2-mcp-telnet", "run", "python", "-m", "src.server"],
      "env": {
        "GMA_HOST": "192.168.1.100",
        "GMA_USER": "administrator",
        "GMA_PASSWORD": "admin"
      }
    }
  }
}
```

### VS Code

The `vscode-mcp-provider/` directory contains a VS Code extension that registers the grandMA2 MCP server for AI assistant discovery.

- Registers the MCP server via the Model Context Protocol stdio transport
- Compatible with Claude, GitHub Copilot (when MCP-supported), and other MCP-aware assistants
- Launches the server using `uv run python -m src.server` in the workspace

```bash
cd vscode-mcp-provider
npm install
npm run compile
# Then install the extension in VS Code (F5 to debug, or package with vsce)
```

See [`vscode-mcp-provider/README.md`](vscode-mcp-provider/README.md) for full details.

## RAG Pipeline

The `rag/` module indexes the repository into a local SQLite vector store for semantic code search, enabling AI assistants to find relevant grandMA2 command examples and documentation.

```
crawl → chunk → embed → store (SQLite) → query → rerank
```

### Setup

1. Get a GitHub PAT with `models:read` scope at [github.com/settings/tokens](https://github.com/settings/tokens)
2. Set your token:
   ```bash
   export GITHUB_MODELS_TOKEN=ghp_...
   ```
   Or add `GITHUB_MODELS_TOKEN=ghp_...` to your `.env` file.

### Usage

```bash
# Ingest repository into vector store
uv run python scripts/rag_ingest.py --provider github -v

# Semantic vector search
uv run python scripts/rag_query.py "store cue with fade" -v

# Text-only keyword search (no token needed)
uv run python scripts/rag_query.py "store cue with fade"
```

### Provider Options

| Flag | Behavior |
|------|----------|
| `--provider github` | Use GitHub Models embeddings (requires `GITHUB_MODELS_TOKEN`) |
| `--provider zero` | Zero-vector stub (for testing without an API token) |
| *(no flag)* | Auto-detect: GitHub if token is set, otherwise zero-vector (ingest) or text search (query) |

<details>
<summary><strong>Pipeline stages</strong></summary>

#### Ingest

| Stage | Module | Description |
|-------|--------|-------------|
| Crawl | `rag/ingest/crawl_repo.py` | Walk repo files, respect ignore patterns (`rag/ignore.py`) |
| Chunk | `rag/ingest/chunk.py` | Split files into overlapping token-bounded chunks |
| Extract | `rag/ingest/extract.py` | Extract symbol names (functions, classes, headings) |
| Embed | `rag/ingest/embed.py` | Generate vector embeddings via GitHub Models API |
| Store | `rag/store/sqlite.py` | Write chunks + vectors to SQLite |
| Orchestrate | `rag/ingest/index.py` | End-to-end ingest pipeline |

#### Retrieve

| Stage | Module | Description |
|-------|--------|-------------|
| Query | `rag/retrieve/query.py` | Embed query, cosine similarity search against stored vectors |
| Rerank | `rag/retrieve/rerank.py` | Sort and filter results by relevance score |

</details>

<details>
<summary><strong>Chunking strategies</strong></summary>

| Language | Strategy | Boundary |
|----------|----------|----------|
| Python | AST-based | Top-level `def`/`class` boundaries via `ast.parse` |
| Markdown | Heading-based | `#` heading lines |
| Other | Line-based | Fixed-size line windows with overlap |

Defaults: max 1200 tokens/chunk, 20-line overlap. Configured in `rag/config.py`.

</details>

## Console Navigation & Prompt Parsing

The navigation system combines three layers to discover console state via telnet:

1. **Command builder** (`changedest()`) generates cd strings with MA2 dot notation
2. **Telnet client** sends the command and captures the raw response
3. **Prompt parser** extracts the current location from the response

<details>
<summary><strong>Prompt parsing patterns</strong></summary>

The parser detects MA2 console prompts using multiple patterns:

| Pattern | Example | Parsed |
|---------|---------|--------|
| Bracket prompt | `[Group 1]>` | location=`Group 1`, type=`Group`, id=`1` |
| Dot notation prompt | `[Group.1]>` | location=`Group.1`, type=`Group`, id=`1` |
| Compound ID | `[Preset.4.1]>` | location=`Preset.4.1`, type=`Preset`, id=`4.1` |
| Trailing slash | `[Sequence 3]>/` | location=`Sequence 3`, type=`Sequence`, id=`3` |
| Angle bracket | `Root>` | location=`Root`, type=`Root` |

When no recognizable prompt is found, the raw response is preserved for manual inspection.

</details>

<details>
<summary><strong>List output parsing</strong></summary>

After cd-ing into a destination, `list` returns tabular output with column headers followed by data rows. The parser automatically detects headers and maps column values to named fields.

**Entry structure:**

| Field | Description |
|-------|-------------|
| `object_type` | Type name (e.g. `Group`, `UserImage`, `History`) |
| `object_id` | Numeric ID within the parent |
| `name` | Display name |
| `col3` | Third column for tabular entries (e.g. version number) |
| `columns` | Dict mapping extra header names to their values |
| `raw_line` | Full original line for manual inspection |

**Column parsing examples:**

| Header Row | Entry | Parsed `columns` |
|------------|-------|-------------------|
| `No.  Name  Width  Height  Bytes  Info` | `UserImage 1 ... PAR  240  240  3629` | `{Width: 240, Height: 240, Bytes: 3629}` |
| `Version  Beta  Date  Name  Info` | `History 1 3.7.0.5 ... Mar 16 2022` | `{Date: Mar 16 2022, ...}` |
| `No.  Name  Key  Color` | `Gel 1 ... R80  100.0 100.0 100.0` | `{Key: R80, Color: 100.0 100.0 100.0}` |
| *(root-level key=value)* | `Settings 3  Agenda=Running (6)` | `{Agenda: Running, child_count: 6}` |

Root-level entries use `key=value` format (parsed automatically), while tabular entries use positional columns aligned to the header row.

</details>

## Tree Scanner

`scripts/scan_tree.py` recursively walks the grandMA2 object tree via Telnet, building a complete JSON map of every node, child, and leaf in the console's internal data structure.

### How It Works

1. `cd /` -- navigate to root
2. `list` -- enumerate children (get valid indexes + full column output)
3. `cd N` -- enter each child by index
4. `list` -- capture raw output (headers + columns + values)
5. Recurse until `list` returns 0 entries (leaf) or max depth is reached
6. `cd ..` / `cd /` -- return to parent between branches

### Usage

```bash
# Quick scan (depth 4, for testing)
uv run python scripts/scan_tree.py --max-depth 4 --output scan_test.json

# Full scan (depth 20, all optimizations)
uv run python scripts/scan_tree.py --max-depth 20 --output scan_full.json

# Resume an interrupted scan
uv run python scripts/scan_tree.py --max-depth 20 --output scan_full.json --resume
```

<details>
<summary><strong>Scanner options</strong></summary>

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | from `.env` | Console IP address |
| `--port` | 30000 | Telnet port |
| `--max-depth` | 20 | Maximum recursion depth |
| `--max-nodes` | 0 | Stop after N nodes (0 = unlimited) |
| `--max-index` | 60 | Fallback index limit when list has no parseable IDs |
| `--failures` | 3 | Stop branch after N consecutive missing indexes |
| `--output` | `scan_output.json` | Output JSON file path |
| `--delay` | 0.08 | Seconds between commands |
| `--timeout` | 0.8 | Telnet read timeout per command |
| `--max-gap-probe` | 5 | Max gap between consecutive IDs to probe |
| `--empty-leaf-limit` | 10 | Stop after N consecutive empty leaves (0 = off) |
| `--health-check-interval` | 500 | Health check every N nodes (0 = disabled) |
| `--no-leaf-shortcut` | false | Disable known-leaf-type optimization |
| `--progress-file` | auto | JSONL progress file path |
| `--resume` | false | Resume scan from progress file |
| `--heartbeat-every` | 200 | Print heartbeat status every N nodes (0 = disabled) |
| `--branch-timeout` | 0 | Per-branch timeout in seconds (0 = unlimited) |
| `--disconnect-timeout` | 5 | Timeout for telnet disconnect in seconds |

</details>

<details>
<summary><strong>Speed optimizations</strong></summary>

The scanner includes several optimizations to handle large trees (7000+ nodes):

- **Known leaf-type shortcutting** -- Builds leaf nodes from parent list data without cd+list, saving ~1s per node for known types (History, Gel, Universe, RDM_Universe, UserImage)
- **Smart gap probing** -- Only fills gaps <=5 between known IDs, preventing ranges like [1, 467] from generating 466 extra probes
- **Duplicate detection** -- Compares raw `list` output signatures to skip identical subtrees (saves ~1000 nodes on a typical full scan)
- **Consecutive empty leaf early exit** -- Stops scanning a branch after 10 consecutive empty slots
- **Subsequent-read timeout** -- Reduced from 0.3s to 0.1s per telnet read, saving ~100 min across a full scan

</details>

<details>
<summary><strong>Resilience features</strong></summary>

- **Auto-reconnect** -- Detects dead connections (empty responses) and reconnects with full path recovery
- **Progressive save** -- Writes completed branches to a JSONL file after each root branch, preventing data loss on interruption
- **Resume support** -- Reloads progress file on startup, skips completed branches, and rebuilds duplicate-detection cache for continuity across sessions
- **Heartbeat logging** -- Prints periodic status during long-running branches so progress is visible even when a single branch takes hours
- **Branch timeout** -- Optional per-branch time limit to skip branches that exceed a threshold, preventing the scanner from getting stuck
- **Disconnect timeout** -- Wraps telnet disconnect in a timeout to prevent process hangs from stale connections
- **Progress file hygiene** -- Fresh (non-resume) runs truncate the progress file to avoid mixing data from prior runs

</details>

## Command Builder Reference

The command builder (`src/commands/`) generates grandMA2 command strings without any network I/O. All functions are pure and return `str`. There are 110+ exported functions covering navigation, selection, playback, values, store, delete, assign, label, info, park, call, variables, and more.

grandMA2 syntax: `[Function] [Object]` -- keywords are classified as **Function** (verbs), **Object** (nouns), or **Helping** (prepositions).

<details>
<summary><strong>Full command builder reference (click to expand)</strong></summary>

### Navigation (ChangeDest)

| Function | Output |
|----------|--------|
| `changedest("/")` | `cd /` |
| `changedest("..")` | `cd ..` |
| `changedest("5")` | `cd 5` |
| `changedest('"MySequence"')` | `cd "MySequence"` |
| `changedest("Group", 1)` | `cd Group.1` |
| `changedest("Preset", "4.1")` | `cd Preset.4.1` |
| `changedest("Group")` | `cd Group` |

### Object Keywords

| Function | Example | Output |
|----------|---------|--------|
| `fixture(34)` | Select by Fixture ID | `fixture 34` |
| `channel(11, sub_id=5)` | Select by Channel ID | `channel 11.5` |
| `group(3)` | Select a group | `group 3` |
| `preset("color", 5)` | Apply a preset | `preset 4.5` |
| `cue(5)` | Reference a cue | `cue 5` |
| `cue_part(5, 2)` | Reference a cue part | `cue 5 part 2` |
| `sequence(3)` | Reference a sequence | `sequence 3` |
| `executor(1)` | Reference an executor | `executor 1` |
| `dmx(101, universe=2)` | Reference DMX address | `dmx 2.101` |
| `dmx_universe(1)` | Reference DMX universe | `dmxuniverse 1` |
| `layout(1)` | Reference a layout | `layout 1` |
| `attribute("Pan")` | Reference an attribute | `attribute "Pan"` |
| `feature(1)` | Reference a feature | `feature 1` |
| `timecode(1)` | Reference a timecode show | `timecode 1` |
| `timer(1)` | Reference a timer | `timer 1` |

### Selection & Clear

| Function | Output |
|----------|--------|
| `select_fixture(1, 10)` | `selfix fixture 1 thru 10` |
| `select_fixture([1, 3, 5])` | `selfix fixture 1 + 3 + 5` |
| `clear()` | `clear` |
| `clear_selection()` | `clearselection` |
| `clear_active()` | `clearactive` |
| `clear_all()` | `clearall` |

### Store

| Function | Output |
|----------|--------|
| `store("macro", 5)` | `store macro 5` |
| `store_cue(1, merge=True)` | `store cue 1 /merge` |
| `store_preset("dimmer", 3)` | `store preset 1.3` |
| `store_group(1)` | `store group 1` |

Store options: `merge`, `overwrite`, `remove`, `noconfirm`, `cueonly`, `tracking`, `source`, and more.

### Playback

| Function | Output |
|----------|--------|
| `go(executor_id=1)` | `go executor 1` |
| `go_back(executor_id=1)` | `goback executor 1` |
| `goto(cue_id=5)` | `goto cue 5` |
| `go_sequence(1)` | `go+ sequence 1` |
| `pause_sequence(1)` | `pause sequence 1` |
| `goto_cue(1, 5)` | `goto cue 5 sequence 1` |
| `go_fast_back()` | `<<<` |
| `go_fast_forward()` | `>>>` |
| `def_go_forward()` | `go+` |
| `def_go_back()` | `goback-` |
| `def_go_pause()` | `pause` |

### At (Values)

`At` can function as both a Function Keyword and a Helping Keyword.

| Function | Output |
|----------|--------|
| `at(75)` | `at 75` |
| `at(cue=3)` | `at cue 3` |
| `at(fade=2)` | `at fade 2` |
| `at_full()` | `at full` |
| `at_zero()` | `at 0` |
| `attribute_at("Pan", 20)` | `attribute "Pan" at 20` |
| `fixture_at(2, 50)` | `fixture 2 at 50` |
| `fixture_at(2, source_fixture=3)` | `fixture 2 at fixture 3` |
| `channel_at(1, 75)` | `channel 1 at 75` |
| `group_at(3, 50)` | `group 3 at 50` |
| `executor_at(3, 50)` | `executor 3 at 50` |
| `preset_type_at(2, 50, end_type=9)` | `presettype 2 thru 9 at 50` |

### Copy, Move, Cut, Paste

| Function | Output |
|----------|--------|
| `copy("group", 1, 5)` | `copy group 1 at 5` |
| `copy("group", 1, end=3, target=11)` | `copy group 1 thru 3 at 11` |
| `copy_cue(2, 6)` | `copy cue 2 at 6` |
| `move("group", 5, 9)` | `move group 5 at 9` |
| `cut("preset", "4.1")` | `cut preset 4.1` |
| `paste("group", 5)` | `paste group 5` |

Copy/Move options: `overwrite`, `merge`, `status`, `cueonly`, `noconfirm`

### Delete & Remove

| Function | Output |
|----------|--------|
| `delete("cue", 7)` | `delete cue 7` |
| `delete_cue(1, end=5, noconfirm=True)` | `delete cue 1 thru 5 /noconfirm` |
| `delete_group(3)` | `delete group 3` |
| `delete_preset("color", 5)` | `delete preset 4.5` |
| `delete_fixture(4)` | `delete fixture 4` |
| `delete_messages()` | `delete messages` |
| `remove("selection")` | `remove selection` |
| `remove_preset_type("position")` | `remove presettype "position"` |
| `remove_fixture(1, if_filter="PresetType 1")` | `remove fixture 1 if PresetType 1` |
| `remove_effect(1)` | `remove effect 1` |

### Assign

| Function | Output |
|----------|--------|
| `assign("sequence", 1, "executor", 6)` | `assign sequence 1 at executor 6` |
| `assign("dmx", "2.101", "channel", 5)` | `assign dmx 2.101 at channel 5` |
| `assign_function("Toggle", "executor", 101)` | `assign toggle at executor 101` |
| `assign_fade(3, 5)` | `assign fade 3 cue 5` |
| `assign_to_layout("group", 1, 1, x=5, y=2)` | `assign group 1 at layout 1 /x=5 /y=2` |
| `assign_property(1, "Telnet", "Login Disabled")` | `assign 1/Telnet="Login Disabled"` |
| `empty("executor", 1)` | `empty executor 1` |
| `temp_fader("executor", 1)` | `temp_fader executor 1` |

### Label & Appearance

| Function | Output |
|----------|--------|
| `label("group", 3, "All Studiocolors")` | `label group 3 "All Studiocolors"` |
| `label_group(1, "Front")` | `label group 1 "Front"` |
| `label_preset("color", 1, "Red")` | `label preset 4.1 "Red"` |
| `appearance("preset", "0.1", red=100)` | `appearance preset 0.1 /r=100` |
| `appearance("group", 1, color="FF0000")` | `appearance group 1 /color=FF0000` |

### Info & List

| Function | Output |
|----------|--------|
| `list_objects("cue")` | `list cue` |
| `list_group()` | `list group` |
| `list_preset("color")` | `list preset "color"` |
| `info("cue", 1)` | `info cue 1` |
| `info_group(3)` | `info group 3` |

### Import / Export

| Function | Output |
|----------|--------|
| `export_object("Group", 1, "mygroups")` | `export Group 1 "mygroups"` |
| `import_object("mygroups", "Group", 5)` | `import "mygroups" at Group 5` |
| `import_fixture_type_cmd("Martin", "Mac700Profile_Extended", "Extended")` | `Import "Martin@Mac700Profile_Extended@Extended"` |
| `import_layer_cmd("dimmers")` | `Import "dimmers"` |
| `import_layer_cmd("mac700s", 2)` | `Import "mac700s" At 2` |

Note: `import_fixture_type_cmd` and `import_layer_cmd` are context-dependent — they must be sent while inside `EditSetup/FixtureTypes` and `EditSetup/Layers` respectively. Use the `import_fixture_type` and `import_fixture_layer` MCP tools which handle the context navigation automatically.

### Park & Unpark

| Function | Output |
|----------|--------|
| `park("fixture", 1)` | `park fixture 1` |
| `park("dmx", 101, value=128)` | `park dmx 101 at 128` |
| `unpark("fixture", 1)` | `unpark fixture 1` |

### Call

| Function | Output |
|----------|--------|
| `call("preset", "2.1")` | `call preset 2.1` |
| `call("cue", 3, sequence=1)` | `call cue 3 sequence 1` |

### Variables

| Function | Output |
|----------|--------|
| `set_var("myvar", 42)` | `setvar "myvar" 42` |
| `set_user_var("speed", 100)` | `setuservar "speed" 100` |
| `add_var("counter", 1)` | `addvar "counter" 1` |
| `add_user_var("counter", 1)` | `adduservar "counter" 1` |

### Helping Keywords

| Function | Output |
|----------|--------|
| `at_relative(10)` | `+ 10` |
| `at_relative(-5)` | `- 5` |
| `add_to_selection("fixture", 5)` | `+ fixture 5` |
| `remove_from_selection("fixture", 3)` | `- fixture 3` |
| `page_next()` | `page +` |
| `page_previous()` | `page -` |
| `condition_and("group", 1)` | `and group 1` |
| `if_condition("PresetType", 1)` | `if PresetType 1` |

### Macro Placeholder (@)

The `@` character is a placeholder for user input in macros (distinct from the `At` keyword).

| Function | Output |
|----------|--------|
| `macro_with_input_after("Load")` | `Load @` |
| `macro_with_input_before("Fade 20")` | `@ Fade 20` |

</details>

## Safety System

### Keyword Categories

The vocabulary (schema v2.0) classifies all 148 grandMA2 keywords into categories:

| Category | Count | Description | Examples |
|----------|-------|-------------|----------|
| `OBJECT` | 56 | Console objects (nouns) | Channel, Fixture, Group, Preset, Executor |
| `FUNCTION` | 79 | Actions (verbs) | Store, Delete, Go, At, List, Info |
| `HELPING` | 7 | Syntax connectors | And, Thru, Fade, Delay, If |
| `SPECIAL_CHAR` | 6 | Operator symbols | Plus +, Minus -, Dot ., Slash / |

Object Keywords carry additional metadata from live telnet verification:

| Field | Description |
|-------|-------------|
| `context_change` | Whether the keyword changes the `[default]>` prompt context |
| `canonical` | Console-normalized spelling (e.g., DMX resolves to Dmx) |
| `notes` | Behavior notes from live telnet testing |

Of the 56 Object Keywords: 51 change the default prompt context, 2 reset it (Channel, Default), and 3 don't change it (Full, Normal, Zero -- these set dimmer values).

### Risk Tiers

Each keyword is also assigned a risk tier for safety gating:

| Tier | Description | Examples |
|------|-------------|----------|
| `SAFE_READ` | Read-only queries | Info, List, CmdHelp, ChangeDest |
| `SAFE_WRITE` | Reversible state changes | Go, At, Clear, Park, SelFix, + all Object Keywords |
| `DESTRUCTIVE` | Data mutation or loss | Delete, Store, Copy, Move, Shutdown |
| `UNKNOWN` | Unrecognized token | -- |

All Object Keywords (Channel, Fixture, Group, etc.) are classified as `SAFE_WRITE` because they change programmer context but don't mutate show data.

### Console Aliases

The vocabulary includes 4 console-normalized aliases verified via live telnet:

| Input | Resolves To |
|-------|-------------|
| `DMX` | `Dmx` |
| `DMXUniverse` | `DmxUniverse` |
| `Sound` | `SoundChannel` |
| `RDM` | `RdmFixtureType` |

### Runtime Safety Gate

The `send_raw_command` tool enforces safety at runtime before any command reaches the console:

1. **Command injection prevention** -- Line breaks (`\r`, `\n`) are rejected to prevent multi-command injection. The telnet client also strips them as a defense-in-depth measure.
2. **Token classification** -- The first token of every command is classified via `classify_token()` against the grandMA2 v3.9 keyword vocabulary.
3. **Tier enforcement** -- Based on `GMA_SAFETY_LEVEL`:
   - `read-only`: Only `SAFE_READ` commands pass
   - `standard` (default): `SAFE_READ` + `SAFE_WRITE` pass; `DESTRUCTIVE` blocked unless `confirm_destructive=True`
   - `admin`: All commands pass without confirmation

<details>
<summary><strong>classify_token() example</strong></summary>

```python
from src.vocab import build_v39_spec, classify_token

spec = build_v39_spec()

result = classify_token("Delete", spec)
# result.risk == RiskTier.DESTRUCTIVE
# result.canonical == "Delete"
# result.category == KeywordCategory.FUNCTION

result = classify_token("Channel", spec)
# result.risk == RiskTier.SAFE_WRITE
# result.category == KeywordCategory.OBJECT

result = classify_token("DMX", spec)
# result.canonical == "Dmx"  (alias resolution)
# result.category == KeywordCategory.OBJECT

# Object Keyword metadata
entry = spec.object_keyword_entries["Channel"]
# entry.context_change == True  (resets prompt to [Channel]>)
```

The vocabulary is sourced from `src/grandMA2_v3_9_telnet_keyword_vocabulary.json` (schema v2.0, categorized keywords with Object Keyword metadata).

</details>

## Project Structure

```
gma2-mcp-telnet/
├── Makefile                        # Shortcuts: server, log, test
├── scripts/
│   ├── main.py                     # Login test script
│   ├── scan_tree.py                # Recursive object-tree scanner
│   ├── rag_ingest.py               # RAG ingestion script
│   ├── rag_query.py                # RAG query script
│   ├── condensed_tree.py           # Condensed tree output formatter
│   ├── parse_log_tree.py           # Log-based tree parser
│   ├── connect.sh                  # Interactive Telnet session via expect
│   ├── test_keywords.py            # Live Object Keyword validation
│   ├── validate_ft_channels.py     # FT ChannelType CD vs DMX order
│   └── research_hierarchy.py       # Preset/Sequence/Executor hierarchy
├── src/
│   ├── server.py                   # MCP server (FastMCP, 82 tools)
│   ├── telnet_client.py            # Async Telnet client (telnetlib3)
│   ├── navigation.py               # Navigation API (cd + list + parsing)
│   ├── prompt_parser.py            # Telnet prompt & list output parser
│   ├── tools.py                    # Global client instance management
│   ├── vocab.py                    # Keyword vocabulary, categories & safety tiers
│   ├── grandMA2_v3_9_telnet_keyword_vocabulary.json  # Schema v2.0
│   └── commands/
│       ├── __init__.py             # Public API (110+ exports)
│       ├── constants.py            # PRESET_TYPES, store option sets
│       ├── helpers.py              # quote_name(), _build_options() flag assembly
│       ├── objects/                # Object keywords (9 modules)
│       └── functions/              # Function keywords (15 modules)
├── rag/
│   ├── config.py                   # Pipeline constants (chunk size, top-k, etc.)
│   ├── types.py                    # Data types (RepoFile, Chunk, SearchHit)
│   ├── ignore.py                   # Ignore patterns for repo crawling
│   ├── ingest/
│   │   ├── crawl_repo.py           # Repository file walker
│   │   ├── chunk.py                # AST/heading/line-based chunking
│   │   ├── extract.py              # Symbol extraction (functions, classes, headings)
│   │   ├── embed.py                # Embedding providers (GitHub Models, zero-vector)
│   │   └── index.py                # End-to-end ingest orchestration
│   ├── retrieve/
│   │   ├── query.py                # Vector similarity + text search
│   │   └── rerank.py               # Result ranking
│   ├── store/
│   │   └── sqlite.py               # SQLite vector store
│   └── utils/
│       ├── hash.py                 # SHA-256 hashing
│       ├── lang.py                 # Language detection
│       └── text.py                 # Text utilities
├── tests/                          # 1147 unit tests + 43 live tests (skipped by default)
├── vscode-mcp-provider/            # VS Code MCP extension
├── doc/
│   └── 2024-09-30_grandMA2_User_Manual_v3-9.pdf
├── pyproject.toml
├── pytest.ini
└── uv.lock
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `mcp>=1.21.0` | Model Context Protocol server framework |
| `python-dotenv>=1.0.0` | Load `.env` configuration |
| `telnetlib3>=2.0.8` | Async Telnet client (replaces deprecated `telnetlib`) |
| `beautifulsoup4>=4.12.0` | HTML parsing for RAG web doc crawler |
| `httpx` *(transitive via mcp)* | HTTP client used by GitHub Models embedding provider |
| `pytest>=9.0.1` | Testing (dev) |
| `pytest-asyncio>=1.3.0` | Async test support (dev) |

Requires Python >= 3.12.

## Development

### Running Tests

```bash
make test                           # or: python -m pytest -v
python -m pytest tests/test_vocab.py   # run a specific file
python -m pytest tests/test_rag_*.py   # RAG pipeline tests
python -m pytest --cov=src tests/      # with coverage
```

### Login Test

```bash
python scripts/main.py              # test Telnet connection to console
```

### Direct Telnet

```bash
make server                         # interactive session via connect.sh
make log GMA_HOST=192.168.1.100     # read-only log stream (port 30001)
```

## Troubleshooting

**Connection fails** -- Verify console IP/port, check Telnet is enabled on the console, check firewall rules. Try `make server` for a raw connection test.

**Authentication errors** -- Confirm username/password, check the user exists on the console, ensure `.env` has no extra spaces.

**Command not working** -- Verify syntax against the grandMA2 User Manual. Ensure referenced objects (fixtures, groups, presets) exist in the show file.

**RAG ingest fails with 401** -- Verify `GITHUB_MODELS_TOKEN` has the `models:read` scope. Regenerate at [github.com/settings/tokens](https://github.com/settings/tokens).

**RAG query returns no results** -- Run `scripts/rag_ingest.py` first. Check that `rag/store/rag.db` exists and is non-empty.

## License

[Apache License 2.0](LICENSE)
