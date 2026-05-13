#!/bin/bash
# .githooks/stop-git-check.sh
# Claude Code Stop hook — ensures all changes are committed and pushed
# before Claude stops responding. Installed via project-level
# .claude/settings.json so all collaborators inherit it.

# Read the JSON input from stdin
input=$(cat)

# Check if stop hook is already active (recursion prevention)
# Use python as jq fallback since jq may not be in PATH on Windows
if command -v jq >/dev/null 2>&1; then
  stop_hook_active=$(echo "$input" | jq -r '.stop_hook_active')
else
  stop_hook_active=$(echo "$input" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('stop_hook_active',''))" 2>/dev/null || echo "")
fi
if [[ "$stop_hook_active" = "true" ]]; then
  exit 0
fi

# Check if we're in a git repository - bail if not
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  exit 0
fi

no_pr_reminder="Do not create a pull request unless the user has explicitly asked for one."

# Check for uncommitted changes (both staged and unstaged)
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "There are uncommitted changes in the repository. Please commit and push these changes to the remote branch. $no_pr_reminder" >&2
  exit 2
fi

# Check for untracked files that might be important
untracked_files=$(git ls-files --others --exclude-standard)
if [[ -n "$untracked_files" ]]; then
  echo "There are untracked files in the repository. Please commit and push these changes to the remote branch. $no_pr_reminder" >&2
  exit 2
fi

current_branch=$(git branch --show-current)
if [[ -n "$current_branch" ]]; then
  if git rev-parse "origin/$current_branch" >/dev/null 2>&1; then
    # Branch exists on remote - compare against it
    unpushed=$(git rev-list "origin/$current_branch..HEAD" --count 2>/dev/null) || unpushed=0
    if [[ "$unpushed" -gt 0 ]]; then
      echo "There are $unpushed unpushed commit(s) on branch '$current_branch'. Please push these changes to the remote repository. $no_pr_reminder" >&2
      exit 2
    fi
  else
    # Branch doesn't exist on remote - compare against default branch
    unpushed=$(git rev-list "origin/HEAD..HEAD" --count 2>/dev/null) || unpushed=0
    if [[ "$unpushed" -gt 0 ]]; then
      echo "Branch '$current_branch' has $unpushed unpushed commit(s) and no remote branch. Please push these changes to the remote repository. $no_pr_reminder" >&2
      exit 2
    fi
  fi
fi

exit 0
