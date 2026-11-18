from pathlib import Path

import pytest

from kinyonga.cli import build_parser, main


def test_parser_requires_a_command_and_a_profile():
    with pytest.raises(SystemExit):
        build_parser().parse_args([])
    with pytest.raises(SystemExit):
        build_parser().parse_args(["new", "my-doc"])


def test_new_creates_a_project_and_says_what_to_do_next(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    assert main(["new", "my-letter", "--profile", "letter", "--dest", str(tmp_path), "--no-git"]) == 0
    assert (tmp_path / "my-letter" / "letter.qmd").is_file()
    assert "make check" in capsys.readouterr().out


def test_check_runs_on_the_given_project(project: Path, capsys: pytest.CaptureFixture[str]):
    assert main(["check", "--project", str(project)]) == 0
    assert "brand check passed" in capsys.readouterr().out


def test_timing_prints_the_planned_time_of_each_slide(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    deck = tmp_path / "deck.qmd"
    deck.write_text(
        "## Cover\n\n::: notes\n[0:30] Hello.\n:::\n\n## A slide\n\n::: notes\n[1:30] Say it.\n:::\n", encoding="utf-8"
    )
    assert main(["timing", str(deck)]) == 0
    output = capsys.readouterr().out
    assert "| Slide | Title | Target | Clock |" in output
    assert "Planned total 2:00" in output


def test_the_cmyk_command_rewrites_the_colours_of_a_pdf(tmp_path):
    source = tmp_path / "in.pdf"
    source.write_bytes(b"0.0431372549 0.0705882353 0.1254901961 rg\n")
    assert main(["cmyk", str(source), str(tmp_path / "out.pdf")]) == 0
    assert (tmp_path / "out.pdf").read_bytes().startswith(b"0.7359 0.5679 0.2318 0.8367 k")
