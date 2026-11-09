"""Create and repair the memory bank: Markdown files, agent links and lifecycle hooks.

Everything here is idempotent and never overwrites user content:

- Markdown files are written only when missing.
- A link location that already holds a file not created by memory-bank is left untouched.
- Hook configuration is merged into existing JSON files; other settings are kept.

Hooks per agent:

- Claude Code (``.claude/settings.json``): ``SessionStart`` runs ``memory-bank hook
  session-start``, whose output Claude Code adds to the context (on_session_start). ``Stop`` runs
  ``memory-bank hook stop``, which makes the agent update ``activeContext.md`` and
  ``progress.md`` when code changed after their last update (on_tool_call / on_session_end).
- OpenCode (``opencode.json``): ``instructions`` loads ``memory-bank/*.md`` into every session.
- Cursor, Pi and any tool reading ``CLAUDE.md`` or ``.cursorrules``: the links to
  ``instructions.md`` carry the read-first / update-last rules.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any, Final

from memory_bank.i18n import t
from memory_bank.templates import INSTRUCTIONS_FILE, READ_ORDER, TEMPLATES, render

Log = Callable[[str], None]

MEMORY_DIR: Final = "memory-bank"
INSTRUCTIONS_PATH: Final = Path(MEMORY_DIR) / INSTRUCTIONS_FILE
BRIDGES: Final[tuple[Path, ...]] = (
    Path(".cursorrules"),
    Path("CLAUDE.md"),
    Path(".opencode") / "rules" / "memory.md",
)
COPY_MARKER: Final = (
    "<!-- memory-bank: copy of memory-bank/instructions.md. "
    "Edit that file and run 'memory-bank sync'. -->\n"
)

CLAUDE_SETTINGS: Final = Path(".claude") / "settings.json"
HOOK_PREFIX: Final = "memory-bank hook "
CLAUDE_HOOKS: Final[dict[str, str]] = {
    "SessionStart": "memory-bank hook session-start",
    "Stop": "memory-bank hook stop",
}

OPENCODE_CONFIG: Final = Path("opencode.json")
OPENCODE_JSONC: Final = Path("opencode.jsonc")
OPENCODE_SCHEMA: Final = "https://opencode.ai/config.json"
OPENCODE_INSTRUCTION: Final = f"{MEMORY_DIR}/*.md"

TRACKED_FILES: Final = frozenset({f"{MEMORY_DIR}/activeContext.md", f"{MEMORY_DIR}/progress.md"})
STOP_REASON: Final = (
    "Code changed after memory-bank/activeContext.md and memory-bank/progress.md were last "
    "updated. Update both files now (current focus, dated recent changes, next steps, what works "
    "and what is left), add an entry to memory-bank/decisionLog.md if you took an architectural "
    "decision, then finish."
)


class InvalidConfigError(ValueError):
    """An existing agent configuration file cannot be merged safely."""


def memory_dir(root: Path) -> Path:
    return root / MEMORY_DIR


# --- Markdown files -------------------------------------------------------------------------


def write_templates(root: Path, detected_stack: list[str], log: Log = print) -> None:
    """Write every template that does not exist yet."""
    directory = memory_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    for name, template in TEMPLATES.items():
        path = directory / name
        relative = path.relative_to(root).as_posix()
        if path.exists():
            log(t("file_kept", path=relative))
            continue
        path.write_text(render(template, detected_stack, today), encoding="utf-8")
        log(t("file_created", path=relative))


# --- Links to instructions.md ---------------------------------------------------------------


def _copy_content(root: Path) -> str:
    return COPY_MARKER + (root / INSTRUCTIONS_PATH).read_text(encoding="utf-8")


def _is_generated_copy(path: Path) -> bool:
    try:
        with path.open(encoding="utf-8") as handle:
            return handle.readline() == COPY_MARKER
    except (OSError, UnicodeDecodeError):
        return False


def _points_to_instructions(link: Path, root: Path) -> bool:
    target = (root / INSTRUCTIONS_PATH).resolve()
    return (link.parent / os.readlink(link)).resolve() == target


def ensure_bridge(root: Path, relative_link: Path, log: Log = print) -> None:
    """Make ``relative_link`` a symlink to instructions.md, or a marked copy as fallback."""
    link = root / relative_link
    shown = relative_link.as_posix()
    target = os.path.relpath(root / INSTRUCTIONS_PATH, link.parent)
    if link.is_symlink():
        if _points_to_instructions(link, root):
            log(t("link_ok", link=shown, target=INSTRUCTIONS_PATH.as_posix()))
        else:
            log(t("link_foreign", link=shown, target=INSTRUCTIONS_PATH.as_posix()))
        return
    if link.exists():
        if not _is_generated_copy(link):
            log(t("link_foreign", link=shown, target=INSTRUCTIONS_PATH.as_posix()))
            return
        content = _copy_content(root)
        if link.read_text(encoding="utf-8") != content:
            link.write_text(content, encoding="utf-8")
            log(t("link_refreshed", link=shown))
        else:
            log(t("link_ok", link=shown, target=INSTRUCTIONS_PATH.as_posix()))
        return
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(target, link)
        log(t("link_created", link=shown, target=target))
    except (OSError, NotImplementedError):
        # Windows without Developer Mode, some network drives and sandboxes forbid symlinks.
        link.write_text(_copy_content(root), encoding="utf-8")
        log(t("link_copied", link=shown, target=INSTRUCTIONS_PATH.as_posix()))


def ensure_bridges(root: Path, log: Log = print) -> None:
    for bridge in BRIDGES:
        ensure_bridge(root, bridge, log)


# --- Hook configuration ---------------------------------------------------------------------


def _load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise InvalidConfigError(str(path)) from error
    if not isinstance(data, dict):
        raise InvalidConfigError(str(path))
    return data


def _expect_list(value: Any, path: Path) -> list[Any]:
    if not isinstance(value, list):
        raise InvalidConfigError(str(path))
    return value


def _merge_claude_hooks(settings: dict[str, Any], path: Path) -> None:
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise InvalidConfigError(str(path))
    for event, command in CLAUDE_HOOKS.items():
        groups = _expect_list(hooks.setdefault(event, []), path)
        found = False
        for group in groups:
            if not isinstance(group, dict):
                raise InvalidConfigError(str(path))
            for hook in _expect_list(group.get("hooks", []), path):
                current = hook.get("command") if isinstance(hook, dict) else None
                if isinstance(current, str) and current.startswith(HOOK_PREFIX):
                    hook["command"] = command  # repairs an outdated command
                    found = True
        if not found:
            groups.append({"hooks": [{"type": "command", "command": command}]})


def _merge_opencode(config: dict[str, Any], path: Path) -> None:
    config.setdefault("$schema", OPENCODE_SCHEMA)
    instructions = _expect_list(config.setdefault("instructions", []), path)
    if OPENCODE_INSTRUCTION not in instructions:
        instructions.append(OPENCODE_INSTRUCTION)


def _update_json(
    root: Path, relative: Path, merge: Callable[[dict[str, Any], Path], None], log: Log
) -> None:
    path = root / relative
    shown = relative.as_posix()
    try:
        data = _load_json_object(path)
        before = json.dumps(data, sort_keys=True)
        merge(data, path)
    except InvalidConfigError:
        log(t("config_invalid", path=shown))
        return
    if path.exists() and json.dumps(data, sort_keys=True) == before:
        log(t("hooks_ok", path=shown))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    log(t("hooks_written", path=shown))


def configure_hooks(root: Path, log: Log = print) -> None:
    """Install or repair the agent lifecycle hooks."""
    _update_json(root, CLAUDE_SETTINGS, _merge_claude_hooks, log)
    if (root / OPENCODE_JSONC).exists() and not (root / OPENCODE_CONFIG).exists():
        log(t("jsonc_skipped", path=OPENCODE_JSONC.as_posix()))
    else:
        _update_json(root, OPENCODE_CONFIG, _merge_opencode, log)


# --- Public commands ------------------------------------------------------------------------


def create_memory_bank(
    project_root: str, detected_stack: list[str] | None = None, log: Log = print
) -> None:
    """Create the memory bank files, the agent links and the hooks."""
    root = Path(project_root).resolve()
    write_templates(root, detected_stack or [], log)
    ensure_bridges(root, log)
    configure_hooks(root, log)


def sync_memory_bank(
    project_root: str, detected_stack: list[str] | None = None, log: Log = print
) -> None:
    """Repair missing files, broken links and outdated hooks; never touches existing notes."""
    create_memory_bank(project_root, detected_stack, log)


def reset_memory_bank(
    project_root: str, detected_stack: list[str] | None = None, log: Log = print
) -> None:
    """Delete memory-bank/ and regenerate everything from scratch."""
    root = Path(project_root).resolve()
    if memory_dir(root).exists():
        shutil.rmtree(memory_dir(root))
    create_memory_bank(str(root), detected_stack, log)


# --- Hook runtime ---------------------------------------------------------------------------


def session_context(project_root: str) -> str:
    """Return the memory bank as one Markdown document, in reading order."""
    directory = memory_dir(Path(project_root))
    if not directory.is_dir():
        return ""
    names = list(READ_ORDER) + sorted(
        p.name for p in directory.glob("*.md") if p.name not in READ_ORDER
    )
    sections = [
        "# Memory Bank (loaded automatically at session start; do not read it again)",
    ]
    for name in names:
        path = directory / name
        if path.is_file():
            content = path.read_text(encoding="utf-8").strip()
            sections.append(f"<!-- {MEMORY_DIR}/{name} -->\n{content}")
    return "\n\n".join(sections) + "\n"


def _changed_paths(root: Path) -> list[str]:
    """Paths with uncommitted changes, from ``git status``."""
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    entries = result.stdout.split("\0")
    paths: list[str] = []
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if len(entry) < 4:
            continue
        paths.append(entry[3:])
        if "R" in entry[:2] or "C" in entry[:2]:
            index += 1  # skip the original path of a rename or copy
    return paths


def _is_memory_file(path: str) -> bool:
    managed = {b.as_posix() for b in BRIDGES} | {
        CLAUDE_SETTINGS.as_posix(),
        OPENCODE_CONFIG.as_posix(),
    }
    return path.startswith(f"{MEMORY_DIR}/") or path in managed


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def needs_memory_update(project_root: str) -> bool:
    """True when a changed code file is newer than activeContext.md or progress.md."""
    root = Path(project_root)
    if not memory_dir(root).is_dir():
        return False
    code = [p for p in _changed_paths(root) if not _is_memory_file(p)]
    if not code:
        return False
    newest_code = max(_mtime(root / p) for p in code)
    oldest_memory = min(_mtime(root / p) for p in TRACKED_FILES)
    return newest_code > oldest_memory


def stop_decision(project_root: str, payload: dict[str, Any]) -> dict[str, str] | None:
    """Claude Code Stop hook: block once so the agent updates the memory bank."""
    if payload.get("stop_hook_active"):
        return None  # the agent already got one reminder in this turn; avoid loops
    if not needs_memory_update(project_root):
        return None
    return {"decision": "block", "reason": STOP_REASON}
