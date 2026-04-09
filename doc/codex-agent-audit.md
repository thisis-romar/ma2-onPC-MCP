# Codex Agent Safety Audit (2026-04-09)

## Scope

This audit covers:

- Git hooks under `.githooks/`
- LLM/repository attribution controls (`NOTICE`, `FORKS.md`, README attribution checks)
- Agent-safe defaults for autonomous coding workflows

## Findings

### Git/GitHub hooks

**Strengths**

- `pre-commit` enforces BSL header checks, trade-secret pattern checks, version consistency checks, and attribution checks.
- `pre-commit` runs Ruff and refreshes the RAG index.
- `pre-push` blocks pushes when required license/attribution files are missing and runs tests.
- `prepare-commit-msg` blocks sensitive business language in commit messages.
- `stop-git-check.sh` protects against leaving uncommitted/unpushed work.

**Risks / gaps**

- Hooks are advisory unless installed (`make install-hooks`), so clean environments may skip protections.
- Hook checks are strong on IP and quality but not specific to agent runtime safety policy.

### LLM/repo attribution policy

**Strengths**

- Attribution files exist (`NOTICE`, `FORKS.md`) and are guarded by hooks.
- README is enforced to include upstream attribution by pre-commit.

**Risks / gaps**

- No explicit AGENTS.md contract existed for agent behavior and safety rails.
- README wording historically overstated auth maturity and learning-loop autonomy.

## Remediations applied

1. Added root `AGENTS.md` with explicit safety constraints for agent execution.
2. Updated docs to clarify scope enforcement is a local stub model (not full external OAuth token validation).
3. Updated docs language from “closed learning loop” to telemetry-backed suggestion loop.
4. Lowered documented default scope to `tier:0` and added `.env.codex.safe`.
5. Added `scripts/codex_smoke.sh` and `make codex-smoke` as an obvious safe validation entrypoint.
6. Provisioned dedicated git worktrees for sub-agents.

## Sub-agent worktrees provisioned

- `../worktrees/subagent-hooks` (branch `subagent/hooks`)
- `../worktrees/subagent-attribution` (branch `subagent/attribution`)
- `../worktrees/subagent-safety-docs` (branch `subagent/safety-docs`)
