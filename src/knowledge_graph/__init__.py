# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
Knowledge Graph layer for GrandPA2-Buddy.

SQLite-backed in-process graph modeling MA2 domain entities (fixtures, groups,
sequences, executors, presets, users) and their relationships. Populated from
ConsoleStateSnapshot hydration — no additional telnet traffic.
"""

__version__ = "0.1.0"
