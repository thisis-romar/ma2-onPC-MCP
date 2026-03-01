server:
	./connect.sh

log:
	@echo "Usage: make log GMA_HOST=<ip>"
	telnet $(GMA_HOST) 30001

test:
	uv run pytest -v
