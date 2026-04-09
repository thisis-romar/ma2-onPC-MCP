# AGENTS.md

This file defines agent operating rules for the entire repository.

## Safety-first operating mode

- Treat all grandMA2 console interactions as **high risk**.
- Default to **no live Telnet access** and no production console connections.
- Prefer read-only analysis, tests, static checks, and dry-run planning.
- Assume secrets are absent unless explicitly provided by a human.

## Hard prohibitions (unless explicitly requested by a human)

- Do **not** enable or rely on bypass flags:
  - `GMA_AUTH_BYPASS`
  - `GMA_RIGHTS_BYPASS`
  - `GMA_LICENSE_BYPASS`
- Do **not** increase default scope or permissions in `.env.template`.
- Do **not** run destructive MA2 operations unattended.
- Do **not** modify auth/rights/destructive codepaths without explicit user approval.

## Safe defaults for agent work

- Start with `GMA_SCOPE=tier:0` in agent workspaces.
- Use local/non-live environments only.
- Never store real console credentials in examples or docs.

## Required validation before proposing changes

Run these checks (or document why a check could not be run):

1. `uv sync`
2. `uv run pytest -q tests/test_auth.py`
3. `uv run pytest -q tests/test_rights.py`
4. `uv run python -m src.server --help`

## Branch, commit, and PR conventions

- Use focused branches for each sub-task.
- Keep commits small and descriptive.
- Include a safety rationale in PR summaries for any behavior-affecting change.
