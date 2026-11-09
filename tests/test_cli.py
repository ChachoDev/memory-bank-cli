from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
from conftest import commit_all, set_language

from memory_bank import __version__, cli, scaffold


class _Terminal(io.StringIO):
    """A stdin that claims to be an interactive terminal."""

    def isatty(self) -> bool:
        return True


def _stdin(monkeypatch: pytest.MonkeyPatch, text: str, *, tty: bool = False) -> None:
    monkeypatch.setattr("sys.stdin", _Terminal(text) if tty else io.StringIO(text))


# --- Help and usage -------------------------------------------------------------------------


@pytest.mark.parametrize("argv", [[], ["help"], ["-h"], ["--help"]])
def test_help(argv: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.run(argv) == cli.EXIT_OK
    out = capsys.readouterr().out
    assert out.startswith(f"memory-bank {__version__}")
    for command in ("start", "sync", "reset", "help"):
        assert f"  {command}" in out


def test_help_is_translated(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    set_language(monkeypatch, "de")
    cli.run(["help"])
    assert "Verwendung: memory-bank <Befehl>" in capsys.readouterr().out


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.run(["--version"]) == cli.EXIT_OK
    assert capsys.readouterr().out.strip() == __version__


def test_unknown_command(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.run(["deploy"]) == cli.EXIT_USAGE
    assert "Unknown command: deploy" in capsys.readouterr().err


@pytest.mark.parametrize("command", ["start", "sync"])
def test_unknown_option(repo: Path, command: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.run([command, "--force"]) == cli.EXIT_USAGE
    assert "Unknown option: --force" in capsys.readouterr().err


def test_main_exits_with_the_command_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["memory-bank", "deploy"])
    with pytest.raises(SystemExit) as exit_info:
        cli.main()
    assert exit_info.value.code == cli.EXIT_USAGE


# --- Step 0: Git ----------------------------------------------------------------------------


@pytest.mark.parametrize("argv", [["start"], ["sync"], ["reset", "--yes"]])
def test_write_commands_require_git(
    no_repo: Path, argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.run(argv) == cli.EXIT_ERROR
    assert "is not inside a Git repository" in capsys.readouterr().err
    assert not (no_repo / "memory-bank").exists()


def test_git_error_is_translated(
    no_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    set_language(monkeypatch, "fr")
    cli.run(["start"])
    assert "n'est pas dans un dépôt Git" in capsys.readouterr().err


def test_reports_missing_git(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def no_git(*_: object, **__: object) -> Any:
        raise FileNotFoundError("git")

    monkeypatch.setattr(subprocess, "run", no_git)
    assert cli.run(["start"]) == cli.EXIT_ERROR
    assert "Git is not installed" in capsys.readouterr().err


# --- start ----------------------------------------------------------------------------------


def test_start_creates_the_memory_bank(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (repo / "Cargo.toml").write_text("[package]\n")
    assert cli.run(["start"]) == cli.EXIT_OK
    out = capsys.readouterr().out
    assert "Existing code detected. Stack: Rust" in out
    assert "Memory bank ready" in out
    assert (repo / "memory-bank" / "instructions.md").is_file()
    assert (repo / "CLAUDE.md").is_symlink()
    assert "- Rust" in (repo / "memory-bank" / "projectbrief.md").read_text()


def test_start_reports_a_blank_project(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cli.run(["start"])
    assert "No existing code detected" in capsys.readouterr().out


def test_start_from_a_subdirectory_uses_the_repository_root(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sub = repo / "src" / "deep"
    sub.mkdir(parents=True)
    monkeypatch.chdir(sub)
    assert cli.run(["start"]) == cli.EXIT_OK
    assert (repo / "memory-bank").is_dir()
    assert not (sub / "memory-bank").exists()


def test_start_stops_when_the_memory_bank_exists(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    cli.run(["start"])
    (repo / "memory-bank" / "progress.md").write_text("mine\n")
    capsys.readouterr()
    assert cli.run(["start"]) == cli.EXIT_ERROR
    assert "already exists" in capsys.readouterr().err
    assert (repo / "memory-bank" / "progress.md").read_text() == "mine\n"


# --- sync -----------------------------------------------------------------------------------


def test_sync_requires_an_existing_memory_bank(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.run(["sync"]) == cli.EXIT_ERROR
    assert "Run 'memory-bank start' first" in capsys.readouterr().err


def test_sync_repairs_without_losing_notes(repo: Path) -> None:
    cli.run(["start"])
    (repo / "memory-bank" / "activeContext.md").write_text("my focus\n")
    (repo / "memory-bank" / "progress.md").unlink()
    (repo / "CLAUDE.md").unlink()
    assert cli.run(["sync"]) == cli.EXIT_OK
    assert (repo / "memory-bank" / "activeContext.md").read_text() == "my focus\n"
    assert (repo / "memory-bank" / "progress.md").is_file()
    assert (repo / "CLAUDE.md").is_symlink()


# --- reset ----------------------------------------------------------------------------------


@pytest.fixture
def with_notes(repo: Path) -> Path:
    cli.run(["start"])
    (repo / "memory-bank" / "progress.md").write_text("precious\n")
    return repo / "memory-bank" / "progress.md"


def test_reset_needs_confirmation_outside_a_terminal(
    with_notes: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _stdin(monkeypatch, "")
    assert cli.run(["reset"]) == cli.EXIT_ERROR
    err = capsys.readouterr().err
    assert "WARNING" in err
    assert "--yes" in err
    assert with_notes.read_text() == "precious\n"


@pytest.mark.parametrize("answer", ["n\n", "\n", "nope\n", ""])
def test_reset_is_cancelled_unless_confirmed(
    with_notes: Path, monkeypatch: pytest.MonkeyPatch, answer: str
) -> None:
    _stdin(monkeypatch, answer, tty=True)
    assert cli.run(["reset"]) == cli.EXIT_ERROR
    assert with_notes.read_text() == "precious\n"


@pytest.mark.parametrize("answer", ["y\n", "YES\n", "s\n", "sí\n", "oui\n", "ja\n"])
def test_reset_accepts_yes_in_every_language(
    with_notes: Path, monkeypatch: pytest.MonkeyPatch, answer: str
) -> None:
    _stdin(monkeypatch, answer, tty=True)
    assert cli.run(["reset"]) == cli.EXIT_OK
    assert with_notes.read_text() != "precious\n"


@pytest.mark.parametrize("flag", ["--yes", "-y"])
def test_reset_with_yes_flag(with_notes: Path, flag: str) -> None:
    assert cli.run(["reset", flag]) == cli.EXIT_OK
    assert with_notes.read_text() != "precious\n"


# --- hook -----------------------------------------------------------------------------------


def test_hook_session_start_prints_the_memory_bank(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    cli.run(["start"])
    capsys.readouterr()
    assert cli.run(["hook", "session-start"]) == cli.EXIT_OK
    assert "<!-- memory-bank/activeContext.md -->" in capsys.readouterr().out


def test_hook_uses_claude_project_dir(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    cli.run(["start"])
    capsys.readouterr()
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(repo))
    monkeypatch.chdir(tmp_path)
    cli.run(["hook", "session-start"])
    assert "<!-- memory-bank/instructions.md -->" in capsys.readouterr().out


def test_hook_is_silent_outside_git(no_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.run(["hook", "session-start"]) == cli.EXIT_OK
    assert capsys.readouterr() == ("", "")


def test_hook_stop_prints_a_block_decision(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    cli.run(["start"])
    commit_all(repo)
    monkeypatch.setattr(scaffold, "needs_memory_update", lambda _: True)
    _stdin(monkeypatch, json.dumps({"stop_hook_active": False}))
    capsys.readouterr()
    assert cli.run(["hook", "stop"]) == cli.EXIT_OK
    assert json.loads(capsys.readouterr().out)["decision"] == "block"


@pytest.mark.parametrize("payload", ["", "not json", "[1]"])
def test_hook_stop_tolerates_bad_input(
    repo: Path, monkeypatch: pytest.MonkeyPatch, payload: str
) -> None:
    cli.run(["start"])
    _stdin(monkeypatch, payload)
    assert cli.run(["hook", "stop"]) == cli.EXIT_OK


def test_hook_stop_never_fails_the_agent(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def broken(*_: object) -> None:
        raise subprocess.CalledProcessError(128, "git")

    monkeypatch.setattr(scaffold, "stop_decision", broken)
    _stdin(monkeypatch, "{}")
    assert cli.run(["hook", "stop"]) == cli.EXIT_OK
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("argv", [["hook"], ["hook", "nope"], ["hook", "stop", "extra"]])
def test_hook_rejects_unknown_events(argv: list[str]) -> None:
    assert cli.run(argv) == cli.EXIT_USAGE
