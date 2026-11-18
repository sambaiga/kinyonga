# Extra targets of the book profile, included by the Makefile.

book:  ## Render the web edition (HTML) and the print edition (LaTeX, needs lualatex)
	$(QUARTO) render

review:  ## Render the fast Typst edition into rendered_review
	$(QUARTO) render --profile review --to kinyonga-book-typst
