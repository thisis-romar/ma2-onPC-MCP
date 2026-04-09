#!/usr/bin/env bash
# .githooks/gitflow-guard.sh
# Local Gitflow branch policy guardrails for commit/push hooks.

set -euo pipefail

MODE="${1:-}"
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "DETACHED")"

# Gitflow branch names allowed for day-to-day work.
# Includes fix/docs to preserve existing contributor ergonomics.
# Transitional compatibility:
# - keep `claude/*` and `work` while migrating existing automation branches.
ALLOWED_BRANCH_RE='^(main|develop|feature\/.+|release\/.+|hotfix\/.+|fix\/.+|docs\/.+|claude\/.+|work)$'
PROTECTED_BRANCH_RE='^(main|develop)$'

_warn() {
    echo "[gitflow-guard] WARNING: $*"
}

_error() {
    echo "[gitflow-guard] ERROR: $*"
}

check_branch_name() {
    if [[ "$CURRENT_BRANCH" == "DETACHED" ]]; then
        _warn "HEAD is detached; skipping branch-name enforcement."
        return 0
    fi

    if [[ ! "$CURRENT_BRANCH" =~ $ALLOWED_BRANCH_RE ]]; then
        _error "Branch '$CURRENT_BRANCH' does not match Gitflow naming."
        _error "Allowed: main, develop, feature/*, release/*, hotfix/*, fix/*, docs/*, claude/*, work"
        return 1
    fi
}

check_no_direct_commit_to_protected() {
    if [[ "${GITFLOW_ALLOW_PROTECTED_COMMIT:-0}" == "1" ]]; then
        _warn "Protected-branch commit guard bypassed by GITFLOW_ALLOW_PROTECTED_COMMIT=1."
        return 0
    fi

    if [[ "$CURRENT_BRANCH" =~ $PROTECTED_BRANCH_RE ]]; then
        _error "Direct commits to '$CURRENT_BRANCH' are blocked by Gitflow policy."
        _error "Create a feature/*, fix/*, docs/*, release/*, or hotfix/* branch instead."
        return 1
    fi
}

check_no_direct_push_to_main() {
    if [[ "${GITFLOW_ALLOW_MAIN_PUSH:-0}" == "1" ]]; then
        _warn "Main push guard bypassed by GITFLOW_ALLOW_MAIN_PUSH=1."
        cat >/dev/null || true
        return 0
    fi

    local failed=0

    # pre-push stdin rows: <local ref> <local sha1> <remote ref> <remote sha1>
    while read -r local_ref _local_sha remote_ref _remote_sha; do
        [[ -z "${local_ref:-}" ]] && continue
        if [[ "$remote_ref" == "refs/heads/main" ]]; then
            _error "Direct push to main is blocked ($local_ref -> $remote_ref)."
            _error "Use PR flow: feature/fix/docs -> develop, then release/* or hotfix/* -> main."
            failed=1
        fi
    done

    return "$failed"
}

case "$MODE" in
    pre-commit)
        check_branch_name
        check_no_direct_commit_to_protected
        ;;
    pre-push)
        check_branch_name
        check_no_direct_push_to_main
        ;;
    *)
        _error "Unknown mode '$MODE'. Use: pre-commit | pre-push"
        exit 2
        ;;
esac
