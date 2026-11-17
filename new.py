"""Create a new document project from a profile, as kobe creates a Python project.

Example:
    ::

        uv run python new.py my-letter --profile letter
"""

import sys

from kinyonga.cli import main

if __name__ == "__main__":
    sys.exit(main(["new", *sys.argv[1:]]))
