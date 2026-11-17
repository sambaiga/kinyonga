from kinyonga.notes import (
    format_clock,
    parse_slides,
    slide_label,
    timing_table,
    total_seconds,
)

DECK = """---
pagetitle: "Demo"
---

## {.title-slide-custom data-state="cover"}

<div class="title-box"><p class="t">The <b>title</b></p></div>

::: notes
[0:30] Greet the audience.
:::

## First slide {.acc-teal}

Body text.

::: notes
[1:05] Explain the first slide.
:::

## {background-color="#0C4A6E" .divider-slide}

<div class="divider"><p class="act">Part 2 · Slides 3 to 4</p></div>

::: notes
[0:10] Introduce part two.
:::

## Slide without notes

Nothing to say.

<!-- ============================ BACKUP ============================ -->

## Backup slide

::: notes
[9:00] Never counted.
:::
"""


def test_parse_slides_stops_at_the_backup_marker():
    slides = parse_slides(DECK)
    assert [slide.title for slide in slides] == [
        "The title",
        "First slide",
        "Part 2 · Slides 3 to 4",
        "Slide without notes",
    ]


def test_parse_slides_reads_planned_time_and_text():
    slides = parse_slides(DECK)
    assert [slide.seconds for slide in slides] == [30, 65, 10, 0]
    assert slides[1].text == "Explain the first slide."
    assert slides[3].text == ""


def test_parse_slides_returns_nothing_for_a_deck_without_headings():
    assert parse_slides("---\ntitle: x\n---\nText only.") == []


def test_notes_without_a_time_marker_have_zero_seconds():
    slides = parse_slides("## A\n\n::: notes\nNo marker here.\n:::\n")
    assert slides[0].seconds == 0
    assert slides[0].text == "No marker here."


def test_format_clock_pads_seconds():
    assert format_clock(65) == "1:05"
    assert format_clock(0) == "0:00"
    assert format_clock(600) == "10:00"


def test_slide_label_leaves_the_first_slides_unnumbered():
    assert [slide_label(index, 2) for index in range(4)] == ["-", "-", "1", "2"]
    assert slide_label(0, 1) == "-"
    assert slide_label(1, 1) == "1"


def test_timing_table_has_a_running_clock():
    slides = parse_slides(DECK)
    rows = timing_table(slides).split("\n")
    assert rows[2] == "| - | The title | 0:30 | 0:30 |"
    assert rows[3] == "| 1 | First slide | 1:05 | 1:35 |"
    assert rows[-1].endswith("| 0:00 | 1:45 |")
    assert total_seconds(slides) == 105
