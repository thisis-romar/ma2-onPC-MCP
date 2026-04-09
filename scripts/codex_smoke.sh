#!/usr/bin/env bash
set -euo pipefail

uv sync
uv run pytest -q tests/test_auth.py
uv run pytest -q tests/test_rights.py
uv run python -m src.server --help
