from pathlib import Path

import pytest

from kinyonga.brand import load_brand, load_settings
from kinyonga.contrast import check_contrast, contrast_ratio, relative_luminance

ROOT = Path(__file__).resolve().parents[2]


def test_black_on_white_is_twenty_one_and_a_colour_on_itself_is_one():
    assert contrast_ratio("#000000", "#FFFFFF") == pytest.approx(21.0)
    assert contrast_ratio("#0369A1", "#0369A1") == pytest.approx(1.0)
    assert relative_luminance("#FFFFFF") == pytest.approx(1.0)
    assert relative_luminance("#000000") == pytest.approx(0.0)


def test_the_order_of_the_colours_does_not_matter():
    assert contrast_ratio("#0369A1", "#FFFFFF") == contrast_ratio("#FFFFFF", "#0369A1")


def test_every_declared_pair_of_the_brand_meets_its_minimum():
    brand = load_brand(ROOT / "brand.yml")
    assert check_contrast(brand, load_settings(ROOT / "kinyonga.yml")["contrast"]) == []


def test_a_pair_below_its_minimum_is_reported():
    brand = load_brand(ROOT / "brand.yml")
    problems = check_contrast(brand, [{"text": "slate-light", "background": "white", "minimum": 4.5}])
    assert len(problems) == 1
    assert "slate-light on white" in problems[0]


def test_a_pair_naming_an_unknown_colour_is_reported_not_raised():
    brand = load_brand(ROOT / "brand.yml")
    problems = check_contrast(brand, [{"text": "magenta", "background": "white", "minimum": 4.5}])
    assert problems == ["contrast pair magenta on white: unknown colour or role 'magenta'"]
