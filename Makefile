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
	chmod +x .githooks/stop-git-check.sh
	@echo "Git hooks installed. Pre-commit: RAG index. Pre-push: test suite. Stop: git check."
