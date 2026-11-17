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
