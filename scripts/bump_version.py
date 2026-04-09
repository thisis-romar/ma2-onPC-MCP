#!/usr/bin/env python3
# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""Bump version across all tracked files and optionally create a git tag.

Updates pyproject.toml, src/__init__.py, LICENSE, and README.md badge
atomically.  Use --check to verify consistency without making changes.

Usage:
    python scripts/bump_version.py --check            # verify version sync
    python scripts/bump_version.py 3.36.0             # bump to 3.36.0
    python scripts/bump_version.py 3.36.0 --tag       # bump + create git tag
    python scripts/bump_version.py --patch             # auto-increment patch
    python scripts/bump_version.py --minor             # auto-increment minor
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

FILES = {
    "pyproject.toml": {
        "path": REPO_ROOT / "pyproject.toml",
        "pattern": r'(version\s*=\s*")[^"]+(")',
    },
    "src/__init__.py": {
        "path": REPO_ROOT / "src" / "__init__.py",
        "pattern": r'(__version__\s*=\s*")[^"]+(")',
    },
    "LICENSE": {
        "path": REPO_ROOT / "LICENSE",
        "pattern": r"(Licensed Work:\s+GrandPA2-Buddy \(ma2-onPC-MCP\) v)[^\n]+",
    },
    "README.md": {
        "path": REPO_ROOT / "README.md",
        "pattern": r'(Version-)[^-]+((-purple\?|-))',
    },
}

# README badge has an additional alt text occurrence
README_ALT_PATTERN = r'(alt="Version )[^"]+(")'


def _read_current_version() -> str:
    """Read current version from pyproject.toml."""
    text = FILES["pyproject.toml"]["path"].read_text()
    m = re.search(r'version\s*=\s*"([^"]+)"', text)
    if not m:
        print("ERROR: Cannot parse version from pyproject.toml", file=sys.stderr)
        sys.exit(1)
    return m.group(1)


def _read_version_from(name: str) -> str | None:
    """Read the version string from a tracked file."""
    info = FILES[name]
    path: Path = info["path"]
    if not path.exists():
        return None
    text = path.read_text()
    if name == "pyproject.toml":
        m = re.search(r'version\s*=\s*"([^"]+)"', text)
    elif name == "src/__init__.py":
        m = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    elif name == "LICENSE":
        m = re.search(r"Licensed Work:\s+GrandPA2-Buddy \(ma2-onPC-MCP\) v([\d.]+)", text)
    elif name == "README.md":
        m = re.search(r"Version-([\d.]+)-purple", text)
    else:
        return None
    return m.group(1) if m else None


def check_consistency() -> bool:
    """Check that all files have the same version. Returns True if consistent."""
    versions: dict[str, str | None] = {}
    for name in FILES:
        versions[name] = _read_version_from(name)

    unique = set(v for v in versions.values() if v is not None)
    if len(unique) == 1:
        print(f"OK: All files at version {unique.pop()}")
        return True

    print("VERSION DRIFT DETECTED:")
    for name, ver in versions.items():
        status = "" if ver == versions["pyproject.toml"] else " ← MISMATCH"
        print(f"  {name}: {ver}{status}")
    return False


def _increment(version: str, part: str) -> str:
    """Increment a semver string by part (major, minor, patch)."""
    parts = version.split(".")
    if len(parts) != 3:
        print(f"ERROR: Version '{version}' is not valid semver (MAJOR.MINOR.PATCH)", file=sys.stderr)
        sys.exit(1)
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    return f"{major}.{minor}.{patch}"


def bump(new_version: str) -> None:
    """Update all tracked files to new_version."""
    current = _read_current_version()
    print(f"Bumping {current} → {new_version}")

    # pyproject.toml
    path = FILES["pyproject.toml"]["path"]
    text = path.read_text()
    text = re.sub(r'(version\s*=\s*")[^"]+"', rf"\g<1>{new_version}\"", text, count=1)
    path.write_text(text)
    print("  Updated pyproject.toml")

    # src/__init__.py
    path = FILES["src/__init__.py"]["path"]
    text = path.read_text()
    text = re.sub(r'(__version__\s*=\s*")[^"]+"', rf"\g<1>{new_version}\"", text, count=1)
    path.write_text(text)
    print("  Updated src/__init__.py")

    # LICENSE
    path = FILES["LICENSE"]["path"]
    text = path.read_text()
    text = re.sub(
        r"(Licensed Work:\s+GrandPA2-Buddy \(ma2-onPC-MCP\) v)[\d.]+",
        rf"\g<1>{new_version}",
        text,
        count=1,
    )
    path.write_text(text)
    print("  Updated LICENSE")

    # README.md — badge URL + alt text
    path = FILES["README.md"]["path"]
    text = path.read_text()
    text = re.sub(r"Version-[\d.]+-purple", f"Version-{new_version}-purple", text)
    text = re.sub(r'alt="Version [^"]+"', f'alt="Version {new_version}"', text)
    path.write_text(text)
    print("  Updated README.md")

    print(f"\nAll files updated to {new_version}")


def create_tag(version: str) -> None:
    """Create an annotated git tag for the given version."""
    tag = f"v{version}"
    result = subprocess.run(
        ["git", "tag", "-a", tag, "-m", f"Release {version}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: git tag failed: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    print(f"Created annotated tag: {tag}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bump project version across all tracked files")
    parser.add_argument("version", nargs="?", help="Target version (e.g. 3.36.0)")
    parser.add_argument("--check", action="store_true", help="Check consistency only, no changes")
    parser.add_argument("--patch", action="store_true", help="Auto-increment patch version")
    parser.add_argument("--minor", action="store_true", help="Auto-increment minor version")
    parser.add_argument("--major", action="store_true", help="Auto-increment major version")
    parser.add_argument("--tag", action="store_true", help="Create annotated git tag after bump")

    args = parser.parse_args()

    if args.check:
        ok = check_consistency()
        sys.exit(0 if ok else 1)

    # Determine target version
    current = _read_current_version()
    if args.version:
        new_version = args.version
    elif args.patch:
        new_version = _increment(current, "patch")
    elif args.minor:
        new_version = _increment(current, "minor")
    elif args.major:
        new_version = _increment(current, "major")
    else:
        parser.error("Provide a version number or use --patch/--minor/--major")
        return

    # Validate not downgrading
    if new_version == current:
        print(f"Already at version {current}, nothing to do.")
        sys.exit(0)

    bump(new_version)

    if args.tag:
        create_tag(new_version)


if __name__ == "__main__":
    main()
