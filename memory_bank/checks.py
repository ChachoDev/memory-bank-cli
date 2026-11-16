"""Read-only consistency checks for an existing memory bank.

The memory bank is written by an AI agent, so it can drift: unfilled placeholders, sections that
disappear, a changelog disguised as ``activeContext.md``, references to files that no longer
exist, or "no known issues" while the code is full of TODO markers. These checks catch the cheap,
objective problems. They never modify a file.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from memory_bank import scaffold
from memory_bank.i18n import t
from memory_bank.scanner import IGNORED_DIRS, SOURCE_EXTENSIONS
from memory_bank.templates import INSTRUCTIONS_VERSION, TEMPLATES

ERROR: Final = "error"
WARNING: Final = "warning"
RECENT_CHANGES_LIMIT: Final = 6
MAX_SCANNED_FILES: Final = 500
MAX_FILE_BYTES: Final = 1_000_000

# The whole bank enters every session's context, so its size is a feature, not a detail.
# Roughly 4 characters per token: 12k characters is about 3k tokens for one note and 40k, about
# 10k tokens for the bank, which leaves a wide margin on a 200k window while still catching a
# bank that has turned into a changelog.
NOTE_SIZE_LIMIT: Final = 12_000
BANK_SIZE_LIMIT: Final = 40_000
CHARS_PER_TOKEN: Final = 4

REQUIRED_SECTIONS: Final[dict[str, tuple[str, ...]]] = {
    "projectbrief.md": (
        "## Overview",
        "## Goals",
        "## Core requirements",
        "## Out of scope",
        "## Technology stack",
        "## Constraints",
    ),
    "productContext.md": (
        "## Problem",
        "## Users",
        "## Value proposition",
        "## User experience goals",
        "## How it should work",
    ),
    "activeContext.md": (
        "## Current focus",
        "## Recent changes",
        "## Next steps",
        "## Open questions and blockers",
        "## Active decisions and considerations",
    ),
    "progress.md": (
        "## Current phase",
        "## What works",
        "## What is left to build",
        "## Known issues",
        "## Milestones",
    ),
    "decisionLog.md": ("## ADR-",),
}

# Lines left behind by the templates. They mean "nobody has filled this in yet".
PLACEHOLDERS: Final[tuple[str, ...]] = (
    "_Nothing detected yet._",
    "_One paragraph: what this project is and who it is for._",
    "_Goal 1: the main outcome the project must deliver._",
    "_Goal 2_",
    "_Goal 3_",
    "_Requirement that must hold for the project to be useful._",
    "_Requirement_",
    "_What this project deliberately does not do._",
    "_Deadlines, budgets, platforms, compliance or performance limits._",
    "_What problem does the product solve? What happens today without it?_",
    "_Primary user_",
    "_Their need_",
    "_The answer_",
    "_One or two sentences on why users choose this product._",
    "_Example: a new user completes the main task in under two minutes._",
    "_Example: every error message says what to do next._",
    "_The main user flows, step by step._",
    "_Bootstrapping the memory bank ({{DATE}})._",
    "_Next concrete task._",
    "_None yet._",
    "_Trade-offs being weighed right now. Move settled ones to `decisionLog.md`._",
    "_Feature or task_",
    "_Smallest useful release_",
    "_Correct or complete this list by hand; the agent will keep it up to date._",
)

SECRET_PATTERNS: Final[tuple[tuple[str, re.Pattern[str]], ...]] = (
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("API key", re.compile(r"\b(?:sk|pk)-[A-Za-z0-9]{20,}\b")),
    ("JUNIE_API_KEY", re.compile(r"\bJUNIE_API_KEY\s*=\s*\S+")),
)

REFERENCE_RE: Final = re.compile(
    r"`([A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:md|py|json|jsonc|toml|ya?ml|txt|cfg|ini|sh))`"
)
UNRENDERED_RE: Final = re.compile(r"\{\{[A-Z_]+\}\}")
INSTRUCTIONS_MARKER_RE: Final = re.compile(r"<!-- memory-bank: instructions v(\d+) -->")
DATE_RE: Final = re.compile(r"\*\*Date:\*\*\s*(\S+)")
MARKER_RE: Final = re.compile(r"\b(?:TODO|FIXME|XXX)\b")
ISO_DATE_RE: Final = re.compile(r"\d{4}-\d{2}-\d{2}")
MANAGED_BRIDGES: Final = frozenset(bridge.as_posix() for bridge in scaffold.BRIDGES)

NONE_WORDS: Final = frozenset(
    {
        "",
        "none",
        "none yet",
        "none known",
        "none reported",
        "nothing",
        "nothing known",
        "no known issue",
        "no known issues",
        "no known problem",
        "no known problems",
        "no issue",
        "no issues",
        "no problem",
        "no problems",
        "n/a",
        "na",
    }
)


@dataclass(frozen=True)
class Issue:
    """One problem found in the memory bank."""

    level: str
    message: str

    @property
    def is_error(self) -> bool:
        return self.level == ERROR


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _shown(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _section_body(text: str, heading: str) -> str:
    """Return the lines under ``heading`` until the next level-two heading."""
    body: list[str] = []
    inside = False
    for line in text.splitlines():
        if line.strip() == heading:
            inside = True
            continue
        if inside and line.startswith("## "):
            break
        if inside:
            body.append(line)
    return "\n".join(body)


def _is_generated_copy(path: Path) -> bool:
    try:
        with path.open(encoding="utf-8") as handle:
            return handle.readline() == scaffold.COPY_MARKER
    except (OSError, UnicodeDecodeError):
        return False


def _check_required_files(root: Path) -> list[Issue]:
    directory = scaffold.memory_dir(root)
    issues: list[Issue] = []
    for name in TEMPLATES:
        path = directory / name
        if not path.is_file():
            issues.append(Issue(ERROR, t("check_missing_file", path=_shown(root, path))))
    return issues


def _check_sections(root: Path) -> list[Issue]:
    directory = scaffold.memory_dir(root)
    issues: list[Issue] = []
    for name, sections in REQUIRED_SECTIONS.items():
        path = directory / name
        if not path.is_file():
            continue
        text = _read(path)
        for section in sections:
            if section not in text:
                issues.append(
                    Issue(
                        ERROR,
                        t("check_missing_section", path=_shown(root, path), section=section),
                    )
                )
    return issues


def _check_instructions_version(root: Path) -> list[Issue]:
    """Warn when ``instructions.md`` predates the current agent rules."""
    path = root / scaffold.INSTRUCTIONS_PATH
    if not path.is_file():
        return []
    match = INSTRUCTIONS_MARKER_RE.search(_read(path))
    if match and int(match.group(1)) >= int(INSTRUCTIONS_VERSION):
        return []
    return [Issue(WARNING, t("check_outdated_template", path=_shown(root, path)))]


def _check_unrendered(root: Path) -> list[Issue]:
    directory = scaffold.memory_dir(root)
    issues: list[Issue] = []
    for path in sorted(directory.glob("*.md")):
        for token in sorted(set(UNRENDERED_RE.findall(_read(path)))):
            issues.append(Issue(ERROR, t("check_unrendered", path=_shown(root, path), token=token)))
    return issues


def _check_placeholders(root: Path) -> list[Issue]:
    directory = scaffold.memory_dir(root)
    issues: list[Issue] = []
    for path in sorted(directory.glob("*.md")):
        text = _read(path)
        for marker in PLACEHOLDERS:
            if marker in text:
                issues.append(
                    Issue(WARNING, t("check_placeholder", path=_shown(root, path), text=marker))
                )
                break
    return issues


def _check_recent_changes(root: Path) -> list[Issue]:
    path = scaffold.memory_dir(root) / "activeContext.md"
    if not path.is_file():
        return []
    body = _section_body(_read(path), "## Recent changes")
    count = sum(1 for line in body.splitlines() if line.lstrip().startswith(("- ", "* ")))
    if count <= RECENT_CHANGES_LIMIT:
        return []
    return [
        Issue(
            WARNING,
            t(
                "check_recent_changes",
                path=_shown(root, path),
                count=count,
                max=RECENT_CHANGES_LIMIT,
            ),
        )
    ]


def _check_references(root: Path) -> list[Issue]:
    directory = scaffold.memory_dir(root)
    issues: list[Issue] = []
    seen: set[str] = set()
    for path in sorted(directory.glob("*.md")):
        for match in REFERENCE_RE.finditer(_read(path)):
            ref = match.group(1)
            if ref in seen or ref in MANAGED_BRIDGES:
                continue
            if (root / ref).exists() or (directory / ref).exists():
                continue
            seen.add(ref)
            issues.append(Issue(WARNING, t("check_broken_ref", path=_shown(root, path), ref=ref)))
    return issues


def _is_none(body: str) -> bool:
    normalized = body.strip().strip("-*_.` ").lower()
    return normalized in NONE_WORDS


def _count_code_markers(root: Path) -> int:
    """Count TODO/FIXME/XXX markers in source files, outside managed folders."""
    count = 0
    scanned = 0
    for current, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name not in IGNORED_DIRS]
        for name in files:
            if scanned >= MAX_SCANNED_FILES:
                return count
            path = Path(current) / name
            if path.suffix.lower() not in SOURCE_EXTENSIONS:
                continue
            scanned += 1
            try:
                if path.stat().st_size > MAX_FILE_BYTES:
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            count += len(MARKER_RE.findall(text))
            if count > 20:
                return count
    return count


def _check_known_issues(root: Path) -> list[Issue]:
    path = scaffold.memory_dir(root) / "progress.md"
    if not path.is_file():
        return []
    body = _section_body(_read(path), "## Known issues")
    if not _is_none(body):
        return []
    count = _count_code_markers(root)
    if not count:
        return []
    return [Issue(WARNING, t("check_known_issues", path=_shown(root, path), count=count))]


def _check_bridges(root: Path) -> list[Issue]:
    instructions = (root / scaffold.INSTRUCTIONS_PATH).resolve()
    target = scaffold.INSTRUCTIONS_PATH.as_posix()
    issues: list[Issue] = []
    for bridge in scaffold.BRIDGES:
        link = root / bridge
        shown = bridge.as_posix()
        if link.is_symlink():
            try:
                points_to = (link.parent / os.readlink(link)).resolve()
            except OSError:
                points_to = None
            if points_to != instructions:
                issues.append(Issue(WARNING, t("check_link", link=shown, target=target)))
            continue
        if not link.exists():
            issues.append(Issue(WARNING, t("check_link", link=shown, target=target)))
            continue
        if not _is_generated_copy(link):
            issues.append(Issue(WARNING, t("check_foreign_link", link=shown, target=target)))
    return issues


def _check_secrets(root: Path) -> list[Issue]:
    directory = scaffold.memory_dir(root)
    issues: list[Issue] = []
    for path in sorted(directory.glob("*.md")):
        text = _read(path)
        for kind, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                issues.append(Issue(ERROR, t("check_secret", path=_shown(root, path), kind=kind)))
                break
    return issues


def _check_dates(root: Path) -> list[Issue]:
    path = scaffold.memory_dir(root) / "decisionLog.md"
    if not path.is_file():
        return []
    issues: list[Issue] = []
    seen: set[str] = set()
    for line in _read(path).splitlines():
        match = DATE_RE.search(line)
        if not match:
            continue
        value = match.group(1)
        if ISO_DATE_RE.fullmatch(value) or value in seen:
            continue
        seen.add(value)
        issues.append(Issue(WARNING, t("check_date", path=_shown(root, path), value=value)))
    return issues


def _check_sizes(root: Path) -> list[Issue]:
    """Warn when a note, or the whole bank, is large enough to weigh on the context."""
    directory = scaffold.memory_dir(root)
    issues: list[Issue] = []
    total = 0
    for path in sorted(directory.glob("*.md")):
        size = len(_read(path))
        total += size
        if size <= NOTE_SIZE_LIMIT:
            continue
        issues.append(
            Issue(
                WARNING,
                t(
                    "check_large_note",
                    path=_shown(root, path),
                    size=size,
                    tokens=size // CHARS_PER_TOKEN,
                    max=NOTE_SIZE_LIMIT,
                ),
            )
        )
    if total > BANK_SIZE_LIMIT:
        issues.append(
            Issue(
                WARNING,
                t(
                    "check_large_bank",
                    size=total,
                    tokens=total // CHARS_PER_TOKEN,
                    max=BANK_SIZE_LIMIT,
                ),
            )
        )
    return issues


def run_checks(project_root: str) -> list[Issue]:
    """Return every consistency problem found in the memory bank, errors first."""
    root = Path(project_root).resolve()
    issues: list[Issue] = []
    issues += _check_required_files(root)
    issues += _check_sections(root)
    issues += _check_instructions_version(root)
    issues += _check_unrendered(root)
    issues += _check_placeholders(root)
    issues += _check_recent_changes(root)
    issues += _check_references(root)
    issues += _check_known_issues(root)
    issues += _check_bridges(root)
    issues += _check_secrets(root)
    issues += _check_dates(root)
    issues += _check_sizes(root)
    return sorted(issues, key=lambda issue: not issue.is_error)
