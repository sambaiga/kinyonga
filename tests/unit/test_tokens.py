from pathlib import Path

from kinyonga.brand import load_brand
from kinyonga.tokens import FILES, check_tokens, render_tokens, write_tokens

ROOT = Path(__file__).resolve().parents[2]


def test_every_file_names_every_palette_colour_and_role():
    brand = load_brand(ROOT / "brand.yml")
    files = render_tokens(brand)
    assert set(files) == set(FILES)
    assert "$kn-blue: #0369A1;" in files["_tokens.scss"]
    assert "--kn-primary: #0369A1;" in files["tokens.css"]
    assert '#let kn-blue-deep = rgb("#0C4A6E")' in files["colors.typ"]
    assert "\\definecolor{knBlueDeep}{HTML}{0C4A6E}" in files["colors.tex"]
    assert all("GENERATED" in text.splitlines()[0] for text in files.values())


def test_written_tokens_pass_the_check_and_an_edit_fails_it(tmp_path: Path):
    brand = load_brand(ROOT / "brand.yml")
    write_tokens(brand, tmp_path)
    assert check_tokens(brand, tmp_path) == []
    (tmp_path / "colors.typ").write_text("// edited by hand\n", encoding="utf-8")
    (tmp_path / "tokens.css").unlink()
    problems = check_tokens(brand, tmp_path)
    assert any("colors.typ differs" in problem for problem in problems)
    assert any("tokens.css is missing" in problem for problem in problems)


def test_the_generated_files_in_the_repository_are_current():
    assert check_tokens(load_brand(ROOT / "brand.yml"), ROOT / "tokens") == []
