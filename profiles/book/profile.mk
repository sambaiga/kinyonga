# Extra targets of the book profile, included by the Makefile.

book:  ## Render the web edition (HTML) and the print edition (LaTeX: needs TinyTeX and rsvg-convert)
	$(QUARTO) render

review:  ## Render the fast Typst edition into rendered_review
	$(QUARTO) render --profile review --to kinyonga-book-typst

press:  ## CMYK press PDF of the print edition (needs Ghostscript): rendered_output/press.pdf
	sh scripts/printpdf.sh rendered_output/Sample-Book.pdf rendered_output/press.pdf
