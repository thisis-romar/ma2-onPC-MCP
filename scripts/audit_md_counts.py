#!/usr/bin/env python3
# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Audit CLAUDE.md and README.md for stale counts.

Compares declared counts (tools, resources, prompts, skills, tests,
command builders, vocab keywords) against the actual codebase.
Exits non-zero if any declared count is stale.

Usage:
    python scripts/audit_md_counts.py          # audit only (exit 1 on drift)
    python scripts/audit_md_counts.py --fix    # auto-fix stale counts in-place
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"
README_MD = REPO_ROOT / "README.md"


# ── Count collectors ─────────────────────────────────────────────────


def _count_mcp_tools() -> int:
    """Count @mcp.tool() decorators across server files."""
    total = 0
    for p in (REPO_ROOT / "src" / "server.py",
              REPO_ROOT / "src" / "tools_community.py",
              REPO_ROOT / "src" / "private" / "tools_professional.py",
              REPO_ROOT / "src" / "private" / "tools_enterprise.py",
              REPO_ROOT / "src" / "private" / "server_orchestration_tools.py"):
        total += p.read_text(encoding="utf-8").count("@mcp.tool()")
    return total


def _count_mcp_resources() -> int:
    return (REPO_ROOT / "src" / "server.py").read_text(encoding="utf-8").count("@mcp.resource(")


def _count_mcp_prompts() -> int:
    return (REPO_ROOT / "src" / "server.py").read_text(encoding="utf-8").count("@mcp.prompt()")


def _count_skills() -> int:
    skills_dir = REPO_ROOT / ".claude" / "skills"
    if not skills_dir.is_dir():
        return 0
    return sum(1 for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists())


def _count_tests() -> int:
    """Run pytest --collect-only and parse the summary line."""
    result = subprocess.run(
        ["uv", "run", "python", "-m", "pytest", "--collect-only", "-q"],
        capture_output=True, text=True, cwd=REPO_ROOT, timeout=60,
    )
    # Last non-empty line looks like: "3027 tests collected in 4.97s"
    for line in reversed(result.stdout.strip().splitlines()):
        m = re.search(r"(\d+) tests? collected", line)
        if m:
            return int(m.group(1))
    return -1  # unknown


def _count_command_exports() -> tuple[int, int]:
    """Return (total_exports, constants)."""
    result = subprocess.run(
        ["uv", "run", "python", "-c",
         "from src.commands import __all__; "
         "consts = [n for n in __all__ if n.isupper()]; "
         f"print(len(__all__), len(consts))"],
        capture_output=True, text=True, cwd=REPO_ROOT, timeout=30,
    )
    parts = result.stdout.strip().split()
    if len(parts) == 2:
        return int(parts[0]), int(parts[1])
    return -1, -1


def _count_vocab_keywords() -> dict[str, int]:
    """Return keyword counts from the vocab JSON."""
    vocab_path = REPO_ROOT / "src" / "grandMA2_v3_9_telnet_keyword_vocabulary.json"
    data = json.loads(vocab_path.read_text(encoding="utf-8"))
    counts: dict[str, int] = {}
    for key in ("function_keywords", "object_keywords", "helping_keywords", "special_chars"):
        val = data.get(key, [])
        counts[key] = len(val) if isinstance(val, list) else int(val)
    counts["total"] = sum(counts.values())
    return counts


# ── Pattern matchers ─────────────────────────────────────────────────


class CountCheck:
    """A single count assertion against file content."""

    def __init__(self, label: str, actual: int, patterns: list[tuple[Path, str]]):
        self.label = label
        self.actual = actual
        # Each pattern is (file, regex) where group(1) is the old number
        self.patterns = patterns
        self.mismatches: list[tuple[Path, str, int, str]] = []  # (file, line, old, full_line)

    def scan(self) -> bool:
        """Return True if all declarations match actual."""
        ok = True
        for fpath, regex in self.patterns:
            text = fpath.read_text(encoding="utf-8")
            for m in re.finditer(regex, text):
                declared = int(m.group(1))
                if declared != self.actual:
                    # Find the line for reporting
                    start = text.rfind("\n", 0, m.start()) + 1
                    end = text.find("\n", m.end())
                    line = text[start:end if end != -1 else len(text)]
                    self.mismatches.append((fpath, line.strip(), declared, m.group(0)))
                    ok = False
        return ok

    def fix(self) -> int:
        """Replace stale numbers in-place. Returns count of fixes applied."""
        fixed = 0
        for fpath, regex in self.patterns:
            text = fpath.read_text(encoding="utf-8")
            new_text = text
            for m in reversed(list(re.finditer(regex, text))):
                declared = int(m.group(1))
                if declared != self.actual:
                    old_span = m.group(0)
                    new_span = old_span.replace(str(declared), str(self.actual), 1)
                    new_text = new_text[:m.start()] + new_span + new_text[m.end():]
                    fixed += 1
            if new_text != text:
                fpath.write_text(new_text, encoding="utf-8")
        return fixed


# ── Build all checks ─────────────────────────────────────────────────


def build_checks() -> list[CountCheck]:
    tools = _count_mcp_tools()
    resources = _count_mcp_resources()
    prompts = _count_mcp_prompts()
    skills = _count_skills()
    tests = _count_tests()
    total_exports, n_consts = _count_command_exports()
    n_funcs = total_exports - n_consts if total_exports > 0 else -1
    vocab = _count_vocab_keywords()

    checks: list[CountCheck] = []

    # Tools — appears in both files in many places
    checks.append(CountCheck("MCP tools", tools, [
        (CLAUDE_MD, r"\*\*(\d+) tools\*\*"),
        (CLAUDE_MD, r"All (\d+) MCP tools"),
        (CLAUDE_MD, r"test_all_(\d+)_tools_mapped"),
        (README_MD, r"MCP%20Tools-(\d+)"),
        (README_MD, r"(\d+) MCP Tools"),
        (README_MD, r"Exposes (\d+) grandMA2"),
        (README_MD, r"(\d+) MCP tools"),
        (README_MD, r"All (\d+) MCP tools"),
        (README_MD, r"All (\d+) tools are mapped"),
        (README_MD, r"(\d+) tools covering"),
    ]))

    # Resources
    checks.append(CountCheck("MCP resources", resources, [
        (CLAUDE_MD, r"\*\*(\d+) resources\*\*"),
        (CLAUDE_MD, r"(\d+) MCP resources"),
    ]))

    # Prompts
    checks.append(CountCheck("MCP prompts", prompts, [
        (CLAUDE_MD, r"\*\*(\d+) prompts\*\*"),
        (CLAUDE_MD, r"(\d+) MCP prompts"),
    ]))

    # Skills
    checks.append(CountCheck("skills", skills, [
        (CLAUDE_MD, r"\*\*(\d+) skills\*\*"),
        (CLAUDE_MD, r"(\d+) agentic tools"),
        (README_MD, r"(\d+) tools \(110"),
        (README_MD, r"(\d+) agentic tools"),
    ]))

    # Tests
    if tests > 0:
        checks.append(CountCheck("tests", tests, [
            (CLAUDE_MD, r"\*\*(\d+) tests\*\*"),
            (README_MD, r"Tests-(\d+)"),
            (README_MD, r"(\d+) Tests"),
        ]))

    # Command builder functions (pure, without constants)
    # CLAUDE.md distinguishes "N pure command-builder functions (M exports incl. K constants)"
    # README.md uses "N pure functions" in the mermaid diagram
    if n_funcs > 0:
        checks.append(CountCheck("command functions", n_funcs, [
            (CLAUDE_MD, r"(\d+) pure command-builder"),
            (README_MD, r"(\d+) pure functions"),
        ]))

    # Command builder total exports (functions + constants)
    # CLAUDE.md: "(272 exports incl. 8 constants)"
    # README.md: "264 exported command-builder functions" (these are totals, not func-only)
    if total_exports > 0:
        checks.append(CountCheck("command exports", total_exports, [
            (CLAUDE_MD, r"(\d+) exports incl"),
            (README_MD, r"(\d+) exported command-builder"),
        ]))

    # Vocab total
    checks.append(CountCheck("vocab keywords", vocab["total"], [
        (CLAUDE_MD, r"(\d+) keyword vocab entries"),
        (README_MD, r"(\d{2,}) keywords"),  # ≥2 digits to avoid false matches
    ]))

    # Vocab breakdown: function keywords
    checks.append(CountCheck("function keywords", vocab["function_keywords"], [
        (CLAUDE_MD, r"(\d+) function"),
    ]))

    # Vocab breakdown: object keywords
    checks.append(CountCheck("object keywords", vocab["object_keywords"], [
        (CLAUDE_MD, r"(\d+) object"),
    ]))

    # Vocab breakdown: helping keywords
    checks.append(CountCheck("helping keywords", vocab["helping_keywords"], [
        (CLAUDE_MD, r"(\d+) helping"),
    ]))

    # Vocab breakdown: special chars
    checks.append(CountCheck("special chars", vocab["special_chars"], [
        (CLAUDE_MD, r"(\d+) special"),
    ]))

    return checks


# ── Main ─────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit MD file counts")
    parser.add_argument("--fix", action="store_true",
                        help="Auto-fix stale counts in CLAUDE.md and README.md")
    args = parser.parse_args()

    checks = build_checks()
    drift: list[CountCheck] = []

    for chk in checks:
        if not chk.scan():
            drift.append(chk)

    if not drift:
        print("[audit] All counts up to date.")
        return 0

    # Report drift
    for chk in drift:
        for fpath, line, old, _ in chk.mismatches:
            print(f"[audit] DRIFT  {chk.label}: {fpath.name} says {old}, actual {chk.actual}")
            print(f"        {line}")

    if args.fix:
        total_fixed = 0
        for chk in drift:
            total_fixed += chk.fix()
        print(f"\n[audit] Fixed {total_fixed} stale count(s). Review the diff before committing.")
        return 0

    print(f"\n[audit] {sum(len(c.mismatches) for c in drift)} stale count(s) found. "
          f"Run with --fix to auto-repair.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
