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
