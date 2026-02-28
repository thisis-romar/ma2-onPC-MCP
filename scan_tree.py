"""
scan_tree.py -- Recursive grandMA2 object-tree scanner via Telnet.

Walks the MA2 console's internal object tree using list-driven traversal:
  1. cd /       — always start at root
  2. list       — enumerate children (get valid indexes from parsed entries)
  3. cd N       — navigate into each child by its parsed index
  4. list       — capture full raw output (headers + columns + values)
  5. cd ..      — return to parent (verified), recover via absolute path if skipped
  6. cd /       — return to root between top-level branches

Key behaviors (validated by live telnet testing on MA2 v3.9):
  - cd / always returns to root (location = "Fixture")
  - cd .. works at most depths but CAN SKIP LEVELS (e.g. depth 4 -> depth 2)
  - cd N to nonexistent index -> Error #72, location unchanged (MISS)
  - Circular refs -> cd N stays at same location (MISS by location check)
  - list output provides valid child indexes (no blind probing needed)
  - Leaves = nodes where list returns 0 entries (natural termination)
  - null parsed location after cd -> treated as MISS, do not recurse

Index extraction strategy:
  - Primary: parse object_id from each list entry as the cd index
  - SubForm fix: when all parsed IDs are identical (e.g. SubForm entries where
    col2=col3=parent_slot), fall back to sequential 1..N indexes
  - Gap probing: after collecting list-derived indexes, probe gaps between
    them (e.g. if list gives [1,2,3,5], probe 4) because some children
    exist but are not shown by list (e.g. VirtualFunctionBlocks at cd 4)

Usage:
    uv run python scan_tree.py [options]

Options:
    --host 127.0.0.1     Console IP (default: from .env)
    --port 30000         Telnet port (default: 30000)
    --max-depth 20       Maximum recursion depth (default: 20)
    --max-nodes 0        Stop after N nodes (0 = unlimited)
    --max-index 60       Fallback index limit when list has no parseable IDs
    --failures 3         Stop a branch after N consecutive missing indexes
    --output scan_output.json
    --delay 0.2          Seconds between commands
    --timeout 2.0        Telnet read timeout per command
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Optional

from dotenv import get_key

from src.navigation import navigate, list_destination
from src.prompt_parser import _strip_ansi
from src.telnet_client import GMA2TelnetClient

# Suppress info/debug noise from navigation and telnet layers
logging.basicConfig(level=logging.WARNING)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class ScanConfig:
    host: str = "127.0.0.1"
    port: int = 30000
    user: str = "administrator"
    password: str = "admin"
    max_depth: int = 20           # default 20 — drill all leaves
    max_nodes: int = 0            # 0 = unlimited; stop after N visited nodes
    max_index: int = 60           # fallback limit when list returns no entries
    stop_after_failures: int = 3  # stop probing after N consecutive misses
    output_path: str = "scan_output.json"
    delay: float = 0.2
    timeout: float = 2.0


# ---------------------------------------------------------------------------
# Tree node
# ---------------------------------------------------------------------------

@dataclass
class TreeNode:
    path: str                        # dot-separated, e.g. "1.3.2"
    index: int                       # the cd N index that entered this node
    location: Optional[str]          # parsed_prompt.location
    object_type: Optional[str]       # parsed_prompt.object_type
    raw_list_text: str               # full stripped list output (headers + all columns)
    raw_list_entries: list[dict]     # serialized ListEntry dicts from list
    is_leaf: bool                    # True = list returned 0 entries
    children: list["TreeNode"] = field(default_factory=list)
    duplicate_of: Optional[str] = None  # path of original if this is a duplicate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LOCATION_TYPE_RE = re.compile(r'^([A-Za-z]\w*)(?:\s|/|$)')


def _entries_signature(entries, raw_list_text: str) -> Optional[str]:
    """Compute a hashable signature from list entries for duplicate detection.

    Uses the full raw list text (all column headers + values) as the
    signature.  This is deliberately strict: two nodes match only if their
    ``list`` output is character-for-character identical after ANSI/prompt
    stripping.  This prevents false matches between nodes that share the
    same child *types* but have different content (e.g. different fixture
    types that both have Modules/Instances/Wheels as children).

    Returns None if no entries (leaves can't be dupes).
    """
    if not entries:
        return None
    # The raw list text includes all column values, names, and counts
    # — a much stricter match than just type|id|name tuples
    return raw_list_text if raw_list_text.strip() else None


def _extract_type(location: Optional[str]) -> Optional[str]:
    """Extract the leading word from a location string as the object_type."""
    if not location:
        return None
    m = _LOCATION_TYPE_RE.match(location)
    return m.group(1) if m else None


def _child_indexes_from_entries(entries, max_index: int) -> list[int]:
    """Extract unique integer indexes from list entries, sorted.

    Uses the object_id from each parsed entry as the cd index.

    Special cases:
      - SubForm bug: if all parsed IDs are the same value (e.g. SubForm
        entries where col2=col3=parent_slot), the IDs don't represent cd
        indexes.  Fall back to sequential 1..N.
      - Gap probing: after collecting list-derived indexes, fill in any
        gaps in the sequence (e.g. list gives [1,2,3,5] -> add 4) because
        some children exist but are not shown by list (VirtualFunctionBlocks).
      - Falls back to range(1, max_index+1) if no entries have valid IDs.
    """
    raw_ids: list[int] = []
    for e in entries:
        oid = e.object_id if hasattr(e, 'object_id') else e.get("object_id")
        if oid is not None:
            try:
                idx = int(str(oid).split(".")[0])
                raw_ids.append(idx)
            except (ValueError, AttributeError):
                pass

    if not raw_ids:
        return list(range(1, max_index + 1))

    # SubForm fix: if all parsed IDs are identical (e.g. all "2"),
    # they represent the parent's slot number, not cd indexes.
    # Fall back to sequential 1..N where N = number of entries.
    unique_ids = set(raw_ids)
    if len(unique_ids) == 1 and len(raw_ids) > 1:
        return list(range(1, len(entries) + 1))

    # Deduplicate and sort
    indexes = sorted(unique_ids)

    # Gap probing: fill gaps between min and max so we don't miss
    # children that exist but aren't shown by list
    if len(indexes) >= 2:
        full_range = list(range(indexes[0], indexes[-1] + 1))
        indexes = full_range

    return indexes


def _clean_list_text(raw: str) -> str:
    """Strip ANSI codes and command echo/prompt lines from raw list output.

    Returns only the data lines (column headers + entries).
    """
    stripped = _strip_ansi(raw)
    lines = stripped.strip().splitlines()
    data_lines = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith("Executing"):
            continue
        if s.startswith("WARNING"):
            continue
        if s.startswith("Error"):
            continue
        # Skip prompt lines (end with > after stripping)
        if re.search(r'>\s*$', s):
            continue
        data_lines.append(s)
    return "\n".join(data_lines)


def _serialize_entries(entries) -> list[dict]:
    """Convert parsed ListEntry objects to serializable dicts."""
    result = []
    for e in entries:
        d = {
            "object_type": e.object_type,
            "object_id": e.object_id,
            "name": e.name,
            "raw_line": e.raw_line,
        }
        col3 = getattr(e, "col3", None)
        if col3 is not None:
            d["col3"] = col3
        result.append(d)
    return result


# ---------------------------------------------------------------------------
# Absolute navigation
# ---------------------------------------------------------------------------

async def _navigate_to_path(
    client: GMA2TelnetClient,
    abs_path: list[int],
    cfg: ScanConfig,
) -> Optional[str]:
    """Navigate from root to an absolute path: cd / then cd N1, cd N2, ...

    Returns the parsed location at the final step, or None if any step failed.
    """
    root_nav = await navigate(client, "/", timeout=cfg.timeout, delay=cfg.delay)
    current_loc = root_nav.parsed_prompt.location

    for idx in abs_path:
        nav = await navigate(client, str(idx), timeout=cfg.timeout, delay=cfg.delay)
        new_loc = nav.parsed_prompt.location
        if new_loc is None or new_loc == current_loc:
            return None
        current_loc = new_loc

    return current_loc


# ---------------------------------------------------------------------------
# Recursive scanner
# ---------------------------------------------------------------------------

async def _scan_children(
    client: GMA2TelnetClient,
    parent_abs_path: list[int],
    parent_location: Optional[str],
    ancestor_locations: set[str],
    child_indexes: list[int],
    depth: int,
    stats: dict,
    cfg: ScanConfig,
    sig_cache: dict,
) -> list[TreeNode]:
    """Scan child indexes at the current console position.

    Assumes the console is cd'd into the parent node (at parent_abs_path).
    On return, the console is back at the parent node.

    For each child:
      1. cd N         — enter child
      2. list         — capture full output (headers + all column values)
      3. [recurse]    — if child has entries, scan its children
         (skip if entries signature matches an already-scanned node)
      4. cd ..        — try to return to parent
      5. [verify]     — if cd .. skipped levels, re-navigate via absolute path
    """
    # Check max_nodes limit
    if cfg.max_nodes > 0 and stats["visited"] >= cfg.max_nodes:
        print(f"  MAX NODES REACHED ({cfg.max_nodes}) — stopping scan")
        return []

    children: list[TreeNode] = []
    consecutive_failures = 0
    parent_path_str = ".".join(str(i) for i in parent_abs_path) if parent_abs_path else ""

    for idx in child_indexes:
        # Check max_nodes limit
        if cfg.max_nodes > 0 and stats["visited"] >= cfg.max_nodes:
            print(f"  MAX NODES REACHED ({cfg.max_nodes}) — stopping branch")
            break

        child_abs_path = parent_abs_path + [idx]
        child_path_str = ".".join(str(i) for i in child_abs_path)

        # cd N — enter child
        nav = await navigate(client, str(idx), timeout=cfg.timeout, delay=cfg.delay)
        child_location = nav.parsed_prompt.location

        # MISS: location is None or unchanged from parent
        if child_location is None or child_location == parent_location:
            stats["skipped"] += 1
            print(
                f"  [d={depth} | {child_path_str} | "
                f"+{stats['visited']} ~{stats['skipped']}] "
                f"cd {idx} -> MISS"
            )
            consecutive_failures += 1
            if consecutive_failures >= cfg.stop_after_failures:
                print(
                    f"  Stopping branch at depth {depth}: "
                    f"{cfg.stop_after_failures} consecutive misses"
                )
                break
            continue  # cd didn't move, no cd .. needed

        # CIRCULAR: child location matches an ancestor
        if child_location in ancestor_locations:
            stats["skipped"] += 1
            print(
                f"  [d={depth} | {child_path_str} | "
                f"+{stats['visited']} ~{stats['skipped']}] "
                f"cd {idx} -> CIRCULAR ({child_location!r})"
            )
            await navigate(client, "..", timeout=cfg.timeout, delay=cfg.delay)
            consecutive_failures += 1
            if consecutive_failures >= cfg.stop_after_failures:
                break
            continue

        consecutive_failures = 0
        stats["visited"] += 1

        # list — capture full raw output + parsed entries
        lst = await list_destination(client, timeout=cfg.timeout, delay=cfg.delay)
        entries = lst.parsed_list.entries
        raw_list_text = _clean_list_text(lst.raw_response)
        raw_entries = _serialize_entries(entries)

        is_leaf = (len(entries) == 0) or (depth >= cfg.max_depth)

        leaf_tag = " [LEAF]" if is_leaf else ""
        if depth >= cfg.max_depth and len(entries) > 0:
            leaf_tag = f" [DEPTH-CAP: {len(entries)} entries not recursed]"
        print(
            f"  [d={depth} | {child_path_str} | "
            f"+{stats['visited']} ~{stats['skipped']}] "
            f"cd {idx} -> {child_location!r} ({len(entries)} entries){leaf_tag}"
        )

        node = TreeNode(
            path=child_path_str,
            index=idx,
            location=child_location,
            object_type=_extract_type(child_location),
            raw_list_text=raw_list_text,
            raw_list_entries=raw_entries,
            is_leaf=is_leaf,
        )

        # Recurse into grandchildren if this is not a leaf
        if not is_leaf:
            sig = _entries_signature(entries, raw_list_text)
            if sig and sig in sig_cache:
                # Duplicate: same list output as a previously scanned node
                original_path = sig_cache[sig]
                node.duplicate_of = original_path
                stats["duplicates"] = stats.get("duplicates", 0) + 1
                dup_count = stats["duplicates"]
                print(
                    f"  DUPLICATE of [{original_path}] "
                    f"-> skipping subtree (dup #{dup_count})"
                )
            else:
                grandchild_indexes = _child_indexes_from_entries(entries, cfg.max_index)
                deeper_ancestors = ancestor_locations | {child_location}

                node.children = await _scan_children(
                    client,
                    parent_abs_path=child_abs_path,
                    parent_location=child_location,
                    ancestor_locations=deeper_ancestors,
                    child_indexes=grandchild_indexes,
                    depth=depth + 1,
                    stats=stats,
                    cfg=cfg,
                    sig_cache=sig_cache,
                )
                # Register this signature after successful full traversal
                if sig:
                    sig_cache[sig] = child_path_str

        children.append(node)

        # cd .. — try to return to parent
        back_nav = await navigate(client, "..", timeout=cfg.timeout, delay=cfg.delay)
        back_location = back_nav.parsed_prompt.location

        if back_location != parent_location:
            # cd .. skipped levels or went somewhere unexpected.
            # Recover by navigating to parent via absolute path.
            print(
                f"  cd .. skipped: at {back_location!r}, "
                f"expected {parent_location!r} -> re-navigating"
            )
            recovered_loc = await _navigate_to_path(client, parent_abs_path, cfg)
            if recovered_loc != parent_location:
                # Could not recover — break out of this branch
                print(
                    f"  RECOVERY FAILED: at {recovered_loc!r}, "
                    f"giving up on branch {parent_path_str}"
                )
                break

    return children


async def scan_tree(
    client: GMA2TelnetClient,
    cfg: ScanConfig,
) -> tuple[list[TreeNode], dict]:
    """Full recursive tree scan from root.

    Algorithm:
      1. cd /  -> root
      2. list  -> get root children with their indexes + full column output
      3. For each root child:
         a. cd N -> enter child
         b. list -> capture all columns and values
         c. Recurse into sub-levels until list returns 0 entries (leaf)
         d. cd / -> return to root between top-level branches
    """
    stats = {"visited": 0, "skipped": 0, "duplicates": 0}
    sig_cache: dict[str, str] = {}  # entries_signature -> first path that had it

    # Step 1: cd / — go to root
    print("Navigating to root (cd /)...")
    root_nav = await navigate(client, "/", timeout=cfg.timeout, delay=cfg.delay)
    root_location = root_nav.parsed_prompt.location
    print(f"Root location: {root_location!r}")

    # Step 2: list — enumerate root children with full output
    print("Listing root children...")
    root_list = await list_destination(
        client, timeout=cfg.timeout, delay=cfg.delay
    )
    root_entries = root_list.parsed_list.entries
    root_list_text = _clean_list_text(root_list.raw_response)
    print(f"Root children: {len(root_entries)} entries parsed\n")

    # Extract valid root indexes from list output
    root_indexes = _child_indexes_from_entries(root_entries, cfg.max_index)
    total_root = len(root_indexes)
    nodes_limit_msg = f", max_nodes={cfg.max_nodes}" if cfg.max_nodes > 0 else ""
    print(
        f"Starting scan: max_depth={cfg.max_depth}{nodes_limit_msg}, "
        f"{total_root} root branches: {root_indexes}\n"
    )

    root_children: list[TreeNode] = []
    consecutive_failures = 0

    for branch_num, idx in enumerate(root_indexes, 1):
        # Check max_nodes limit
        if cfg.max_nodes > 0 and stats["visited"] >= cfg.max_nodes:
            print(f"\nMAX NODES REACHED ({cfg.max_nodes}) — stopping scan")
            break

        # Progress indicator
        print(f"\n--- Root branch {branch_num}/{total_root} (index {idx}) ---")

        # cd N — enter root child
        nav = await navigate(client, str(idx), timeout=cfg.timeout, delay=cfg.delay)
        child_location = nav.parsed_prompt.location

        # MISS check
        if child_location is None or child_location == root_location:
            stats["skipped"] += 1
            print(
                f"  [d=1 | {idx} | "
                f"+{stats['visited']} ~{stats['skipped']}] "
                f"cd {idx} -> MISS"
            )
            consecutive_failures += 1
            if consecutive_failures >= cfg.stop_after_failures:
                print(
                    f"\nStopping root scan: {cfg.stop_after_failures} "
                    f"consecutive misses."
                )
                break
            # cd / to reset (in case cd N put us somewhere weird)
            await navigate(client, "/", timeout=cfg.timeout, delay=cfg.delay)
            continue

        consecutive_failures = 0
        stats["visited"] += 1

        # list at this root child — capture full output
        lst = await list_destination(client, timeout=cfg.timeout, delay=cfg.delay)
        entries = lst.parsed_list.entries
        list_text = _clean_list_text(lst.raw_response)
        raw_entries = _serialize_entries(entries)

        is_leaf = len(entries) == 0

        leaf_tag = " [LEAF]" if is_leaf else ""
        print(
            f"  [d=1 | {idx} | "
            f"+{stats['visited']} ~{stats['skipped']}] "
            f"cd {idx} -> {child_location!r} ({len(entries)} entries){leaf_tag}"
        )

        node = TreeNode(
            path=str(idx),
            index=idx,
            location=child_location,
            object_type=_extract_type(child_location),
            raw_list_text=list_text,
            raw_list_entries=raw_entries,
            is_leaf=is_leaf,
        )

        # Recurse into children if not a leaf
        if not is_leaf:
            sig = _entries_signature(entries, list_text)
            if sig and sig in sig_cache:
                original_path = sig_cache[sig]
                node.duplicate_of = original_path
                stats["duplicates"] += 1
                print(
                    f"  DUPLICATE of [{original_path}] "
                    f"-> skipping subtree (dup #{stats['duplicates']})"
                )
            else:
                child_indexes = _child_indexes_from_entries(entries, cfg.max_index)
                ancestor_locations = {root_location, child_location}

                node.children = await _scan_children(
                    client,
                    parent_abs_path=[idx],
                    parent_location=child_location,
                    ancestor_locations=ancestor_locations,
                    child_indexes=child_indexes,
                    depth=2,
                    stats=stats,
                    cfg=cfg,
                    sig_cache=sig_cache,
                )
                if sig:
                    sig_cache[sig] = str(idx)

        root_children.append(node)

        # cd / — always return to root between top-level branches
        await navigate(client, "/", timeout=cfg.timeout, delay=cfg.delay)

        # Progress summary after each root branch
        print(
            f"  Branch {branch_num}/{total_root} done. "
            f"Total: {stats['visited']} visited, {stats['skipped']} skipped"
        )

    return root_children, stats


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------

def node_to_dict(node: TreeNode) -> dict:
    d = {
        "path": node.path,
        "index": node.index,
        "location": node.location,
        "object_type": node.object_type,
        "entry_count": len(node.raw_list_entries),
        "raw_list_text": node.raw_list_text,
        "entries": node.raw_list_entries,
        "is_leaf": node.is_leaf,
        "children": [node_to_dict(c) for c in node.children],
    }
    if node.duplicate_of:
        d["duplicate_of"] = node.duplicate_of
    return d


def print_tree(nodes: list[TreeNode], indent: int = 0) -> None:
    """Pretty-print the discovered tree to stdout."""
    prefix = "  " * indent
    for node in nodes:
        n_entries = len(node.raw_list_entries)
        leaf_tag = " [leaf]" if node.is_leaf else ""
        dup_tag = f" [DUPLICATE of {node.duplicate_of}]" if node.duplicate_of else ""
        n_children = len(node.children)
        children_tag = f" [{n_children} children]" if n_children else ""
        print(
            f"{prefix}[{node.path}] {node.location!r}"
            f"  ({n_entries} entries){children_tag}{leaf_tag}{dup_tag}"
        )
        if node.duplicate_of:
            # Don't expand duplicates
            continue
        if node.raw_list_entries and not node.children:
            for e in node.raw_list_entries[:5]:
                name = e.get("name") or e.get("object_id") or ""
                otype = e.get("object_type") or ""
                oid = e.get("object_id") or ""
                print(f"{prefix}  * {otype} {oid}  {name}")
            if len(node.raw_list_entries) > 5:
                print(f"{prefix}  ... ({len(node.raw_list_entries) - 5} more)")
        print_tree(node.children, indent + 1)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main_async(cfg: ScanConfig) -> None:
    # Fix Windows cp1252 encoding errors when printing Unicode location names
    import sys, io
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )

    print(f"Connecting to {cfg.host}:{cfg.port} as {cfg.user}...")
    client = GMA2TelnetClient(
        host=cfg.host,
        port=cfg.port,
        user=cfg.user,
        password=cfg.password,
    )

    try:
        await client.connect()
        await client.login()
        print("Connected and logged in.\n")

        t_start = time.monotonic()
        root_children, stats = await scan_tree(client, cfg)
        elapsed = time.monotonic() - t_start

    finally:
        await client.disconnect()
        print("\nDisconnected.")

    # Write JSON output
    output = {
        "scan_meta": {
            "host": cfg.host,
            "port": cfg.port,
            "max_depth": cfg.max_depth,
            "max_nodes": cfg.max_nodes,
            "max_index": cfg.max_index,
            "stop_after_failures": cfg.stop_after_failures,
            "elapsed_seconds": round(elapsed, 2),
            "nodes_visited": stats["visited"],
            "nodes_skipped": stats["skipped"],
        },
        "root_children": [node_to_dict(n) for n in root_children],
    }

    with open(cfg.output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    # Print summary tree
    print("\n=== DISCOVERED TREE ===\n")
    print_tree(root_children)

    print(f"\n=== SCAN COMPLETE ===")
    print(f"  Nodes visited : {stats['visited']}")
    print(f"  Indexes missed: {stats['skipped']}")
    print(f"  Dupes skipped : {stats.get('duplicates', 0)}")
    print(f"  Elapsed time  : {elapsed:.1f}s")
    print(f"  Output written: {cfg.output_path}")


def parse_args() -> ScanConfig:
    env_host = get_key(".env", "GMA_HOST") or "127.0.0.1"
    env_user = get_key(".env", "GMA_USER") or "administrator"
    env_pass = get_key(".env", "GMA_PASSWORD") or "admin"

    p = argparse.ArgumentParser(description="Recursive grandMA2 tree scanner")
    p.add_argument("--host",       default=env_host)
    p.add_argument("--port",       type=int, default=30000)
    p.add_argument("--user",       default=env_user)
    p.add_argument("--password",   default=env_pass)
    p.add_argument("--max-depth",  type=int, default=20,   dest="max_depth")
    p.add_argument("--max-nodes",  type=int, default=0,    dest="max_nodes")
    p.add_argument("--max-index",  type=int, default=60,   dest="max_index")
    p.add_argument("--failures",   type=int, default=3)
    p.add_argument("--output",     default="scan_output.json")
    p.add_argument("--delay",      type=float, default=0.2)
    p.add_argument("--timeout",    type=float, default=2.0)
    args = p.parse_args()

    return ScanConfig(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        max_depth=args.max_depth,
        max_nodes=args.max_nodes,
        max_index=args.max_index,
        stop_after_failures=args.failures,
        output_path=args.output,
        delay=args.delay,
        timeout=args.timeout,
    )


if __name__ == "__main__":
    cfg = parse_args()
    asyncio.run(main_async(cfg))
