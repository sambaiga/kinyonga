# sample-project

A document project in the kinyonga brand. Read this first.

## Commands

| Task | Command |
|---|---|
| Install (pins Quarto too) | `uv sync` |
| Brand, tokens, fonts, spelling | `make check` |
| Render one document | `make letter` (the name of the `.qmd`) |
| Render all / live preview | `make all` / `make preview DOC=letter` |
| Rewrite tokens after editing `brand.yml` | `make sync` |

## Rules

1. `brand.yml` is the only place a colour, font or logo is written. After editing it run `make sync`; never edit
   `tokens/` or an extension's `brand.yml`, `tokens/` or `fonts/` by hand.
2. `profile.yml` holds who you are (name, email, links); documents read it, so write a fact once.
3. Render through `uv run quarto` (the Makefile does), never a system Quarto: the pinned one defines the output.
4. Git: feature branch, conventional commit titles, stage explicit paths (never `git add -A`), no AI co-author
   trailer, open a pull request and wait to be told to merge.
