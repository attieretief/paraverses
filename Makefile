.PHONY: dev build

dev:
	@python3 -m venv .venv
	@.venv/bin/pip install -qr requirements-dev.txt
	@.venv/bin/python scripts/dev.py

build:
	@python3 -m venv .venv
	@.venv/bin/pip install -qr requirements.txt
	@.venv/bin/python scripts/build_site.py
