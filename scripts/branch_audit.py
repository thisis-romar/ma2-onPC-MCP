#!/usr/bin/env python3
# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Multi-branch audit script implementing 8 dimensions.

Audits both main and the current feature branch, producing a structured
JSON report at doc/audit-report.json.

Dimensions:
  D1  changelog_health         CHANGELOG.md format, version monotonicity, gaps
  D2  version_sync             pyproject / __init__ / CHANGELOG latest entry
  D3  frontmatter_validation   YAML front matter on all .md files
  D4  mcp_surface_extended     Resources (17), Prompts (13), Skills (34)
  D5  tier_mapping             TOOL_LICENSE_TIERS + _OPERATION_MIN_RIGHT coverage
  D6  hooks_content            .githooks presence, executability, SHA256
  D7  config_drift             Cross-branch config file hash comparison
  D8  lint_baseline            Ruff error count per branch

Usage:
    python scripts/branch_audit.py
    python scripts/branch_audit.py --branches main HEAD
    python scripts/branch_audit.py --output doc/audit-report.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Tool source files — checked in both monolith (main) and submodule (feature) layouts.
# Excludes auth.py and license.py: their @mcp.tool() references are docstring examples,
# not actual tool registrations.
_TOOL_FILES_SUBMODULE = [
    "src/server.py",
    "src/tools_community.py",
    "src/private/tools_professional.py",
    "src/private/tools_enterprise.py",
    "src/private/server_orchestration_tools.py",
]
_TOOL_FILES_MONOLITH = [
    "src/server.py",
    "src/tools_community.py",
    "src/tools_professional.py",
    "src/tools_enterprise.py",
    "src/server_orchestration_tools.py",
]

_EXPECTED_HOOKS = ["pre-commit", "pre-push", "prepare-commit-msg", "stop-git-check.sh"]

_CONFIG_FILES = [
    ".mcp.json", ".claude/settings.json", "pytest.ini",
    "pyproject.toml", ".env.template", ".gitignore",
]

_FM_EXCLUDE_PARTS = {".venv", ".pytest_cache", "node_modules", ".git", "vscode-mcp-provider"}
_FM_REQUIRED = {"title", "description", "version", "created", "last_updated"}
_ISO_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
_SEMVER_RE = re.compile(r"\d+\.\d+\.\d+")


# ── Data structures ──────────────────────────────────────────────────


@dataclass
class Finding:
    dimension: str
    check: str
    severity: str  # sev1, sev2, sev3, sev4
    message: str
    evidence: dict | None = None


@dataclass
class DimensionResult:
    id: str
    status: str  # pass, warn, fail
    findings: list[Finding] = field(default_factory=list)
    evidence: dict = field(default_factory=dict)


@dataclass
class BranchContext:
    root: Path
    branch: str


# ── Helpers ──────────────────────────────────────────────────────────


def _sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_version_tuple(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in v.split("."))


def _tool_source_files(root: Path) -> list[Path]:
    """Return existing tool source files, trying submodule layout first."""
    sub = [root / f for f in _TOOL_FILES_SUBMODULE]
    if all(p.exists() for p in sub if "private" in str(p)):
        return [p for p in sub if p.exists()]
    mono = [root / f for f in _TOOL_FILES_MONOLITH]
    return [p for p in mono if p.exists()]


def _collect_tool_names(root: Path) -> set[str]:
    """Extract @mcp.tool() decorated function names from source files."""
    # Allow optional leading whitespace (orchestration tools are indented
    # inside a register_*() wrapper function).
    # Use [ \t]* (horizontal whitespace) instead of \s* to prevent
    # exponential backtracking where \s* would compete with \n.
    tool_re = re.compile(
        r"^[ \t]*@mcp\.tool\(\)[ \t]*\n(?:[ \t]*@[\w.]+(?:\(.*?\))?[ \t]*\n)*"
        r"[ \t]*async\s+def\s+(\w+)\(",
        re.MULTILINE,
    )
    names: set[str] = set()
    for src in _tool_source_files(root):
        names.update(m.group(1) for m in tool_re.finditer(src.read_text(encoding="utf-8")))
    return names


def _status(findings: list[Finding]) -> str:
    if any(f.severity == "sev1" for f in findings):
        return "fail"
    if any(f.severity in ("sev2", "sev3") for f in findings):
        return "warn"
    if findings:
        return "warn"
    return "pass"




# ── D1: Changelog Health ────────────────────────────────────────────


def dim_changelog_health(ctx: BranchContext) -> DimensionResult:
    findings: list[Finding] = []
    cl_path = ctx.root / "CHANGELOG.md"
    dim = "changelog_health"

    if not cl_path.exists():
        return DimensionResult(dim, "fail", [
            Finding(dim, "exists", "sev1", "CHANGELOG.md missing"),
        ])

    text = cl_path.read_text(encoding="utf-8")

    # Front matter
    fm = re.match(r"^---\n(.+?)\n---", text, re.DOTALL)
    if not fm:
        findings.append(Finding(dim, "frontmatter", "sev2", "Missing YAML front matter"))
    else:
        for fld in ("title", "description", "version", "created", "last_updated"):
            if f"{fld}:" not in fm.group(1):
                findings.append(Finding(dim, f"fm_{fld}", "sev3",
                                        f"Missing front matter field: {fld}"))

    # Parse version entries
    ver_re = re.compile(r"^## \[(\d+\.\d+\.\d+)\] — (\d{4}-\d{2}-\d{2})", re.MULTILINE)
    versions = [(m.group(1), m.group(2)) for m in ver_re.finditer(text)]
    evidence = {"version_count": len(versions),
                "versions": [v[0] for v in versions]}

    # Monotonicity
    for i in range(len(versions) - 1):
        cur = _parse_version_tuple(versions[i][0])
        nxt = _parse_version_tuple(versions[i + 1][0])
        if cur <= nxt:
            findings.append(Finding(dim, "monotonicity", "sev2",
                f"Non-monotonic: [{versions[i][0]}] followed by [{versions[i+1][0]}]"))

    # Gap detection (same major, minor gap > 1)
    gaps: list[str] = []
    for i in range(len(versions) - 1):
        cur = _parse_version_tuple(versions[i][0])
        nxt = _parse_version_tuple(versions[i + 1][0])
        if cur[0] == nxt[0]:
            minor_gap = cur[1] - nxt[1]
            if minor_gap > 1:
                gaps.append(f"{versions[i][0]} -> {versions[i+1][0]} (skipped {minor_gap - 1} minor)")
    if gaps:
        findings.append(Finding(dim, "version_gaps", "sev4",
            f"{len(gaps)} version gap(s) detected", evidence={"gaps": gaps}))

    # Keep a Changelog headers
    kac = {"Added", "Changed", "Fixed", "Removed", "Deprecated", "Security"}
    found = set(re.findall(r"^### (\w+)", text, re.MULTILINE))
    used = kac & found
    evidence["kac_headers_used"] = sorted(used)

    # Latest entry matches pyproject.toml
    pp = ctx.root / "pyproject.toml"
    if pp.exists() and versions:
        pp_m = re.search(r'version\s*=\s*"([^"]+)"', pp.read_text(encoding="utf-8"))
        if pp_m and pp_m.group(1) != versions[0][0]:
            findings.append(Finding(dim, "pyproject_match", "sev2",
                f"Latest CHANGELOG [{versions[0][0]}] != pyproject.toml [{pp_m.group(1)}]"))

    return DimensionResult(dim, _status(findings), findings, evidence)


# ── D2: Version Sync ────────────────────────────────────────────────


def dim_version_sync(ctx: BranchContext) -> DimensionResult:
    findings: list[Finding] = []
    dim = "version_sync"
    versions: dict[str, str | None] = {}

    # pyproject.toml
    pp = ctx.root / "pyproject.toml"
    if pp.exists():
        m = re.search(r'version\s*=\s*"([^"]+)"', pp.read_text(encoding="utf-8"))
        versions["pyproject.toml"] = m.group(1) if m else None
    else:
        versions["pyproject.toml"] = None

    # src/__init__.py
    init = ctx.root / "src" / "__init__.py"
    if init.exists():
        m = re.search(r'__version__\s*=\s*"([^"]+)"', init.read_text(encoding="utf-8"))
        versions["src/__init__.py"] = m.group(1) if m else None
    else:
        versions["src/__init__.py"] = None

    # CHANGELOG.md latest entry (NOT frontmatter version)
    cl = ctx.root / "CHANGELOG.md"
    if cl.exists():
        m = re.search(r"^## \[(\d+\.\d+\.\d+)\]", cl.read_text(encoding="utf-8"), re.MULTILINE)
        versions["CHANGELOG.md (latest entry)"] = m.group(1) if m else None
    else:
        versions["CHANGELOG.md (latest entry)"] = None

    # README.md frontmatter (doc version — info only, not error if different)
    rm = ctx.root / "README.md"
    if rm.exists():
        fm = re.match(r"^---\n(.+?)\n---", rm.read_text(encoding="utf-8"), re.DOTALL)
        if fm:
            m = re.search(r"^version:\s*(.+)$", fm.group(1), re.MULTILINE)
            versions["README.md (doc version)"] = m.group(1).strip() if m else None
        else:
            versions["README.md (doc version)"] = None
    else:
        versions["README.md (doc version)"] = None

    # Compare canonical trio: pyproject == __init__ == changelog latest
    canonical = {k: v for k, v in versions.items() if "README" not in k}
    vals = [v for v in canonical.values() if v is not None]
    if len(set(vals)) > 1:
        findings.append(Finding(dim, "canonical_sync", "sev2",
            f"Version mismatch: {canonical}"))
    elif not vals:
        findings.append(Finding(dim, "canonical_sync", "sev1",
            "No version found in any canonical location"))

    # Info: README doc version
    readme_v = versions.get("README.md (doc version)")
    canon_v = versions.get("pyproject.toml")
    if readme_v and canon_v and readme_v != canon_v:
        findings.append(Finding(dim, "readme_doc_version", "sev4",
            f"README doc version ({readme_v}) differs from package version ({canon_v}) — expected for doc versioning"))

    return DimensionResult(dim, _status(findings), findings, evidence={"versions": versions})




# ── D3: Frontmatter Validation ──────────────────────────────────────


def dim_frontmatter_validation(ctx: BranchContext) -> DimensionResult:
    findings: list[Finding] = []
    dim = "frontmatter_validation"
    checked = 0
    missing_fm = 0
    missing_fields: list[str] = []

    for md in sorted(ctx.root.rglob("*.md")):
        if any(part in _FM_EXCLUDE_PARTS for part in md.parts):
            continue
        rel = md.relative_to(ctx.root)
        checked += 1

        try:
            text = md.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        fm = re.match(r"^---\n(.+?)\n---", text, re.DOTALL)
        if not fm:
            missing_fm += 1
            findings.append(Finding(dim, "has_frontmatter", "sev3",
                                    f"{rel}: missing front matter"))
            continue

        fm_text = fm.group(1)
        for fld in _FM_REQUIRED:
            if f"{fld}:" not in fm_text:
                missing_fields.append(f"{rel}:{fld}")
                findings.append(Finding(dim, f"field_{fld}", "sev3",
                                        f"{rel}: missing field '{fld}'"))

        # Validate created/last_updated are ISO 8601
        for date_field in ("created", "last_updated"):
            m = re.search(rf"^{date_field}:\s*(.+)$", fm_text, re.MULTILINE)
            if m and not _ISO_RE.fullmatch(m.group(1).strip()):
                findings.append(Finding(dim, f"{date_field}_format", "sev3",
                    f"{rel}: {date_field} not ISO 8601: {m.group(1).strip()}"))

        # Check last_updated >= created
        cr_m = re.search(r"^created:\s*(.+)$", fm_text, re.MULTILINE)
        lu_m = re.search(r"^last_updated:\s*(.+)$", fm_text, re.MULTILINE)
        if cr_m and lu_m:
            cr_val = cr_m.group(1).strip()
            lu_val = lu_m.group(1).strip()
            if _ISO_RE.fullmatch(cr_val) and _ISO_RE.fullmatch(lu_val) and lu_val < cr_val:
                findings.append(Finding(dim, "date_order", "sev3",
                    f"{rel}: last_updated ({lu_val}) < created ({cr_val})"))

        # Version is semver
        v_m = re.search(r"^version:\s*(.+)$", fm_text, re.MULTILINE)
        if v_m and not _SEMVER_RE.fullmatch(v_m.group(1).strip()):
            findings.append(Finding(dim, "version_semver", "sev3",
                f"{rel}: version not semver: {v_m.group(1).strip()}"))

    evidence = {"files_checked": checked, "missing_frontmatter": missing_fm,
                "missing_fields_count": len(missing_fields)}
    return DimensionResult(dim, _status(findings), findings, evidence)


# ── D4: MCP Surface Extended ────────────────────────────────────────


def dim_mcp_surface_extended(ctx: BranchContext) -> DimensionResult:
    findings: list[Finding] = []
    dim = "mcp_surface_extended"

    server_py = ctx.root / "src" / "server.py"
    if not server_py.exists():
        return DimensionResult(dim, "fail", [
            Finding(dim, "server_exists", "sev1", "src/server.py not found"),
        ])

    text = server_py.read_text(encoding="utf-8")
    resources = text.count("@mcp.resource(")
    prompts = text.count("@mcp.prompt()")

    skills_dir = ctx.root / ".claude" / "skills"
    skills = 0
    if skills_dir.is_dir():
        skills = sum(1 for d in skills_dir.iterdir()
                     if d.is_dir() and (d / "SKILL.md").exists())

    # Tool count
    tools = sum(
        src.read_text(encoding="utf-8").count("@mcp.tool()")
        for src in _tool_source_files(ctx.root)
    )

    evidence = {"tools": tools, "resources": resources, "prompts": prompts, "skills": skills}

    # Compare against CLAUDE.md claims
    claude_md = ctx.root / "CLAUDE.md"
    if claude_md.exists():
        cm_text = claude_md.read_text(encoding="utf-8")
        for label, actual, patterns in [
            ("resources", resources, [r"\*\*(\d+) resources\*\*", r"(\d+) MCP resources"]),
            ("prompts", prompts, [r"\*\*(\d+) prompts\*\*", r"(\d+) MCP prompts"]),
            ("skills", skills, [r"\*\*(\d+) skills\*\*"]),
        ]:
            for pat in patterns:
                m = re.search(pat, cm_text)
                if m and int(m.group(1)) != actual:
                    findings.append(Finding(dim, f"claim_{label}", "sev2",
                        f"CLAUDE.md claims {m.group(1)} {label}, actual {actual}"))
                    break

    return DimensionResult(dim, _status(findings), findings, evidence)




# ── D5: Tier Mapping Completeness ───────────────────────────────────


def dim_tier_mapping(ctx: BranchContext) -> DimensionResult:
    findings: list[Finding] = []
    dim = "tier_mapping"

    tool_names = _collect_tool_names(ctx.root)
    evidence: dict = {"tool_count": len(tool_names)}

    # Parse TOOL_LICENSE_TIERS
    tiers_path = ctx.root / "src" / "license_tiers.py"
    tier_mapped: set[str] = set()
    tier_counts: dict[str, int] = {"COMMUNITY": 0, "PROFESSIONAL": 0, "ENTERPRISE": 0}
    if tiers_path.exists():
        tiers_text = tiers_path.read_text(encoding="utf-8")
        tier_re = re.compile(r'"(\w+)":\s*(PRO|ENT)')
        for m in tier_re.finditer(tiers_text):
            tier_mapped.add(m.group(1))
            if m.group(2) == "PRO":
                tier_counts["PROFESSIONAL"] += 1
            else:
                tier_counts["ENTERPRISE"] += 1
        # COMMUNITY = tools NOT in the map
        tier_counts["COMMUNITY"] = len(tool_names) - len(tier_mapped & tool_names)
    else:
        findings.append(Finding(dim, "tiers_file", "sev2",
                                "src/license_tiers.py not found"))

    evidence["tier_distribution"] = tier_counts
    evidence["tier_mapped_count"] = len(tier_mapped)

    # Phantom entries in tier map (mapped but no matching tool)
    phantom_tiers = tier_mapped - tool_names
    if phantom_tiers:
        findings.append(Finding(dim, "phantom_tiers", "sev4",
            f"{len(phantom_tiers)} phantom entries in TOOL_LICENSE_TIERS",
            evidence={"phantoms": sorted(phantom_tiers)}))

    # Parse _OPERATION_MIN_RIGHT
    rights_path = ctx.root / "src" / "rights.py"
    rights_mapped: set[str] = set()
    if rights_path.exists():
        rights_text = rights_path.read_text(encoding="utf-8")
        rights_re = re.compile(r'"(\w+)":\s*MA2Right\.\w+')
        rights_mapped = {m.group(1) for m in rights_re.finditer(rights_text)}
    else:
        findings.append(Finding(dim, "rights_file", "sev2",
                                "src/rights.py not found"))

    evidence["rights_mapped_count"] = len(rights_mapped)

    # Tools missing from _OPERATION_MIN_RIGHT
    missing_rights = tool_names - rights_mapped
    if missing_rights:
        findings.append(Finding(dim, "missing_rights", "sev2",
            f"{len(missing_rights)} tool(s) missing from _OPERATION_MIN_RIGHT",
            evidence={"missing": sorted(missing_rights)}))

    # Phantom entries in rights map
    phantom_rights = rights_mapped - tool_names
    if phantom_rights:
        findings.append(Finding(dim, "phantom_rights", "sev4",
            f"{len(phantom_rights)} phantom entries in _OPERATION_MIN_RIGHT",
            evidence={"phantoms": sorted(phantom_rights)}))

    return DimensionResult(dim, _status(findings), findings, evidence)


# ── D6: Hooks Content ───────────────────────────────────────────────


def dim_hooks_content(ctx: BranchContext) -> DimensionResult:
    findings: list[Finding] = []
    dim = "hooks_content"
    hooks_dir = ctx.root / ".githooks"
    hashes: dict[str, str | None] = {}

    for hook in _EXPECTED_HOOKS:
        path = hooks_dir / hook
        if not path.exists():
            findings.append(Finding(dim, f"exists_{hook}", "sev2",
                                    f"Missing hook: {hook}"))
            hashes[hook] = None
            continue
        if not os.access(path, os.X_OK):
            findings.append(Finding(dim, f"exec_{hook}", "sev3",
                                    f"Hook not executable: {hook}"))
        hashes[hook] = hashlib.sha256(path.read_bytes()).hexdigest()

    # Makefile install-hooks target
    makefile = ctx.root / "Makefile"
    if makefile.exists():
        if "install-hooks" not in makefile.read_text(encoding="utf-8"):
            findings.append(Finding(dim, "makefile_target", "sev3",
                                    "Makefile missing install-hooks target"))
    else:
        findings.append(Finding(dim, "makefile_exists", "sev3",
                                "Makefile not found"))

    return DimensionResult(dim, _status(findings), findings,
                           evidence={"hook_hashes": hashes})


# ── D7: Config Drift (cross-branch) ─────────────────────────────────


def dim_config_drift(main_ctx: BranchContext, feat_ctx: BranchContext) -> DimensionResult:
    findings: list[Finding] = []
    dim = "config_drift"
    evidence: dict[str, dict] = {}

    for cf in _CONFIG_FILES:
        main_hash = _sha256(main_ctx.root / cf)
        feat_hash = _sha256(feat_ctx.root / cf)
        if main_hash != feat_hash:
            status_label = "added" if main_hash is None else "removed" if feat_hash is None else "changed"
            findings.append(Finding(dim, f"drift_{cf}", "sev4",
                f"Config drift ({status_label}): {cf}"))
            evidence[cf] = {"main": main_hash, "feature": feat_hash, "status": status_label}

    return DimensionResult(dim, _status(findings), findings, evidence)


# ── D8: Lint Baseline ────────────────────────────────────────────────


def dim_lint_baseline(ctx: BranchContext) -> DimensionResult:
    findings: list[Finding] = []
    dim = "lint_baseline"

    ruff = shutil.which("ruff")
    if not ruff:
        return DimensionResult(dim, "warn", [
            Finding(dim, "ruff_available", "sev3", "ruff not found in PATH"),
        ])

    # Build list of dirs that exist
    dirs = [str(d) for d in [ctx.root / "src", ctx.root / "tests", ctx.root / "rag"]
            if d.is_dir()]
    if not dirs:
        return DimensionResult(dim, "warn", [
            Finding(dim, "no_source_dirs", "sev3", "No source dirs found"),
        ])

    result = subprocess.run(
        [ruff, "check", "--output-format", "json", "--quiet"] + dirs,
        capture_output=True, text=True, cwd=str(ctx.root), timeout=120,
    )

    error_count = 0
    by_rule: dict[str, int] = {}
    if result.stdout.strip().startswith("["):
        try:
            errors = json.loads(result.stdout)
            error_count = len(errors)
            by_rule = dict(Counter(e.get("code", "unknown") for e in errors))
        except json.JSONDecodeError:
            findings.append(Finding(dim, "parse_error", "sev3",
                                    "Failed to parse ruff JSON output"))

    if error_count > 0:
        findings.append(Finding(dim, "lint_errors", "sev4",
            f"{error_count} lint error(s) found",
            evidence={"by_rule": by_rule}))

    return DimensionResult(dim, _status(findings), findings,
                           evidence={"error_count": error_count, "by_rule": by_rule})




# ── Orchestration ────────────────────────────────────────────────────


def audit_branch(ctx: BranchContext) -> dict:
    """Run all per-branch dimensions and return results dict."""
    dimensions = [
        dim_changelog_health,
        dim_version_sync,
        dim_frontmatter_validation,
        dim_mcp_surface_extended,
        dim_tier_mapping,
        dim_hooks_content,
        dim_lint_baseline,
    ]
    results: dict[str, dict] = {}
    for dim_fn in dimensions:
        try:
            result = dim_fn(ctx)
            results[result.id] = {
                "status": result.status,
                "findings": [asdict(f) for f in result.findings],
                "evidence": result.evidence,
            }
        except Exception as exc:
            results[dim_fn.__name__.removeprefix("dim_")] = {
                "status": "error",
                "findings": [{
                    "dimension": dim_fn.__name__,
                    "check": "execution",
                    "severity": "sev2",
                    "message": f"Dimension failed: {exc}",
                    "evidence": None,
                }],
                "evidence": {},
            }
    return results


def _get_current_branch(repo: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, cwd=str(repo),
    )
    return result.stdout.strip() or "HEAD"


def _summarize(per_branch: dict, cross: dict) -> dict:
    severity_counts: dict[str, int] = {"sev1": 0, "sev2": 0, "sev3": 0, "sev4": 0}
    status_counts: dict[str, int] = {"pass": 0, "warn": 0, "fail": 0, "error": 0}

    for branch_data in per_branch.values():
        for dim_data in branch_data.values():
            status_counts[dim_data.get("status", "error")] = \
                status_counts.get(dim_data.get("status", "error"), 0) + 1
            for f in dim_data.get("findings", []):
                sev = f.get("severity", "sev4")
                severity_counts[sev] = severity_counts.get(sev, 0) + 1

    for dim_data in cross.values():
        for f in dim_data.get("findings", []):
            sev = f.get("severity", "sev4")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

    total = sum(severity_counts.values())
    return {
        "total_findings": total,
        "by_severity": severity_counts,
        "dimensions_passed": status_counts.get("pass", 0),
        "dimensions_warned": status_counts.get("warn", 0),
        "dimensions_failed": status_counts.get("fail", 0),
        "dimensions_errored": status_counts.get("error", 0),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Multi-branch audit — 8 dimensions")
    parser.add_argument("--branches", nargs="*", default=["main", "HEAD"],
                        help="Branches to audit (default: main HEAD)")
    parser.add_argument("--output", default="doc/audit-report.json",
                        help="Output JSON path (default: doc/audit-report.json)")
    args = parser.parse_args()

    repo_root = REPO_ROOT
    current_branch = _get_current_branch(repo_root)
    worktrees: list[str] = []
    contexts: dict[str, BranchContext] = {}
    per_branch: dict[str, dict] = {}

    print(f"[audit] Starting audit on {len(args.branches)} branch(es)...")
    print(f"[audit] Current branch: {current_branch}")

    try:
        for branch in args.branches:
            label = current_branch if branch == "HEAD" else branch
            print(f"\n[audit] === Auditing branch: {label} ===")

            if branch == "HEAD":
                ctx = BranchContext(repo_root, current_branch)
            else:
                wt = tempfile.mkdtemp(prefix=f"ma2-audit-{branch.replace('/', '-')}-")
                print(f"[audit] Creating worktree at {wt}")
                result = subprocess.run(
                    ["git", "worktree", "add", wt, branch],
                    capture_output=True, text=True, cwd=str(repo_root),
                )
                if result.returncode != 0:
                    print(f"[audit] ERROR: Failed to create worktree for {branch}: {result.stderr}")
                    continue
                worktrees.append(wt)
                ctx = BranchContext(Path(wt), branch)

            contexts[label] = ctx
            per_branch[label] = audit_branch(ctx)

            # Print per-dimension status
            for dim_id, dim_data in per_branch[label].items():
                status = dim_data["status"]
                n_findings = len(dim_data.get("findings", []))
                icon = {"pass": "OK", "warn": "!!", "fail": "XX", "error": "ER"}[status]
                print(f"  [{icon}] {dim_id}: {status} ({n_findings} finding(s))")

        # Cross-branch comparison
        cross: dict[str, dict] = {}
        ctx_list = list(contexts.values())
        if len(ctx_list) >= 2:
            print("\n[audit] === Cross-branch comparison ===")
            drift = dim_config_drift(ctx_list[0], ctx_list[1])
            cross["config_drift"] = {
                "status": drift.status,
                "findings": [asdict(f) for f in drift.findings],
                "evidence": drift.evidence,
            }
            n = len(drift.findings)
            print(f"  [{('OK' if n == 0 else '!!')}] config_drift: {drift.status} ({n} finding(s))")

            # Lint delta
            e0 = per_branch.get(ctx_list[0].branch, {}).get("lint_baseline", {}).get("evidence", {})
            e1 = per_branch.get(ctx_list[1].branch, {}).get("lint_baseline", {}).get("evidence", {})
            cross["lint_delta"] = {
                f"{ctx_list[0].branch}_errors": e0.get("error_count", "?"),
                f"{ctx_list[1].branch}_errors": e1.get("error_count", "?"),
            }

        # Build report
        report = {
            "meta": {
                "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "script_version": "1.0.0",
                "branches_audited": [b if b != "HEAD" else current_branch for b in args.branches],
            },
            "per_branch": per_branch,
            "cross_branch": cross,
            "summary": _summarize(per_branch, cross),
        }

        # Write report
        out_path = repo_root / args.output
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        print(f"\n[audit] Report written to {out_path}")

        # Summary
        s = report["summary"]
        print("\n[audit] === SUMMARY ===")
        print(f"  Total findings: {s['total_findings']}")
        print(f"  By severity: sev1={s['by_severity']['sev1']}, sev2={s['by_severity']['sev2']}, "
              f"sev3={s['by_severity']['sev3']}, sev4={s['by_severity']['sev4']}")
        print(f"  Dimensions: {s['dimensions_passed']} pass, {s['dimensions_warned']} warn, "
              f"{s['dimensions_failed']} fail, {s['dimensions_errored']} error")

        return 1 if s["by_severity"]["sev1"] > 0 else 0

    finally:
        for wt in worktrees:
            print(f"[audit] Cleaning up worktree {wt}")
            subprocess.run(
                ["git", "worktree", "remove", "--force", wt],
                capture_output=True, cwd=str(repo_root),
            )


if __name__ == "__main__":
    sys.exit(main())
