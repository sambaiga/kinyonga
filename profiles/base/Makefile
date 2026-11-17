# Document commands. Everything runs through `uv run`, so the pinned Quarto in pyproject.toml is the one used.
# Targets are discovered from the .qmd files present, so `make letter` works as soon as letter.qmd exists.

QUARTO := uv run quarto
DOCS := $(basename $(wildcard *.qmd))

.DEFAULT_GOAL := help
.PHONY: help sync check hooks all preview clean

help:  ## Show the targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/'
	@echo ""
	@echo "  Documents here:  $(DOCS)"
	@echo "  Render one:      make $(firstword $(DOCS))"

sync:  ## Write the tokens and brand copies from brand.yml
	uv run python -m tools.kn sync

check:  ## Brand, tokens, fonts, contrast and spelling
	uv run python -m tools.kn check
	uv run codespell

hooks:  ## Install the git hooks with prek
	uv run prek install --install-hooks --hook-type pre-commit --hook-type commit-msg

# A profile can add targets in profile.mk (the CV adds `make ats`).
-include profile.mk

%: %.qmd
	$(QUARTO) render $<

all: $(DOCS)  ## Render every document

DOC ?= $(firstword $(DOCS))
preview:  ## Live preview: make preview DOC=letter
	$(QUARTO) preview $(DOC).qmd

clean:  ## Remove rendered output and caches
	rm -rf rendered_output .quarto _freeze
