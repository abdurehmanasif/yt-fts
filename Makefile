.PHONY: build install clean test dev-setup uv-sync uv-install uv-test

# Traditional pip targets (maintained for backward compatibility)
build:
	python -m build

install:
	pip install -e .

clean:
	rm -rf build dist *.egg-info .venv
	-pip uninstall -y yt-fts

test:
	pytest tests/

# uv targets
uv-sync:
	uv sync

uv-install:
	uv pip install -e .

uv-test:
	uv run pytest tests/

uv-lock:
	uv lock

# Development setup (prefers uv if available)
dev-setup:
	@if command -v uv > /dev/null 2>&1; then \
		echo "Setting up with uv..."; \
		uv venv; \
		uv sync; \
	else \
		echo "uv not found, using pip..."; \
		python -m venv .venv; \
		. .venv/bin/activate && pip install -e .; \
	fi
