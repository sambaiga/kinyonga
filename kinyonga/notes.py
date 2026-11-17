"""Slides, speaker notes and planned times of a Quarto reveal.js deck, from the ``.qmd`` source.

A deck is a ``.qmd`` file whose slides start at ``## `` headings. The speaker notes of a slide sit in a
``::: notes`` block and begin with a planned time written ``[m:ss]``. Everything after an HTML comment that holds the
word BACKUP, for example ``<!-- ===== BACKUP ===== -->``, is left out: backup slides carry no planned time.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
import re

BACKUP_MARKER = re.compile(r"<!--[^\n]*\bBACKUP\b[^\n]*-->")
NOTES_BLOCK = re.compile(r"::: notes\n(.*?)\n:::", re.DOTALL)
PLANNED_TIME = re.compile(r"\[(\d+):(\d{2})\]\s*")
HEADING_TEXT = re.compile(r'<p class="(?:act|dq|t)">(.*?)</p>', re.DOTALL)
HEADING_ATTRIBUTES = re.compile(r"\s*\{.*\}\s*$")
HTML_TAG = re.compile(r"<[^>]+>")
UNTITLED = "Untitled slide"


@dataclass(frozen=True)
class Slide:
    """One slide of a deck.

    Attributes:
        title: The heading of the slide, or the text of its divider or cover when it has no heading.
        seconds: Planned speaking time in seconds; 0 when the slide has no planned time.
        text: The speaker notes without the time marker.
    """

    title: str
    seconds: int
    text: str


def format_clock(seconds: int) -> str:
    """Format a duration as minutes and seconds.

    Args:
        seconds: A duration in seconds.

    Returns:
        The duration as ``m:ss``, for example ``1:05``.
    """
    minutes, rest = divmod(seconds, 60)
    return f"{minutes}:{rest:02d}"


def _slide_title(heading: str, body: str) -> str:
    """Return the title of a slide from its heading, or from its divider or cover text when it has none.

    Args:
        heading: The text after ``## `` on the heading line, which may hold only attributes such as ``{.divider}``.
        body: The rest of the slide, searched for divider or cover text when the heading has none.

    Returns:
        The heading without its attributes, the plain text of the divider or cover, or ``Untitled slide``.
    """
    if not heading.startswith("{"):
        return HEADING_ATTRIBUTES.sub("", heading).strip()
    found = HEADING_TEXT.search(body)
    if found is None:
        return UNTITLED
    return " ".join(HTML_TAG.sub(" ", found.group(1)).split())


def _parse_notes(body: str) -> tuple[int, str]:
    """Return the planned seconds and the text of the speaker notes in a slide body.

    Args:
        body: The slide text after its heading.

    Returns:
        The planned seconds and the notes text; ``(0, "")`` when the slide has no notes block and 0 seconds
        when the notes carry no time marker.
    """
    block = NOTES_BLOCK.search(body)
    if block is None:
        return 0, ""
    text = block.group(1).strip()
    marker = PLANNED_TIME.match(text)
    if marker is None:
        return 0, text
    seconds = int(marker.group(1)) * 60 + int(marker.group(2))
    return seconds, text[marker.end() :].strip()


def parse_slides(markdown: str) -> list[Slide]:
    """Split a deck into slides with their notes and planned times.

    Args:
        markdown: The text of the ``.qmd`` file.

    Returns:
        One ``Slide`` per ``## `` heading before the backup marker, in order.
    """
    main = BACKUP_MARKER.split(markdown, maxsplit=1)[0]
    slides = []
    for part in re.split(r"^## ", main, flags=re.MULTILINE)[1:]:
        heading, _, body = part.partition("\n")
        seconds, text = _parse_notes(body)
        slides.append(Slide(_slide_title(heading, body), seconds, text))
    return slides


def load_deck(path: Path) -> list[Slide]:
    """Read a deck file and parse its slides.

    Args:
        path: The ``.qmd`` file.

    Returns:
        The slides of the deck, as in ``parse_slides``.
    """
    return parse_slides(path.read_text(encoding="utf-8"))


def total_seconds(slides: Sequence[Slide]) -> int:
    """Return the planned speaking time of all slides.

    Args:
        slides: The slides of the deck.

    Returns:
        The sum of the planned times, in seconds.
    """
    return sum(slide.seconds for slide in slides)


def slide_label(index: int, unnumbered: int) -> str:
    """Return the number shown for a slide.

    Args:
        index: The position of the slide in the deck, starting at 0.
        unnumbered: How many slides at the start carry no number, for example the cover.

    Returns:
        ``-`` for an unnumbered slide, else its number counted from 1 after the unnumbered ones.
    """
    return "-" if index < unnumbered else str(index - unnumbered + 1)


def timing_table(slides: Sequence[Slide], unnumbered: int = 1) -> str:
    """Build a Markdown table of the planned time of each slide and the running clock.

    Args:
        slides: The slides of the deck.
        unnumbered: How many slides at the start carry no number.

    Returns:
        The table, with the columns slide, title, target and clock.
    """
    rows = ["| Slide | Title | Target | Clock |", "|---|---|---|---|"]
    clock = 0
    for index, slide in enumerate(slides):
        clock += slide.seconds
        label = slide_label(index, unnumbered)
        rows.append(f"| {label} | {slide.title} | {format_clock(slide.seconds)} | {format_clock(clock)} |")
    return "\n".join(rows)
