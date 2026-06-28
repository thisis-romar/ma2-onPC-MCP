#!/usr/bin/env bash
# Phase 0 setup: install grandMA2 manual brain MCP server
# Run once on the operator machine before launching show-file subagents.
# Requires: Node.js 20+, C/C++ toolchain + Python 3 (for native sqlite3 module)
#
# After this script completes, update .mcp.json with the correct BRAIN_DIR path.
# Then restart the Claude Code session for the brain MCP to be available.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BRAIN_DIR="${1:-"$REPO_ROOT/../grandMA2-user.manual-agent.brain"}"
VAULT_DIR="${2:-"$REPO_ROOT/../grandma2-manual-vault"}"

echo "=== MA2 Brain MCP Setup ==="
echo "Brain dir : $BRAIN_DIR"
echo "Vault dir : $VAULT_DIR"
echo ""

# Clone vault if not already present
if [ ! -d "$VAULT_DIR/.git" ]; then
    echo "[1/5] Cloning grandma2-manual-vault..."
    git clone https://github.com/thisis-romar/grandma2-manual-vault.git "$VAULT_DIR"
else
    echo "[1/5] Vault already cloned — pulling latest..."
    git -C "$VAULT_DIR" pull --ff-only
fi

# Clone brain if not already present
if [ ! -d "$BRAIN_DIR/.git" ]; then
    echo "[2/5] Cloning grandMA2-user.manual-agent.brain..."
    git clone https://github.com/thisis-romar/grandMA2-user.manual-agent.brain.git "$BRAIN_DIR"
else
    echo "[2/5] Brain already cloned — pulling latest..."
    git -C "$BRAIN_DIR" pull --ff-only
fi

# Submodules
echo "[3/5] Initialising submodules..."
git -C "$BRAIN_DIR" submodule update --init --recursive

# Install deps (npm ci for reproducible install)
echo "[4/5] Installing Node dependencies..."
npm --prefix "$BRAIN_DIR" ci

# Build the FTS5 index over the vault
echo "[5/5] Indexing vault (building SQLite FTS5 database)..."
npm --prefix "$BRAIN_DIR" run index -- "$VAULT_DIR"

echo ""
echo "=== Setup complete ==="
echo ""
echo "Add the following entry to .mcp.json to register the brain server:"
echo ""
echo '    "ma2-brain": {'
echo '      "command": "npm",'
echo "      \"args\": [\"run\", \"serve\", \"$VAULT_DIR\"],"
echo "      \"cwd\": \"$BRAIN_DIR\""
echo '    }'
echo ""
echo "Then restart your Claude Code session."
