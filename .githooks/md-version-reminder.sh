#!/bin/bash
# .githooks/md-version-reminder.sh
# Claude Code PostToolUse hook — reminds about .md version bumps.
# Receives tool input/output JSON on stdin.
# Advisory only (always exits 0). Hard enforcement is in the pre-commit hook.

input=$(cat)

# Require jq for JSON parsing
if ! command -v jq >/dev/null 2>&1; then
    echo "WARNING: jq not installed — md-version-reminder hook disabled. Install jq for .md version bump reminders." >&2
    exit 0
fi

# Extract file_path from the tool input JSON
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null)

# If no file path or not a .md file, exit silently
if [[ -z "$file_path" ]] || [[ "$file_path" != *.md ]]; then
    exit 0
fi

# Check if the file has YAML front matter with a version field
if [[ -f "$file_path" ]] && head -1 "$file_path" | grep -q "^---$"; then
    if grep -q "^version:" "$file_path"; then
        echo "REMINDER: You edited $file_path — remember to bump its front matter 'version' and 'last_updated' before committing. Rules: PATCH for fixes/typos, MINOR for new content, MAJOR for restructures." >&2
    fi
fi

exit 0
