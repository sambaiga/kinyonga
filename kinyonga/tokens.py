"""Turn the brand into the token files that SCSS, CSS, Typst and LaTeX import.

Quarto reads ``brand.yml`` itself for Typst, HTML and reveal.js, but the hand-written theme files, the LaTeX
preamble and the shared components need the same colours by name. They are generated here, never written twice,
so a colour cannot drift: ``check_tokens`` regenerates and compares.
"""

from pathlib import Path

from .brand import Brand

HEADER = "GENERATED from brand.yml by `kinyonga sync`. Do not edit: change brand.yml and run `make sync`."
PREFIX = "kn"
FILES = ("_tokens.scss", "tokens.css", "colors.typ", "colors.tex")


def _names(brand: Brand) -> dict[str, str]:
    """Return every colour the files define: the palette first, then the roles.

    Args:
        brand: The brand.

    Returns:
        Name to ``#RRGGBB``; a role is listed under its own name, for example ``primary``.
    """
    names = dict(brand.palette)
    names.update({role: brand.palette[target] for role, target in brand.roles.items() if role not in names})
    return names


def _camel(name: str) -> str:
    """Return a name as a LaTeX-safe identifier.

    Args:
        name: A hyphenated name such as ``blue-deep``.

    Returns:
        The name with the prefix and no hyphen, for example ``knBlueDeep``.
    """
    return PREFIX + "".join(part.capitalize() for part in name.split("-"))


def render_tokens(brand: Brand) -> dict[str, str]:
    """Build the contents of every token file.

    Args:
        brand: The brand.

    Returns:
        File name to its text, for the names in ``FILES``.
    """
    colours = _names(brand)
    scss = [f"// {HEADER}"]
    css = [f"/* {HEADER} */", ":root {"]
    typst = [f"// {HEADER}"]
    tex = [f"% {HEADER}"]
    for name, value in colours.items():
        scss.append(f"${PREFIX}-{name}: {value};")
        css.append(f"  --{PREFIX}-{name}: {value};")
        typst.append(f'#let {PREFIX}-{name} = rgb("{value}")')
        tex.append(f"\\definecolor{{{_camel(name)}}}{{HTML}}{{{value[1:]}}}")
    scss.append(f'$kn-font-body: "{brand.base_family}";')
    scss.append(f'$kn-font-heading: "{brand.heading_family}";')
    css.append(f'  --{PREFIX}-font-body: "{brand.base_family}";')
    css.append(f'  --{PREFIX}-font-heading: "{brand.heading_family}";')
    css.append("}")
    typst.append(f'#let {PREFIX}-font-body = "{brand.base_family}"')
    typst.append(f'#let {PREFIX}-font-heading = "{brand.heading_family}"')
    tex.append(f"\\newcommand{{\\knFontBody}}{{{brand.base_family}}}")
    tex.append(f"\\newcommand{{\\knFontHeading}}{{{brand.heading_family}}}")
    return {
        "_tokens.scss": "\n".join(scss) + "\n",
        "tokens.css": "\n".join(css) + "\n",
        "colors.typ": "\n".join(typst) + "\n",
        "colors.tex": "\n".join(tex) + "\n",
    }


def write_tokens(brand: Brand, folder: Path) -> list[Path]:
    """Write the token files into a folder, creating it.

    Args:
        brand: The brand.
        folder: Where to write.

    Returns:
        The files written.
    """
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    for name, text in render_tokens(brand).items():
        path = folder / name
        path.write_text(text, encoding="utf-8")
        written.append(path)
    return written


def check_tokens(brand: Brand, folder: Path) -> list[str]:
    """Compare the token files in a folder with what the brand generates.

    Args:
        brand: The brand.
        folder: The folder that should hold the token files.

    Returns:
        One message for each file that is missing or differs; empty when all are current.
    """
    problems = []
    for name, expected in render_tokens(brand).items():
        path = folder / name
        if not path.is_file():
            problems.append(f"{path} is missing")
        elif path.read_text(encoding="utf-8") != expected:
            problems.append(f"{path} differs from brand.yml; run `make sync`")
    return problems
