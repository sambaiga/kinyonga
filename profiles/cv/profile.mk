# Extra targets of the CV profile, included by the Makefile.

ats:  ## ATS edition of the PDF: spelled-out labels, no icons (cv-ats.pdf)
	$(QUARTO) render cv.qmd --to kinyonga-cv-typst -M ats:true -o cv-ats.pdf
