"""Render a generated project with the pinned Quarto and check the PDF. Run by `make verify`; slow."""

import os
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
    info = subprocess.run(["pdfinfo", str(pdf)], check=True, capture_output=True, text=True).stdout
    assert "Title:           Application for the post of Senior Data Scientist" in info
    assert "sambaiga@gmail.com" in text
    assert "\N{EN DASH}" not in text


@pytest.fixture(scope="module")
def cv_project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A generated CV project whose data has a typographic dash and a soft hyphen, rendered to PDF, ATS PDF and HTML."""
    created = new_project(
        Project("my-cv", "cv", author="Test Person"), tmp_path_factory.mktemp("cv") / "my-cv", git=False
    )
    subprocess.run(["uv", "sync"], cwd=created, check=True, capture_output=True)
    data = created / "cv.yml"
    text = data.read_text(encoding="utf-8").replace(
        "Mentored four data scientists", "Mentored four data\N{EM DASH}scientists and co\N{SOFT HYPHEN}operated"
    )
    data.write_text(
        text.replace("Directed a predictive", "In 2019\N{EN DASH}2020 directed a predictive"), encoding="utf-8"
    )
    quarto = ["uv", "run", "quarto", "render", "cv.qmd"]
    subprocess.run([*quarto, "--to", "kinyonga-cv-typst"], cwd=created, check=True, capture_output=True)
    subprocess.run([*quarto, "--to", "kinyonga-cv-html"], cwd=created, check=True, capture_output=True)
    subprocess.run(
        [*quarto, "--to", "kinyonga-cv-typst", "-M", "ats:true", "-o", "cv-ats.pdf"],
        cwd=created,
        check=True,
        capture_output=True,
    )
    return created


def pdf_text(pdf: Path, mode: str = "-raw") -> str:
    return subprocess.run(["pdftotext", mode, str(pdf), "-"], check=True, capture_output=True, text=True).stdout


SECTIONS = ["Professional Summary", "Key Achievements", "Experience", "Education", "Skills", "Selected Publications"]


@pytest.mark.skipif(shutil.which("uv") is None or shutil.which("pdftotext") is None, reason="needs uv and poppler")
@pytest.mark.parametrize("name", ["cv.pdf", "cv-ats.pdf"])
def test_the_cv_pdf_reads_cleanly_to_an_ats(cv_project: Path, name: str):
    pdf = cv_project / "rendered_output" / name
    text = pdf_text(pdf)
    lines = text.splitlines()
    assert lines[0] == "Test Person"
    positions = [text.index(section) for section in SECTIONS]
    assert positions == sorted(positions)
    assert "sambaiga@gmail.com" in text
    for bad in ("\N{EN DASH}", "\N{EM DASH}", "\N{SOFT HYPHEN}"):
        assert bad not in text
    assert not any("" <= char <= "" for char in text)
    assert "data-scientists and cooperated" in text.replace("\n", " ")
    assert "In 2019-2020 directed a predictive" in text.replace("\n", " ")
    assert "2021-2022" in text
    info = subprocess.run(["pdfinfo", str(pdf)], check=True, capture_output=True, text=True).stdout
    pages = int(next(line for line in info.splitlines() if line.startswith("Pages:")).split()[1])
    assert pages <= 2
    assert "Tagged:          yes" in info
    assert "Title:           Test Person" in info
    fonts = subprocess.run(["pdffonts", str(pdf)], check=True, capture_output=True, text=True).stdout
    assert "Jost" in fonts
    assert "LibreFranklin" in fonts
    assert "Libertinus" not in fonts


@pytest.mark.skipif(shutil.which("uv") is None or shutil.which("pdftotext") is None, reason="needs uv and poppler")
def test_the_ats_edition_spells_the_labels_out_and_the_default_uses_icons(cv_project: Path):
    default = pdf_text(cv_project / "rendered_output" / "cv.pdf")
    ats = pdf_text(cv_project / "rendered_output" / "cv-ats.pdf")
    assert "Email: sambaiga@gmail.com" in ats
    assert "Phone:" in ats
    assert "Email:" not in default
    assert "Sample Organisation, Dublin, Ireland" in ats


def test_the_cv_html_has_one_visible_name_and_the_contact_details(cv_project: Path):
    html = (cv_project / "rendered_output" / "cv.html").read_text(encoding="utf-8")
    assert html.count('<h1 class="kn-name">Test Person</h1>') == 1
    assert "sambaiga@gmail.com" in html
    assert "\N{EN DASH}" not in html
    assert "Other Formats" not in html


@pytest.mark.skipif(shutil.which("uv") is None, reason="needs uv")
def test_the_cv_pdf_validates_as_pdf_ua(cv_project: Path):
    """Render the CV as PDF/UA-1 and let veraPDF validate it; CI sets KINYONGA_REQUIRE_VERAPDF to require it."""
    result = subprocess.run(
        [
            "uv",
            "run",
            "quarto",
            "render",
            "cv.qmd",
            "--to",
            "kinyonga-cv-typst",
            "-M",
            "pdf-standard:ua-1",
            "-o",
            "cv-ua.pdf",
        ],
        cwd=cv_project,
        check=True,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    if "verapdf is not installed" in output:
        assert not os.environ.get("KINYONGA_REQUIRE_VERAPDF"), "veraPDF is required here: `quarto install verapdf`"
        pytest.skip("veraPDF is not installed")
    assert "PASSED" in output


@pytest.fixture(scope="module")
def slides_project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A generated slides project, rendered with the pinned Quarto."""
    created = new_project(
        Project("my-talk", "slides", author="Test Person"), tmp_path_factory.mktemp("sl") / "my-talk", git=False
    )
    subprocess.run(["uv", "sync"], cwd=created, check=True, capture_output=True)
    subprocess.run(["make", "deck"], cwd=created, check=True, capture_output=True)
    return created


@pytest.mark.skipif(shutil.which("uv") is None, reason="needs uv")
def test_the_deck_renders_in_the_brand_with_one_cover_and_no_page_logo(slides_project: Path):
    html = (slides_project / "rendered_output" / "deck.html").read_text(encoding="utf-8")
    assert "<section" in html
    assert html.count("title-slide-custom") >= 1
    assert "slide-logo" not in html
    assert 'class="quarto-title-block"' not in html
    css = "".join(
        path.read_text(encoding="utf-8") for path in (slides_project / "rendered_output").rglob("quarto-*.css")
    )
    assert "Jost" in css
    assert "Libre Franklin" in css
    # .acc-orange switches to orange (it used to point at blue); the orange comes from the brand tokens
    assert "section.acc-orange{--acc:var(--orange)" in css.replace(" ", "")
    assert "--orange:#e26029" in css.replace(" ", "").lower()
    # the icon font is inlined, so the deck works offline
    assert "data:font/woff2;base64" in "".join(
        path.read_text(encoding="utf-8")
        for path in (slides_project / "rendered_output").rglob("bootstrap-icons.min.css")
    )


@pytest.mark.skipif(shutil.which("uv") is None, reason="needs uv")
def test_make_timing_adds_up_the_notes_of_the_starter_deck(slides_project: Path):
    output = subprocess.run(["make", "timing"], cwd=slides_project, check=True, capture_output=True, text=True).stdout
    assert "| Slide | Title | Target | Clock |" in output
    assert "Planned total" in output


def has_latex() -> bool:
    """Say whether a LaTeX engine is available, from the system or from the TinyTeX that Quarto installs."""
    tinytex = (Path.home() / ".TinyTeX", Path.home() / "Library" / "TinyTeX")
    return shutil.which("lualatex") is not None or any(path.is_dir() for path in tinytex)


@pytest.fixture(scope="module")
def book_project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A generated book project, rendered to HTML, LaTeX and Typst with the pinned Quarto."""
    created = new_project(
        Project("my-book", "book", author="Test Person"), tmp_path_factory.mktemp("bk") / "my-book", git=False
    )
    subprocess.run(["uv", "sync"], cwd=created, check=True, capture_output=True)
    subprocess.run(["make", "review"], cwd=created, check=True, capture_output=True)
    if has_latex():
        done = subprocess.run(["make", "book"], cwd=created, capture_output=True, text=True)
        assert done.returncode == 0, done.stdout[-3000:] + done.stderr[-3000:]
    return created


def book_pdf_problems(pdf: Path) -> list[str]:
    """Report what is wrong with a rendered book PDF: its fonts, its chapters and its numbered figure and table."""
    fonts = subprocess.run(["pdffonts", str(pdf)], check=True, capture_output=True, text=True).stdout
    text = pdf_text(pdf)
    problems = [f"{name} is not embedded" for name in ("Jost", "LibreFranklin") if name not in fonts]
    problems += [f"{name} is used" for name in ("Libertinus", "Helvetica") if name in fonts]
    problems += [
        f"{phrase!r} is missing"
        for phrase in ("A first chapter", "A second chapter", "Figure 1.1", "Table 1.1")
        if phrase not in text
    ]
    return problems


@pytest.mark.skipif(shutil.which("uv") is None or shutil.which("pdftotext") is None, reason="needs uv and poppler")
def test_the_typst_book_is_one_merged_book_in_the_brand_fonts_only(book_project: Path):
    assert book_pdf_problems(book_project / "rendered_review" / "Sample-Book.pdf") == []


@pytest.mark.skipif(
    shutil.which("uv") is None or shutil.which("pdftotext") is None or not has_latex(),
    reason="needs uv, poppler and LaTeX",
)
def test_the_latex_book_is_in_the_brand_fonts_with_a_cover_and_contents(book_project: Path):
    pdf = book_project / "rendered_output" / "Sample-Book.pdf"
    problems = [p for p in book_pdf_problems(pdf) if "Helvetica" not in p]
    assert problems == []
    assert "Table of contents" in pdf_text(pdf)


@pytest.mark.skipif(shutil.which("uv") is None or not has_latex(), reason="needs uv and LaTeX")
def test_the_book_html_has_every_chapter_and_no_iframe(book_project: Path):
    out = book_project / "rendered_output"
    for page in ("index", "ch1", "ch2", "references"):
        assert (out / f"{page}.html").is_file()
    assert "<iframe" not in (out / "ch1.html").read_text(encoding="utf-8")
