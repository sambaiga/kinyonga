"""RGB to CMYK for the print files of a book or a cover, with black generation and a limit on the total ink.

A printer lays down four inks, and the total of the four, in percent, is limited by the paper: about 240 % on uncoated
stock and 300 % on coated. A dark navy built by the plain conversion, which gives each of cyan, magenta and yellow the
complement of red, green and blue, needs about 280 % of ink and no black at all. That dries slowly, sets off onto the
next sheet and prints muddy.

This module converts colours the way a print workflow does. *Black generation* moves the grey that cyan, magenta and
yellow have in common onto the black plate, and grows smoothly with the darkness of the colour, so that light blues keep
almost no black. Neutral greys go to the black plate alone. Then the total ink is capped by scaling down the three
coloured inks and keeping the black. No profile of the press is used, so this fixes the amount of ink and gets the
colour close; a printer's ICC profile and a proof still decide the colour.

:func:`convert` rewrites the colour operators of an uncompressed PDF in place, at the length of the text they replace,
so that the offsets of the file stay valid and no PDF library is needed. The module needs only the standard library.
"""

import re

#: The total of the four inks, as a fraction: 240 %, the limit of uncoated stock and so of every stock.
INK_LIMIT = 2.4

_NUMBER = r"-?(?:\d+\.?\d*|\.\d+)"
_RGB = re.compile(rf"(?<![\w.])({_NUMBER})(\s+)({_NUMBER})(\s+)({_NUMBER})(\s+)(rg|RG)(?![\w])")


def _smoothstep(x: float, low: float, high: float) -> float:
    """Return zero below ``low``, one above ``high`` and a smooth rise between.

    Args:
        x: The value.
        low: Where the rise starts.
        high: Where the rise ends.

    Returns:
        A number from 0 to 1.
    """
    t = min(max((x - low) / (high - low), 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


def to_cmyk(
    rgb: tuple[float, float, float], *, limit: float = INK_LIMIT, start: float = 0.0, full: float = 1.0
) -> tuple[float, float, float, float]:
    """Convert RGB to CMYK with black generation and a limit on the total ink.

    Args:
        rgb: Red, green and blue, each from 0 to 1.
        limit: The largest total of the four inks, as a fraction (2.4 is 240 %).
        start: The darkness, as the smallest of cyan, magenta and yellow, from which black generation begins.
        full: The darkness from which all of the grey they have in common is moved to black.

    Returns:
        Cyan, magenta, yellow and black, each from 0 to 1.

    Examples:
        >>> [round(v, 3) for v in to_cmyk((11 / 255, 18 / 255, 32 / 255))]
        [0.736, 0.568, 0.232, 0.837]
        >>> to_cmyk((1.0, 1.0, 1.0))
        (0.0, 0.0, 0.0, 0.0)
        >>> to_cmyk((0.5, 0.5, 0.5))
        (0.0, 0.0, 0.0, 0.5)
    """
    cmy = [1.0 - min(max(v, 0.0), 1.0) for v in rgb]
    grey = min(cmy)
    neutral = max(cmy) - grey < 1e-3
    black = grey if neutral else grey * _smoothstep(grey, start, full)
    room = 1.0 - black if black < 1.0 else 1.0
    ink = [min(max((v - black) / room, 0.0), 1.0) for v in cmy]
    coloured = sum(ink)
    scale = max(limit - black, 0.0) / max(coloured, 1e-12) if coloured + black > limit else 1.0
    return (ink[0] * scale, ink[1] * scale, ink[2] * scale, black)


def _fit(values: list[float], room: int, operator: str) -> str | None:
    """Write a CMYK operator with as many decimals as fit in a number of characters.

    Args:
        values: The ink amounts.
        room: The characters available.
        operator: The operator, for example ``k``.

    Returns:
        The text with the most decimals (at least two) that fits, or ``None`` when none does.
    """
    for decimals in (4, 3, 2):
        text = " ".join(f"{v:.{decimals}f}".rstrip("0").rstrip(".") or "0" for v in values) + f" {operator}"
        if len(text) <= room:
            return text
    return None


def _replace(match: re.Match[str]) -> str:
    """Return one colour operator in CMYK, or in grey for a neutral, padded to the length it replaces.

    Args:
        match: A match of an RGB fill or stroke operator.

    Returns:
        The replacement text, as long as the match.

    Raises:
        ValueError: If the colour is written too briefly to be replaced in place.
    """
    r, g, b = (float(match.group(i)) for i in (1, 3, 5))
    stroke = match.group(7) == "RG"
    cyan, magenta, yellow, black = to_cmyk((r, g, b))
    if max(cyan, magenta, yellow) == 0.0:
        text = _fit([1.0 - black], len(match.group(0)), "G" if stroke else "g")
    else:
        text = _fit([cyan, magenta, yellow, black], len(match.group(0)), "K" if stroke else "k")
    if text is None:
        msg = f"the colour {match.group(0)!r} is too short to be written in CMYK in place"
        raise ValueError(msg)
    return text.ljust(len(match.group(0)))


def convert(pdf: bytes) -> bytes:
    r"""Rewrite the ``rg`` and ``RG`` operators of an uncompressed PDF as CMYK, at the same length.

    Args:
        pdf: A PDF whose content streams are not compressed.

    Returns:
        The PDF with every RGB fill and stroke colour set in CMYK; its length and offsets are unchanged.

    Raises:
        ValueError: If a colour is written too briefly to be replaced in place.

    Examples:
        >>> convert(b"0.0431372549 0.0705882353 0.1254901961 rg\n")
        b'0.7359 0.5679 0.2318 0.8367 k            \n'
    """
    converted = _RGB.sub(_replace, pdf.decode("latin-1")).encode("latin-1")
    if len(converted) != len(pdf):
        msg = "the conversion changed the length of the file"
        raise ValueError(msg)
    return converted
