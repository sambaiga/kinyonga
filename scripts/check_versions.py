"""Fail when the version of an extension differs from the version of the package, so that a tag names one release."""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
VERSION = re.compile(r"^version:\s*['\"]?([0-9][^'\"\s]*)['\"]?\s*$", re.MULTILINE)


def package_version(root: Path) -> str:
    """Read the version of the package from ``pyproject.toml``.

    Args:
        root: The repository folder.

    Returns:
        The version string.
    """
    match = re.search(r'^version\s*=\s*"([^"]+)"', (root / "pyproject.toml").read_text(encoding="utf-8"), re.MULTILINE)
    if match is None:
        msg = "pyproject.toml has no version"
        raise ValueError(msg)
    return match.group(1)


def mismatches(root: Path) -> list[str]:
    """List the extensions whose ``version:`` differs from the package version.

    Args:
        root: The repository folder.

    Returns:
        One message for each extension that is missing a version or has another one.
    """
    expected = package_version(root)
    problems = []
    for manifest in sorted((root / "_extensions").glob("*/_extension.yml")):
        match = VERSION.search(manifest.read_text(encoding="utf-8"))
        found = match.group(1) if match else None
        if found != expected:
            problems.append(f"{manifest.parent.name} has version {found}, the package has {expected}")
    return problems


def main() -> int:
    """Run the check.

    Returns:
        0 when every extension matches, 1 otherwise.
    """
    problems = mismatches(ROOT)
    for problem in problems:
        sys.stderr.write(f"{problem}\n")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
