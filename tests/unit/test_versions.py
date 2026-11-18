"""Tests for the extension version check."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check_versions.py"
spec = spec_from_file_location("check_versions", SCRIPT)
assert spec is not None
assert spec.loader is not None
check_versions = module_from_spec(spec)
spec.loader.exec_module(check_versions)
ROOT, mismatches, package_version = check_versions.ROOT, check_versions.mismatches, check_versions.package_version


def make_repo(tmp_path: Path, version: str) -> Path:
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "1.2.3"\n', encoding="utf-8")
    extension = tmp_path / "_extensions" / "kinyonga-x"
    extension.mkdir(parents=True)
    (extension / "_extension.yml").write_text(f"title: x\nversion: {version}\n", encoding="utf-8")
    return tmp_path


def test_the_package_version_is_read(tmp_path: Path):
    assert package_version(make_repo(tmp_path, "1.2.3")) == "1.2.3"


def test_matching_versions_pass(tmp_path: Path):
    assert mismatches(make_repo(tmp_path, "1.2.3")) == []


def test_a_different_version_is_reported(tmp_path: Path):
    assert mismatches(make_repo(tmp_path, "0.9.0")) == ["kinyonga-x has version 0.9.0, the package has 1.2.3"]


def test_the_extensions_of_this_repository_match_the_package():
    assert mismatches(ROOT) == []
