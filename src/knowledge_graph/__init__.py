# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
Knowledge Graph layer for GrandPA2-Buddy.

SQLite-backed in-process graph modeling MA2 domain entities (fixtures, groups,
sequences, executors, presets, users) and their relationships. Populated from
ConsoleStateSnapshot hydration — no additional telnet traffic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .store import GraphStore

__version__ = "0.1.0"

_graph_store: GraphStore | None = None


def get_graph_store() -> GraphStore | None:
    """Return the global GraphStore instance, or None if not initialized."""
    return _graph_store


def set_graph_store(store: GraphStore) -> None:
    """Set the global GraphStore instance (called during server startup or orchestrator init)."""
    global _graph_store
    _graph_store = store
