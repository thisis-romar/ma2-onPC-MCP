# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
server_core.py — Shared infrastructure for all MCP tool modules.

Extracts singletons and the ``_handle_errors`` decorator from the monolithic
``server.py`` so that tool modules (community and pro) can import them without
circular dependencies.

Exports:
    mcp                 — FastMCP server instance (singleton)
    get_client          — async function returning a live GMA2TelnetClient
    _handle_errors      — decorator wrapping every @mcp.tool()
    _get_telemetry      — lazy ToolTelemetry singleton accessor
    _validate_object_exists  — probe whether a pool object exists
    _get_sequence_for_executor — resolve executor → sequence
    _SEQ_FOR_EXECUTOR_RE     — compiled regex for sequence parsing
    _parse_listvar      — parse ListVar telnet output
    _read_selected_exec — read $SELECTEDEXEC and $SELECTEDEXECCUE
    _parse_preset_tree_list — parse preset type tree output
"""

from __future__ import annotations

import asyncio
import functools
import json
import logging
import os
import re
import time

from mcp.server.fastmcp import FastMCP

from src.context import _current_session_id
from src.credentials import get_operator_identity, resolve_console_credentials
from src.license import get_license_tier, has_tier
from src.license_tiers import TOOL_LICENSE_TIERS
from src.rights import get_session_ma2_right, is_permitted, min_right_for_tool
from src.session_manager import SessionManager
from src.telemetry import ToolTelemetry, infer_risk_tier
from src.telnet_client import GMA2TelnetClient
from src.tools import set_gma2_client
from src.vocab import RiskTier, build_v39_spec, classify_token

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment configuration (read once at import time)
# ---------------------------------------------------------------------------
_GMA_HOST = os.getenv("GMA_HOST", "127.0.0.1")
_GMA_PORT = int(os.getenv("GMA_PORT", "30000"))
_GMA_SAFETY_LEVEL = os.getenv("GMA_SAFETY_LEVEL", "standard").lower()
_vocab_spec = build_v39_spec()

# ---------------------------------------------------------------------------
# FastMCP server instance — singleton, imported by all tool modules
# ---------------------------------------------------------------------------
mcp = FastMCP(
    name="grandMA2-MCP",
    instructions="""grandMA2 MCP server — 198 tools, 18 resources, 13 prompts.

Use suggest_tool_for_task(task_description) to find the right tool for any task.
It supports hybrid retrieval (keyword + semantic), metadata filtering by risk_tier
and license_tier, and returns related skills from the skill registry.

Core workflows:
  Inspect  → navigate_console, list_console_destination, query_object_list, get_object_info
  Plan     → inspect + list_system_variables + suggest_tool_for_task
  Execute  → run_orchestrated_task (handles preflight, execution, verification)
  Agent    → run_agent_goal (autonomous: plan → policy → execute → verify → trace)

SAFETY: DESTRUCTIVE tools require confirm_destructive=True.
Rights: read ma2://docs/rights-matrix before any mutating operation.
License tiers: COMMUNITY (free), PROFESSIONAL, ENTERPRISE — check with suggest_tool_for_task.
""",
)

# ---------------------------------------------------------------------------
# Per-operator session pool
# ---------------------------------------------------------------------------
_session_manager: SessionManager | None = None
_session_manager_lock = asyncio.Lock()


async def _get_session_manager() -> SessionManager:
    global _session_manager
    async with _session_manager_lock:
        if _session_manager is None:
            _session_manager = SessionManager(host=_GMA_HOST, port=_GMA_PORT)
            _session_manager.start_keepalive()
    return _session_manager


# ---------------------------------------------------------------------------
# Telemetry singleton — created lazily, shared by all tool wrappers
# ---------------------------------------------------------------------------
_telemetry_singleton: ToolTelemetry | None = None


def _get_telemetry() -> ToolTelemetry:
    """Return the module-level ToolTelemetry singleton (lazy init)."""
    global _telemetry_singleton
    if _telemetry_singleton is None:
        _telemetry_singleton = ToolTelemetry()
    return _telemetry_singleton


# ---------------------------------------------------------------------------
# get_client — returns a live Telnet client for the current operator
# ---------------------------------------------------------------------------
async def get_client() -> GMA2TelnetClient:
    """
    Return a live Telnet client for the current operator.

    Routes through the SessionManager so each operator identity gets its own
    Telnet connection authenticated with the console user that matches their
    OAuth scope tier (dual-enforcement).

    Stub mode  — ``GMA_USER`` set  : single identity, uses GMA_USER/GMA_PASSWORD
    Tier mode  — ``GMA_USER`` unset: identity = "tier:N", credentials from
                                     bootstrap user table in src/credentials.py
    OAuth mode — replace get_operator_identity() with JWT sub-claim extraction
    """
    from src.auth import get_granted_scopes
    scopes = get_granted_scopes()
    identity = get_operator_identity(scopes)
    username, password = resolve_console_credentials(scopes)

    manager = await _get_session_manager()
    client = await manager.get(identity, username, password)
    set_gma2_client(client)
    return client


# ---------------------------------------------------------------------------
# _handle_errors — decorator wrapping every @mcp.tool()
# ---------------------------------------------------------------------------
def _handle_errors(func):
    """Decorator that catches exceptions in MCP tools and returns JSON errors.

    Also records every invocation to the ``tool_invocations`` telemetry table
    (controlled by the ``GMA_TELEMETRY`` env var; default enabled).
    Risk tier and operator identity are inferred once at decoration time.
    License tier is resolved from ``TOOL_LICENSE_TIERS`` at decoration time.
    MA2 native rights are checked at runtime via ``_OPERATION_MIN_RIGHT``.
    """
    _risk_tier = infer_risk_tier(func)
    _required_tier = TOOL_LICENSE_TIERS.get(func.__name__)
    _required_right = min_right_for_tool(func.__name__)

    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> str:
        # --- License tier gate (before any console I/O) ---
        if _required_tier and not has_tier(_required_tier):
            return json.dumps({
                "blocked": True,
                "error": (
                    f"Tool '{func.__name__}' requires the '{_required_tier}' "
                    f"license tier. Current tier: '{get_license_tier()}'."
                ),
                "license_required": str(_required_tier),
                "current_tier": str(get_license_tier()),
            }, indent=2)

        # --- MA2 native rights gate (before any console I/O) ---
        session_right = get_session_ma2_right()
        if not is_permitted(func.__name__, session_right):
            return json.dumps({
                "blocked": True,
                "error": (
                    f"Tool '{func.__name__}' requires MA2 rights "
                    f"'{_required_right.value}' (current: '{session_right.value}')."
                ),
                "required_ma2_right": _required_right.value,
                "current_ma2_right": session_right.value,
            }, indent=2)

        t0 = time.monotonic()
        result: str = ""
        error_class: str | None = None
        try:
            result = await func(*args, **kwargs)
        except ConnectionError as e:
            logger.error("Connection error in %s: %s", func.__name__, e)
            error_class = "ConnectionError"
            result = json.dumps({"error": f"Connection failed: {e}", "blocked": True}, indent=2)
        except RuntimeError as e:
            logger.error("Runtime error in %s: %s", func.__name__, e)
            error_class = "RuntimeError"
            result = json.dumps({"error": f"Runtime error: {e}", "blocked": True}, indent=2)
        except Exception as e:
            logger.error("Unexpected error in %s: %s", func.__name__, e, exc_info=True)
            error_class = type(e).__name__
            result = json.dumps({"error": f"Unexpected error: {e}", "blocked": True}, indent=2)
        finally:
            if os.getenv("GMA_TELEMETRY", "1") != "0":
                try:  # noqa: SIM105
                    _get_telemetry().record_sync(
                        tool_name=func.__name__,
                        inputs_json=json.dumps(
                            {k: str(v)[:200] for k, v in kwargs.items()}, default=str
                        ),
                        output_preview=result[:500] if result else "",
                        error_class=error_class,
                        latency_ms=(time.monotonic() - t0) * 1000,
                        risk_tier=_risk_tier,
                        operator=os.getenv("GMA_USER", "unknown"),
                        session_id=_current_session_id.get(),
                    )
                except Exception:  # noqa: BLE001, SIM105
                    pass  # telemetry must never break a tool call
        return result

    return wrapper


# ---------------------------------------------------------------------------
# Private helpers — object existence probing
# ---------------------------------------------------------------------------

# Regex to parse sequence ID from "list executor PAGE.ID" response.
# Matches "Sequence=Seq 278" and "Sequence=Seq 278(2)".
_SEQ_FOR_EXECUTOR_RE = re.compile(r"Sequence=Seq\s+(\d+)", re.IGNORECASE)


async def _validate_object_exists(
    client: GMA2TelnetClient,
    object_type: str,
    object_id: int | str,
) -> tuple[bool, str]:
    """
    Probe whether an object exists using 'list {object_type} {object_id}'.

    MA2 returns "NO OBJECTS FOUND FOR LIST" when the object does not exist.
    Any other response (including data rows) is treated as existence confirmed.

    Not decorated with @_handle_errors — exceptions propagate to the
    enclosing tool's decorator.

    Args:
        client: Connected GMA2TelnetClient (already obtained by the caller).
        object_type: MA2 keyword, e.g. "fixture", "cue", "group".
        object_id: Integer ID or compound string, e.g. "99 sequence 278".

    Returns:
        (exists: bool, raw_response: str)
    """
    probe_cmd = f"list {object_type} {object_id}"
    raw = await client.send_command_with_response(probe_cmd)
    exists = "NO OBJECTS FOUND" not in raw.upper()
    logger.debug("_validate_object_exists %r → exists=%s", probe_cmd, exists)
    return exists, raw


async def _get_sequence_for_executor(
    client: GMA2TelnetClient,
    executor_id: int,
    page: int = 1,
) -> tuple[int | None, str]:
    """
    Resolve the sequence linked to an executor via 'list executor PAGE.ID'.

    Parses "Sequence=Seq N" from the response. Returns (None, raw) if the
    executor has no sequence assigned or is not found.

    Args:
        client: Connected GMA2TelnetClient (already obtained by the caller).
        executor_id: Executor number within the page.
        page: Executor page number (default 1).

    Returns:
        (sequence_id: int | None, raw_response: str)
    """
    probe_cmd = f"list executor {page}.{executor_id}"
    raw = await client.send_command_with_response(probe_cmd)
    m = _SEQ_FOR_EXECUTOR_RE.search(raw)
    if m:
        seq_id = int(m.group(1))
        logger.debug(
            "_get_sequence_for_executor: executor %d.%d → sequence %d",
            page, executor_id, seq_id,
        )
        return seq_id, raw
    logger.debug(
        "_get_sequence_for_executor: executor %d.%d — no sequence in response",
        page, executor_id,
    )
    return None, raw


# ---------------------------------------------------------------------------
# Shared helpers — ListVar parsing, selected executor, preset tree
# ---------------------------------------------------------------------------

def _parse_listvar(raw: str, filter_prefix: str | None = None) -> dict[str, str]:
    """Parse ListVar telnet output into a {$NAME: value} dict.

    ListVar lines have the format:  $Global : $VARNAME = VALUE
    """
    variables: dict[str, str] = {}
    for line in raw.splitlines():
        line = line.strip()
        if "=" not in line or line.startswith("["):
            continue
        # Strip scope prefix: "$Global : $VARNAME = VALUE" → "$VARNAME = VALUE"
        if " : " in line:
            _, _, line = line.partition(" : ")
            line = line.strip()
        name, _, value = line.partition("=")
        name = name.strip().lstrip("$")
        value = value.strip()
        if not name:
            continue
        if filter_prefix is None or name.upper().startswith(filter_prefix.upper()):
            variables[f"${name}"] = value
    return variables


async def _read_selected_exec(client) -> tuple[str | None, str | None]:
    """Read $SELECTEDEXEC and $SELECTEDEXECCUE from the console.

    Returns (exec_value, cue_value). Both are None if ListVar fails or the
    variables are absent in the response.
    """
    try:
        raw = await client.send_command_with_response("ListVar")
        variables = _parse_listvar(raw)
        return variables.get("$SELECTEDEXEC"), variables.get("$SELECTEDEXECCUE")
    except Exception:
        return None, None


def _parse_preset_tree_list(raw: str) -> list[dict]:
    """Parse grandMA2 list output from the PresetType cd-tree.

    Handles rows of the form:
      ``PresetType N  LibName  ScreenName  ...``
      ``Feature N  LibName  ScreenName  ...``
      ``Attribute N  LibName  ScreenName  ...``
      ``SubAttribute N  LibName  ScreenName  ...``

    These rows have only one numeric ID (not the two required by the standard
    tabular parser), so they are skipped by parse_list_output().
    """
    _ANSI = re.compile(r"\x1b\[[0-9;]*m|\x1b\[K")
    _ROW = re.compile(
        r"^\s*(PresetType|Feature|Attribute|SubAttribute)\s+(\d+)\s+(\S+)\s+(.*?)\s*$",
        re.IGNORECASE,
    )
    entries = []
    for line in raw.splitlines():
        line = _ANSI.sub("", line).strip()
        m = _ROW.match(line)
        if m:
            obj_type, obj_id, lib_name, rest = m.group(1), m.group(2), m.group(3), m.group(4)
            # rest may contain "ScreenName  IdentifiedAs  DefaultScope  (count)"
            parts = re.split(r"\s{2,}", rest)
            entry = {
                "type": obj_type,
                "id": int(obj_id),
                "library_name": lib_name,
            }
            if parts:
                entry["screen_name"] = parts[0].strip()
            if len(parts) > 1:
                entry["identified_as"] = parts[1].strip()
            if len(parts) > 2:
                entry["extra"] = parts[2].strip()
            entries.append(entry)
    return entries
