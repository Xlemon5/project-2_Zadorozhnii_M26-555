.PHONY: install project database build publish package-install lint

install:
	uv sync

project:
	uv run project

database:
	uv run database

build:
	uv build

publish: build
	uv publish --dry-run --trusted-publishing never

package-install: build
	uv pip install --python .venv/bin/python dist/*.whl

lint:
	uv run ruff check .
