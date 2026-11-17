"""Create a new document project from a profile, as kobe creates a Python project.

A profile is a real, runnable project (``profiles/cv`` and so on) that sits on the shared ``profiles/base``. Generating
a project copies the base, then the profile over it, adds the brand, the fonts and the extension the profile needs,
vendors the brand tools as ``tools/kn``, replaces the sample names and runs ``sync``. There is no template language:
what is generated is a snapshot of plain files.
"""

from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess

from .sync import sync_project

PROFILES = ("letter",)
NAME_PATTERN = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
SAMPLE_NAME = "sample-project"
SAMPLE_OWNER = "sample-owner"
SAMPLE_DESCRIPTION = "Sample description"
SAMPLE_AUTHOR = "Sample Author"
SAMPLE_EMAIL = "sample@example.org"
RENAMED = {"pre-commit-config": ".pre-commit-config.yaml", "gitignore": ".gitignore"}
IGNORED = shutil.ignore_patterns("__pycache__", ".quarto", "_freeze", "rendered_output", "*.pyc", ".DS_Store")
VENDORED = ("__init__.py", "brand.py", "contrast.py", "sync.py", "tokens.py")
TEXT_SUFFIXES = {".md", ".yml", ".yaml", ".toml", ".qmd", ".py", ".txt", ".typ", ".tex", ".scss", ".css", ""}


@dataclass(frozen=True)
class Project:
    """The facts a new project is created with.

    Attributes:
        name: Lower-case words joined by hyphens.
        profile: One of ``PROFILES``.
        owner: The GitHub user or organisation.
        description: One sentence about the project.
        author: The author's name.
        email: The author's email.
    """

    name: str
    profile: str
    owner: str = "sambaiga"
    description: str = "A document project in the kinyonga brand"
    author: str = "sambaiga"
    email: str = "sambaiga@gmail.com"


def validate_name(name: str) -> str:
    """Check that a project name is lower-case words joined by single hyphens.

    Args:
        name: The proposed name.

    Returns:
        The name, unchanged.

    Raises:
        ValueError: If the name does not fit the pattern.
    """
    if not NAME_PATTERN.fullmatch(name):
        msg = f"invalid project name {name!r}: use lower-case letters and digits in words joined by single hyphens"
        raise ValueError(msg)
    return name


def source_root() -> Path:
    """Locate the folder that holds ``profiles``, ``_extensions``, ``fonts`` and ``brand.yml``.

    Returns:
        The packaged data folder of an installed copy, or the repository root of a source checkout.
    """
    packaged = Path(__file__).parent / "_data"
    return packaged if (packaged / "profiles").is_dir() else Path(__file__).resolve().parent.parent


def _copy(source: Path, destination: Path) -> None:
    """Copy a folder over another, renaming the files that cannot carry their final name in the source.

    Args:
        source: The folder to copy.
        destination: The folder to copy into; it may exist.
    """
    shutil.copytree(source, destination, dirs_exist_ok=True, ignore=IGNORED)
    for path in sorted(destination.rglob("*")):
        if path.name in RENAMED:
            path.rename(path.with_name(RENAMED[path.name]))


def _replace_names(folder: Path, project: Project) -> None:
    """Replace the sample names in every text file of a project.

    Args:
        folder: The project folder.
        project: The facts to write in.
    """
    swaps = {
        SAMPLE_NAME: project.name,
        SAMPLE_OWNER: project.owner,
        SAMPLE_DESCRIPTION: project.description,
        SAMPLE_AUTHOR: project.author,
        SAMPLE_EMAIL: project.email,
    }
    for path in folder.rglob("*"):
        if path.is_file() and path.suffix in TEXT_SUFFIXES and ".git/" not in path.as_posix():
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for sample, value in swaps.items():
                text = text.replace(sample, value)
            path.write_text(text, encoding="utf-8")


def new_project(project: Project, destination: Path, *, git: bool = True) -> Path:
    """Create a project from a profile.

    Args:
        project: The facts of the new project.
        destination: The folder to create the project in; it must not exist.
        git: Whether to run ``git init`` in it.

    Returns:
        The folder of the new project.

    Raises:
        ValueError: If the name or the profile is not valid.
        FileExistsError: If the folder already exists.
    """
    validate_name(project.name)
    if project.profile not in PROFILES:
        msg = f"unknown profile {project.profile!r}: choose from {', '.join(PROFILES)}"
        raise ValueError(msg)
    if destination.exists():
        msg = f"{destination} already exists"
        raise FileExistsError(msg)
    source = source_root()
    _copy(source / "profiles" / "base", destination)
    _copy(source / "profiles" / project.profile, destination)
    for name in ("brand.yml", "kinyonga.yml"):
        shutil.copyfile(source / name, destination / name)
    shutil.copytree(source / "fonts", destination / "fonts")
    _copy(
        source / "_extensions" / f"kinyonga-{project.profile}",
        destination / "_extensions" / f"kinyonga-{project.profile}",
    )
    tools = destination / "tools" / "kn"
    tools.mkdir(parents=True)
    (tools.parent / "__init__.py").write_text("", encoding="utf-8")
    for name in VENDORED:
        shutil.copyfile(Path(__file__).parent / name, tools / name)
    (tools / "__main__.py").write_text(
        '"""Run the brand tools: python -m tools.kn sync|check."""\n\nimport sys\n\nfrom .sync import main\n\n'
        "sys.exit(main())\n",
        encoding="utf-8",
    )
    _replace_names(destination, project)
    sync_project(destination)
    if git:
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=destination, check=True)
    return destination
