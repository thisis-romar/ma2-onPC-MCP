"""
Tests for grandMA2 Vocabulary & Safety-Tier Classification Module
"""

import pytest

from src.vocab import (
    RiskTier,
    KeywordKind,
    ResolvedToken,
    build_v39_spec,
    classify_token,
    parse_changedest,
    parse_list,
    _norm_token,
    _kind_for_normalized,
    _load_keywords_from_json,
)


@pytest.fixture
def spec():
    """Build the v3.9 vocabulary spec for testing."""
    return build_v39_spec()


# =============================================================================
# Normalization
# =============================================================================


class TestNormToken:
    def test_lowercase(self):
        assert _norm_token("GoBack") == "goback"

    def test_strip_whitespace(self):
        assert _norm_token("  Store  ") == "store"

    def test_collapse_internal_spaces(self):
        assert _norm_token("Plus  +") == "plus +"

    def test_empty_string(self):
        assert _norm_token("") == ""


# =============================================================================
# JSON loading
# =============================================================================


class TestLoadKeywords:
    def test_missing_file_gives_helpful_error(self):
        with pytest.raises(FileNotFoundError, match="keyword vocabulary file not found"):
            _load_keywords_from_json("/nonexistent/path/keywords.json")


# =============================================================================
# classify_token
# =============================================================================


class TestClassifyToken:
    def test_known_keyword(self, spec):
        result = classify_token("Store", spec)
        assert result.kind == KeywordKind.KEYWORD
        assert result.canonical == "Store"
        assert result.risk == RiskTier.DESTRUCTIVE

    def test_case_insensitive(self, spec):
        result = classify_token("store", spec)
        assert result.kind == KeywordKind.KEYWORD
        assert result.canonical == "Store"
        assert result.risk == RiskTier.DESTRUCTIVE

    def test_safe_read_keyword(self, spec):
        result = classify_token("Info", spec)
        assert result.risk == RiskTier.SAFE_READ

    def test_safe_write_keyword(self, spec):
        result = classify_token("Go", spec)
        assert result.risk == RiskTier.SAFE_WRITE

    def test_destructive_keyword(self, spec):
        result = classify_token("Delete", spec)
        assert result.risk == RiskTier.DESTRUCTIVE

    def test_unknown_keyword(self, spec):
        result = classify_token("NotAKeyword", spec)
        assert result.kind == KeywordKind.UNKNOWN
        assert result.canonical is None
        assert result.risk == RiskTier.UNKNOWN

    def test_alias_shortcut(self, spec):
        result = classify_token("li", spec)
        assert result.kind == KeywordKind.KEYWORD
        assert result.canonical == "List"
        assert result.risk == RiskTier.SAFE_READ

    def test_changedest_alias(self, spec):
        result = classify_token("cd", spec)
        assert result.kind == KeywordKind.KEYWORD
        assert result.canonical == "ChangeDest"

    def test_cd_special_dotdot(self, spec):
        result = classify_token("..", spec)
        assert result.kind == KeywordKind.PUNCT_TOKEN
        assert result.risk == RiskTier.SAFE_READ

    def test_cd_special_slash(self, spec):
        result = classify_token("/", spec)
        assert result.kind == KeywordKind.PUNCT_TOKEN

    def test_special_char_entry(self, spec):
        result = classify_token("Plus +", spec)
        assert result.kind == KeywordKind.SPECIAL_CHAR_ENTRY

    def test_special_char_dot(self, spec):
        result = classify_token("Dot .", spec)
        assert result.kind == KeywordKind.SPECIAL_CHAR_ENTRY


# =============================================================================
# Risk tier coverage: all implemented command builder keywords should have a tier
# =============================================================================


class TestRiskTierCoverage:
    """Verify that all keywords used in src/commands/ have a defined risk tier."""

    IMPLEMENTED_KEYWORDS = [
        # Function keywords from src/commands/
        "Store", "Delete", "Copy", "Move", "Edit", "Cut", "Paste",
        "Label", "Appearance", "Assign", "Remove", "Empty",
        # Playback
        "Go", "GoBack", "Goto", "GoFastBack", "GoFastForward",
        "DefGoBack", "DefGoForward", "DefGoPause", "Pause",
        # Selection & Clear
        "SelFix", "Clear", "ClearAll", "ClearSelection", "ClearActive",
        # Values
        "At", "Call", "Park", "Unpark",
        # Info
        "List", "Info",
        # Variables
        "SetVar", "SetUserVar", "AddVar", "AddUserVar",
        # TempFader
        "TempFader",
    ]

    def test_all_implemented_keywords_have_risk_tier(self, spec):
        missing = []
        for kw in self.IMPLEMENTED_KEYWORDS:
            result = classify_token(kw, spec)
            if result.risk == RiskTier.UNKNOWN:
                missing.append(kw)
        assert missing == [], f"Keywords missing risk tier: {missing}"


# =============================================================================
# Canonical spelling round-trip
# =============================================================================


class TestCanonicalSpelling:
    """Verify that canonical spellings are preserved correctly."""

    def test_compound_keywords(self, spec):
        compound = [
            ("selfix", "SelFix"),
            ("goback", "GoBack"),
            ("gofastback", "GoFastBack"),
            ("clearall", "ClearAll"),
            ("defgoback", "DefGoBack"),
            ("listuservar", "ListUserVar"),
            ("changedest", "ChangeDest"),
        ]
        for normalized, expected in compound:
            result = classify_token(normalized, spec)
            assert result.canonical == expected, (
                f"Expected canonical '{expected}' for '{normalized}', "
                f"got '{result.canonical}'"
            )


# =============================================================================
# parse_changedest
# =============================================================================


class TestParseChangeDest:
    def test_no_args(self, spec):
        result = parse_changedest([], spec)
        assert result.mode == "UNKNOWN"

    def test_dotdot(self, spec):
        result = parse_changedest([".."], spec)
        assert result.mode == "UP_ONE_LEVEL"

    def test_slash(self, spec):
        result = parse_changedest(["/"], spec)
        assert result.mode == "ROOT"

    def test_element_index(self, spec):
        result = parse_changedest(["5"], spec)
        assert result.mode == "INDEX"
        assert result.arg1 == "5"

    def test_element_name(self, spec):
        result = parse_changedest(['"MySequence"'], spec)
        assert result.mode == "NAME"
        assert result.arg1 == "MySequence"

    def test_object_type_and_id(self, spec):
        result = parse_changedest(["Sequence", "3"], spec)
        assert result.mode == "OBJECT"
        assert result.arg1 == "Sequence"
        assert result.arg2 == "3"


# =============================================================================
# parse_list
# =============================================================================


class TestParseList:
    def test_empty(self, spec):
        result = parse_list([], spec)
        assert result.object_list is None
        assert result.options == {}
        assert result.discovery is False

    def test_discovery(self, spec):
        result = parse_list(["/?"], spec)
        assert result.discovery is True

    def test_object_list(self, spec):
        result = parse_list(["Preset", "4"], spec)
        assert result.object_list == "Preset 4"

    def test_option_flag(self, spec):
        result = parse_list(["/noconfirm"], spec)
        assert result.options == {"noconfirm": "true"}

    def test_option_with_value(self, spec):
        result = parse_list(["/source=output"], spec)
        assert result.options == {"source": "output"}

    def test_mixed_object_and_options(self, spec):
        result = parse_list(["Preset", "4", "/source=output"], spec)
        assert result.object_list == "Preset 4"
        assert result.options == {"source": "output"}


# =============================================================================
# VocabSpec construction
# =============================================================================


class TestVocabSpec:
    def test_spec_has_canonical_keywords(self, spec):
        assert len(spec.canonical_keywords) > 50

    def test_spec_has_normalized_map(self, spec):
        assert "store" in spec.normalized_to_canonical
        assert spec.normalized_to_canonical["store"] == "Store"

    def test_changedest_aliases(self, spec):
        assert "cd" in spec.changedest_aliases
        assert spec.changedest_aliases["cd"] == "ChangeDest"

    def test_list_discovery_token(self, spec):
        assert spec.list_option_discovery == "/?"
