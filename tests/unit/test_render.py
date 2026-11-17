"""Render a generated project with the pinned Quarto and check the PDF. Run by `make verify`; slow."""

from pathlib import Path
import shutil
import subprocess

import pytest

from kinyonga.generate import Project, new_project

pytestmark = pytest.mark.render


@pytest.mark.skipif(shutil.which("uv") is None or shutil.which("pdftotext") is None, reason="needs uv and poppler")
def test_a_generated_letter_renders_in_the_brand_fonts(tmp_path: Path):
    created = new_project(Project("my-letter", "letter"), tmp_path / "my-letter", git=False)
    subprocess.run(["uv", "sync"], cwd=created, check=True, capture_output=True)
    subprocess.run(["make", "letter"], cwd=created, check=True, capture_output=True)
    pdf = created / "rendered_output" / "letter.pdf"
    fonts = subprocess.run(["pdffonts", str(pdf)], check=True, capture_output=True, text=True).stdout
    assert "Jost" in fonts
    assert "LibreFranklin" in fonts
    assert "Libertinus" not in fonts
    text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], check=True, capture_output=True, text=True).stdout
    assert "Dear Hiring Manager" in text
    assert "sambaiga@gmail.com" in text
    assert "\N{EN DASH}" not in text
