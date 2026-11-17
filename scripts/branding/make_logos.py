"""Draw the kinyonga logo set: a chameleon whose body is four patches of the brand, one for each kind of document.

The body is clipped from one silhouette and split into slate (the letter), deep blue (the book), blue (the slides)
and orange (the CV, with the eye), so the four patches stay apart in greyscale and for colour-blind readers. The
curled tail is a spiral and the branch gives the animal something to hold. Colours come from ``brand.yml``; the
wordmark is Jost SemiBold and the tagline Libre Franklin, both converted to outlines with fontTools, so every SVG is
self-contained. The fonts are the ones in ``fonts/``: no argument is needed.

Usage:
    uv run python scripts/branding/make_logos.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from kinyonga.brand import load_brand

ROOT = Path(__file__).resolve().parents[2]
TAGLINE = "one brand, every document"

# Shapes on a 120 x 100 canvas.
BODY = (
    "M 24 55 C 25 39 42 29 61 30 C 73 31 83 34 89 27 C 93 22 99 22 102 27 "
    "C 105 33 114 39 113 46 C 112 52 101 55 93 54 C 86 54 82 61 74 65 C 62 72 37 73 26 63 Z"
)
TAIL = "M 27 58 C 12 63 5 52 14 45 C 21 40 31 45 27 52 C 25 55 20 53 21 50"
FRONT_LEG = "M 76 64 L 79 78 C 79 82 85 82 85 78"
HIND_LEG = "M 46 69 L 43 80 C 42 84 36 83 37 79"
BRANCH = "M 4 84 C 40 80 80 83 116 79"
CASQUE = "M 93 27 C 95 18 103 17 105 24"


def mark_group(brand, *, mono: str | None = None, ground: str | None = None, dark: bool = False) -> str:
    """Return the chameleon as SVG elements on a 120 x 100 canvas.

    Args:
        brand: The brand.
        mono: A single colour for a one-colour mark; ``None`` for the four patches.
        ground: The colour of the tile behind the mark, or ``None`` for a transparent ground.
        dark: Whether the mark sits on a dark ground: the branch, legs and tail turn light so they stay visible.

    Returns:
        The SVG markup, to be placed inside an ``svg`` element.
    """
    slate, deep, blue, orange = (brand.colour(name) for name in ("slate", "blue-deep", "blue", "orange"))
    ink, white = brand.colour("ink"), brand.colour("white")
    stroke = mono or (brand.colour("slate-light") if dark else slate)
    branch = mono or (brand.colour("slate") if dark else ink)
    legs = mono or (brand.colour("slate-light") if dark else deep)
    parts = []
    if ground:
        parts.append(f'<rect x="0" y="0" width="120" height="100" rx="18" fill="{ground}"/>')
    parts.append(f'<path d="{BRANCH}" fill="none" stroke="{branch}" stroke-width="3.2" stroke-linecap="round"/>')
    parts.append(f'<path d="{TAIL}" fill="none" stroke="{stroke}" stroke-width="6.5" stroke-linecap="round"/>')
    leg_style = f'fill="none" stroke="{legs}" stroke-width="5.5" stroke-linecap="round" stroke-linejoin="round"'
    parts.extend(f'<path d="{leg}" {leg_style}/>' for leg in (HIND_LEG, FRONT_LEG))
    if mono:
        parts.append(f'<path d="{BODY}" fill="{mono}"/>')
        parts.append(f'<circle cx="98" cy="33" r="4.2" fill="{ground or white}"/>')
        return "\n".join(parts)
    parts.append(f'<clipPath id="body"><path d="{BODY}"/></clipPath>')
    patches = ((slate, 20, 46), (deep, 46, 66), (blue, 66, 88), (orange, 88, 118))
    parts.append('<g clip-path="url(#body)">')
    parts.extend(
        f'<rect x="{left}" y="10" width="{right - left}" height="70" fill="{colour}"/>'
        for colour, left, right in patches
    )
    seam = ground or (brand.colour("ink") if dark else white)
    parts.extend(f'<rect x="{left - 0.9}" y="10" width="1.8" height="70" fill="{seam}"/>' for _, left, _ in patches[1:])
    parts.append("</g>")
    parts.append(f'<path d="{CASQUE}" fill="none" stroke="{orange}" stroke-width="4" stroke-linecap="round"/>')
    parts.append(f'<circle cx="98" cy="33" r="4.6" fill="{white}"/><circle cx="98.6" cy="33" r="2.3" fill="{ink}"/>')
    return "\n".join(parts)


def outline(
    font_path: Path, text: str, size: float, x: float, baseline: float, tracking: float = 0.0
) -> tuple[str, float]:
    """Convert a line of text to SVG path data.

    Args:
        font_path: The TrueType file.
        text: The text.
        size: The font size in canvas units.
        x: The left edge.
        baseline: The baseline.
        tracking: Extra space after each glyph, in em.

    Returns:
        The path data and the width of the line.
    """
    font = TTFont(font_path)
    glyphs, metrics = font.getGlyphSet(), font["hmtx"]
    cmap = font.getBestCmap() or {}
    scale = size / float(getattr(font["head"], "unitsPerEm", 1000))
    pen = SVGPathPen(glyphs)
    cursor = x
    for char in text:
        name = cmap[ord(char)]
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, cursor, baseline)))
        cursor += metrics[name][0] * scale + tracking * size
    return pen.getCommands(), cursor - x


def svg(width: float, height: float, body: str, background: str | None = None) -> str:
    """Wrap SVG elements in a document.

    Args:
        width: The viewBox width.
        height: The viewBox height.
        body: The elements.
        background: An optional ground colour.

    Returns:
        The SVG text.
    """
    ground = f'<rect width="{width}" height="{height}" fill="{background}"/>' if background else ""
    header = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:g} {height:g}" fill="none">'
    return f"{header}\n{ground}\n{body}\n</svg>\n"


def lockup(brand, fonts: Path, *, dark: bool) -> str:
    """Build the horizontal logo: the mark, the wordmark and the tagline.

    Args:
        brand: The brand.
        fonts: The folder with the fonts.
        dark: Whether the lockup sits on a dark ground.

    Returns:
        The SVG text.
    """
    ink = brand.colour("white") if dark else brand.colour("ink")
    muted = brand.colour("slate-light") if dark else brand.colour("slate")
    word, _ = outline(fonts / "Jost-SemiBold.ttf", "kinyonga", 46, 132, 62, tracking=0.01)
    line, _ = outline(fonts / "LibreFranklin-Regular.ttf", TAGLINE, 13.5, 134, 84, tracking=0.04)
    body = (
        f'<g transform="translate(0 6)">{mark_group(brand, dark=dark)}</g>\n'
        f'<path d="{word}" fill="{ink}"/>\n<path d="{line}" fill="{muted}"/>'
    )
    return svg(470, 112, body, background=brand.colour("ink") if dark else None)


def write_all(out: Path) -> list[Path]:
    """Write the logo set.

    Args:
        out: The folder to write into.

    Returns:
        The files written.
    """
    brand = load_brand(ROOT / "brand.yml")
    fonts = ROOT / "fonts"
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "mark.svg": svg(120, 100, mark_group(brand)),
        "mark-mono.svg": svg(120, 100, mark_group(brand, mono=brand.colour("ink"))),
        "logo.svg": lockup(brand, fonts, dark=False),
        "logo-dark.svg": lockup(brand, fonts, dark=True),
        "avatar.svg": svg(
            120, 120, f'<g transform="translate(0 10)">{mark_group(brand, ground=brand.colour("ink"), dark=True)}</g>'
        ),
        "favicon.svg": svg(120, 100, mark_group(brand, ground=brand.colour("ink"), dark=True)),
    }
    written = []
    for name, text in files.items():
        path = out / name
        path.write_text(text, encoding="utf-8")
        written.append(path)
    return written


def main() -> None:
    """Parse the arguments and write the logo set."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, default=ROOT / "assets")
    for path in write_all(parser.parse_args().out):
        print(path)


if __name__ == "__main__":
    main()
