"""
grandMA2 v3.9 — Telnet Command Vocabulary (full-context refactor)

Design goals
- Treat MA's "All keywords" list as the canonical *presence* vocabulary.
- Keep aliases/shortcuts as a separate overlay (runtime-authoritative via CmdHelp).
- Provide deterministic token normalization + classification hooks for safety middleware.
- Provide first-class handling for ChangeDest/CD and List/List*.
- Categorize keywords into Object, Function, Helping, and Special Char groups.

Files
- Vendored full keyword set JSON (schema v2.0):
  - grandMA2_v3_9_telnet_keyword_vocabulary.json
"""

from __future__ import annotations

import json
import logging
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum

logger = logging.getLogger(__name__)


# =============================================================================
# Core: loading + normalization
# =============================================================================

DEFAULT_V39_KEYWORD_JSON = os.path.join(
    os.path.dirname(__file__),
    "grandMA2_v3_9_telnet_keyword_vocabulary.json",
)


def _norm_token(tok: str) -> str:
    """
    Normalization used for dictionary lookups:
    - trim
    - lowercase
    - collapse internal whitespace
    """
    tok = tok.strip()
    tok = re.sub(r"\s+", " ", tok)
    return tok.lower()


# =============================================================================
# Safety tiers (middleware hooks)
# =============================================================================

class RiskTier(StrEnum):
    SAFE_READ = "SAFE_READ"
    SAFE_WRITE = "SAFE_WRITE"
    DESTRUCTIVE = "DESTRUCTIVE"
    UNKNOWN = "UNKNOWN"


# =============================================================================
# Keyword categories (coarse classification)
# =============================================================================

class KeywordKind(StrEnum):
    KEYWORD = "KEYWORD"
    SPECIAL_CHAR_ENTRY = "SPECIAL_CHAR"
    PUNCT_TOKEN = "PUNCT_TOKEN"
    UNKNOWN = "UNKNOWN"


class KeywordCategory(StrEnum):
    """Vocabulary-level category for a keyword."""
    OBJECT = "OBJECT"
    FUNCTION = "FUNCTION"
    HELPING = "HELPING"
    SPECIAL_CHAR = "SPECIAL_CHAR"


# Explicit set of known special-character entry names from the MA keyword list.
# Using an explicit set instead of a regex (fixes V4: regex was overly broad).
_SPECIAL_CHAR_ENTRIES = frozenset({
    "asterisk *",
    "dot .",
    "dollar $",
    "slash /",
    "plus +",
    "minus -",
})


# =============================================================================
# Data structures for vocabulary payload (JSON schema v2.0)
# =============================================================================

@dataclass(frozen=True)
class ObjectKeywordEntry:
    """Metadata for an Object Keyword from the vocabulary JSON."""
    keyword: str
    canonical: str
    context_change: bool
    notes: str = ""


@dataclass(frozen=True)
class VocabPayload:
    """Parsed vocabulary payload from JSON (schema v2.0)."""
    object_keywords: list[ObjectKeywordEntry]
    function_keywords: list[str]
    helping_keywords: list[str]
    special_chars: list[str]
    aliases: dict[str, str]


# =============================================================================
# VocabSpec: full vocabulary + overlays
# =============================================================================

@dataclass(frozen=True)
class VocabSpec:
    """
    Full vocabulary + overlays.
    """
    # Canonical keyword presence (from MA "All keywords")
    canonical_keywords: set[str]  # stored in normalized form

    # Normalized -> canonical spelling map for exact round-tripping
    normalized_to_canonical: Mapping[str, str]

    # Aliases/shortcuts -> canonical keyword spelling
    aliases_to_canonical: Mapping[str, str]

    # CD (ChangeDest) specifics
    changedest_aliases: Mapping[str, str]
    changedest_specials: Mapping[str, str]

    # List specifics
    list_option_discovery: str

    # Safety tiers (canonical spellings)
    safe_read: set[str]
    safe_write: set[str]
    destructive: set[str]

    # Object keyword metadata
    object_keywords: frozenset[str] = field(default_factory=frozenset)
    object_keyword_entries: Mapping[str, ObjectKeywordEntry] = field(
        default_factory=dict,
    )

    # Keyword category map (canonical spelling -> category)
    keyword_categories: Mapping[str, KeywordCategory] = field(
        default_factory=dict,
    )


# =============================================================================
# JSON loader (schema v2.0)
# =============================================================================

def _load_keywords_from_json(path: str) -> VocabPayload:
    """
    Load the keyword vocabulary from the vendored JSON file (schema v2.0).

    The JSON file contains categorized keywords:
    - object_keywords: list of objects with keyword, canonical, context_change, notes
    - function_keywords: flat list of function keyword strings
    - helping_keywords: flat list of helping keyword strings
    - special_chars: flat list of special character entry strings
    - aliases: dict mapping alias -> canonical target

    Raises:
        FileNotFoundError: If the keyword vocabulary JSON file is missing.
        json.JSONDecodeError: If the JSON file is malformed.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"grandMA2 keyword vocabulary file not found: {path}. "
            "Ensure grandMA2_v3_9_telnet_keyword_vocabulary.json is present "
            "alongside vocab.py in the src/ directory."
        )
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)

    # Parse object keywords (rich entries)
    object_keywords = []
    for entry in payload.get("object_keywords", []):
        object_keywords.append(ObjectKeywordEntry(
            keyword=entry["keyword"],
            canonical=entry.get("canonical", entry["keyword"]),
            context_change=entry.get("context_change", True),
            notes=entry.get("notes", ""),
        ))

    return VocabPayload(
        object_keywords=object_keywords,
        function_keywords=list(payload.get("function_keywords", [])),
        helping_keywords=list(payload.get("helping_keywords", [])),
        special_chars=list(payload.get("special_chars", [])),
        aliases=dict(payload.get("aliases", {})),
    )


# =============================================================================
# Build the v3.9 spec
# =============================================================================

def build_v39_spec(
    keyword_json_path: str = DEFAULT_V39_KEYWORD_JSON,
) -> VocabSpec:
    vocab = _load_keywords_from_json(keyword_json_path)

    # Build canonical presence vocabulary (normalized) and reverse map
    canonical: set[str] = set()
    normalized_to_canonical: dict[str, str] = {}
    keyword_categories: dict[str, KeywordCategory] = {}
    object_keyword_entries: dict[str, ObjectKeywordEntry] = {}
    object_kw_canonicals: set[str] = set()

    # ---- Object Keywords (processed first; take category precedence)
    for entry in vocab.object_keywords:
        norm = _norm_token(entry.canonical)
        canonical.add(norm)
        if norm not in normalized_to_canonical:
            normalized_to_canonical[norm] = entry.canonical
        keyword_categories[entry.canonical] = KeywordCategory.OBJECT
        object_keyword_entries[entry.canonical] = entry
        object_kw_canonicals.add(entry.canonical)

    # ---- Function Keywords
    for kw in vocab.function_keywords:
        norm = _norm_token(kw)
        canonical.add(norm)
        if norm not in normalized_to_canonical:
            normalized_to_canonical[norm] = kw
        # Only set category if not already claimed by Object
        if kw not in keyword_categories:
            keyword_categories[kw] = KeywordCategory.FUNCTION

    # ---- Helping Keywords
    for kw in vocab.helping_keywords:
        norm = _norm_token(kw)
        canonical.add(norm)
        if norm not in normalized_to_canonical:
            normalized_to_canonical[norm] = kw
        if kw not in keyword_categories:
            keyword_categories[kw] = KeywordCategory.HELPING

    # ---- Special chars
    for kw in vocab.special_chars:
        norm = _norm_token(kw)
        canonical.add(norm)
        if norm not in normalized_to_canonical:
            normalized_to_canonical[norm] = kw
        keyword_categories[kw] = KeywordCategory.SPECIAL_CHAR

    # ---- ChangeDest/CD overlay
    changedest_aliases = {
        _norm_token("changedest"): "ChangeDest",
        _norm_token("cd"): "ChangeDest",
        _norm_token("chang"): "ChangeDest",
    }
    changedest_specials = {
        "..": "UP_ONE_LEVEL",
        "/": "ROOT",
    }

    # ---- Alias overlay (shortcuts + JSON-defined aliases)
    aliases: dict[str, str] = {
        _norm_token("li"): "List",
        _norm_token("listef"): "ListEffectLibrary",
        _norm_token("listm"): "ListMacroLibrary",
        _norm_token("listp"): "ListPluginLibrary",
    }
    # Add JSON-defined aliases (DMX->Dmx, DMXUniverse->DmxUniverse, etc.)
    for alias_name, canonical_target in vocab.aliases.items():
        aliases[_norm_token(alias_name)] = canonical_target

    # ---- Safety tier defaults
    # NOTE: "Blackout" is classified as SAFE_WRITE because it is a toggle
    # and easily reversible. However, in a live show context, it kills all
    # lighting output and could be disruptive. Operators should be aware.
    safe_read = {
        "Info", "List", "ListEffectLibrary", "ListFaderModules",
        "ListLibrary", "ListMacroLibrary", "ListOops", "ListOwner",
        "ListPluginLibrary", "ListShows", "ListUpdate", "ListUserVar",
        "ListVar", "GetUserVar", "Select", "CmdHelp",
        "ChangeDest",
    }
    safe_write = {
        "At", "Go", "GoBack", "Goto", "On", "Off", "Toggle",
        "Top", "Temp", "TempFader", "Pause", "Release", "Blackout",
        "Blind", "Highlight", "Solo", "Clear", "ClearAll",
        "ClearSelection", "ClearActive", "Flash", "Freeze",
        "SetVar", "AddVar", "SetUserVar", "AddUserVar", "Park", "Unpark",
        "SelFix", "DefGoBack", "DefGoForward", "DefGoPause",
        "GoFastBack", "GoFastForward", "Oops", "Call",
    }
    # All Object Keywords are SAFE_WRITE (they change programmer context)
    safe_write |= object_kw_canonicals

    destructive = {
        "Delete", "Store", "Copy", "Move", "Update", "Edit",
        "Assign", "Label", "Appearance", "Import", "Export",
        "Login", "Logout", "Remove", "Cut", "Paste", "Empty",
        "NewShow", "LoadShow", "SaveShow", "DeleteShow",
        "Shutdown", "Reboot", "Restart", "Reset",
    }

    return VocabSpec(
        canonical_keywords=canonical,
        normalized_to_canonical=normalized_to_canonical,
        aliases_to_canonical=aliases,
        changedest_aliases=changedest_aliases,
        changedest_specials=changedest_specials,
        list_option_discovery="/?",
        safe_read=set(safe_read),
        safe_write=set(safe_write),
        destructive=set(destructive),
        object_keywords=frozenset(object_kw_canonicals),
        object_keyword_entries=object_keyword_entries,
        keyword_categories=keyword_categories,
    )


# =============================================================================
# Lookup / classification API
# =============================================================================

@dataclass(frozen=True)
class ResolvedToken:
    raw: str
    normalized: str
    kind: KeywordKind
    canonical: str | None
    risk: RiskTier
    category: KeywordCategory | None = None


def classify_token(tok: str, spec: VocabSpec) -> ResolvedToken:
    n = _norm_token(tok)

    # CD specials are punctuation tokens, not MA "keywords"
    if tok in spec.changedest_specials:
        return ResolvedToken(
            raw=tok,
            normalized=n,
            kind=KeywordKind.PUNCT_TOKEN,
            canonical=None,
            risk=RiskTier.SAFE_READ,
        )

    # Alias overlay (shortcuts, convenience tokens)
    if n in spec.aliases_to_canonical:
        canonical = spec.aliases_to_canonical[n]
        return ResolvedToken(
            raw=tok,
            normalized=n,
            kind=KeywordKind.KEYWORD,
            canonical=canonical,
            risk=_risk_for_canonical(canonical, spec),
            category=spec.keyword_categories.get(canonical),
        )

    # ChangeDest alias overlay
    if n in spec.changedest_aliases:
        canonical = spec.changedest_aliases[n]
        return ResolvedToken(
            raw=tok,
            normalized=n,
            kind=KeywordKind.KEYWORD,
            canonical=canonical,
            risk=_risk_for_canonical(canonical, spec),
            category=spec.keyword_categories.get(canonical),
        )

    # Canonical presence check (from "All keywords")
    if n in spec.canonical_keywords:
        canonical = spec.normalized_to_canonical.get(n, tok)
        return ResolvedToken(
            raw=tok,
            normalized=n,
            kind=_kind_for_normalized(n),
            canonical=canonical,
            risk=_risk_for_canonical(canonical, spec),
            category=spec.keyword_categories.get(canonical),
        )

    return ResolvedToken(
        raw=tok,
        normalized=n,
        kind=KeywordKind.UNKNOWN,
        canonical=None,
        risk=RiskTier.UNKNOWN,
    )


def _kind_for_normalized(normalized: str) -> KeywordKind:
    """Classify keyword kind using the explicit special-char entry set."""
    if normalized in _SPECIAL_CHAR_ENTRIES:
        return KeywordKind.SPECIAL_CHAR_ENTRY
    return KeywordKind.KEYWORD


def _risk_for_canonical(canonical: str, spec: VocabSpec) -> RiskTier:
    if canonical in spec.safe_read:
        return RiskTier.SAFE_READ
    if canonical in spec.safe_write:
        return RiskTier.SAFE_WRITE
    if canonical in spec.destructive:
        return RiskTier.DESTRUCTIVE
    return RiskTier.UNKNOWN


# =============================================================================
# High-level helpers: CD parsing + List parsing
# =============================================================================

@dataclass(frozen=True)
class ChangeDestOp:
    """Parsed ChangeDest intent. (Does not execute anything.)"""
    mode: str  # ROOT | UP_ONE_LEVEL | INDEX | NAME | OBJECT | UNKNOWN
    arg1: str | None = None
    arg2: str | None = None


def parse_changedest(args: Sequence[str], spec: VocabSpec) -> ChangeDestOp:
    """
    Implements MA's documented CD forms:
      CD [Element-index]
      CD "Element name"
      CD [Object-type] [Object-ID]
      CD ..
      CD /
    """
    if not args:
        return ChangeDestOp(mode="UNKNOWN")

    if args[0] in spec.changedest_specials:
        return ChangeDestOp(mode=spec.changedest_specials[args[0]])

    # Element-index (integer)
    if args[0].isdigit():
        return ChangeDestOp(mode="INDEX", arg1=args[0])

    # Name (quoted or raw)
    if len(args) == 1:
        return ChangeDestOp(mode="NAME", arg1=args[0].strip('"'))

    # Object-type + Object-ID
    return ChangeDestOp(mode="OBJECT", arg1=args[0], arg2=args[1])


@dataclass(frozen=True)
class ListOp:
    """Parsed List intent. (Does not execute anything.)"""
    object_list: str | None
    options: Mapping[str, str]
    discovery: bool


_LIST_OPT_RE = re.compile(r"^/([A-Za-z0-9_]+)(?:=(.*))?$")


def parse_list(tokens_after_list: Sequence[str], spec: VocabSpec) -> ListOp:
    """
    Minimal deterministic List parser:
      - If "/?" present => discovery=True
      - Parses /option=value or /option as flags
      - Everything before first /option token is treated as object_list text
    """
    discovery = False
    options: dict[str, str] = {}
    obj_parts: list[str] = []

    for t in tokens_after_list:
        if t == spec.list_option_discovery:
            discovery = True
            continue

        m = _LIST_OPT_RE.match(t)
        if m:
            k = m.group(1)
            v = m.group(2) if m.group(2) is not None else "true"
            options[k] = v
        else:
            obj_parts.append(t)

    object_list = " ".join(obj_parts).strip() or None
    return ListOp(object_list=object_list, options=options, discovery=discovery)


# =============================================================================
# CD Numeric Index Map (live-validated on grandMA2 onPC 3.9.60.65)
# =============================================================================

CD_NUMERIC_INDEX: dict[int, str] = {
    1: "Showfile",           2: "TimeConfig",         3: "Settings",
    4: "DMX_Protocols",      5: "NetConfig",           6: "CITPNetConfig",
    7: "TrackingSystems",    8: "UserImagePool",       9: "RDM_Data",
    10: "LiveSetup",         11: "EditSetup",          13: "Macros",
    14: "FlightRecordings",  15: "Plugins",            16: "Gels",
    17: "Presets",           18: "Worlds",             19: "Filters",
    20: "FadePaths",         21: "Programmer",         22: "Groups",
    23: "Forms",             24: "Effects",            25: "Sequences",
    26: "Timers",            27: "MasterSections",     30: "ExecutorPages",
    31: "ChannelPages",      33: "Songs",              34: "Agendas",
    35: "Timecodes",         36: "RemoteTypes",        37: "DMXSnapshotPool",
    38: "Layouts",           39: "UserProfiles",       40: "Users",
    41: "PixelMapperContainer", 42: "NDP_Root",        43: "UserStationCollect",
    46: "Temp",
}

# Indexes confirmed INVALID (Error #72: COMMAND NOT EXECUTED) on MA2 3.9.60.65
CD_INVALID_INDEXES: frozenset[int] = frozenset({12, 28, 29, 32, 44, 45, 47, 48, 49, 50})
