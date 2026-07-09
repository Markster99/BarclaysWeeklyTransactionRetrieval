.PHONY: install test lint typecheck mock-run check-secrets sample

install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check src tests scripts

typecheck:
	mypy src

mock-run:
	barclays-weekly run --mock

sample:
	python scripts/generate_sample_output.py

check-secrets:
	python scripts/check_no_secrets.py
