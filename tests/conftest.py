"""Shared fixtures: an isolated Git repository and a deterministic language."""

from __future__ import annotations

import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from memory_bank import i18n

LOCALE_VARS = ("MEMORY_BANK_LANG", "LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE")


def git(root: Path, *args: str) -> str:
    """Run git in ``root`` with a fixed identity and no user hooks."""
    result = subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def commit_all(root: Path) -> None:
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "snapshot")


def set_language(monkeypatch: pytest.MonkeyPatch, language: str) -> None:
    monkeypatch.setenv("MEMORY_BANK_LANG", language)
    i18n.detect_language.cache_clear()


@pytest.fixture(autouse=True)
def english(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Every test starts in English, whatever the developer's locale is."""
    for var in LOCALE_VARS:
        monkeypatch.delenv(var, raising=False)
    set_language(monkeypatch, "en")
    yield
    i18n.detect_language.cache_clear()


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An empty Git repository, also the current directory."""
    root = (tmp_path / "project").resolve()
    root.mkdir()
    git(root, "init", "-q")
    monkeypatch.chdir(root)
    return root


@pytest.fixture
def no_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A directory outside any Git repository, also the current directory."""
    root = (tmp_path / "plain").resolve()
    root.mkdir()
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.resolve()))
    monkeypatch.chdir(root)
    return root
