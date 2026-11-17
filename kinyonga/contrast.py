"""WCAG contrast of the brand's text and background pairs."""

from .brand import Brand, BrandError


def _channel(value: int) -> float:
    """Return one sRGB channel as linear light.

    Args:
        value: The channel, 0 to 255.

    Returns:
        The linear value, 0 to 1.
    """
    scaled = value / 255
    return scaled / 12.92 if scaled <= 0.03928 else ((scaled + 0.055) / 1.055) ** 2.4


def relative_luminance(colour: str) -> float:
    """Return the WCAG relative luminance of a colour.

    Args:
        colour: ``#RRGGBB``.

    Returns:
        The luminance, 0 for black and 1 for white.
    """
    red, green, blue = (int(colour[index : index + 2], 16) for index in (1, 3, 5))
    return 0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)


def contrast_ratio(first: str, second: str) -> float:
    """Return the WCAG contrast ratio of two colours.

    Args:
        first: ``#RRGGBB``.
        second: ``#RRGGBB``.

    Returns:
        The ratio, from 1 (identical) to 21 (black on white).
    """
    light, dark = sorted((relative_luminance(first), relative_luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def check_contrast(brand: Brand, pairs: list[dict]) -> list[str]:
    """Check the declared text and background pairs against their minimum ratio.

    Args:
        brand: The brand.
        pairs: Mappings with ``text``, ``background`` and ``minimum``.

    Returns:
        One message for each pair below its minimum or naming an unknown colour; empty when all pass.
    """
    problems = []
    for pair in pairs:
        try:
            ratio = contrast_ratio(brand.colour(pair["text"]), brand.colour(pair["background"]))
        except BrandError as error:
            problems.append(f"contrast pair {pair['text']} on {pair['background']}: {error}")
            continue
        if ratio < float(pair["minimum"]):
            problems.append(
                f"{pair['text']} on {pair['background']} has contrast {ratio:.2f}, below {float(pair['minimum']):.1f}"
            )
    return problems
