#!/usr/bin/env bash
# .githooks/detect-claude-model.sh
# Detect the active Claude model from available runtime sources.
# Returns the model ID (e.g. claude-opus-4-6) on stdout.
# Exit 0 = detected, exit 1 = not in Claude Code context.
#
# Detection priority:
#   1. Process arguments (--model flag on running claude process)
#   2. Session transcript JSONL (model field in assistant messages)
#   3. Fallback: "unknown"

set -euo pipefail

# Quick exit if not in Claude Code
if [ "${CLAUDECODE:-}" != "1" ]; then
    exit 1
fi

# Method 1: Parse process arguments with session affinity via parent PID chain
# Filter to processes in our ancestry to avoid cross-session attribution
MODEL=""
if [ -n "${PPID:-}" ]; then
    # Walk up the process tree to find the claude process for THIS session
    PID="$PPID"
    while [ "$PID" -gt 1 ] 2>/dev/null; do
        CMDLINE=$(cat "/proc/$PID/cmdline" 2>/dev/null | tr '\0' ' ' || true)
        if echo "$CMDLINE" | grep -qP -- '--model '; then
            MODEL=$(echo "$CMDLINE" | grep -oP -- '--model \K[^ \[\]]+' || true)
            break
        fi
        PID=$(awk '{print $4}' "/proc/$PID/stat" 2>/dev/null || echo 0)
    done
fi
# Fallback: broad search if ancestry walk failed
if [ -z "$MODEL" ]; then
    MODEL=$(ps aux 2>/dev/null | grep -oP -- '--model \K[^ \[\]]+' | head -1 || true)
fi
if [ -n "$MODEL" ]; then
    echo "$MODEL"
    exit 0
fi

# Method 2: Parse session transcript JSONL
SESSION_ID="${CLAUDE_CODE_SESSION_ID:-}"
if [ -n "$SESSION_ID" ]; then
    PROJECTS_DIR="$HOME/.claude/projects"
    if [ -d "$PROJECTS_DIR" ]; then
        # Find the most recent JSONL for this project
        TRANSCRIPT=$(find "$PROJECTS_DIR" -name "*.jsonl" -newer /tmp -mmin -60 2>/dev/null | head -1 || true)
        if [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ]; then
            MODEL=$(grep -oP '"model"\s*:\s*"\K[^"]+' "$TRANSCRIPT" 2>/dev/null | head -1 || true)
            if [ -n "$MODEL" ]; then
                echo "$MODEL"
                exit 0
            fi
        fi
    fi
fi

echo "unknown"
exit 0
