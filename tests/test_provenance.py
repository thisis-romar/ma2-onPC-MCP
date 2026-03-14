"""
Content Provenance & Manifest Tests

Tests for content licensing constants, XML provenance comment builder,
and JSON content manifest builder for marketplace distribution.

Test Classes:
- TestContentConstants: Validate CONTENT_LICENSES, CONTENT_TIERS, CONTENT_SOURCES
- TestBuildProvenanceComment: Tests for build_provenance_comment()
- TestBuildContentManifest: Tests for build_content_manifest()
"""

import json

import pytest


class TestContentConstants:
    """Tests for content licensing and provenance constants."""

    def test_content_licenses_not_empty(self):
        """All license entries must have non-empty descriptions."""
        from src.commands.constants import CONTENT_LICENSES

        assert len(CONTENT_LICENSES) > 0
        for key, value in CONTENT_LICENSES.items():
            assert key, "License key must not be empty"
            assert value, f"License '{key}' has empty description"

    def test_content_tiers_not_empty(self):
        """All tier entries must have non-empty descriptions."""
        from src.commands.constants import CONTENT_TIERS

        assert len(CONTENT_TIERS) > 0
        for key, value in CONTENT_TIERS.items():
            assert key, "Tier key must not be empty"
            assert value, f"Tier '{key}' has empty description"

    def test_content_sources_not_empty(self):
        """All source entries must have non-empty descriptions."""
        from src.commands.constants import CONTENT_SOURCES

        assert len(CONTENT_SOURCES) > 0
        for key, value in CONTENT_SOURCES.items():
            assert key, "Source key must not be empty"
            assert value, f"Source '{key}' has empty description"

    def test_expected_tiers_present(self):
        """Free, free-hybrid, and premium tiers must exist."""
        from src.commands.constants import CONTENT_TIERS

        assert "free" in CONTENT_TIERS
        assert "free-hybrid" in CONTENT_TIERS
        assert "premium" in CONTENT_TIERS

    def test_expected_sources_present(self):
        """Human, ai-assisted, and ai-generated sources must exist."""
        from src.commands.constants import CONTENT_SOURCES

        assert "human" in CONTENT_SOURCES
        assert "ai-assisted" in CONTENT_SOURCES
        assert "ai-generated" in CONTENT_SOURCES


class TestBuildProvenanceComment:
    """Tests for build_provenance_comment() XML comment builder."""

    def test_valid_defaults(self):
        """Default parameters produce a valid XML comment."""
        from src.commands.functions.importexport import build_provenance_comment

        result = build_provenance_comment()
        assert result.startswith("<!-- emblem:provenance")
        assert result.endswith("-->")

    def test_all_fields_present(self):
        """All provenance fields appear in the output."""
        from src.commands.functions.importexport import build_provenance_comment

        result = build_provenance_comment(
            creator="acme-lighting",
            source="human",
            license="cc-by-4.0",
            tool="my-tool",
            human_contribution="Custom color palette",
            version="2.0.0",
        )
        assert "creator: acme-lighting" in result
        assert "source: human" in result
        assert "license: cc-by-4.0" in result
        assert "tool: my-tool/2.0.0" in result
        assert "human_contribution: Custom color palette" in result
        assert "generated:" in result

    def test_is_xml_comment(self):
        """Output is a valid XML comment (starts <!--, ends -->)."""
        from src.commands.functions.importexport import build_provenance_comment

        result = build_provenance_comment()
        assert result.startswith("<!--")
        assert result.endswith("-->")

    def test_no_human_contribution_omits_field(self):
        """Empty human_contribution omits the field entirely."""
        from src.commands.functions.importexport import build_provenance_comment

        result = build_provenance_comment(human_contribution="")
        assert "human_contribution" not in result

    def test_invalid_source_rejected(self):
        """Unknown source classification raises ValueError."""
        from src.commands.functions.importexport import build_provenance_comment

        with pytest.raises(ValueError, match="Invalid source"):
            build_provenance_comment(source="robot")

    def test_invalid_license_rejected(self):
        """Unknown license raises ValueError."""
        from src.commands.functions.importexport import build_provenance_comment

        with pytest.raises(ValueError, match="Invalid license"):
            build_provenance_comment(license="gpl-3.0")

    def test_empty_creator_rejected(self):
        """Empty creator raises ValueError."""
        from src.commands.functions.importexport import build_provenance_comment

        with pytest.raises(ValueError, match="creator must not be empty"):
            build_provenance_comment(creator="")

    def test_xml_comment_injection_prevented(self):
        """Field values containing --> are rejected."""
        from src.commands.functions.importexport import build_provenance_comment

        with pytest.raises(ValueError, match="must not contain"):
            build_provenance_comment(human_contribution="evil --> injection")


class TestBuildContentManifest:
    """Tests for build_content_manifest() JSON manifest builder."""

    def _base_args(self, **overrides):
        """Helper: return valid base arguments with optional overrides."""
        args = {
            "name": "test-bundle",
            "description": "Test content bundle",
            "contents": [{"type": "filter", "file": "filter_003.xml"}],
            "tier": "premium",
            "price_eur": 15.0,
        }
        args.update(overrides)
        return args

    def test_valid_premium_manifest(self):
        """Valid premium manifest with price produces valid JSON."""
        from src.commands.functions.importexport import build_content_manifest

        result = build_content_manifest(**self._base_args())
        data = json.loads(result)
        assert data["name"] == "test-bundle"
        assert data["tier"] == "premium"
        assert data["price_eur"] == 15.0
        assert data["schema"] == "emblem-content-manifest/1.0"

    def test_valid_free_hybrid_manifest(self):
        """Free-hybrid tier works without price."""
        from src.commands.functions.importexport import build_content_manifest

        result = build_content_manifest(
            **self._base_args(tier="free-hybrid", price_eur=None)
        )
        data = json.loads(result)
        assert data["tier"] == "free-hybrid"
        assert "price_eur" not in data

    def test_premium_requires_price(self):
        """Premium tier without price raises ValueError."""
        from src.commands.functions.importexport import build_content_manifest

        with pytest.raises(ValueError, match="price_eur is required"):
            build_content_manifest(**self._base_args(price_eur=None))

    def test_free_forbids_price(self):
        """Free tier with price raises ValueError."""
        from src.commands.functions.importexport import build_content_manifest

        with pytest.raises(ValueError, match="price_eur is not allowed"):
            build_content_manifest(
                **self._base_args(tier="free", price_eur=10.0)
            )

    def test_empty_contents_rejected(self):
        """Empty contents list raises ValueError."""
        from src.commands.functions.importexport import build_content_manifest

        with pytest.raises(ValueError, match="contents must not be empty"):
            build_content_manifest(**self._base_args(contents=[]))

    def test_empty_name_rejected(self):
        """Empty name raises ValueError."""
        from src.commands.functions.importexport import build_content_manifest

        with pytest.raises(ValueError, match="name must not be empty"):
            build_content_manifest(**self._base_args(name=""))

    def test_invalid_tier_rejected(self):
        """Unknown tier raises ValueError."""
        from src.commands.functions.importexport import build_content_manifest

        with pytest.raises(ValueError, match="Invalid tier"):
            build_content_manifest(**self._base_args(tier="platinum"))

    def test_invalid_license_rejected(self):
        """Unknown license raises ValueError."""
        from src.commands.functions.importexport import build_content_manifest

        with pytest.raises(ValueError, match="Invalid license"):
            build_content_manifest(**self._base_args(license="bsd-2"))

    def test_invalid_source_rejected(self):
        """Unknown source raises ValueError."""
        from src.commands.functions.importexport import build_content_manifest

        with pytest.raises(ValueError, match="Invalid source"):
            build_content_manifest(**self._base_args(source="robot"))

    def test_json_parseable(self):
        """Output is valid JSON."""
        from src.commands.functions.importexport import build_content_manifest

        result = build_content_manifest(**self._base_args())
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_schema_field_present(self):
        """Schema version field is present."""
        from src.commands.functions.importexport import build_content_manifest

        result = build_content_manifest(**self._base_args())
        data = json.loads(result)
        assert "schema" in data
        assert data["schema"].startswith("emblem-content-manifest/")

    def test_dependencies_included(self):
        """Dependencies appear in manifest when provided."""
        from src.commands.functions.importexport import build_content_manifest

        result = build_content_manifest(
            **self._base_args(
                dependencies=["Mac700 Profile Extended", "Generic Dimmer"]
            )
        )
        data = json.loads(result)
        assert data["dependencies"] == [
            "Mac700 Profile Extended",
            "Generic Dimmer",
        ]

    def test_human_contribution_included(self):
        """Human contribution appears in manifest when provided."""
        from src.commands.functions.importexport import build_content_manifest

        result = build_content_manifest(
            **self._base_args(human_contribution="Color palette for touring")
        )
        data = json.loads(result)
        assert data["human_contribution"] == "Color palette for touring"
