server:
	./scripts/connect.sh

log:
	@echo "Usage: make log GMA_HOST=<ip>"
	telnet $(GMA_HOST) 30001

test:
	uv run pytest -v

install-hooks:
	git config core.hooksPath .githooks
	chmod +x .githooks/pre-commit
	chmod +x .githooks/pre-push
	chmod +x .githooks/prepare-commit-msg
	chmod +x .githooks/stop-git-check.sh
	chmod +x .githooks/md-version-reminder.sh
	@echo "Git hooks installed. Pre-commit: IP checks + MD version discipline + RAG index. Pre-push: IP checks + test suite. Prepare-commit-msg: trade secret filter. Stop: git check. PostToolUse: MD version reminder."
