# Traps

What went wrong while building kinyonga, and what to do instead. Each entry names the symptom, the cause and the fix.

## Quarto

- **A custom format name is split at the last hyphen.** `kinyonga-cv-typst` means extension `kinyonga-cv`, format
  `typst`. One extension therefore gives one format per base format, so the letter and the CV (both Typst) are separate
  extensions. The book gives html, pdf and typst.
- **Reserved metadata keys.** `website`, `profile` and `github` mean something to Quarto. Contact details sit under
  `identity` in `profile.yml`.
- **A header without an identifier is dropped** by Quarto when a Lua filter builds the page. Always give ids.
- **A level-1 Pandoc header sectionizes the page.** Emit the name as a raw HTML block instead.
- **`format-resources` copies files flat** next to the document at render time (fonts, SVG, icons). The generated
  `.gitignore` ignores the copies, and `kinyonga check` requires every font and logo to be listed.
- **Both PDF editions of a book write the same file name.** A comma is not accepted in `--to`. `make book` renders HTML
  and LaTeX; `make review` renders Typst into `rendered_review` through the `review` profile.
- **A custom Typst format compiles chapters one by one** ("cannot reference heading without numbering") unless it has
  the structure of the bundled orange-book extension: the three partials and the `post-quarto` filter, with
  `quarto-required: ">=1.9.17"`.
- **The Sass warning "variable used before declaration"** appears for the token variables. The output is correct.

## Brand and fonts

- **LaTeX has no brand support.** Colours come from the generated `tokens/colors.tex`; never write a hex value in a
  `.tex`, `.typ`, `.scss` or `.lua` file (`kinyonga check` fails on it).
- **The brand logo is placed on every Typst page and every reveal slide.** Turn it off (`#set page(background: none)`,
  `logo: false`) where it does not belong.
- **`$brand.typography.*.family` already renders as `("Jost",)`.** Do not wrap it in another tuple.
- **After a font change, clear `.quarto/typst-font-cache`.**
- **Set the body font before the Typst book template.** Set after it, the cover, contents and page numbers keep the
  template serif.

## Typst

- An alpha gradient renders solid; a second `page(background:)` replaces the first; the back page belongs inside
  `#show: doc =>`; escape `@`; a heading rule targets level 1; `table.cell` forces alignment.
- **orange-book starts chapters on odd pages**, which leaves blank pages in a single-sided edition. The vendored copy
  is patched to use a plain page break (see THIRD_PARTY.md).

## CV and ATS

- Use plain hyphens; typographic dashes, soft hyphens and private-use characters are read as boxes. `cv.yml` is linted.
- Hyphenation and ligatures are off. Icons are SVG images marked `pdf.artifact`, never a font, so the PDF passes
  PDF/UA-1 (veraPDF).
- The single-column, linear reading order is part of the design; do not add columns.

## LaTeX print edition

- SVG figures need `rsvg-convert` (librsvg) on the path; CI installs it.
- `\maketitle` is neutralised so the cover can read the title; the cover sets `\booktitle` for the running head.
- Quarto's callouts are restyled through `\colorlet` at `\AtBeginDocument`; no custom environment is needed.
- hyperref's default link colour is red; the page style sets it to the brand blue.

## Reveal.js

- Quarto's footer script sets `display` inline, so only the hide rules need `!important`.
- `has-dark-background` needs hex background colours.
- Quarto adds its own title slide when `title` or `author` is in the front matter; leave both out.

## Workflow

- Squash-merge titles must be conventional commits; a rebase onto a squashed base needs `git rebase --onto`.
- Never commit an AI trailer; the `commit-msg` hook rejects it.
- Do not run a heavy job in parallel on an 8 GB laptop.
