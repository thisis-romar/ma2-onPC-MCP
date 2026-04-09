#!/usr/bin/env python3
# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Audit markdown version discipline across full git history.

For each .md file, walks all commits that touched it and classifies
each transition as: correct_bump, missing_bump, overbump, underbump,
skip, regression, metadata_only, or no_frontmatter.

Produces per-file scorecards and an overall summary.

Usage:
    python scripts/audit_md_version_history.py                      # all .md files
    python scripts/audit_md_version_history.py CLAUDE.md README.md  # specific files
    python scripts/audit_md_version_history.py --json               # machine-readable
    python scripts/audit_md_version_history.py --summary-only       # just scores
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
FM_RE = re.compile(r"^---\n(.+?)\n---", re.DOTALL)
HEADING_RE = re.compile(r"^#{2,}\s+", re.MULTILINE)

# Paths to skip (no front matter or separate sub-project)
EXCLUDE_PATHS = {".github/pull_request_template.md"}
EXCLUDE_PARTS = {".venv", ".pytest_cache", "node_modules", ".git", "vscode-mcp-provider"}


@dataclass
class Transition:
    """One commit's version transition for a file."""

    commit_hash: str
    commit_msg: str
    old_version: str | None
    new_version: str | None
    classification: str  # correct_bump, missing_bump, overbump, underbump, skip, regression, metadata_only, no_frontmatter


@dataclass
class FileReport:
    """Audit report for a single .md file."""

    filepath: str
    total_commits: int = 0
    transitions: list[Transition] = field(default_factory=list)

    @property
    def score(self) -> float | None:
        """Discipline score: correct / (correct + violations) * 100."""
        correct = sum(1 for t in self.transitions if t.classification == "correct_bump")
        violations = sum(
            1
            for t in self.transitions
            if t.classification in ("missing_bump", "skip", "regression")
        )
        total = correct + violations
        if total == 0:
            return None
        return round(correct / total * 100, 1)


def parse_front_matter(text: str) -> dict[str, str] | None:
    """Extract version and last_updated from YAML front matter."""
    m = FM_RE.match(text)
    if not m:
        return None
    fm = m.group(1)
    result: dict[str, str] = {}
    for f in ("version", "last_updated"):
        line_m = re.search(rf"^{f}:\s*(.+)$", fm, re.MULTILINE)
        if line_m:
            result[f] = line_m.group(1).strip()
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


def git_show(ref: str, filepath: str) -> str | None:
    """Get file content at a specific git ref."""
    result = subprocess.run(
        ["git", "show", f"{ref}:{filepath}"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        return None
    return result.stdout


def get_commit_log(filepath: str) -> list[tuple[str, str]]:
    """Return [(hash, subject)] for all commits touching a file, newest first."""
    result = subprocess.run(
        ["git", "log", "--follow", "--format=%H %s", "--", filepath],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    entries = []
    for line in result.stdout.strip().splitlines():
        if not line.strip():
            continue
        parts = line.split(" ", 1)
        commit_hash = parts[0]
        msg = parts[1] if len(parts) > 1 else ""
        entries.append((commit_hash, msg))
    return entries


def count_new_headings(old_text: str, new_text: str) -> int:
    """Count markdown headings (##+ ) present in new but not old."""
    old_headings = set(HEADING_RE.findall(old_text))
    new_headings = set(HEADING_RE.findall(new_text))
    # Actually count heading LINES, not just patterns
    old_heading_lines = {
        line.strip() for line in old_text.splitlines() if HEADING_RE.match(line)
    }
    new_heading_lines = {
        line.strip() for line in new_text.splitlines() if HEADING_RE.match(line)
    }
    return len(new_heading_lines - old_heading_lines)


def content_diff_size(old_text: str, new_text: str) -> int:
    """Count lines changed (added + removed) outside front matter."""
    old_lines = set(strip_frontmatter(old_text).splitlines())
    new_lines = set(strip_frontmatter(new_text).splitlines())
    added = new_lines - old_lines
    removed = old_lines - new_lines
    return len(added) + len(removed)


def classify_transition(
    old_content: str | None,
    new_content: str | None,
) -> tuple[str, str | None, str | None]:
    """Classify a version transition between two commits.

    Returns (classification, old_version, new_version).
    """
    if new_content is None:
        return ("no_frontmatter", None, None)

    new_fm = parse_front_matter(new_content)
    if new_fm is None or "version" not in new_fm:
        return ("no_frontmatter", None, None)

    new_ver = new_fm["version"]
    new_sv = parse_semver(new_ver)

    if old_content is None:
        # File didn't exist before — first commit
        return ("no_frontmatter", None, new_ver)

    old_fm = parse_front_matter(old_content)
    if old_fm is None or "version" not in old_fm:
        return ("no_frontmatter", None, new_ver)

    old_ver = old_fm["version"]
    old_sv = parse_semver(old_ver)

    if old_sv is None or new_sv is None:
        return ("no_frontmatter", old_ver, new_ver)

    # Check if content beyond front matter changed
    content_changed = strip_frontmatter(old_content) != strip_frontmatter(new_content)

    if not content_changed:
        return ("metadata_only", old_ver, new_ver)

    # Content changed — now classify the version transition
    if new_sv == old_sv:
        return ("missing_bump", old_ver, new_ver)

    if new_sv < old_sv:
        return ("regression", old_ver, new_ver)

    # Version increased — check magnitude
    major_d = new_sv[0] - old_sv[0]
    minor_d = new_sv[1] - old_sv[1]
    patch_d = new_sv[2] - old_sv[2]

    # Check for skips
    skipped = False
    if major_d > 1:
        skipped = True
    elif major_d == 0:
        if minor_d > 1:
            skipped = True
        elif minor_d == 0 and patch_d > 1:
            skipped = True

    if skipped:
        return ("skip", old_ver, new_ver)

    # Version bumped by exactly 1 in some component — check bump level
    new_headings = count_new_headings(old_content, new_content)
    diff_size = content_diff_size(old_content, new_content)

    bump_type = "patch"
    if major_d >= 1:
        bump_type = "major"
    elif minor_d >= 1:
        bump_type = "minor"

    # Heuristic: new headings suggest MINOR-worthy, small diff suggests PATCH-worthy
    if bump_type == "minor" and new_headings == 0 and diff_size < 5:
        return ("overbump", old_ver, new_ver)

    if bump_type == "patch" and new_headings > 0:
        return ("underbump", old_ver, new_ver)

    return ("correct_bump", old_ver, new_ver)


def is_excluded(filepath: str) -> bool:
    if filepath in EXCLUDE_PATHS:
        return True
    parts = Path(filepath).parts
    return any(part in EXCLUDE_PARTS for part in parts)


def get_all_md_files() -> list[str]:
    """Get all tracked .md files."""
    result = subprocess.run(
        ["git", "ls-files", "*.md"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    return [f.strip() for f in result.stdout.strip().splitlines() if f.strip()]


def audit_file(filepath: str) -> FileReport:
    """Audit version discipline for a single file across all commits."""
    report = FileReport(filepath=filepath)
    commits = get_commit_log(filepath)
    report.total_commits = len(commits)

    if len(commits) < 2:
        return report

    # Walk from oldest to newest (reverse the list)
    commits = list(reversed(commits))

    for i in range(1, len(commits)):
        old_hash, _ = commits[i - 1]
        new_hash, new_msg = commits[i]

        old_content = git_show(old_hash, filepath)
        new_content = git_show(new_hash, filepath)

        classification, old_ver, new_ver = classify_transition(old_content, new_content)

        report.transitions.append(
            Transition(
                commit_hash=new_hash[:7],
                commit_msg=new_msg[:60],
                old_version=old_ver,
                new_version=new_ver,
                classification=classification,
            )
        )

    return report


def print_report(reports: list[FileReport], summary_only: bool = False) -> None:
    """Print human-readable audit report."""
    totals: dict[str, int] = {}

    for report in sorted(reports, key=lambda r: r.filepath):
        score = report.score
        score_str = f"{score:.0f}%" if score is not None else "N/A"

        if not summary_only:
            print(f"\n=== {report.filepath} ({report.total_commits} commits, score: {score_str}) ===")
            for t in report.transitions:
                old_v = t.old_version or "—"
                new_v = t.new_version or "—"
                print(f"  {old_v:>10} → {new_v:<10}  {t.commit_hash}  {t.classification:<16}  \"{t.commit_msg}\"")

        for t in report.transitions:
            totals[t.classification] = totals.get(t.classification, 0) + 1

    # Summary
    scored_reports = [r for r in reports if r.score is not None]
    if scored_reports:
        avg_score = sum(r.score for r in scored_reports) / len(scored_reports)
    else:
        avg_score = 0.0

    print(f"\n{'=' * 60}")
    print(f"=== SUMMARY ===")
    print(f"  Files audited:            {len(reports)}")
    print(f"  Files with scored history: {len(scored_reports)}")
    print(f"  Overall discipline score: {avg_score:.0f}%")
    print()
    for cls in (
        "correct_bump",
        "missing_bump",
        "overbump",
        "underbump",
        "skip",
        "regression",
        "metadata_only",
        "no_frontmatter",
    ):
        count = totals.get(cls, 0)
        if count > 0:
            print(f"  {cls:<20} {count:>4}")


def json_report(reports: list[FileReport]) -> dict:
    """Generate JSON-serializable audit report."""
    files = []
    for r in sorted(reports, key=lambda r: r.filepath):
        files.append(
            {
                "filepath": r.filepath,
                "total_commits": r.total_commits,
                "score": r.score,
                "transitions": [
                    {
                        "commit": t.commit_hash,
                        "message": t.commit_msg,
                        "old_version": t.old_version,
                        "new_version": t.new_version,
                        "classification": t.classification,
                    }
                    for t in r.transitions
                ],
            }
        )

    scored = [r for r in reports if r.score is not None]
    avg = sum(r.score for r in scored) / len(scored) if scored else 0.0

    totals: dict[str, int] = {}
    for r in reports:
        for t in r.transitions:
            totals[t.classification] = totals.get(t.classification, 0) + 1

    return {
        "files_audited": len(reports),
        "overall_score": round(avg, 1),
        "totals": totals,
        "files": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit .md version discipline across git history")
    parser.add_argument("files", nargs="*", help="Specific .md files to audit (default: all tracked)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--summary-only", action="store_true", help="Only print summary scores")
    args = parser.parse_args()

    if args.files:
        files = args.files
    else:
        files = get_all_md_files()

    files = [f for f in files if not is_excluded(f)]

    if not files:
        print("No .md files to audit.")
        return 0

    reports = []
    for filepath in files:
        reports.append(audit_file(filepath))

    if args.json:
        print(json.dumps(json_report(reports), indent=2))
    else:
        print_report(reports, summary_only=args.summary_only)

    return 0


if __name__ == "__main__":
    sys.exit(main())
