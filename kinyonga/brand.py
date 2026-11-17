"""Read the brand file: the palette, the semantic roles and the fonts.

``brand.yml`` is the file Quarto reads natively (Quarto 1.6 and later). This module reads the same file so that the
kit can turn it into the token files that LaTeX, SCSS and CSS need, and check that the fonts it names exist.
"""

from dataclasses import dataclass
from pathlib import Path
import re

import yaml

HEX_COLOUR = re.compile(r"^#[0-9A-Fa-f]{6}$")


class BrandError(ValueError):
    """Raised when the brand file is missing, malformed or inconsistent."""


@dataclass(frozen=True)
class FontFile:
    """One font file of a family.

    Attributes:
        family: The family name, for example ``Jost``.
        path: The file, relative to the brand file.
        weight: The numeric weight, for example 600.
        style: ``normal`` or ``italic``.
    """

    family: str
    path: str
    weight: int
    style: str


@dataclass(frozen=True)
class Brand:
    """The brand: palette, roles and fonts.

    Attributes:
        palette: Colour name to upper-case ``#RRGGBB``.
        roles: Semantic role (``primary``, ``link``) to the palette name it uses.
        fonts: Every declared font file.
        base_family: The family of body text.
        heading_family: The family of headings.
    """

    palette: dict[str, str]
    roles: dict[str, str]
    fonts: tuple[FontFile, ...]
    base_family: str
    heading_family: str

    def colour(self, name: str) -> str:
        """Return the hex value of a palette colour or of a role.

        Args:
            name: A palette name (``blue``) or a role (``primary``).

        Returns:
            The colour as upper-case ``#RRGGBB``.

        Raises:
            BrandError: If the name is neither a palette colour nor a role.
        """
        if name in self.palette:
            return self.palette[name]
        if name in self.roles:
            return self.palette[self.roles[name]]
        msg = f"unknown colour or role {name!r}"
        raise BrandError(msg)


def _read_yaml(path: Path) -> dict:
    """Read a YAML file that must hold a mapping.

    Args:
        path: The file.

    Returns:
        The parsed mapping.

    Raises:
        BrandError: If the file is missing or does not hold a mapping.
    """
    if not path.is_file():
        msg = f"{path} was not found"
        raise BrandError(msg)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        msg = f"{path} must hold a mapping"
        raise BrandError(msg)
    return data


def _fonts(typography: dict) -> tuple[FontFile, ...]:
    """Collect the font files declared under ``typography.fonts``.

    Args:
        typography: The ``typography`` mapping of the brand file.

    Returns:
        The font files, in the order declared.
    """
    files = [
        FontFile(family["family"], entry["path"], int(entry.get("weight", 400)), entry.get("style", "normal"))
        for family in typography.get("fonts", [])
        for entry in family.get("files", [])
    ]
    return tuple(files)


def load_brand(path: Path) -> Brand:
    """Read and validate a brand file.

    Args:
        path: The ``brand.yml`` file.

    Returns:
        The brand.

    Raises:
        BrandError: If a colour is not ``#RRGGBB``, a role names an unknown colour, or the file is malformed.
    """
    data = _read_yaml(path)
    color = data.get("color", {})
    palette = {}
    for name, value in color.get("palette", {}).items():
        if not isinstance(value, str) or not HEX_COLOUR.match(value):
            msg = f"palette colour {name!r} must be #RRGGBB, not {value!r}"
            raise BrandError(msg)
        palette[name] = value.upper()
    roles = {role: name for role, name in color.items() if role != "palette"}
    unknown = sorted(name for name in roles.values() if name not in palette)
    if unknown:
        msg = f"roles name colours that are not in the palette: {unknown}"
        raise BrandError(msg)
    typography = data.get("typography", {})
    base = typography.get("base", {}).get("family")
    headings = typography.get("headings", {}).get("family")
    if not palette or base is None or headings is None:
        msg = "the brand file needs a palette and base and headings families"
        raise BrandError(msg)
    return Brand(palette, roles, _fonts(typography), base, headings)


def missing_fonts(brand: Brand, folder: Path) -> list[str]:
    """List the font files the brand declares that do not exist.

    Args:
        brand: The brand.
        folder: The folder the font paths are relative to (the folder of the brand file).

    Returns:
        The declared paths that are not files, sorted.
    """
    return sorted({font.path for font in brand.fonts if not (folder / font.path).is_file()})


def load_settings(path: Path) -> dict:
    """Read the kit's own settings file, ``kinyonga.yml``.

    Args:
        path: The settings file.

    Returns:
        The settings, an empty mapping when the file does not exist.
    """
    return _read_yaml(path) if path.is_file() else {}
