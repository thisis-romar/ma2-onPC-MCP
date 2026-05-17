# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
tests/test_md_version_discipline.py — Unit tests for MD version discipline.

Tests the validation logic in scripts/validate_md_versions.py and
the audit logic in scripts/audit_md_version_history.py.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

# Import the validation script as a module
_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"

_spec_validate = importlib.util.spec_from_file_location(
    "validate_md_versions", _SCRIPTS / "validate_md_versions.py"
)
validate_mod = importlib.util.module_from_spec(_spec_validate)
sys.modules["validate_md_versions"] = validate_mod
_spec_validate.loader.exec_module(validate_mod)

_spec_audit = importlib.util.spec_from_file_location(
    "audit_md_version_history", _SCRIPTS / "audit_md_version_history.py"
)
audit_mod = importlib.util.module_from_spec(_spec_audit)
sys.modules["audit_md_version_history"] = audit_mod
_spec_audit.loader.exec_module(audit_mod)


# ── Shared fixtures ─────────────────────────────────────────────────────

VALID_FM = """\
---
title: Test Doc
description: A test document
version: {version}
created: 2026-01-01T00:00:00Z
last_updated: {last_updated}
---

## Content

Some body text here.
"""

VALID_FM_WITH_HEADING = """\
---
title: Test Doc
description: A test document
version: {version}
created: 2026-01-01T00:00:00Z
last_updated: {last_updated}
---

## Content

Some body text here.

## New Section

Added new content.
"""


def _make_doc(version: str = "1.0.0", last_updated: str = "2026-01-01T00:00:00Z",
              body: str = "## Content\n\nSome body text here.") -> str:
    return (
        f"---\ntitle: Test Doc\ndescription: A test document\n"
        f"version: {version}\ncreated: 2026-01-01T00:00:00Z\n"
        f"last_updated: {last_updated}\n---\n\n{body}\n"
    )


# ── Test parse_semver ────────────────────────────────────────────────────


class TestParseSemver:
    def test_valid(self):
        assert validate_mod.parse_semver("1.2.3") == (1, 2, 3)

    def test_valid_zeros(self):
        assert validate_mod.parse_semver("0.0.0") == (0, 0, 0)

    def test_valid_large(self):
        assert validate_mod.parse_semver("42.100.7") == (42, 100, 7)

    def test_invalid_two_parts(self):
        assert validate_mod.parse_semver("1.2") is None

    def test_invalid_alpha(self):
        assert validate_mod.parse_semver("abc") is None

    def test_invalid_prerelease(self):
        assert validate_mod.parse_semver("1.0.0-beta") is None

    def test_empty(self):
        assert validate_mod.parse_semver("") is None


# ── Test parse_front_matter ──────────────────────────────────────────────


class TestParseFrontMatter:
    def test_valid(self):
        doc = _make_doc("2.1.0", "2026-04-01T12:00:00Z")
        fm = validate_mod.parse_front_matter(doc)
        assert fm is not None
        assert fm["version"] == "2.1.0"
        assert fm["last_updated"] == "2026-04-01T12:00:00Z"

    def test_no_frontmatter(self):
        assert validate_mod.parse_front_matter("# Just a heading\n\nBody.") is None

    def test_missing_version(self):
        doc = "---\ntitle: Test\nlast_updated: 2026-01-01T00:00:00Z\n---\nBody."
        fm = validate_mod.parse_front_matter(doc)
        assert fm is not None
        assert "version" not in fm
        assert fm["last_updated"] == "2026-01-01T00:00:00Z"

    def test_missing_last_updated(self):
        doc = "---\ntitle: Test\nversion: 1.0.0\n---\nBody."
        fm = validate_mod.parse_front_matter(doc)
        assert fm is not None
        assert fm["version"] == "1.0.0"
        assert "last_updated" not in fm


# ── Test content_changed_beyond_frontmatter ──────────────────────────────


class TestContentChanged:
    def test_identical(self):
        doc = _make_doc()
        assert validate_mod.content_changed_beyond_frontmatter(doc, doc) is False

    def test_only_version_changed(self):
        old = _make_doc("1.0.0", "2026-01-01T00:00:00Z")
        new = _make_doc("1.0.1", "2026-04-01T00:00:00Z")
        assert validate_mod.content_changed_beyond_frontmatter(old, new) is False

    def test_body_changed(self):
        old = _make_doc(body="## Content\n\nOld text.")
        new = _make_doc(body="## Content\n\nNew text.")
        assert validate_mod.content_changed_beyond_frontmatter(old, new) is True

    def test_heading_added(self):
        old = _make_doc(body="## Content\n\nText.")
        new = _make_doc(body="## Content\n\nText.\n\n## New Section\n\nMore.")
        assert validate_mod.content_changed_beyond_frontmatter(old, new) is True


# ── Test validate_file (with mocked git) ─────────────────────────────────


class TestValidateFile:
    """Test validate_file by mocking git_show to return controlled content."""

    def _mock_git_show(self, head_content, staged_content):
        """Return a mock for git_show that returns head/staged content."""
        def mock(ref, filepath):
            if ref == "HEAD":
                return head_content
            if ref == "":
                return staged_content
            return None
        return mock

    def test_new_file_valid(self):
        """New file (not in HEAD) with valid front matter passes."""
        staged = _make_doc("1.0.0", "2026-04-01T00:00:00Z")
        with patch.object(validate_mod, "git_show", self._mock_git_show(None, staged)):
            findings = validate_mod.validate_file("new.md")
        assert len(findings) == 0

    def test_missing_bump(self):
        """Content changed but version not bumped -> error."""
        old = _make_doc("1.0.0", "2026-01-01T00:00:00Z", body="Old content.")
        new = _make_doc("1.0.0", "2026-04-01T00:00:00Z", body="New content.")
        with patch.object(validate_mod, "git_show", self._mock_git_show(old, new)):
            findings = validate_mod.validate_file("test.md")
        checks = [f["check"] for f in findings]
        assert "missing_bump" in checks

    def test_stale_timestamp(self):
        """Content changed but last_updated not bumped -> error."""
        old = _make_doc("1.0.0", "2026-01-01T00:00:00Z", body="Old content.")
        new = _make_doc("1.0.1", "2026-01-01T00:00:00Z", body="New content.")
        with patch.object(validate_mod, "git_show", self._mock_git_show(old, new)):
            findings = validate_mod.validate_file("test.md")
        checks = [f["check"] for f in findings]
        assert "stale_timestamp" in checks

    def test_correct_bump(self):
        """Content changed with proper version + timestamp bump -> pass."""
        old = _make_doc("1.0.0", "2026-01-01T00:00:00Z", body="Old content.")
        new = _make_doc("1.0.1", "2026-04-01T00:00:00Z", body="New content.")
        with patch.object(validate_mod, "git_show", self._mock_git_show(old, new)):
            findings = validate_mod.validate_file("test.md")
        assert len(findings) == 0

    def test_regression(self):
        """Version decreased -> error."""
        old = _make_doc("2.0.0", "2026-01-01T00:00:00Z", body="Old.")
        new = _make_doc("1.9.0", "2026-04-01T00:00:00Z", body="New.")
        with patch.object(validate_mod, "git_show", self._mock_git_show(old, new)):
            findings = validate_mod.validate_file("test.md")
        checks = [f["check"] for f in findings]
        assert "regression" in checks

    def test_skipped_version(self):
        """Version jumped by more than 1 -> warning."""
        old = _make_doc("1.0.0", "2026-01-01T00:00:00Z", body="Old.")
        new = _make_doc("1.0.3", "2026-04-01T00:00:00Z", body="New.")
        with patch.object(validate_mod, "git_show", self._mock_git_show(old, new)):
            findings = validate_mod.validate_file("test.md")
        checks = [f["check"] for f in findings]
        assert "skipped_version" in checks
        # Verify it's a warning, not error
        for f in findings:
            if f["check"] == "skipped_version":
                assert f["severity"] == "warning"

    def test_metadata_only_no_error(self):
        """Only front matter changed (no body change) -> no findings."""
        old = _make_doc("1.0.0", "2026-01-01T00:00:00Z")
        new = _make_doc("1.0.1", "2026-04-01T00:00:00Z")
        with patch.object(validate_mod, "git_show", self._mock_git_show(old, new)):
            findings = validate_mod.validate_file("test.md")
        assert len(findings) == 0

    def test_no_frontmatter_in_staged(self):
        """Staged file has no front matter -> error."""
        staged = "# Just a heading\n\nNo front matter here."
        with patch.object(validate_mod, "git_show", self._mock_git_show(None, staged)):
            findings = validate_mod.validate_file("test.md")
        checks = [f["check"] for f in findings]
        assert "has_frontmatter" in checks

    def test_invalid_timestamp_format(self):
        """Non-ISO timestamp -> error."""
        staged = _make_doc("1.0.0", "April 1, 2026")
        with patch.object(validate_mod, "git_show", self._mock_git_show(None, staged)):
            findings = validate_mod.validate_file("test.md")
        checks = [f["check"] for f in findings]
        assert "timestamp_format" in checks

    def test_minor_bump_resets_patch(self):
        """1.0.5 -> 1.1.0 is a valid MINOR bump."""
        old = _make_doc("1.0.5", "2026-01-01T00:00:00Z", body="Old.")
        new = _make_doc("1.1.0", "2026-04-01T00:00:00Z", body="New.")
        with patch.object(validate_mod, "git_show", self._mock_git_show(old, new)):
            findings = validate_mod.validate_file("test.md")
        assert len(findings) == 0

    def test_major_bump_resets(self):
        """1.5.3 -> 2.0.0 is a valid MAJOR bump."""
        old = _make_doc("1.5.3", "2026-01-01T00:00:00Z", body="Old.")
        new = _make_doc("2.0.0", "2026-04-01T00:00:00Z", body="New.")
        with patch.object(validate_mod, "git_show", self._mock_git_show(old, new)):
            findings = validate_mod.validate_file("test.md")
        assert len(findings) == 0


# ── Test exclusions ──────────────────────────────────────────────────────


class TestExclusions:
    def test_github_template_excluded(self):
        assert validate_mod.is_excluded(".github/pull_request_template.md") is True

    def test_vscode_excluded(self):
        assert validate_mod.is_excluded("vscode-mcp-provider/README.md") is True

    def test_venv_excluded(self):
        assert validate_mod.is_excluded(".venv/lib/something.md") is True

    def test_claude_md_not_excluded(self):
        assert validate_mod.is_excluded("CLAUDE.md") is False

    def test_skill_not_excluded(self):
        assert validate_mod.is_excluded(".claude/skills/busking/SKILL.md") is False

    def test_doc_not_excluded(self):
        assert validate_mod.is_excluded("doc/gap-audit.md") is False


# ── Test audit classification ────────────────────────────────────────────


class TestAuditClassification:
    """Test classify_transition from the audit module."""

    def test_missing_bump(self):
        old = _make_doc("1.0.0", body="Old content.")
        new = _make_doc("1.0.0", body="New content.")
        cls, old_v, new_v = audit_mod.classify_transition(old, new)
        assert cls == "missing_bump"

    def test_correct_bump(self):
        old = _make_doc("1.0.0", body="Old content.")
        new = _make_doc("1.0.1", body="New content.")
        cls, _, _ = audit_mod.classify_transition(old, new)
        assert cls == "correct_bump"

    def test_regression(self):
        old = _make_doc("2.0.0", body="Old.")
        new = _make_doc("1.5.0", body="New.")
        cls, _, _ = audit_mod.classify_transition(old, new)
        assert cls == "regression"

    def test_skip(self):
        old = _make_doc("1.0.0", body="Old.")
        new = _make_doc("1.0.5", body="New.")
        cls, _, _ = audit_mod.classify_transition(old, new)
        assert cls == "skip"

    def test_metadata_only(self):
        old = _make_doc("1.0.0")
        new = _make_doc("1.0.1")  # same body, only version changed
        cls, _, _ = audit_mod.classify_transition(old, new)
        assert cls == "metadata_only"

    def test_no_frontmatter(self):
        cls, _, _ = audit_mod.classify_transition(None, "# No FM\n\nBody.")
        assert cls == "no_frontmatter"

    def test_new_file(self):
        new = _make_doc("1.0.0")
        cls, old_v, new_v = audit_mod.classify_transition(None, new)
        assert cls == "no_frontmatter"
        assert old_v is None
        assert new_v == "1.0.0"
