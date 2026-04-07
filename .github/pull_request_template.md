## What does this change?


## Safety classification
- [ ] SAFE_READ — read-only queries, no console side-effects
- [ ] SAFE_WRITE — non-destructive console mutations (go, at, clear, park)
- [ ] DESTRUCTIVE — irreversible mutations (delete, store, copy, move, assign)

If DESTRUCTIVE: describe the `confirm_destructive` gate and how it's tested.

## How to test
- [ ] `uv run python -m pytest -v -m "not live"`
- [ ] `uv run ruff check src/ tests/ rag/`
- [ ] `uv run mypy src/ rag/`
- [ ] (If applicable) Live integration test with console

## Risk notes
Describe any risk to tool dispatch, Telnet command building, auth/scope enforcement, or show data integrity.

## Checklist
- [ ] Command builders in `src/commands/` are pure functions (no I/O)
- [ ] New `.md` files have YAML front matter
- [ ] DESTRUCTIVE tools accept `confirm_destructive: bool = False`
- [ ] Tests added for new functionality
