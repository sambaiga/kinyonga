<p align="center"><em>kinyonga</em>: a chameleon in four colours, one for each kind of document.</p>

*Kinyonga* is Swahili for chameleon, the animal that changes its colour to fit every surrounding and stays the same animal. This repository is where a new document project starts: a generator, one brand, and a ready Quarto project for each kind of document. It follows [kobe](https://github.com/sambaiga/kobe), which does the same for Python projects.

```bash
uv run python new.py my-letter --profile letter          # from a clone, exactly as in kobe
uvx --from git+https://github.com/sambaiga/kinyonga kinyonga new my-letter --profile letter
cd my-letter && uv sync && make check && make all
```

`uv sync` installs the pinned Quarto too, so a project renders the same on a machine that never had Quarto.

## Profiles

| Profile | Gives you | Status |
|---|---|---|
| `letter` | A letterhead letter in Typst; sender and contact line from `profile.yml` | ready |
| `cv` | An ATS-friendly CV from `cv.yml`: a tagged PDF that validates as PDF/UA (Typst) and an HTML page; `make ats` for an edition with spelled-out labels and no icons | ready |
| `slides` | A reveal.js deck with the shared components, click PDF and phone remote | planned |
| `book` | A book in HTML and PDF (LaTeX for print, Typst for review) | planned |

## What every project gets

- **One brand.** `brand.yml` is the only place a colour, font or logo is written. Quarto 1.6+ reads it natively for Typst, HTML and reveal.js; `make sync` generates the token files LaTeX, SCSS and CSS need and copies the brand, tokens and fonts into each extension, so an extension also works alone with `quarto add`.
- **One identity.** `profile.yml` holds your name, email and links; every document reads it (under `identity`, because `website` and `profile` mean something to Quarto).
- **A pinned toolchain.** `quarto-cli>=1.11,<1.12` in `pyproject.toml`, `uv.lock` committed, `make` targets discovered from the `.qmd` files.
- **Checks.** `make check`: brand copies equal `brand.yml`, tokens current, fonts present and listed in `format-resources`, WCAG AA contrast of the text and background pairs in `kinyonga.yml`, spelling. Hooks (prek), a commit-message rule that rejects AI trailers, and a CI workflow that renders every document.

## In this repository

```text
brand.yml  kinyonga.yml  fonts/     the one brand, the contrast pairs, the vendored OFL fonts (Jost, Libre Franklin)
tokens/                              generated from brand.yml: _tokens.scss, tokens.css, colors.typ, colors.tex
_extensions/kinyonga-letter, -cv/     one extension per document kind (Quarto allows one format per base format)
icons/                               Bootstrap Icons as SVG (MIT); sync ships brand-coloured copies with the CV extension
profiles/base, profiles/letter       real, runnable projects; the generator copies base, then the profile
kinyonga/                            the generator and the brand tools (sync, check, contrast), with tests
```

`make check` runs ruff, ty, deptry, the brand check and the fast tests; `make verify` generates each profile, renders it with the pinned Quarto and checks the PDF fonts and text.

## Release

```bash
uv run cz bump --changelog   # bumps the version, writes CHANGELOG.md, tags vX.Y.Z
git push --follow-tags       # the tag starts .github/workflows/publish_pypi.yaml
```
