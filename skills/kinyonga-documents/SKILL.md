---
name: kinyonga-documents
description: Create and maintain Quarto documents (CV, letter, slides, book) with kinyonga, the one-brand generator. Use when starting a document project, changing the brand, adding a CV entry, or when a kinyonga render, check or CI job fails.
---

# kinyonga documents

kinyonga is a generator like kobe: `uv run python new.py NAME --profile letter|cv|slides|book` (or `uvx --from
git+https://github.com/sambaiga/kinyonga kinyonga new NAME --profile cv`) writes a runnable Quarto project with the
pinned Quarto, the brand, the extension for the profile, hooks, a Makefile and CI.

## Rules

1. **One brand source.** Change colours, fonts and logos only in `brand.yml`, then `make sync`. Never edit `tokens/`,
   the copies inside `_extensions/`, or write a hex value in a theme file. `make check` fails on drift, on fonts or
   logos missing from `format-resources`, on contrast below WCAG AA for the pairs in `kinyonga.yml`, and on literals.
2. **CV data lives in `cv.yml`** under `cv:`; `make check` validates it and lints it for ATS. Plain hyphens only;
   `make ats` renders the spelled-out edition.
3. **Slides**: `[m:ss]` marks in speaker notes drive `make timing`; the phone remote and the click PDF come from
   `slides-template`.
4. **Book**: `make book` (HTML and LaTeX, needs TinyTeX and rsvg-convert) and `make review` (Typst). Static figures
   only in print; no `<iframe>`.
5. Run `uv run` for everything; `make check` before every commit, `make verify` renders every profile.
6. Read `docs/traps.md` before debugging a render: most failures are listed there.

## Release

The version of the package and of every extension must match (`make versions`). Tag `vX.Y.Z` on main; users can
`quarto add sambaiga/kinyonga@vX.Y.Z`.
