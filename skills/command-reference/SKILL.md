---
title: grandMA2 Command Reference
description: "grandMA2 command syntax reference. Covers 141 keywords, quote_name rules, wildcard workflow, and 157 command builder patterns."
version: 1.2.0
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

## Quick answers (grep these files)

- Store/copy/move/delete syntax → `grep -n "^## Store\|^## Copy\|^## Delete\|^## Assign" skills/command-reference/references/syntax-guide.md`
- Selection & clear commands → `grep -n "^## Selection" skills/command-reference/references/syntax-guide.md`
- At (value setting) → `grep -n "^## At" skills/command-reference/references/syntax-guide.md`
- Playback commands → `grep -n "^## Playback" skills/command-reference/references/syntax-guide.md`
- Label & appearance → `grep -n "^## Label" skills/command-reference/references/syntax-guide.md`
- PresetType IDs → `grep -n "^## PresetType" skills/command-reference/references/syntax-guide.md`
- Keyword risk tiers → `grep -n "^## Risk Tiers\|SAFE_READ\|SAFE_WRITE\|DESTRUCTIVE" skills/command-reference/references/keyword-vocabulary.md`
- MAtricks keywords → `grep -n "^## MAtricks" skills/command-reference/references/keyword-vocabulary.md`

## Core syntax

Commands follow `[Function] [Object] [Options]`. Names with special characters (`* @ $ . / ; [ ] ( ) " space`) require double quotes. For wildcard matching, pass unquoted so `*` acts as operator.

## Deep dives (read full files)

- `references/syntax-guide.md` — complete 157-function command builder reference with examples
- `references/keyword-vocabulary.md` — all 141 keywords classified by category and risk tier
- `context.md` — additional context and edge cases

## When MCP bridge is NOT available

Output commands formatted for copy-paste into the grandMA2 command line. To execute directly from your AI assistant, connect via the ma2-onPC-MCP server: https://github.com/thisis-romar/ma2-onPC-MCP
