.PHONY: help sync hooks lint fmt typecheck test deps check verify brand

help:  ## Show the targets
	@grep -E '^[a-z]+:.*##' Makefile | sed 's/:.*##/\t/'

sync:  ## Install the locked environment (run `uv sync` once to create uv.lock)
	uv sync --locked

hooks:  ## Install the git hooks with prek
	uv run prek install --install-hooks --hook-type pre-commit --hook-type commit-msg --hook-type pre-push

lint:  ## Ruff check and format check
	uv run ruff check . --no-fix
	uv run ruff format --check .

fmt:  ## Fix what ruff can fix
	uv run ruff check . --fix
	uv run ruff format .

typecheck:  ## Type check with ty
	uv run ty check

test:  ## Run the tests with coverage
	uv run pytest

deps:  ## Unused and missing dependencies
	uv run deptry .

brand:  ## Write the tokens and brand copies from brand.yml, then check them
	uv run python -m kinyonga sync
	uv run python -m kinyonga check

check: lint typecheck deps brand test  ## Everything CI runs

verify:  ## Generate every profile, render it with the pinned Quarto and check the output
	uv run pytest -m render --no-cov -p no:cacheprovider
