# GMA2 MCP

MCP server for controlling grandMA2 lighting consoles via Telnet.

Exposes grandMA2 commands as [Model Context Protocol](https://modelcontextprotocol.io/) tools so that AI assistants (Claude Desktop, etc.) can operate a lighting console programmatically.

## Quick Start

```bash
# 1. Install
git clone <repository-url> && cd gma2-mcp-telnet
uv sync

# 2. Configure
cp .env.template .env        # then edit with your console IP

# 3. Run
uv run python -m src.server  # starts MCP server (stdio transport)
```

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  MCP Server Layer              src/server.py             │
│  6 tools: create_fixture_group, execute_sequence,        │
│           send_raw_command, navigate_console,             │
│           get_console_location, list_console_destination  │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│  Navigation Layer          src/navigation.py             │
│  navigate(), get_current_location(), list_destination()  │
│  Combines command builder + telnet I/O + prompt parsing  │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│  Command Builder Layer     src/commands/                  │
│  100+ pure functions generating grandMA2 command strings  │
│  Including changedest() for cd dot-notation commands      │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│  Telnet Client Layer       src/telnet_client.py           │
│  Async connection, auth, send/receive via telnetlib3      │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Prompt Parser             src/prompt_parser.py           │
│  parse_prompt() — detect console location from responses  │
│  parse_list_output() — extract entries + column headers   │
│    with automatic header detection and column mapping     │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Vocabulary & Safety       src/vocab.py                   │
│  Keyword classification and risk-tier analysis            │
└──────────────────────────────────────────────────────────┘
```

All network I/O is isolated in `telnet_client.py`. Command builders are pure functions that return strings. The navigation layer orchestrates cd/list workflows with parsed telnet feedback.

## Configuration

Create a `.env` file (see `.env.template`):

```env
GMA_HOST=192.168.1.100     # grandMA2 console IP (required)
GMA_USER=administrator     # default: administrator
GMA_PASSWORD=admin         # default: admin
GMA_PORT=30000             # default: 30000 (30001 = read-only)
LOG_LEVEL=INFO             # default: INFO
```

## MCP Tools

The server exposes six tools to MCP clients:

| Tool | Description |
|------|-------------|
| `create_fixture_group` | Select a range of fixtures and save as a named group |
| `execute_sequence` | Control sequence playback: go, pause, or goto cue |
| `send_raw_command` | Send any grandMA2 command (use with caution) |
| `navigate_console` | Navigate the console object tree via ChangeDest (cd) |
| `get_console_location` | Query the current console destination without navigating |
| `list_console_destination` | List objects at the current destination with parsed entries |

### Navigation Tools

The navigation tools provide structured exploration of the grandMA2 object tree:

```
cd /            → go to root
cd ..           → go up one level
cd Group.1      → navigate to Group 1 (dot notation)
cd 5            → navigate by element index
cd "MySeq"      → navigate by name
list            → enumerate objects at current destination
list group      → list only groups at current destination
```

**Workflow:** Use `navigate_console` to cd into a location, then `list_console_destination` to enumerate children. Both return JSON with raw telnet responses and parsed structure (object-type, object-id, element name).

**Dot notation:** MA2 uses `[object-type].[object-id]` for object references (e.g., `Group.1`, `Preset.4.1`, `Sequence.3`).

### Claude Desktop Registration

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

## Console Navigation & Prompt Parsing

The navigation system combines three layers to discover console state via telnet:

1. **Command builder** (`changedest()`) generates cd strings with MA2 dot notation
2. **Telnet client** sends the command and captures the raw response
3. **Prompt parser** extracts the current location from the response

### Prompt Parsing

The parser detects MA2 console prompts using multiple patterns:

| Pattern | Example | Parsed |
|---------|---------|--------|
| Bracket prompt | `[Group 1]>` | location=`Group 1`, type=`Group`, id=`1` |
| Dot notation prompt | `[Group.1]>` | location=`Group.1`, type=`Group`, id=`1` |
| Compound ID | `[Preset.4.1]>` | location=`Preset.4.1`, type=`Preset`, id=`4.1` |
| Trailing slash | `[Sequence 3]>/` | location=`Sequence 3`, type=`Sequence`, id=`3` |
| Angle bracket | `Root>` | location=`Root`, type=`Root` |

When no recognizable prompt is found, the raw response is preserved for manual inspection.

### List Output Parsing

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

## Tree Scanner

`scan_tree.py` recursively walks the grandMA2 object tree via Telnet, building a complete JSON map of every node, child, and leaf in the console's internal data structure.

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
uv run python scan_tree.py --max-depth 4 --output scan_test.json

# Full scan (depth 20, all optimizations)
uv run python scan_tree.py --max-depth 20 --output scan_full.json

# Resume an interrupted scan
uv run python scan_tree.py --max-depth 20 --output scan_full.json --resume
```

### Scanner Options

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

### Speed Optimizations

The scanner includes several optimizations to handle large trees (7000+ nodes):

- **Known leaf-type shortcutting** -- Builds leaf nodes from parent list data without cd+list, saving ~1s per node for known types (History, Gel, Universe, RDM_Universe, UserImage)
- **Smart gap probing** -- Only fills gaps <=5 between known IDs, preventing ranges like [1, 467] from generating 466 extra probes
- **Duplicate detection** -- Compares raw `list` output signatures to skip identical subtrees (saves ~1000 nodes on a typical full scan)
- **Consecutive empty leaf early exit** -- Stops scanning a branch after 10 consecutive empty slots
- **Subsequent-read timeout** -- Reduced from 0.3s to 0.1s per telnet read, saving ~100 min across a full scan

### Resilience Features

- **Auto-reconnect** -- Detects dead connections (empty responses) and reconnects with full path recovery
- **Progressive save** -- Writes completed branches to a JSONL file after each root branch, preventing data loss on interruption
- **Resume support** -- Reloads progress file on startup, skips completed branches, and rebuilds duplicate-detection cache for continuity across sessions
- **Heartbeat logging** -- Prints periodic status during long-running branches so progress is visible even when a single branch takes hours
- **Branch timeout** -- Optional per-branch time limit to skip branches that exceed a threshold, preventing the scanner from getting stuck
- **Disconnect timeout** -- Wraps telnet disconnect in a timeout to prevent process hangs from stale connections
- **Progress file hygiene** -- Fresh (non-resume) runs truncate the progress file to avoid mixing data from prior runs

## Command Builder Reference

The command builder (`src/commands/`) generates grandMA2 command strings without any network I/O. All functions return `str`.

grandMA2 syntax: `[Function] [Object]` -- keywords are classified as **Function** (verbs), **Object** (nouns), or **Helping** (prepositions).

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
| `preset("color", 5)` | Apply a preset | `preset 2.5` |
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
| `empty("executor", 1)` | `empty executor 1` |
| `temp_fader("executor", 1)` | `temp_fader executor 1` |

### Label & Appearance

| Function | Output |
|----------|--------|
| `label("group", 3, "All Studiocolors")` | `label group 3 "All Studiocolors"` |
| `label_group(1, "Front")` | `label group 1 "Front"` |
| `label_preset("color", 1, "Red")` | `label preset 2.1 "Red"` |
| `appearance("preset", "0.1", red=100)` | `appearance preset 0.1 /r=100` |
| `appearance("group", 1, color="FF0000")` | `appearance group 1 /color=FF0000` |

### Info & List

| Function | Output |
|----------|--------|
| `list_objects("cue")` | `list cue` |
| `list_group()` | `list group` |
| `list_preset("color")` | `list preset 4` |
| `info("cue", 1)` | `info cue 1` |
| `info_group(3)` | `info group 3` |

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

## Vocabulary & Safety Tiers

The `src/vocab.py` module classifies all grandMA2 keywords into risk tiers for use in safety middleware:

| Tier | Description | Examples |
|------|-------------|----------|
| `SAFE_READ` | Read-only queries | Info, List, CmdHelp, GetUserVar |
| `SAFE_WRITE` | Reversible state changes | Go, At, Clear, Park, SelFix |
| `DESTRUCTIVE` | Data mutation or loss | Delete, Store, Copy, Move, Shutdown |
| `UNKNOWN` | Unrecognized token | -- |

```python
from src.vocab import build_v39_spec, classify_token

spec = build_v39_spec()

result = classify_token("Delete", spec)
# result.risk == RiskTier.DESTRUCTIVE
# result.canonical == "Delete"

result = classify_token("li", spec)
# result.risk == RiskTier.SAFE_READ  (alias for "List")
```

The vocabulary is sourced from `src/grandMA2_v3_9_telnet_keyword_vocabulary.json` (grandMA2 v3.9).

## VS Code MCP Provider

The `vscode-mcp-provider/` directory contains a VS Code extension that registers the grandMA2 MCP server for AI assistant discovery.

### Features

- Registers the MCP server via the Model Context Protocol stdio transport
- Compatible with Claude, GitHub Copilot (when MCP-supported), and other MCP-aware assistants
- Launches the server using `uv run python -m src.server` in the workspace

### Setup

```bash
cd vscode-mcp-provider
npm install
npm run compile
# Then install the extension in VS Code (F5 to debug, or package with vsce)
```

## Project Structure

```
gma2-mcp-telnet/
├── main.py                         # Login test script
├── scan_tree.py                    # Recursive object-tree scanner
├── connect.sh                      # Interactive Telnet session via expect
├── Makefile                        # Shortcuts: server, log, test
├── src/
│   ├── server.py                   # MCP server (FastMCP, 6 tools)
│   ├── telnet_client.py            # Async Telnet client (telnetlib3)
│   ├── navigation.py               # Navigation API (cd + list + parsing)
│   ├── prompt_parser.py            # Telnet prompt & list output parser
│   ├── tools.py                    # Global client instance management
│   ├── vocab.py                    # Keyword vocabulary & safety tiers
│   ├── grandMA2_v3_9_telnet_keyword_vocabulary.json
│   └── commands/
│       ├── __init__.py             # Public API (100+ exports)
│       ├── constants.py            # PRESET_TYPES, store option sets
│       ├── helpers.py              # Internal option builder
│       ├── objects/                # Object keywords (9 modules)
│       └── functions/              # Function keywords (14 modules)
├── tests/                          # 588 tests (pytest + pytest-asyncio)
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
| `pytest>=9.0.1` | Testing (dev) |
| `pytest-asyncio>=1.3.0` | Async test support (dev) |

Requires Python >= 3.12.

## Development

### Running Tests

```bash
make test                           # or: uv run pytest -v
uv run pytest tests/test_vocab.py   # run a specific file
uv run pytest --cov=src tests/      # with coverage
```

### Login Test

```bash
python main.py                      # test Telnet connection to console
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

## License

Specify your license here.
