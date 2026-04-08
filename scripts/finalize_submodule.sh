#!/usr/bin/env bash
# finalize_submodule.sh — Convert src/private/ from tracked directory to git submodule.
#
# Prerequisites:
#   1. Create https://github.com/thisis-romar/ma2-onPC-MCP-private (private repo)
#   2. Run this script from the repo root
#
# What this script does:
#   1. Initializes a temp git repo with the 3 paid-tier files
#   2. Pushes them to the private remote
#   3. Removes src/private/ from public tracking
#   4. Re-adds it as a proper git submodule
#   5. Commits the .gitmodules + submodule reference
#
# Usage:
#   bash scripts/finalize_submodule.sh [PRIVATE_REPO_URL]
#
# Default URL: https://github.com/thisis-romar/ma2-onPC-MCP-private.git

set -euo pipefail

PRIVATE_URL="${1:-https://github.com/thisis-romar/ma2-onPC-MCP-private.git}"
PRIVATE_DIR="src/private"
TMPDIR="$(mktemp -d)"

echo "==> Step 1: Prepare private repo content in $TMPDIR"
cp "$PRIVATE_DIR/tools_professional.py" "$TMPDIR/"
cp "$PRIVATE_DIR/tools_enterprise.py" "$TMPDIR/"
cp "$PRIVATE_DIR/server_orchestration_tools.py" "$TMPDIR/"
cp "$PRIVATE_DIR/__init__.py" "$TMPDIR/"

cd "$TMPDIR"
git init -b main
git add -A
git commit -m "feat: initial PROFESSIONAL + ENTERPRISE paid-tier tools

Extracted from thisis-romar/ma2-onPC-MCP src/private/ directory.

Contains:
  - tools_professional.py  (124 PROFESSIONAL MCP tools)
  - tools_enterprise.py    (20 ENTERPRISE MCP tools)
  - server_orchestration_tools.py  (34 ENTERPRISE agentic tools)
  - __init__.py  (src.private package root)"

echo "==> Step 2: Push to private remote ($PRIVATE_URL)"
git remote add origin "$PRIVATE_URL"
git push -u origin main

echo "==> Step 3: Remove src/private/ from public tracking"
cd - > /dev/null
git rm -r --cached "$PRIVATE_DIR"
rm -rf "$PRIVATE_DIR"

echo "==> Step 4: Add git submodule"
git submodule add "$PRIVATE_URL" "$PRIVATE_DIR"

echo "==> Step 5: Commit submodule reference"
git add .gitmodules "$PRIVATE_DIR"
git commit -m "feat: wire src/private/ as git submodule

Converts tracked src/private/ directory to a proper git submodule
pointing to $PRIVATE_URL.

Paid-tier tools (PROFESSIONAL + ENTERPRISE) now live in the
private repository. Public-only clones serve 20 COMMUNITY tools
via graceful degradation in server.py."

echo ""
echo "==> Done! Submodule wired successfully."
echo "    Private repo: $PRIVATE_URL"
echo "    Submodule path: $PRIVATE_DIR"
echo ""
echo "Next steps:"
echo "  1. git push origin <branch>"
echo "  2. Clone with submodule: git clone --recurse-submodules <public-url>"
echo "  3. Existing clones: git submodule update --init --recursive"

# Cleanup
rm -rf "$TMPDIR"
