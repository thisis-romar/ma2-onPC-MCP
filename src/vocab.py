"""
grandMA2 v3.9 — Telnet Command Vocabulary (full-context refactor)

Design goals
- Treat MA's "All keywords" list as the canonical *presence* vocabulary.
- Keep aliases/shortcuts as a separate overlay (runtime-authoritative via CmdHelp).
- Provide deterministic token normalization + classification hooks for safety middleware.
- Provide first-class handling for ChangeDest/CD and List/List*.

Files
- Vendored full keyword set JSON:
  - grandMA2_v3_9_telnet_keyword_vocabulary.json
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Optional, Sequence, Set

import json
import logging
import os
import re


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


def _load_keywords_from_json(path: str) -> list[str]:
    """
    Load the keyword list from the vendored JSON file.

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
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return list(payload.get("keywords", []))


# =============================================================================
# Safety tiers (middleware hooks)
# =============================================================================

class RiskTier(str, Enum):
    SAFE_READ = "SAFE_READ"
    SAFE_WRITE = "SAFE_WRITE"
    DESTRUCTIVE = "DESTRUCTIVE"
    UNKNOWN = "UNKNOWN"


# =============================================================================
# Keyword categories (coarse classification)
# =============================================================================

class KeywordKind(str, Enum):
    KEYWORD = "KEYWORD"
    SPECIAL_CHAR_ENTRY = "SPECIAL_CHAR"
    PUNCT_TOKEN = "PUNCT_TOKEN"
    UNKNOWN = "UNKNOWN"


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


@dataclass(frozen=True)
class VocabSpec:
    """
    Full vocabulary + overlays.
    """
    # Canonical keyword presence (from MA "All keywords")
    canonical_keywords: Set[str]  # stored in normalized form

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
    safe_read: Set[str]
    safe_write: Set[str]
    destructive: Set[str]


# =============================================================================
# Build the v3.9 spec
# =============================================================================

def build_v39_spec(
    keyword_json_path: str = DEFAULT_V39_KEYWORD_JSON,
) -> VocabSpec:
    raw_keywords = _load_keywords_from_json(keyword_json_path)

    # Build canonical presence vocabulary (normalized) and a reverse map
    canonical = set()
    normalized_to_canonical: dict[str, str] = {}
    for k in raw_keywords:
        norm = _norm_token(k)
        canonical.add(norm)
        # Keep the first spelling seen (the JSON should have canonical spellings)
        if norm not in normalized_to_canonical:
            normalized_to_canonical[norm] = k

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

    # ---- Alias overlay (shortcuts, convenience tokens)
    aliases: dict[str, str] = {
        _norm_token("li"): "List",
        _norm_token("listef"): "ListEffectLibrary",
        _norm_token("listm"): "ListMacroLibrary",
        _norm_token("listp"): "ListPluginLibrary",
    }

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
    )


# =============================================================================
# Lookup / classification API
# =============================================================================

@dataclass(frozen=True)
class ResolvedToken:
    raw: str
    normalized: str
    kind: KeywordKind
    canonical: Optional[str]
    risk: RiskTier


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
    arg1: Optional[str] = None
    arg2: Optional[str] = None


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
    object_list: Optional[str]
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
