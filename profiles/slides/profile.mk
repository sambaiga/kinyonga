# Extra targets of the slides profile, included by the Makefile.

timing:  ## Planned time of each slide, from the [m:ss] marks in the speaker notes
	uv run python -m tools.kn timing deck.qmd
