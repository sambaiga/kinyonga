from pathlib import Path

from kinyonga.sync import check_project, extension_dirs, main, recolour, sync_project


def test_a_synced_project_passes_the_check(project: Path):
    assert [path.name for path in extension_dirs(project)] == ["kinyonga-cv", "kinyonga-letter"]
    assert check_project(project) == []


def test_each_extension_carries_its_own_brand_tokens_and_fonts(project: Path):
    extension = extension_dirs(project)[1]
    assert (extension / "brand.yml").read_bytes() == (project / "brand.yml").read_bytes()
    assert (extension / "tokens" / "colors.typ").is_file()
    assert (extension / "fonts" / "Jost-SemiBold.ttf").is_file()
    assert (extension / "fonts" / "OFL-Jost.txt").is_file()
    assert (extension / "assets" / "logo.svg").is_file()


def test_editing_the_brand_without_a_sync_is_reported(project: Path):
    text = (project / "brand.yml").read_text(encoding="utf-8")
    (project / "brand.yml").write_text(text.replace("#0369A1", "#0369A2"), encoding="utf-8")
    problems = check_project(project)
    assert any("differs from brand.yml" in problem for problem in problems)
    assert any("colors.typ differs" in problem for problem in problems)
    sync_project(project)
    assert check_project(project) == []


def test_a_font_missing_from_an_extension_or_not_listed_is_reported(project: Path):
    extension = extension_dirs(project)[1]
    (extension / "fonts" / "Jost-Bold.ttf").unlink()
    manifest = extension / "_extension.yml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace("        - fonts/LibreFranklin-Italic.ttf\n", ""), encoding="utf-8"
    )
    problems = check_project(project)
    assert any("Jost-Bold.ttf is missing" in problem for problem in problems)
    assert any("does not list fonts/LibreFranklin-Italic.ttf" in problem for problem in problems)


def test_a_missing_declared_font_and_a_failing_contrast_pair_are_reported(project: Path):
    (project / "fonts" / "Jost-Bold.ttf").unlink()
    settings = project / "kinyonga.yml"
    settings.write_text("contrast:\n  - {text: slate-light, background: white, minimum: 4.5}\n", encoding="utf-8")
    problems = check_project(project)
    assert any("font file fonts/Jost-Bold.ttf is missing" in problem for problem in problems)
    assert any("slate-light on white" in problem for problem in problems)


def test_a_project_without_a_brand_reports_one_problem(tmp_path: Path):
    assert len(check_project(tmp_path)) == 1


def test_the_command_syncs_then_checks(project: Path, capsys):
    assert main(["sync", "--project", str(project)]) == 0
    assert "synced" in capsys.readouterr().out
    assert main(["check", "--project", str(project)]) == 0
    assert "brand check passed" in capsys.readouterr().out
    (project / "tokens" / "colors.tex").write_text("edited\n", encoding="utf-8")
    assert main(["check", "--project", str(project)]) == 1
    assert "problem(s)" in capsys.readouterr().out


def test_a_logo_not_listed_under_format_resources_is_reported(project: Path):
    manifest = extension_dirs(project)[1] / "_extension.yml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace("        - assets/mark.svg\n", ""), encoding="utf-8"
    )
    assert any("does not list assets/mark.svg" in problem for problem in check_project(project))


def test_icons_are_shipped_in_the_brand_colour(project: Path):
    extension = extension_dirs(project)[0]
    shipped = (extension / "icons" / "envelope.svg").read_text(encoding="utf-8")
    source = (project / "icons" / "envelope.svg").read_text(encoding="utf-8")
    assert 'fill="currentColor"' in source
    assert 'fill="#0369A1"' in shipped
    assert recolour(source, "#0369A1") == shipped


def test_an_icon_in_the_wrong_colour_or_without_a_source_is_reported(project: Path):
    extension = extension_dirs(project)[0]
    (extension / "icons" / "envelope.svg").write_text("<svg/>", encoding="utf-8")
    (project / "icons" / "globe.svg").unlink()
    problems = check_project(project)
    assert any("envelope.svg differs" in problem for problem in problems)
    assert any("globe.svg is missing; the extension lists icons/globe.svg" in problem for problem in problems)


def test_a_broken_cv_in_the_project_is_reported_with_its_file(project: Path):
    (project / "cv.yml").write_text("cv:\n  headline: Only a headline\n", encoding="utf-8")
    problems = check_project(project)
    assert "cv.yml: cv.summary is required" in problems
    assert "cv.yml: cv.experience is required" in problems
