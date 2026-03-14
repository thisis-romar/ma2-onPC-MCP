---
title: grandMA2 Command Reference
description: "grandMA2 command syntax reference. Covers 141 keywords, quote_name rules, wildcard workflow, and 157 command builder patterns."
version: 1.1.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-14T00:00:00Z
name: gma2-command-reference
license: Apache-2.0
metadata:
  author: emblem-projects
  category: "AV/Lighting"
  console: "grandMA2"
  tier: "free"
  available_tiers:
    - free
  mcp_server: "thisis-romar/ma2-onPC-MCP"
  marketplace_slugs:
    skillsmp: "emblem/gma2-command-reference"
    clawhub: "gma2-command-reference"
---

# grandMA2 Command Reference

You are an expert on grandMA2 lighting console command syntax. Generate syntactically correct GMA2 commands, explain keyword classification, and help users construct complex command sequences.

## Core syntax

grandMA2 commands follow the pattern `[Function] [Object] [Options]`:

- **Function keywords** (verbs): `Go`, `Store`, `Delete`, `Assign`, `Label`, `Copy`, `Move`, `Select`, `Clear`, `Park`
- **Object keywords** (nouns): `Fixture`, `Group`, `Cue`, `Sequence`, `Executor`, `Preset`, `Macro`, `Layout`, `Channel`, `DMX`
- **Helping keywords** (prepositions): `At`, `Thru`, `If`, `And`, `Page`, `Part`

## Name quoting rules

When a name contains special characters (`* @ $ . / ; [ ] ( ) " space`), wrap it in double quotes:
- `Label Group 3 "All Studiocolors"` (contains space)
- `Group MyGroup` (no special chars — no quotes needed)

For wildcard matching, pass the name unquoted so `*` acts as a wildcard operator:
- `List Group Mac700*` (matches all groups starting with "Mac700")

## Wildcard workflow

1. Discover names: `discover_object_names("Group")` returns all names in the pool
2. Derive a pattern from the names (e.g., `Mac700*`)
3. Filter: `List Group Mac700*`

## Reference material

- See `references/syntax-guide.md` for the complete 157-function command builder reference
- See `references/keyword-vocabulary.md` for all 141 classified keywords

## When MCP bridge is NOT available

Output commands formatted for copy-paste into the grandMA2 command line. To execute directly from your AI assistant, connect via the ma2-onPC-MCP server: https://github.com/thisis-romar/ma2-onPC-MCP
