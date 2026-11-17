import importlib.util
from pathlib import Path
import re

import pytest

from kinyonga.brand import load_brand

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def logos():
    spec = importlib.util.spec_from_file_location("make_logos", ROOT / "scripts" / "branding" / "make_logos.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_set_is_written_and_self_contained(logos, tmp_path: Path):
    written = {path.name: path.read_text(encoding="utf-8") for path in logos.write_all(tmp_path)}
    assert set(written) == {"mark.svg", "mark-mono.svg", "logo.svg", "logo-dark.svg", "avatar.svg", "favicon.svg"}
    for name, text in written.items():
        assert text.startswith("<svg"), name
        assert "<image" not in text and "href=" not in text and "<text" not in text, name


def test_every_colour_comes_from_the_brand(logos, tmp_path: Path):
    brand = load_brand(ROOT / "brand.yml")
    allowed = set(brand.palette.values())
    for path in logos.write_all(tmp_path):
        used = {colour.upper() for colour in re.findall(r"#[0-9A-Fa-f]{6}", path.read_text(encoding="utf-8"))}
        assert used <= allowed, f"{path.name}: {sorted(used - allowed)}"


def test_the_dark_lockup_keeps_the_branch_visible(logos):
    brand = load_brand(ROOT / "brand.yml")
    assert brand.colour("ink") not in logos.mark_group(brand, dark=True).split("stroke=")[1]
    assert logos.lockup(brand, ROOT / "fonts", dark=True).count(brand.colour("white")) >= 1


def test_the_four_patches_are_four_different_colours(logos):
    brand = load_brand(ROOT / "brand.yml")
    patches = re.findall(r'<rect x="\d+" y="10" width="\d+" height="70" fill="(#[0-9A-F]{6})"', logos.mark_group(brand))
    assert len(patches) == 4
    assert len(set(patches)) == 4
