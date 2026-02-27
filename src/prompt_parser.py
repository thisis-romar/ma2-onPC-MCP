"""
grandMA2 Telnet Prompt Parser

Parses raw telnet output to detect the grandMA2 command-line prompt and
extract the current navigation destination (object tree location).

The exact prompt format is discovered empirically by sending commands and
inspecting responses.  This module uses a flexible multi-pattern approach
so it can be refined as we learn the real format from live consoles.

Candidate prompt patterns (ordered by specificity):
  1. ``[something]>``  or ``[something]>/`` — bracket-delimited
  2. Lines ending with ``>`` after stripping whitespace
  3. Fallback: no prompt detected
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ConsolePrompt:
    """Parsed console prompt state extracted from raw telnet output.

    Attributes:
        raw_response: The complete raw telnet output.
        prompt_line: The detected prompt line (e.g. ``[Group 1]>``), or
            ``None`` if no prompt pattern was matched.
        location: Extracted location text from inside the prompt brackets
            (e.g. ``"Group 1"``), or ``None``.
        object_type: Parsed object type if the location contains a
            recognizable ``Type ID`` pattern (e.g. ``"Group"``), or ``None``.
        object_id: Parsed object ID from the location (e.g. ``"1"``),
            or ``None``.
    """

    raw_response: str
    prompt_line: Optional[str] = None
    location: Optional[str] = None
    object_type: Optional[str] = None
    object_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Prompt detection patterns (tried in order)
# ---------------------------------------------------------------------------

# Pattern 1: bracket-delimited prompt  [content]>  or  [content]>/
_BRACKET_PROMPT_RE = re.compile(r"\[(.+?)\]\s*>/?\s*$", re.MULTILINE)

# Pattern 2: line ending with >
_ANGLE_PROMPT_RE = re.compile(r"^(.+)>\s*$", re.MULTILINE)

# ---------------------------------------------------------------------------
# Location splitting: "Group 1" or "Group.1" -> object_type="Group", object_id="1"
# ---------------------------------------------------------------------------

# Space-separated: "Group 1", "Preset 4.1"
_LOCATION_SPLIT_SPACE_RE = re.compile(r"^([A-Za-z]+)\s+(\d+(?:\.\d+)?)$")
# Dot-separated: "Group.1", "Preset.4.1"  (MA2 object reference notation)
_LOCATION_SPLIT_DOT_RE = re.compile(r"^([A-Za-z]+)\.(\d+(?:\.\d+)?)$")
# Single word: "Fixture", "Root", "channel"
_LOCATION_SINGLE_RE = re.compile(r"^[A-Za-z]\w*$")


def _split_location(location: str) -> tuple[Optional[str], Optional[str]]:
    """Attempt to split a location string into object_type and object_id.

    Recognises both space-separated (``"Group 1"``) and dot-separated
    (``"Group.1"``) forms, single-word locations (``"Fixture"``), and
    returns ``(None, None)`` for anything else.
    """
    if not location:
        return None, None

    # "Group 1", "Preset 4.1"
    m = _LOCATION_SPLIT_SPACE_RE.match(location)
    if m:
        return m.group(1), m.group(2)

    # "Group.1", "Preset.4.1"
    m = _LOCATION_SPLIT_DOT_RE.match(location)
    if m:
        return m.group(1), m.group(2)

    # "Fixture", "Root", "channel"
    if _LOCATION_SINGLE_RE.match(location):
        return location, None

    return None, None


def parse_prompt(raw: str) -> ConsolePrompt:
    """Parse raw telnet output and attempt to detect the MA2 prompt.

    Tries multiple candidate patterns against the raw output.  Returns a
    :class:`ConsolePrompt` with as much information as could be extracted.
    If no prompt pattern matches, ``prompt_line`` and derived fields will
    be ``None`` — the ``raw_response`` is always preserved so callers can
    inspect the output manually.

    Args:
        raw: Raw telnet output string.

    Returns:
        Parsed :class:`ConsolePrompt`.
    """
    if not raw:
        return ConsolePrompt(raw_response=raw)

    # Try pattern 1: bracket-delimited [content]>
    matches = list(_BRACKET_PROMPT_RE.finditer(raw))
    if matches:
        # Use the last match (prompt is typically at the end of output)
        last = matches[-1]
        prompt_line = last.group(0).strip()
        location = last.group(1).strip()
        obj_type, obj_id = _split_location(location)
        return ConsolePrompt(
            raw_response=raw,
            prompt_line=prompt_line,
            location=location,
            object_type=obj_type,
            object_id=obj_id,
        )

    # Try pattern 2: line ending with >
    matches = list(_ANGLE_PROMPT_RE.finditer(raw))
    if matches:
        last = matches[-1]
        prompt_line = last.group(0).strip()
        content = last.group(1).strip()
        # The content before > might contain location info
        obj_type, obj_id = _split_location(content)
        return ConsolePrompt(
            raw_response=raw,
            prompt_line=prompt_line,
            location=content if content else None,
            object_type=obj_type,
            object_id=obj_id,
        )

    # No prompt detected — return raw only
    return ConsolePrompt(raw_response=raw)


# ---------------------------------------------------------------------------
# List output parsing: extract object entries from MA2 "list" feedback
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ListEntry:
    """Single object entry parsed from MA2 list output.

    Attributes:
        object_type: Object type (e.g. ``"Group"``, ``"Sequence"``), or ``None``.
        object_id: Object ID (e.g. ``"1"``, ``"4.1"``), or ``None``.
        name: Element name / label (e.g. ``"Front Wash"``), or ``None``.
        raw_line: The original line from the list output.
    """

    object_type: Optional[str] = None
    object_id: Optional[str] = None
    name: Optional[str] = None
    raw_line: Optional[str] = None


@dataclass(frozen=True)
class ListOutput:
    """Parsed result of an MA2 ``list`` command.

    Attributes:
        raw_response: Complete raw telnet output.
        entries: Extracted list entries.
        prompt: Trailing prompt parsed from the output (if present).
    """

    raw_response: str
    entries: tuple[ListEntry, ...]
    prompt: Optional[ConsolePrompt] = None


# Patterns for extracting entries from list output lines:
#
# MA2 list output format is not yet validated against a live console.
# Hypothesized row formats (will be refined empirically):
#
#   1.  Dot notation:     "Group.1   Front Wash"
#   2.  ID + Name:        "1   Front Wash"         (when inside a typed pool)
#   3.  Type ID Name:     "Group  1  Front Wash"   (tabular columns)
#   4.  Quoted name:      '1  "Front Wash"'

# Pattern: Type.ID with optional name (e.g. "Group.1  Front Wash")
_LIST_DOT_RE = re.compile(
    r"^\s*([A-Za-z]\w*)\.(\d+(?:\.\d+)?)"
    r"(?:\s+(.+?))?\s*$"
)

# Pattern: bare numeric ID with optional name (e.g. "1  Front Wash")
_LIST_ID_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)"
    r"(?:\s+(.+?))?\s*$"
)


def parse_list_output(raw: str) -> ListOutput:
    """Parse raw telnet output from a ``list`` command.

    Extracts object entries (type, id, name) from each line of the list
    output.  Also detects a trailing prompt if present.

    The parser is intentionally lenient — unrecognised lines are skipped,
    and the raw output is always preserved.

    Args:
        raw: Raw telnet output string from a ``list`` command.

    Returns:
        :class:`ListOutput` with extracted entries and optional prompt.
    """
    if not raw or not raw.strip():
        return ListOutput(raw_response=raw, entries=())

    lines = raw.strip().splitlines()
    entries: list[ListEntry] = []
    prompt: Optional[ConsolePrompt] = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Skip lines that look like a prompt (don't treat as data)
        if _BRACKET_PROMPT_RE.search(stripped):
            prompt = parse_prompt(stripped)
            continue

        # Try dot notation: Group.1  Front Wash
        m = _LIST_DOT_RE.match(stripped)
        if m:
            name_raw = m.group(3)
            name = name_raw.strip('"') if name_raw else None
            entries.append(ListEntry(
                object_type=m.group(1),
                object_id=m.group(2),
                name=name,
                raw_line=stripped,
            ))
            continue

        # Try bare ID: 1  Front Wash
        m = _LIST_ID_RE.match(stripped)
        if m:
            name_raw = m.group(2)
            name = name_raw.strip('"') if name_raw else None
            entries.append(ListEntry(
                object_type=None,
                object_id=m.group(1),
                name=name,
                raw_line=stripped,
            ))
            continue

        # Unrecognised line — skip silently (could be a header, separator, etc.)

    return ListOutput(
        raw_response=raw,
        entries=tuple(entries),
        prompt=prompt,
    )
