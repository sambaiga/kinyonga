from pathlib import Path

import pytest
import yaml

from kinyonga.cvdata import CvError, ats_problems, check_cv, load_cv, validate_cv

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "profiles" / "cv" / "cv.yml"


def sample() -> dict:
    return yaml.safe_load(SAMPLE.read_text(encoding="utf-8"))


def test_the_sample_cv_is_valid_and_clean():
    assert check_cv(SAMPLE) == []


def test_years_as_numbers_count_as_text():
    data = sample()
    assert isinstance(data["cv"]["experience"][0]["roles"][0]["start"], int)
    assert validate_cv(data) == []


@pytest.mark.parametrize("data", [None, [], {"cv": []}, {"other": {}}])
def test_the_data_must_be_a_mapping_under_cv(data):
    assert validate_cv(data) == ["cv.yml must hold a mapping under the key `cv`"]


@pytest.mark.parametrize("key", ["headline", "summary", "experience"])
def test_the_required_sections_are_reported(key: str):
    data = sample()
    del data["cv"][key]
    assert f"cv.{key} is required" in validate_cv(data)


def test_the_optional_sections_may_be_absent():
    data = sample()
    for key in ("achievements", "education", "skills", "publications"):
        del data["cv"][key]
    assert validate_cv(data) == []


def test_an_experience_entry_without_an_organisation_or_roles_is_reported():
    data = sample()
    data["cv"]["experience"].append({"location": "Nowhere"})
    problems = validate_cv(data)
    assert "cv.experience[2] needs org" in problems
    assert "cv.experience[2] needs at least one role" in problems


def test_a_role_needs_title_and_dates_and_bullets_must_be_text():
    data = sample()
    data["cv"]["experience"][0]["roles"][0] = {"title": "", "bullets": ["fine", ["nested"], None]}
    problems = validate_cv(data)
    assert "cv.experience[0].roles[0] needs title" in problems
    assert "cv.experience[0].roles[0] needs start" in problems
    assert "cv.experience[0].roles[0] needs end" in problems
    assert "cv.experience[0].roles[0].bullets[1] must be text" in problems
    assert "cv.experience[0].roles[0].bullets[2] must be text" in problems


def test_lists_that_are_not_lists_and_entries_that_are_not_mappings_are_reported():
    data = sample()
    data["cv"]["education"] = "PhD"
    data["cv"]["skills"] = ["Python"]
    data["cv"]["achievements"] = [{"label": "Only a label"}]
    data["cv"]["publications"] = [{"a": 1}]
    data["cv"]["experience"][0]["roles"][0]["bullets"] = "one string"
    problems = validate_cv(data)
    assert "cv.education must be a list" in problems
    assert "cv.skills[0] must be a mapping" in problems
    assert "cv.achievements[0] needs text" in problems
    assert "cv.publications[0] must be text" in problems
    assert "cv.experience[0].roles[0].bullets must be a list" in problems


def test_a_skill_group_needs_items_and_an_education_entry_needs_its_fields():
    data = sample()
    data["cv"]["skills"] = [{"group": "Tools", "items": []}]
    data["cv"]["education"] = [{"degree": "BSc"}]
    problems = validate_cv(data)
    assert "cv.skills[0] needs items" in problems
    assert "cv.education[0] needs school" in problems
    assert "cv.education[0] needs year" in problems


def test_typographic_dashes_soft_hyphens_and_private_use_characters_are_advised_against():
    data = sample()
    data["cv"]["experience"][0]["roles"][0]["bullets"] = ["2019\N{EN DASH}2022", "co\N{SOFT HYPHEN}operate", " icon"]
    data["cv"]["summary"] = "A summary \N{EM DASH} with a dash"
    problems = ats_problems(data)
    assert "cv.experience[0].roles[0].bullets[0] has a typographic dash; use a plain hyphen" in problems
    assert "cv.experience[0].roles[0].bullets[1] has a soft hyphen; remove it" in problems
    assert any("bullets[2] has a private-use character" in problem for problem in problems)
    assert "cv.summary has a typographic dash; use a plain hyphen" in problems


def test_check_reports_a_missing_file_a_bad_mapping_and_bad_yaml(tmp_path: Path):
    assert check_cv(tmp_path / "missing.yml") == [f"{tmp_path / 'missing.yml'} was not found"]
    (tmp_path / "list.yml").write_text("- a\n", encoding="utf-8")
    assert "must hold a mapping" in check_cv(tmp_path / "list.yml")[0]
    (tmp_path / "bad.yml").write_text("cv: [unclosed\n", encoding="utf-8")
    assert "is not valid YAML" in check_cv(tmp_path / "bad.yml")[0]


def test_load_cv_raises_for_a_missing_file(tmp_path: Path):
    with pytest.raises(CvError, match="was not found"):
        load_cv(tmp_path / "nope.yml")
