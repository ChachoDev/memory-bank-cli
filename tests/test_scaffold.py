from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
from typing import Any

import pytest
from conftest import commit_all, git

from memory_bank import scaffold
from memory_bank.templates import TEMPLATES

INSTRUCTIONS = Path("memory-bank") / "instructions.md"


def _messages() -> tuple[list[str], scaffold.Log]:
    lines: list[str] = []
    return lines, lines.append


def _settings(root: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((root / ".claude" / "settings.json").read_text())
    return data


def _commands(settings: dict[str, Any], event: str) -> list[str]:
    return [hook["command"] for group in settings["hooks"][event] for hook in group["hooks"]]


def _deny_symlinks(monkeypatch: pytest.MonkeyPatch) -> None:
    def deny(*_: object, **__: object) -> None:
        raise OSError("symlinks are not permitted")

    monkeypatch.setattr(os, "symlink", deny)


# --- Markdown files -------------------------------------------------------------------------


def test_creates_every_template_with_stack_and_date(repo: Path) -> None:
    scaffold.create_memory_bank(str(repo), ["Rust"], log=lambda _: None)
    for name in TEMPLATES:
        assert (repo / "memory-bank" / name).is_file()
    assert "- Rust" in (repo / "memory-bank" / "projectbrief.md").read_text()
    today = dt.date.today().isoformat()
    assert today in (repo / "memory-bank" / "activeContext.md").read_text()


def test_never_overwrites_an_existing_note(repo: Path) -> None:
    (repo / "memory-bank").mkdir()
    (repo / "memory-bank" / "progress.md").write_text("my progress\n")
    lines, log = _messages()
    scaffold.create_memory_bank(str(repo), [], log=log)
    assert (repo / "memory-bank" / "progress.md").read_text() == "my progress\n"
    assert "  = kept memory-bank/progress.md" in lines


# --- Links ----------------------------------------------------------------------------------


@pytest.mark.parametrize("bridge", scaffold.BRIDGES)
def test_links_point_relatively_to_instructions(repo: Path, bridge: Path) -> None:
    scaffold.create_memory_bank(str(repo), [], log=lambda _: None)
    link = repo / bridge
    assert link.is_symlink()
    assert not os.path.isabs(os.readlink(link))
    assert link.resolve() == (repo / INSTRUCTIONS).resolve()


def test_links_survive_moving_the_repository(repo: Path) -> None:
    scaffold.create_memory_bank(str(repo), [], log=lambda _: None)
    moved = repo.rename(repo.parent / "moved")
    assert (moved / "CLAUDE.md").read_text() == (moved / INSTRUCTIONS).read_text()


def test_leaves_a_foreign_file_untouched(repo: Path) -> None:
    (repo / "CLAUDE.md").write_text("# my rules\n")
    lines, log = _messages()
    scaffold.create_memory_bank(str(repo), [], log=log)
    assert (repo / "CLAUDE.md").read_text() == "# my rules\n"
    assert any(line.startswith("  ! CLAUDE.md exists") for line in lines)


def test_leaves_a_foreign_symlink_untouched(repo: Path) -> None:
    (repo / "elsewhere.md").write_text("other\n")
    (repo / ".cursorrules").symlink_to("elsewhere.md")
    scaffold.create_memory_bank(str(repo), [], log=lambda _: None)
    assert os.readlink(repo / ".cursorrules") == "elsewhere.md"


def test_writes_marked_copies_when_symlinks_are_denied(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _deny_symlinks(monkeypatch)
    scaffold.create_memory_bank(str(repo), [], log=lambda _: None)
    copy = repo / "CLAUDE.md"
    assert not copy.is_symlink()
    content = copy.read_text()
    assert content.startswith(scaffold.COPY_MARKER)
    assert content.endswith((repo / INSTRUCTIONS).read_text())


def test_sync_refreshes_copies_after_instructions_change(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _deny_symlinks(monkeypatch)
    scaffold.create_memory_bank(str(repo), [], log=lambda _: None)
    with (repo / INSTRUCTIONS).open("a") as handle:
        handle.write("\nNEW RULE\n")
    lines, log = _messages()
    scaffold.sync_memory_bank(str(repo), [], log=log)
    assert (repo / ".cursorrules").read_text().endswith("NEW RULE\n")
    assert "  ~ refreshed the copy .cursorrules" in lines


def test_sync_recreates_a_deleted_link(repo: Path) -> None:
    scaffold.create_memory_bank(str(repo), [], log=lambda _: None)
    (repo / "CLAUDE.md").unlink()
    scaffold.sync_memory_bank(str(repo), [], log=lambda _: None)
    assert (repo / "CLAUDE.md").is_symlink()


# --- Hook configuration ---------------------------------------------------------------------


def test_configures_claude_code_hooks(repo: Path) -> None:
    scaffold.create_memory_bank(str(repo), [], log=lambda _: None)
    settings = _settings(repo)
    assert _commands(settings, "SessionStart") == ["memory-bank hook session-start"]
    assert _commands(settings, "Stop") == ["memory-bank hook stop"]


def test_merges_hooks_into_existing_settings(repo: Path) -> None:
    (repo / ".claude").mkdir()
    existing = {
        "model": "opus",
        "hooks": {
            "Stop": [{"hooks": [{"type": "command", "command": "./notify.sh"}]}],
            "SessionStart": [{"hooks": [{"type": "command", "command": "memory-bank hook old"}]}],
        },
    }
    (repo / ".claude" / "settings.json").write_text(json.dumps(existing))
    scaffold.create_memory_bank(str(repo), [], log=lambda _: None)
    settings = _settings(repo)
    assert settings["model"] == "opus"
    assert _commands(settings, "Stop") == ["./notify.sh", "memory-bank hook stop"]
    assert _commands(settings, "SessionStart") == ["memory-bank hook session-start"]


def test_hook_configuration_is_idempotent(repo: Path) -> None:
    scaffold.create_memory_bank(str(repo), [], log=lambda _: None)
    before = (repo / ".claude" / "settings.json").read_text()
    lines, log = _messages()
    scaffold.sync_memory_bank(str(repo), [], log=log)
    assert (repo / ".claude" / "settings.json").read_text() == before
    assert "  = hooks up to date in .claude/settings.json" in lines


@pytest.mark.parametrize("content", ["{not json", "[1, 2]", '{"hooks": []}'])
def test_leaves_invalid_settings_untouched(repo: Path, content: str) -> None:
    (repo / ".claude").mkdir()
    (repo / ".claude" / "settings.json").write_text(content)
    lines, log = _messages()
    scaffold.create_memory_bank(str(repo), [], log=log)
    assert (repo / ".claude" / "settings.json").read_text() == content
    assert any(line.startswith("  ! .claude/settings.json is not valid JSON") for line in lines)


def test_configures_opencode_instructions(repo: Path) -> None:
    (repo / "opencode.json").write_text(json.dumps({"instructions": ["CONTRIBUTING.md"]}))
    scaffold.create_memory_bank(str(repo), [], log=lambda _: None)
    config = json.loads((repo / "opencode.json").read_text())
    assert config["instructions"] == ["CONTRIBUTING.md", "memory-bank/*.md"]
    assert config["$schema"] == scaffold.OPENCODE_SCHEMA


def test_does_not_edit_opencode_jsonc(repo: Path) -> None:
    (repo / "opencode.jsonc").write_text("{ // comment\n}\n")
    lines, log = _messages()
    scaffold.create_memory_bank(str(repo), [], log=log)
    assert not (repo / "opencode.json").exists()
    assert (repo / "opencode.jsonc").read_text() == "{ // comment\n}\n"
    assert any(line.startswith("  ! opencode.jsonc found") for line in lines)


# --- Reset ----------------------------------------------------------------------------------


def test_reset_discards_notes_and_regenerates(repo: Path) -> None:
    scaffold.create_memory_bank(str(repo), [], log=lambda _: None)
    (repo / "memory-bank" / "progress.md").write_text("old notes\n")
    (repo / "memory-bank" / "extra.md").write_text("extra\n")
    scaffold.reset_memory_bank(str(repo), [], log=lambda _: None)
    assert (repo / "memory-bank" / "progress.md").read_text() != "old notes\n"
    assert not (repo / "memory-bank" / "extra.md").exists()


def test_reset_works_without_an_existing_memory_bank(repo: Path) -> None:
    scaffold.reset_memory_bank(str(repo), [], log=lambda _: None)
    assert (repo / INSTRUCTIONS).is_file()


# --- Hook runtime ---------------------------------------------------------------------------


def test_session_context_is_empty_without_a_memory_bank(repo: Path) -> None:
    assert scaffold.session_context(str(repo)) == ""


def test_session_context_includes_every_file_in_reading_order(repo: Path) -> None:
    scaffold.create_memory_bank(str(repo), [], log=lambda _: None)
    (repo / "memory-bank" / "apiNotes.md").write_text("# API notes\n")
    context = scaffold.session_context(str(repo))
    order = [
        "instructions.md",
        "projectbrief.md",
        "productContext.md",
        "activeContext.md",
        "progress.md",
        "decisionLog.md",
        "apiNotes.md",
    ]
    positions = [context.index(f"<!-- memory-bank/{name} -->") for name in order]
    assert positions == sorted(positions)


@pytest.fixture
def committed(repo: Path) -> Path:
    """A repository with code and a memory bank, all committed."""
    (repo / "app.py").write_text("print(1)\n")
    scaffold.create_memory_bank(str(repo), [], log=lambda _: None)
    commit_all(repo)
    return repo


def _age(root: Path, relative: str, seconds: float) -> None:
    """Make ``relative`` look ``seconds`` older than now."""
    stamp = dt.datetime.now().timestamp() - seconds
    os.utime(root / relative, (stamp, stamp))


def _age_memory(root: Path, seconds: float) -> None:
    for name in scaffold.TRACKED_FILES:
        _age(root, name, seconds)


def test_stop_allows_a_clean_tree(committed: Path) -> None:
    assert scaffold.stop_decision(str(committed), {}) is None


def test_stop_blocks_when_code_is_newer_than_memory(committed: Path) -> None:
    _age_memory(committed, 60)
    (committed / "app.py").write_text("print(2)\n")
    decision = scaffold.stop_decision(str(committed), {"stop_hook_active": False})
    assert decision == {"decision": "block", "reason": scaffold.STOP_REASON}


def test_stop_blocks_for_new_untracked_files(committed: Path) -> None:
    _age_memory(committed, 60)
    (committed / "pkg").mkdir()
    (committed / "pkg" / "new.py").write_text("x = 1\n")
    assert scaffold.stop_decision(str(committed), {}) is not None


def test_stop_never_blocks_twice_in_a_turn(committed: Path) -> None:
    _age_memory(committed, 60)
    (committed / "app.py").write_text("print(2)\n")
    assert scaffold.stop_decision(str(committed), {"stop_hook_active": True}) is None


def test_stop_allows_once_memory_is_updated(committed: Path) -> None:
    (committed / "app.py").write_text("print(2)\n")
    _age(committed, "app.py", 60)
    assert scaffold.stop_decision(str(committed), {}) is None


def test_stop_blocks_when_only_one_memory_file_was_updated(committed: Path) -> None:
    _age(committed, "memory-bank/progress.md", 120)
    (committed / "app.py").write_text("print(2)\n")
    _age(committed, "app.py", 60)
    assert scaffold.stop_decision(str(committed), {}) is not None


def test_stop_ignores_changes_to_managed_files(committed: Path) -> None:
    _age_memory(committed, 60)
    (committed / "memory-bank" / "decisionLog.md").write_text("# Decisions\n")
    (committed / "opencode.json").write_text("{}\n")
    assert scaffold.stop_decision(str(committed), {}) is None


def test_stop_handles_renamed_files(committed: Path) -> None:
    _age_memory(committed, 60)
    git(committed, "mv", "app.py", "main.py")
    assert scaffold.stop_decision(str(committed), {}) is not None


def test_stop_allows_when_there_is_no_memory_bank(repo: Path) -> None:
    (repo / "app.py").write_text("print(1)\n")
    assert scaffold.stop_decision(str(repo), {}) is None
