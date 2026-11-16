from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest
from conftest import git

from memory_bank import cli, scaffold

HOOK = Path(".git") / "hooks" / "pre-commit"
posix_only = pytest.mark.skipif(os.name == "nt", reason="the managed hook is a POSIX shell script")


def _hook(repo: Path) -> Path:
    return repo / HOOK


def _bin_dir(base: Path) -> Path:
    """An isolated PATH that always finds git and nothing else."""
    bin_dir = base / "bin"
    bin_dir.mkdir()
    executable = shutil.which("git")
    assert executable is not None
    (bin_dir / "git").symlink_to(executable)
    return bin_dir


def _fake_binary(base: Path, status: int, message: str = "") -> Path:
    bin_dir = _bin_dir(base)
    tool = bin_dir / "memory-bank"
    body = f'echo "{message}"\n' if message else ""
    tool.write_text(f"#!/bin/sh\n{body}exit {status}\n", encoding="utf-8")
    tool.chmod(0o755)
    return bin_dir


def _run_hook(repo: Path, bin_dir: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PATH"] = str(bin_dir)
    return subprocess.run(
        ["/bin/sh", str(_hook(repo))],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def _install(repo: Path) -> bool:
    return scaffold.install_git_hooks(str(repo), log=lambda _: None)


# --- start and the explicit command ---------------------------------------------------------


def test_start_installs_the_git_hook(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.run(["start"]) == cli.EXIT_OK
    hook = _hook(repo)
    assert hook.is_file()
    assert scaffold.GIT_HOOK_MARKER in hook.read_text(encoding="utf-8")
    if os.name != "nt":
        assert os.access(hook, os.X_OK)
    assert "installed the Git pre-commit hook" in capsys.readouterr().out


def test_start_keeps_a_foreign_hook(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    hook = _hook(repo)
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\necho mine\n", encoding="utf-8")
    assert cli.run(["start"]) == cli.EXIT_OK
    assert hook.read_text(encoding="utf-8") == "#!/bin/sh\necho mine\n"
    assert "not managed by memory-bank" in capsys.readouterr().out


def test_install_is_idempotent(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert _install(repo)
    capsys.readouterr()
    assert cli.run(["git-hooks", "install"]) == cli.EXIT_OK
    assert "is up to date" in capsys.readouterr().out


def test_install_refreshes_an_outdated_managed_hook(repo: Path) -> None:
    hook = _hook(repo)
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(f"#!/bin/sh\n{scaffold.GIT_HOOK_MARKER}\nexit 0\n", encoding="utf-8")
    assert _install(repo)
    content = hook.read_text(encoding="utf-8")
    assert "--strict" not in content
    assert "memory-bank check" in content


def test_install_refuses_a_custom_hooks_path(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    git(repo, "config", "core.hooksPath", ".husky")
    assert cli.run(["git-hooks", "install"]) == cli.EXIT_ERROR
    assert not (repo / ".husky" / "pre-commit").exists()
    assert "custom hooks path" in capsys.readouterr().out


def test_uninstall_removes_the_managed_hook(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert _install(repo)
    capsys.readouterr()
    assert cli.run(["git-hooks", "uninstall"]) == cli.EXIT_OK
    assert not _hook(repo).exists()
    assert "removed the Git pre-commit hook" in capsys.readouterr().out


def test_uninstall_leaves_a_foreign_hook(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    hook = _hook(repo)
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\necho mine\n", encoding="utf-8")
    assert cli.run(["git-hooks", "uninstall"]) == cli.EXIT_OK
    assert hook.read_text(encoding="utf-8") == "#!/bin/sh\necho mine\n"
    assert "not managed by memory-bank" in capsys.readouterr().out


def test_uninstall_when_absent(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.run(["git-hooks", "uninstall"]) == cli.EXIT_OK
    assert "no memory-bank Git hook" in capsys.readouterr().out


def test_git_hooks_requires_git(no_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.run(["git-hooks", "install"]) == cli.EXIT_ERROR
    assert "is not inside a Git repository" in capsys.readouterr().err


@pytest.mark.parametrize(
    "argv", [["git-hooks"], ["git-hooks", "status"], ["git-hooks", "install", "x"]]
)
def test_git_hooks_rejects_unknown_subcommands(argv: list[str]) -> None:
    assert cli.run(argv) == cli.EXIT_USAGE


def test_sync_does_not_install_the_git_hook(repo: Path) -> None:
    assert cli.run(["start"]) == cli.EXIT_OK
    assert cli.run(["git-hooks", "uninstall"]) == cli.EXIT_OK
    assert cli.run(["sync"]) == cli.EXIT_OK
    assert not _hook(repo).exists()


# --- the managed script ---------------------------------------------------------------------


@posix_only
def test_the_hook_blocks_when_check_fails(repo: Path) -> None:
    scaffold.create_memory_bank(str(repo), [], log=lambda _: None)
    assert _install(repo)
    result = _run_hook(repo, _fake_binary(repo.parent, 1))
    assert result.returncode == 1
    assert "commit blocked" in result.stderr


@posix_only
def test_the_hook_is_silent_when_check_passes(repo: Path) -> None:
    scaffold.create_memory_bank(str(repo), [], log=lambda _: None)
    assert _install(repo)
    result = _run_hook(repo, _fake_binary(repo.parent, 0))
    assert result.returncode == 0
    assert result.stderr == ""


@posix_only
def test_the_hook_hides_warnings_when_check_passes(repo: Path) -> None:
    scaffold.create_memory_bank(str(repo), [], log=lambda _: None)
    assert _install(repo)
    result = _run_hook(repo, _fake_binary(repo.parent, 0, "warning: a placeholder"))
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


@posix_only
def test_the_hook_shows_the_errors_when_it_blocks(repo: Path) -> None:
    scaffold.create_memory_bank(str(repo), [], log=lambda _: None)
    assert _install(repo)
    result = _run_hook(repo, _fake_binary(repo.parent, 1, "error: a missing file"))
    assert result.returncode == 1
    assert "error: a missing file" in result.stderr
    assert "commit blocked" in result.stderr


@posix_only
def test_the_hook_allows_the_commit_when_check_fails_unexpectedly(repo: Path) -> None:
    scaffold.create_memory_bank(str(repo), [], log=lambda _: None)
    assert _install(repo)
    result = _run_hook(repo, _fake_binary(repo.parent, 3))
    assert result.returncode == 0
    assert "unexpectedly" in result.stderr


@posix_only
def test_the_hook_does_nothing_without_a_memory_bank(repo: Path) -> None:
    assert _install(repo)
    result = _run_hook(repo, _fake_binary(repo.parent, 1))
    assert result.returncode == 0
    assert result.stderr == ""


@posix_only
def test_the_hook_does_nothing_without_the_binary(repo: Path) -> None:
    scaffold.create_memory_bank(str(repo), [], log=lambda _: None)
    assert _install(repo)
    result = _run_hook(repo, _bin_dir(repo.parent))
    assert result.returncode == 0
    assert result.stderr == ""
