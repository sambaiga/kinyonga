"""Validate the data of a CV and lint it for applicant tracking systems.

A CV is written once in ``cv.yml`` under the key ``cv`` and rendered to a PDF and an HTML page by the ``kinyonga-cv``
extension. This module checks that the data has the shape the extension expects and reports, in plain words, anything
an applicant tracking system (ATS) reads badly: typographic dashes, soft hyphens and private-use characters. It needs
only the standard library and PyYAML, so a generated project vendors it as ``tools/kn/cvdata.py``.

The shape::

    cv:
      headline: Lead Data Scientist | Applied ML
      summary: One paragraph.
      achievements:                 # optional
        - {label: Leadership, text: Secured 1.6M in funding.}
      experience:
        - org: Eaton
          location: Dublin, Ireland  # optional
          roles:
            - {title: Lead Data Scientist, unit: CIP, start: 2022, end: Present, summary: ..., bullets: [...]}
      education:                    # optional
        - {degree: PhD in Computer Science, school: Instituto Superior Tecnico, year: 2025, location: Lisbon}
      skills:                       # optional
        - {group: Methods, items: [forecasting, anomaly detection]}
      publications:                 # optional
        - "Author, A. (2025). Title. Venue."
"""

from pathlib import Path
import re

import yaml

DASHES = {"\N{EN DASH}": "-", "\N{EM DASH}": "-", "\N{MINUS SIGN}": "-"}
SOFT_HYPHEN = "\N{SOFT HYPHEN}"
PRIVATE_USE = re.compile("[-]")
SECTIONS = ("headline", "summary", "experience")
OPTIONAL = ("achievements", "education", "skills", "publications")


class CvError(ValueError):
    """Raised when a CV file is missing or is not a YAML mapping."""


def _text(value: object) -> str | None:
    """Return a field as text, or ``None`` when it is empty or not a scalar.

    Args:
        value: A YAML value; numbers such as the year 2022 count as text.

    Returns:
        The stripped text, or ``None``.
    """
    if isinstance(value, bool) or value is None or isinstance(value, (list, dict)):
        return None
    text = str(value).strip()
    return text or None


def _required(entry: object, keys: tuple[str, ...], where: str) -> list[str]:
    """Report the keys an entry is missing.

    Args:
        entry: The YAML value that should be a mapping.
        keys: The keys it must have, each as non-empty text.
        where: A path for the messages, for example ``experience[0]``.

    Returns:
        One message for each problem.
    """
    if not isinstance(entry, dict):
        return [f"{where} must be a mapping"]
    return [f"{where} needs {key}" for key in keys if _text(entry.get(key)) is None]


def _list(value: object, where: str) -> tuple[list, list[str]]:
    """Return a field as a list, with a message when it is not one.

    Args:
        value: The YAML value.
        where: A path for the message.

    Returns:
        The list (empty when the value is missing or wrong) and the problems.
    """
    if value is None:
        return [], []
    if not isinstance(value, list):
        return [], [f"{where} must be a list"]
    return value, []


def _role_problems(role: object, where: str) -> list[str]:
    """Report the problems of one role.

    Args:
        role: The role mapping.
        where: A path for the messages.

    Returns:
        One message for each problem.
    """
    problems = _required(role, ("title", "start", "end"), where)
    if isinstance(role, dict):
        bullets, issues = _list(role.get("bullets"), f"{where}.bullets")
        problems.extend(issues)
        problems.extend(
            f"{where}.bullets[{i}] must be text" for i, bullet in enumerate(bullets) if _text(bullet) is None
        )
    return problems


def validate_cv(data: object) -> list[str]:
    """Check the shape of the CV data.

    Args:
        data: The parsed ``cv.yml``.

    Returns:
        One message for each problem; empty when the data has the shape the extension expects.
    """
    if not isinstance(data, dict) or not isinstance(data.get("cv"), dict):
        return ["cv.yml must hold a mapping under the key `cv`"]
    cv = data["cv"]
    problems = [f"cv.{key} is required" for key in SECTIONS if cv.get(key) in (None, "", [])]

    def items(key: str) -> list:
        found, issues = _list(cv.get(key), f"cv.{key}")
        problems.extend(issues)
        return found

    for index, job in enumerate(items("experience")):
        problems.extend(_required(job, ("org",), f"cv.experience[{index}]"))
        roles, issues = _list(job.get("roles") if isinstance(job, dict) else None, f"cv.experience[{index}].roles")
        problems.extend(issues)
        if isinstance(job, dict) and not roles:
            problems.append(f"cv.experience[{index}] needs at least one role")
        for number, role in enumerate(roles):
            problems.extend(_role_problems(role, f"cv.experience[{index}].roles[{number}]"))
    for index, entry in enumerate(items("achievements")):
        problems.extend(_required(entry, ("label", "text"), f"cv.achievements[{index}]"))
    for index, entry in enumerate(items("education")):
        problems.extend(_required(entry, ("degree", "school", "year"), f"cv.education[{index}]"))
    for index, entry in enumerate(items("skills")):
        problems.extend(_required(entry, ("group",), f"cv.skills[{index}]"))
        if isinstance(entry, dict) and not _list(entry.get("items"), f"cv.skills[{index}].items")[0]:
            problems.append(f"cv.skills[{index}] needs items")
    for index, entry in enumerate(items("publications")):
        if _text(entry) is None:
            problems.append(f"cv.publications[{index}] must be text")
    return problems


def _strings(value: object, path: str = ""):
    """Yield every string of a nested YAML value with its path.

    Args:
        value: The YAML value.
        path: The path of the value, for the messages.

    Yields:
        ``(path, text)`` for each string.
    """
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _strings(item, f"{path}.{key}" if path else str(key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _strings(item, f"{path}[{index}]")


def ats_problems(data: object) -> list[str]:
    """Report what an applicant tracking system may read badly.

    The extension normalises dashes when it renders, so these are advice: the text of the source then reads the same
    in the PDF, the HTML and an ATS parser.

    Args:
        data: The parsed ``cv.yml``.

    Returns:
        One message for each field with a typographic dash, a soft hyphen or a private-use character.
    """
    problems = []
    for path, text in _strings(data):
        if any(dash in text for dash in DASHES):
            problems.append(f"{path} has a typographic dash; use a plain hyphen")
        if SOFT_HYPHEN in text:
            problems.append(f"{path} has a soft hyphen; remove it")
        if PRIVATE_USE.search(text):
            problems.append(f"{path} has a private-use character; an ATS reads it as a box")
    return problems


def load_cv(path: Path) -> dict:
    """Read a CV file.

    Args:
        path: The ``cv.yml`` file.

    Returns:
        The parsed data.

    Raises:
        CvError: If the file is missing or is not a YAML mapping.
    """
    if not path.is_file():
        msg = f"{path} was not found"
        raise CvError(msg)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        msg = f"{path} must hold a mapping"
        raise CvError(msg)
    return data


def check_cv(path: Path) -> list[str]:
    """Validate a CV file and lint it for ATS.

    Args:
        path: The ``cv.yml`` file.

    Returns:
        One message for each problem; empty when the file is valid and clean.
    """
    try:
        data = load_cv(path)
    except CvError as error:
        return [str(error)]
    except yaml.YAMLError as error:
        return [f"{path} is not valid YAML: {error}"]
    return validate_cv(data) + ats_problems(data)
