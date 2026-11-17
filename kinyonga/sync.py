"""Keep every extension's brand, tokens and fonts equal to the project's brand file, and check that they are.

A Quarto extension is installed alone (``quarto add``), so each one carries its own copy of ``brand.yml``, the
generated tokens and the fonts it names. ``sync_project`` writes those copies; ``check_project`` fails when one
differs, a font is missing, or a contrast pair is below its minimum. The module needs only the standard library and
PyYAML, so a generated project vendors it as ``tools/kn`` and needs no dependency on this package.
"""

import argparse
from collections.abc import Sequence
from pathlib import Path
import re
import shutil
import sys

import yaml

from .brand import Brand, BrandError, load_brand, load_settings, missing_fonts
from .contrast import check_contrast
from .cvdata import check_cv
from .tokens import check_tokens, write_tokens

ICONS = "icons"


def recolour(svg: str, colour: str) -> str:
    """Give a single-colour icon the brand colour.

    Bootstrap Icons draw with ``currentColor``, which Typst renders black; the extension ships copies with the colour
    written in, so the brand colour is still defined only in ``brand.yml``.

    Args:
        svg: The icon source.
        colour: ``#RRGGBB``.

    Returns:
        The icon with ``fill="currentColor"`` replaced by the colour.
    """
    return svg.replace('fill="currentColor"', f'fill="{colour}"')


def _icon_names(extension: Path) -> list[str]:
    """List the icon files an extension lists under ``format-resources``.

    Args:
        extension: The extension folder.

    Returns:
        The file names (``envelope.svg``) of the entries under ``icons/``, sorted.
    """
    return sorted(Path(item).name for item in _listed_resources(extension) if item.startswith(f"{ICONS}/"))


SHARED = "shared"


def _shared_files(root: Path, extension: Path) -> list[str]:
    """List the shared files an extension takes, as named in ``kinyonga.yml`` under ``shared``.

    Args:
        root: The project folder.
        extension: The extension folder.

    Returns:
        The file names, for example ``_components.scss``.
    """
    return list(load_settings(root / "kinyonga.yml").get("shared", {}).get(extension.name, []))


HEX_LITERAL = re.compile(r"#[0-9A-Fa-f]{6}\b")
LITERAL_SUFFIXES = {".scss", ".css", ".typ", ".tex", ".lua", ".qmd", ".html"}
# Folders and files that hold generated or third-party text and may carry any colour.
LITERAL_SKIP = {
    "tokens",
    "packages",
    "bootstrap-icons",
    "fonts",
    "assets",
    "icons",
    ".venv",
    ".quarto",
    "rendered_output",
    "_freeze",
}


def literal_problems(root: Path, brand: Brand) -> list[str]:
    """Find hand-written colours that are not in the brand palette.

    A colour is written once, in ``brand.yml``. A theme, template or deck that writes ``#RRGGBB`` itself must use a
    palette colour; one outside it is a copy that will drift. Generated and third-party folders are skipped.

    Args:
        root: The project folder.
        brand: The brand.

    Returns:
        One message for each file with a colour outside the palette; empty when every literal is a palette colour.
    """
    allowed = set(brand.palette.values())
    problems = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if not path.is_file() or path.suffix not in LITERAL_SUFFIXES or LITERAL_SKIP & set(relative.parts):
            continue
        found = {match.upper() for match in HEX_LITERAL.findall(path.read_text(encoding="utf-8", errors="ignore"))}
        outside = sorted(found - allowed)
        if outside:
            problems.append(f"{relative} writes colours outside the brand palette: {', '.join(outside)}")
    return problems


def extension_dirs(root: Path) -> list[Path]:
    """List the extensions of a project.

    Args:
        root: The project folder.

    Returns:
        The folders under ``_extensions`` that hold an ``_extension.yml``, sorted.
    """
    return sorted(path.parent for path in (root / "_extensions").glob("*/_extension.yml"))


def _font_files(brand: Brand, source: Path) -> list[Path]:
    """Return the font files and licence texts to ship with an extension.

    Args:
        brand: The brand.
        source: The folder the brand's font paths are relative to.

    Returns:
        The declared font files and any ``OFL-*.txt`` next to them, without duplicates.
    """
    files = {source / font.path for font in brand.fonts} | {source / logo for logo in brand.logos}
    for font in brand.fonts:
        files.update((source / font.path).parent.glob("OFL-*.txt"))
    return sorted(files)


def sync_project(root: Path) -> list[Path]:
    """Write the generated tokens and the brand copies into the project and its extensions.

    Args:
        root: The project folder, which holds ``brand.yml``.

    Returns:
        The folders that were updated: the project's ``tokens`` folder and each extension.
    """
    brand = load_brand(root / "brand.yml")
    updated = [root / "tokens"]
    write_tokens(brand, root / "tokens")
    for extension in extension_dirs(root):
        shutil.copyfile(root / "brand.yml", extension / "brand.yml")
        write_tokens(brand, extension / "tokens")
        for file in _font_files(brand, root):
            target = extension / file.relative_to(root)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(file, target)
        for name in _shared_files(root, extension):
            (extension / SHARED).mkdir(exist_ok=True)
            shutil.copyfile(root / SHARED / name, extension / SHARED / name)
        for name in _icon_names(extension):
            source = root / ICONS / name
            if source.is_file():
                (extension / ICONS).mkdir(exist_ok=True)
                text = recolour(source.read_text(encoding="utf-8"), brand.colour("primary"))
                (extension / ICONS / name).write_text(text, encoding="utf-8")
        updated.append(extension)
    return updated


def _listed_resources(extension: Path) -> set[str]:
    """Return every ``format-resources`` entry of an extension.

    Args:
        extension: The extension folder.

    Returns:
        The listed paths across all its formats.
    """
    data = yaml.safe_load((extension / "_extension.yml").read_text(encoding="utf-8")) or {}
    listed: set[str] = set()
    for options in (data.get("contributes", {}).get("formats", {}) or {}).values():
        listed.update(str(item) for item in (options or {}).get("format-resources", []) or [])
    return listed


def _check_extension(root: Path, brand: Brand, extension: Path) -> list[str]:
    """Check one extension against the project's brand.

    Args:
        root: The project folder.
        brand: The brand.
        extension: The extension folder.

    Returns:
        The problems found; empty when the extension is current.
    """
    problems = []
    copy = extension / "brand.yml"
    if not copy.is_file() or copy.read_bytes() != (root / "brand.yml").read_bytes():
        problems.append(f"{copy} differs from brand.yml; run `make sync`")
    problems.extend(check_tokens(brand, extension / "tokens"))
    listed = _listed_resources(extension)
    for name in _shared_files(root, extension):
        source, shipped = root / SHARED / name, extension / SHARED / name
        if not source.is_file():
            problems.append(f"{source} is missing; kinyonga.yml lists it for {extension.name}")
        elif not shipped.is_file() or shipped.read_bytes() != source.read_bytes():
            problems.append(f"{shipped} differs from {source}; run `make sync`")
    for name in _icon_names(extension):
        source = root / ICONS / name
        shipped = extension / ICONS / name
        if not source.is_file():
            problems.append(f"{source} is missing; the extension lists icons/{name}")
        elif not shipped.is_file() or shipped.read_text(encoding="utf-8") != recolour(
            source.read_text(encoding="utf-8"), brand.colour("primary")
        ):
            problems.append(f"{shipped} differs from {source} in the brand colour; run `make sync`")
    for file in _font_files(brand, root):
        shipped = file.relative_to(root).as_posix()
        if not (extension / shipped).is_file():
            problems.append(f"{extension / shipped} is missing; run `make sync`")
        elif file.suffix in {".ttf", ".svg"} and shipped not in listed:
            problems.append(f"{extension / '_extension.yml'} does not list {shipped} under format-resources")
    return problems


def check_project(root: Path) -> list[str]:
    """Check that a project's brand, tokens, extensions, fonts and contrast are consistent.

    Args:
        root: The project folder.

    Returns:
        One message for each problem; empty when everything is consistent.
    """
    try:
        brand = load_brand(root / "brand.yml")
    except BrandError as error:
        return [str(error)]
    problems = [f"font file {path} is missing" for path in missing_fonts(brand, root)]
    problems.extend(check_tokens(brand, root / "tokens"))
    for extension in extension_dirs(root):
        problems.extend(_check_extension(root, brand, extension))
    problems.extend(literal_problems(root, brand))
    if (root / "cv.yml").is_file():
        problems.extend(f"cv.yml: {problem}" for problem in check_cv(root / "cv.yml"))
    settings = load_settings(root / "kinyonga.yml")
    problems.extend(check_contrast(brand, settings.get("contrast", [])))
    return problems


def main(argv: Sequence[str] | None = None) -> int:
    """Run ``sync`` or ``check`` on a project; the entry point of the vendored ``tools/kn``.

    Args:
        argv: The arguments; ``sys.argv`` is used when omitted.

    Returns:
        The exit status: 0 on success, 1 when ``check`` finds problems.
    """
    parser = argparse.ArgumentParser(prog="kn", description="Sync and check the brand of a document project.")
    parser.add_argument("command", choices=("sync", "check", "timing"))
    parser.add_argument("deck", nargs="?", type=Path, help="the deck, for timing")
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="the project folder")
    args = parser.parse_args(argv)
    if args.command == "timing":
        from .notes import format_clock, load_deck, timing_table, total_seconds

        slides = load_deck(args.deck)
        sys.stdout.write(f"{timing_table(slides)}\n\nPlanned total {format_clock(total_seconds(slides))}\n")
        return 0
    if args.command == "sync":
        for path in sync_project(args.project):
            sys.stdout.write(f"synced {path}\n")
        return 0
    problems = check_project(args.project)
    for problem in problems:
        sys.stderr.write(f"{problem}\n")
    sys.stdout.write("brand check passed\n" if not problems else f"{len(problems)} problem(s)\n")
    return 1 if problems else 0
