#!/usr/bin/env python3
# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Validate markdown front matter version discipline for staged files.

For each staged .md file, compares the version/last_updated in HEAD
against the staged version. Catches:
  - Missing bumps (content changed, version not bumped)
  - Regressions (new version < old version)
  - Skipped versions (increment by >1 in any component)
  - Invalid timestamps (last_updated not ISO 8601)
  - Stale timestamps (last_updated not bumped when content changed)

Only validates files actually staged in the current commit.
Never touches, bumps, or flags files that were not modified.

Usage:
    python scripts/validate_md_versions.py --staged          # staged .md files
    python scripts/validate_md_versions.py FILE1 FILE2       # specific files
    python scripts/validate_md_versions.py --staged --json   # machine-readable
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
ISO_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
FM_RE = re.compile(r"^---\n(.+?)\n---", re.DOTALL)

# Paths excluded from version discipline
EXCLUDE_PATHS = {".github/pull_request_template.md"}
EXCLUDE_PARTS = frozenset(
    {".venv", ".pytest_cache", "node_modules", ".git", "vscode-mcp-provider"}
)


def parse_front_matter(text: str) -> dict[str, str] | None:
    """Extract version and last_updated from YAML front matter."""
    m = FM_RE.match(text)
    if not m:
        return None
    fm = m.group(1)
    result: dict[str, str] = {}
    for field in ("version", "last_updated"):
        line_m = re.search(rf"^{field}:\s*(.+)$", fm, re.MULTILINE)
        if line_m:
            result[field] = line_m.group(1).strip()
    return result


def parse_semver(v: str) -> tuple[int, int, int] | None:
    m = SEMVER_RE.match(v)
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def strip_frontmatter(text: str) -> str:
    """Return content after the front matter block."""
    m = FM_RE.match(text)
    if m:
        return text[m.end() :].strip()
    return text.strip()


def content_changed_beyond_frontmatter(old_text: str, new_text: str) -> bool:
    """Return True if content outside the front matter block changed.

    This prevents false positives when someone only bumps the
    version/last_updated (metadata-only change).
    """
    return strip_frontmatter(old_text) != strip_frontmatter(new_text)


def git_show(ref: str, filepath: str) -> str | None:
    """Get file content at a git ref. Returns None if not found."""
    result = subprocess.run(
        ["git", "show", f"{ref}:{filepath}"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        return None
    return result.stdout


def get_staged_md_files() -> list[str]:
    """Return list of staged .md files (Added, Copied, Modified)."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM", "--", "*.md"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    return [f.strip() for f in result.stdout.strip().splitlines() if f.strip()]


def is_excluded(filepath: str) -> bool:
    if filepath in EXCLUDE_PATHS:
        return True
    parts = Path(filepath).parts
    return any(part in EXCLUDE_PARTS for part in parts)


def validate_file(filepath: str) -> list[dict]:
    """Validate a single staged .md file. Returns list of findings."""
    findings: list[dict] = []

    staged_content = git_show("", filepath)  # empty ref = staging area (index)
    if staged_content is None:
        return []

    staged_fm = parse_front_matter(staged_content)
    if staged_fm is None:
        findings.append(
            {
                "file": filepath,
                "check": "has_frontmatter",
                "severity": "error",
                "message": f"{filepath}: no YAML front matter found",
            }
        )
        return findings

    # Validate last_updated is ISO 8601
    lu = staged_fm.get("last_updated", "")
    if lu and not ISO_RE.fullmatch(lu):
        findings.append(
            {
                "file": filepath,
                "check": "timestamp_format",
                "severity": "error",
                "message": (
                    f"{filepath}: last_updated '{lu}' is not ISO 8601 "
                    "(YYYY-MM-DDTHH:MM:SSZ)"
                ),
            }
        )

    # Validate version is semver
    staged_version = staged_fm.get("version", "")
    staged_sv = parse_semver(staged_version)
    if not staged_sv:
        if staged_version:
            findings.append(
                {
                    "file": filepath,
                    "check": "version_format",
                    "severity": "error",
                    "message": f"{filepath}: version '{staged_version}' is not valid semver",
                }
            )
        return findings

    # Get HEAD version for comparison
    head_content = git_show("HEAD", filepath)
    if head_content is None:
        # New file — no previous version to compare. Format checks only.
        return findings

    head_fm = parse_front_matter(head_content)
    if head_fm is None:
        # File didn't have front matter before. Accept the new version.
        return findings

    head_version = head_fm.get("version", "")
    head_sv = parse_semver(head_version)
    if not head_sv:
        # Previous version was malformed. Accept the new one.
        return findings

    has_content_change = content_changed_beyond_frontmatter(head_content, staged_content)

    # CHECK 1: Missing bump — content changed but version didn't
    if has_content_change and staged_sv == head_sv:
        findings.append(
            {
                "file": filepath,
                "check": "missing_bump",
                "severity": "error",
                "message": (
                    f"{filepath}: content changed but version unchanged "
                    f"(still {staged_version}). Bump version per "
                    "markdown-frontmatter.md rules."
                ),
            }
        )

    # CHECK 2: Missing last_updated bump — content changed but timestamp didn't
    head_lu = head_fm.get("last_updated", "")
    if has_content_change and lu and head_lu and lu == head_lu:
        findings.append(
            {
                "file": filepath,
                "check": "stale_timestamp",
                "severity": "error",
                "message": (
                    f"{filepath}: content changed but last_updated unchanged "
                    f"(still {lu}). Update last_updated to current time."
                ),
            }
        )

    # CHECK 3: Regression — new version < old version
    if staged_sv < head_sv:
        findings.append(
            {
                "file": filepath,
                "check": "regression",
                "severity": "error",
                "message": (
                    f"{filepath}: version regression {head_version} -> "
                    f"{staged_version}. Never downgrade a version."
                ),
            }
        )

    # CHECK 4: Skipped version — increment by more than 1 in any component
    if staged_sv > head_sv:
        major_d = staged_sv[0] - head_sv[0]
        minor_d = staged_sv[1] - head_sv[1]
        patch_d = staged_sv[2] - head_sv[2]

        skipped = False
        if major_d > 1:
            skipped = True
        elif major_d == 0:
            if minor_d > 1:
                skipped = True
            elif minor_d == 0 and patch_d > 1:
                skipped = True

        if skipped:
            findings.append(
                {
                    "file": filepath,
                    "check": "skipped_version",
                    "severity": "warning",
                    "message": (
                        f"{filepath}: version skipped {head_version} -> "
                        f"{staged_version}. Increment by exactly 1."
                    ),
                }
            )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate MD version discipline")
    parser.add_argument("files", nargs="*", help="Specific .md files to check")
    parser.add_argument(
        "--staged", action="store_true", help="Check all staged .md files"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output findings as JSON"
    )
    args = parser.parse_args()

    if args.staged:
        files = get_staged_md_files()
    elif args.files:
        files = args.files
    else:
        parser.error("Provide --staged or file paths")
        return 2

    # Filter exclusions
    files = [f for f in files if not is_excluded(f)]

    if not files:
        if not args.json:
            print("[md-version] No .md files to check.")
        return 0

    all_findings: list[dict] = []
    for filepath in files:
        all_findings.extend(validate_file(filepath))

    if args.json:
        print(json.dumps(all_findings, indent=2))
    else:
        if not all_findings:
            print(
                f"[md-version] All {len(files)} staged .md file(s) pass "
                "version discipline."
            )
        else:
            errors = [f for f in all_findings if f["severity"] == "error"]
            warnings = [f for f in all_findings if f["severity"] == "warning"]
            for f in all_findings:
                prefix = "ERROR" if f["severity"] == "error" else "WARNING"
                print(f"[md-version] {prefix}: {f['message']}")
            if errors:
                print(
                    f"\n[md-version] {len(errors)} error(s), "
                    f"{len(warnings)} warning(s). Commit blocked."
                )

    errors = [f for f in all_findings if f["severity"] == "error"]
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
