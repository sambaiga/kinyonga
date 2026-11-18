"""The ``kinyonga`` command: new, sync, check, timing and cmyk."""

import argparse
from collections.abc import Sequence
from pathlib import Path
import sys

from .cmyk import convert as to_cmyk_pdf
from .generate import PROFILES, Project, new_project
from .notes import format_clock, load_deck, timing_table, total_seconds
from .sync import main as sync_main


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser.

    Returns:
        The parser with the ``new``, ``sync`` and ``check`` commands.
    """
    parser = argparse.ArgumentParser(prog="kinyonga", description="Create and check Quarto document projects.")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("new", help="create a project from a profile")
    create.add_argument("name", help="lower-case words joined by hyphens, for example my-cv")
    create.add_argument("--profile", required=True, choices=PROFILES)
    create.add_argument("--dest", type=Path, default=Path.cwd(), help="folder to create the project in")
    create.add_argument("--description", default=Project.description)
    create.add_argument("--author", default=Project.author)
    create.add_argument("--email", default=Project.email)
    create.add_argument("--owner", default=Project.owner)
    create.add_argument("--no-git", action="store_true")
    timing = commands.add_parser("timing", help="print the planned time of each slide of a deck")
    timing.add_argument("deck", type=Path)
    timing.add_argument("--unnumbered", type=int, default=1, help="slides at the start without a number")
    press = commands.add_parser(
        "cmyk", help="rewrite the RGB colours of an uncompressed PDF as CMYK, in place of length"
    )
    press.add_argument("source", type=Path)
    press.add_argument("output", type=Path)
    for name, text in (
        ("sync", "write the tokens and brand copies"),
        ("check", "check brand, tokens, fonts, contrast"),
    ):
        sub = commands.add_parser(name, help=text)
        sub.add_argument("--project", type=Path, default=Path.cwd())
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command.

    Args:
        argv: The arguments after the command name; ``sys.argv`` is used when omitted.

    Returns:
        The exit status.
    """
    args = build_parser().parse_args(argv)
    if args.command == "new":
        project = Project(args.name, args.profile, args.owner, args.description, args.author, args.email)
        created = new_project(project, args.dest / args.name, git=not args.no_git)
        sys.stdout.write(f"Created {created}\n\nNext:\n  cd {created}\n  uv sync\n  make check\n  make all\n")
        return 0
    if args.command == "timing":
        slides = load_deck(args.deck)
        sys.stdout.write(
            f"{timing_table(slides, args.unnumbered)}\n\nPlanned total {format_clock(total_seconds(slides))}\n"
        )
        return 0
    if args.command == "cmyk":
        args.output.write_bytes(to_cmyk_pdf(args.source.read_bytes()))
        sys.stdout.write(f"Wrote {args.output}\n")
        return 0
    return sync_main([args.command, "--project", str(args.project)])
