from pathlib import Path

import pytest

from kinyonga.generate import PROFILES, Project, new_project, validate_name
from kinyonga.sync import check_project


@pytest.mark.parametrize("name", ["my-cv", "cv", "a1-b2-c3"])
def test_valid_names_are_returned_unchanged(name: str):
    assert validate_name(name) == name


@pytest.mark.parametrize("name", ["My-CV", "my_cv", "-cv", "cv-", "my--cv", "1cv", ""])
def test_invalid_names_are_refused(name: str):
    with pytest.raises(ValueError, match="invalid project name"):
        validate_name(name)


def test_a_new_project_has_its_names_replaced_and_passes_the_check(tmp_path: Path):
    project = Project(
        "my-letter", "letter", owner="someone", description="My letters", author="A. Writer", email="a@b.org"
    )
    created = new_project(project, tmp_path / "my-letter", git=False)
    assert (created / ".pre-commit-config.yaml").is_file()
    assert (created / ".gitignore").is_file()
    assert (created / "letter.qmd").is_file()
    assert (created / "tools" / "kn" / "sync.py").is_file()
    assert 'name = "my-letter"' in (created / "pyproject.toml").read_text(encoding="utf-8")
    assert "A. Writer" in (created / "profile.yml").read_text(encoding="utf-8")
    assert "sample-project" not in "".join(
        path.read_text(encoding="utf-8") for path in (created / "README.md", created / "CLAUDE.md")
    )
    assert check_project(created) == []


def test_a_new_project_with_git_has_a_repository(tmp_path: Path):
    created = new_project(Project("my-letter", "letter"), tmp_path / "my-letter")
    assert (created / ".git").is_dir()


def test_an_unknown_profile_or_an_existing_folder_is_refused(tmp_path: Path):
    with pytest.raises(ValueError, match="unknown profile"):
        new_project(Project("my-doc", "poster"), tmp_path / "my-doc")
    (tmp_path / "taken").mkdir()
    with pytest.raises(FileExistsError):
        new_project(Project("taken", PROFILES[0]), tmp_path / "taken")


def test_a_new_cv_project_has_its_data_icons_and_extra_target_and_passes_the_check(tmp_path: Path):
    project = Project("my-cv", "cv", author="A. Writer")
    created = new_project(project, tmp_path / "my-cv", git=False)
    assert (created / "cv.yml").is_file()
    assert (created / "profile.mk").is_file()
    assert (created / "icons" / "envelope.svg").is_file()
    assert (created / "_extensions" / "kinyonga-cv" / "filters" / "cv.lua").is_file()
    assert (created / "tools" / "kn" / "cvdata.py").is_file()
    assert "title: A. Writer" in (created / "cv.qmd").read_text(encoding="utf-8")
    assert not (created / "letter.qmd").exists()
    assert check_project(created) == []


def test_a_letter_project_does_not_carry_the_icons(tmp_path: Path):
    created = new_project(Project("my-letter", "letter"), tmp_path / "my-letter", git=False)
    assert not (created / "icons").exists()


def test_a_new_slides_project_has_its_deck_shared_components_and_timing_target(tmp_path: Path):
    created = new_project(Project("my-talk", "slides", author="A. Writer"), tmp_path / "my-talk", git=False)
    assert (created / "deck.qmd").is_file()
    assert (created / "profile.mk").read_text(encoding="utf-8").startswith("# Extra targets of the slides profile")
    assert (created / "shared" / "_components.scss").is_file()
    assert (created / "_extensions" / "kinyonga-slides" / "scss" / "kinyonga-slides.scss").is_file()
    assert (created / "_extensions" / "kinyonga-slides" / "shared" / "_components.scss").is_file()
    assert not (created / "icons").exists()
    assert check_project(created) == []


def test_a_new_book_project_has_chapters_the_book_extension_and_shared_components(tmp_path: Path):
    created = new_project(Project("my-book", "book", author="A. Writer"), tmp_path / "my-book", git=False)
    assert "type: book" in (created / "_quarto.yml").read_text(encoding="utf-8")
    assert (created / "ch1.qmd").is_file()
    assert (created / "_extensions" / "kinyonga-book" / "scss" / "kinyonga-book.scss").is_file()
    assert (created / "_extensions" / "kinyonga-book" / "shared" / "_components.scss").is_file()
    assert (created / "_extensions" / "kinyonga-book" / "tokens" / "colors.typ").is_file()
    assert check_project(created) == []


def test_the_latex_cover_shows_a_finished_cover_alone_when_one_is_supplied(tmp_path: Path):
    created = new_project(Project("my-book", "book", author="A. Writer"), tmp_path / "my-book", git=False)
    cover = (created / "_extensions" / "kinyonga-book" / "latex" / "cover.tex").read_text(encoding="utf-8")
    assert "assets/cover-full.pdf" in cover
    assert cover.count("{") == cover.count("}")
