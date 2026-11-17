from pathlib import Path

import pytest

from kinyonga.brand import BrandError, load_brand, load_settings, missing_fonts

ROOT = Path(__file__).resolve().parents[2]


def write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


GOOD = """
color:
  palette: {blue: "#0369a1", ink: "#1e293b"}
  primary: blue
typography:
  fonts:
    - family: Jost
      source: file
      files: [{path: fonts/Jost-SemiBold.ttf, weight: 600, style: normal}]
  base: {family: Libre Franklin}
  headings: {family: Jost}
"""


def test_the_project_brand_loads():
    brand = load_brand(ROOT / "brand.yml")
    assert brand.colour("blue") == "#0369A1"
    assert brand.colour("primary") == "#0369A1"
    assert (brand.base_family, brand.heading_family) == ("Libre Franklin", "Jost")


def test_colours_are_upper_case_and_roles_resolve(tmp_path: Path):
    brand = load_brand(write(tmp_path / "brand.yml", GOOD))
    assert brand.palette["ink"] == "#1E293B"
    assert brand.roles == {"primary": "blue"}
    assert brand.fonts[0].weight == 600


def test_an_unknown_colour_is_refused(tmp_path: Path):
    brand = load_brand(write(tmp_path / "brand.yml", GOOD))
    with pytest.raises(BrandError, match="unknown colour"):
        brand.colour("magenta")


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ('"#0369a1"', '"blue"', "must be #RRGGBB"),
        ("primary: blue", "primary: magenta", "not in the palette"),
        ("base: {family: Libre Franklin}", "base: {}", "needs a palette"),
    ],
)
def test_a_malformed_brand_is_refused(tmp_path: Path, old: str, new: str, message: str):
    with pytest.raises(BrandError, match=message):
        load_brand(write(tmp_path / "brand.yml", GOOD.replace(old, new)))


def test_a_missing_or_non_mapping_file_is_refused(tmp_path: Path):
    with pytest.raises(BrandError, match="was not found"):
        load_brand(tmp_path / "missing.yml")
    with pytest.raises(BrandError, match="must hold a mapping"):
        load_brand(write(tmp_path / "list.yml", "- a\n- b\n"))


def test_missing_fonts_lists_declared_files_that_do_not_exist(tmp_path: Path):
    brand = load_brand(write(tmp_path / "brand.yml", GOOD))
    assert missing_fonts(brand, tmp_path) == ["fonts/Jost-SemiBold.ttf"]
    assert missing_fonts(load_brand(ROOT / "brand.yml"), ROOT) == []


def test_settings_are_empty_when_the_file_is_absent(tmp_path: Path):
    assert load_settings(tmp_path / "kinyonga.yml") == {}
    assert "contrast" in load_settings(ROOT / "kinyonga.yml")


def test_logos_are_read_and_checked_with_the_fonts(tmp_path: Path):
    brand = load_brand(ROOT / "brand.yml")
    assert brand.logos == ("assets/logo-dark.svg", "assets/logo.svg", "assets/mark.svg")
    assert missing_fonts(brand, ROOT) == []
    assert "assets/logo.svg" in missing_fonts(brand, tmp_path)
