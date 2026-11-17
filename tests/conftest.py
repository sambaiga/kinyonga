from pathlib import Path
import shutil

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A copy of the project's brand, settings, fonts and extensions, with the generated tokens in place."""
    from kinyonga.sync import sync_project

    for name in ("brand.yml", "kinyonga.yml"):
        shutil.copyfile(ROOT / name, tmp_path / name)
    shutil.copytree(ROOT / "fonts", tmp_path / "fonts")
    shutil.copytree(
        ROOT / "_extensions", tmp_path / "_extensions", ignore=shutil.ignore_patterns("tokens", "fonts", "brand.yml")
    )
    sync_project(tmp_path)
    return tmp_path
