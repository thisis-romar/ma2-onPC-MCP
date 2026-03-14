---
title: Enterprise Tier
description: Placeholder for enterprise multi-console features
version: 0.2.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-14T00:00:00Z
---

# Enterprise Tier (Planned)

This directory is reserved for enterprise features including:

- **Multi-console routing** — manage multiple grandMA2 consoles from a single AI session
- **Safety interlocks** — hardware-level safety systems for live production environments
- **Audit logging** — complete command audit trail for production compliance
- **Session management** — multi-user session control and conflict prevention

## Content Marketplace Roadmap

The monetization infrastructure supports three tiers:

| Tier | What's included | Status |
|------|-----------------|--------|
| **Free** | Command reference, show architecture, networking skills (knowledge only) | Live |
| **Free-hybrid** | Macros, programming, Lua scripting skills + MCP execution | Live |
| **Premium** | Curated content libraries (filters, MAtricks, presets, macros) | Infrastructure ready |

### Premium content pipeline

All generated content (XML files for filters, MAtricks, fixture layers) now embeds **provenance metadata** as XML comments — tracking creator, source classification (human/ai-assisted/ai-generated), license, and human contribution notes. This metadata:

- Travels with the content file (MA2 ignores XML comments on import)
- Strengthens copyright claims by documenting human creative contribution
- Enables marketplace attribution and license enforcement

Content bundles use a **manifest.json** format (`build_content_manifest()`) for marketplace distribution, specifying name, version, pricing, dependencies, and fixture compatibility.

### Market context

- ~170+ paid products exist across AddOnDesk, MATools, MBLightarts, and Gumroad
- Established price points: €10-15/plugin, €65-500/bundle
- MA Lighting's EULA explicitly preserves user content ownership (Section 1)
- No enforcement history against content sellers

## Status

Enterprise features will be built on demand when production companies express interest.

## Contact

For enterprise inquiries, visit: https://github.com/thisis-romar/ma2-onPC-MCP
