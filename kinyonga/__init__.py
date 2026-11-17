"""One generator for Quarto documents in one brand: a CV, a book, slides and a letter."""

from importlib.metadata import PackageNotFoundError, version

__all__ = ["__version__"]

try:
    __version__ = version("kinyonga")
except PackageNotFoundError:  # running from a source tree that is not installed
    __version__ = "0+unknown"
