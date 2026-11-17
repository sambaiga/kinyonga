# Extra targets of the book profile, included by the Makefile.

book:  ## Render the web edition and the print edition
	$(QUARTO) render
