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
	chmod +x .githooks/pre-release
	@echo "Git hooks installed. Pre-commit: staging hygiene + IP checks + MD version discipline + RAG index. Pre-push: IP checks + test suite. Pre-release: version sync validation."

release:
	@if [ -z "$(VERSION)" ]; then echo "Usage: make release VERSION=X.Y.Z"; exit 1; fi
	bash .githooks/pre-release $(VERSION)
	git tag -a v$(VERSION) -m "Release v$(VERSION)"
	@echo "Tag v$(VERSION) created. Push with: git push origin main && git push origin v$(VERSION)"
