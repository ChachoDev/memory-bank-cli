"""Command-line entry point: ``memory-bank help | start | sync | reset | hook <event>``."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, Final

from memory_bank import __version__, scaffold
from memory_bank.i18n import YES_ANSWERS, t
from memory_bank.scanner import scan_project

EXIT_OK: Final = 0
EXIT_ERROR: Final = 1
EXIT_USAGE: Final = 2
YES_FLAGS: Final = frozenset({"-y", "--yes"})


class GitCheckError(Exception):
    """Step 0 failed: there is no usable Git repository."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def _error(message: str) -> None:
    print(message, file=sys.stderr)


def require_git_root(start: Path) -> Path:
    """Step 0: return the root of the Git repository containing ``start``, or fail."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as error:
        raise GitCheckError(t("git_missing")) from error
    if result.returncode != 0 or not result.stdout.strip():
        raise GitCheckError(t("not_git_repo", path=start))
    return Path(result.stdout.strip()).resolve()


def _scan(root: Path) -> list[str]:
    print(t("scanning", path=root))
    result = scan_project(str(root))
    stack = result["detected_stack"]
    if stack:
        print(t("stack_detected", stack=", ".join(stack)))
    elif result["has_code"]:
        print(t("code_no_stack"))
    else:
        print(t("no_code"))
    return stack


def cmd_help(_: list[str]) -> int:
    print(t("help", version=__version__))
    return EXIT_OK


def cmd_start(args: list[str]) -> int:
    _reject_options(args, allowed=frozenset())
    root = require_git_root(Path.cwd())
    if scaffold.memory_dir(root).exists():
        _error(t("already_exists", path=scaffold.memory_dir(root)))
        return EXIT_ERROR
    scaffold.create_memory_bank(str(root), _scan(root))
    print(t("start_done"))
    return EXIT_OK


def cmd_sync(args: list[str]) -> int:
    _reject_options(args, allowed=frozenset())
    root = require_git_root(Path.cwd())
    if not scaffold.memory_dir(root).is_dir():
        _error(t("not_initialized", path=root))
        return EXIT_ERROR
    scaffold.sync_memory_bank(str(root), _scan(root))
    print(t("sync_done"))
    return EXIT_OK


def _confirmed(args: list[str]) -> bool:
    if YES_FLAGS & set(args):
        return True
    if not sys.stdin.isatty():
        _error(t("reset_needs_yes"))
        return False
    try:
        answer = input(t("reset_confirm"))
    except EOFError:
        return False
    return answer.strip().lower() in YES_ANSWERS


def cmd_reset(args: list[str]) -> int:
    _reject_options(args, allowed=YES_FLAGS)
    root = require_git_root(Path.cwd())
    _error(t("reset_warning", path=scaffold.memory_dir(root)))
    if not _confirmed(args):
        print(t("reset_aborted"))
        return EXIT_ERROR
    scaffold.reset_memory_bank(str(root), _scan(root))
    print(t("reset_done"))
    return EXIT_OK


def _hook_root() -> Path | None:
    start = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())
    try:
        return require_git_root(start)
    except GitCheckError:
        return None


def _read_payload() -> dict[str, Any]:
    if sys.stdin.isatty():
        return {}
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def cmd_hook(args: list[str]) -> int:
    """Agent hooks: never block the agent because of a memory-bank failure."""
    if len(args) != 1 or args[0] not in {"session-start", "stop"}:
        _error(t("unknown_command", command=" ".join(["hook", *args])))
        return EXIT_USAGE
    root = _hook_root()
    if root is None:
        return EXIT_OK
    if args[0] == "session-start":
        sys.stdout.write(scaffold.session_context(str(root)))
        return EXIT_OK
    try:
        decision = scaffold.stop_decision(str(root), _read_payload())
    except (OSError, subprocess.CalledProcessError):
        return EXIT_OK
    if decision is not None:
        print(json.dumps(decision))
    return EXIT_OK


class UsageError(Exception):
    def __init__(self, option: str) -> None:
        super().__init__(option)
        self.option = option


def _reject_options(args: list[str], allowed: frozenset[str]) -> None:
    for arg in args:
        if arg not in allowed:
            raise UsageError(arg)


COMMANDS: Final[dict[str, Callable[[list[str]], int]]] = {
    "help": cmd_help,
    "-h": cmd_help,
    "--help": cmd_help,
    "start": cmd_start,
    "sync": cmd_sync,
    "reset": cmd_reset,
    "hook": cmd_hook,
}


def run(argv: list[str]) -> int:
    if not argv:
        return cmd_help([])
    if argv[0] == "--version":
        print(__version__)
        return EXIT_OK
    command = COMMANDS.get(argv[0])
    if command is None:
        _error(t("unknown_command", command=argv[0]))
        return EXIT_USAGE
    try:
        return command(argv[1:])
    except GitCheckError as error:
        _error(error.message)
        return EXIT_ERROR
    except UsageError as error:
        _error(t("unknown_option", option=error.option))
        return EXIT_USAGE


def main() -> None:
    sys.exit(run(sys.argv[1:]))


if __name__ == "__main__":
    main()
