from __future__ import annotations

from pathlib import Path

import pytest
from conftest import clean_memory_bank

from memory_bank import checks, scaffold


def _start(repo: Path) -> None:
    scaffold.create_memory_bank(str(repo), [], log=lambda _: None)


def _messages(repo: Path) -> list[str]:
    return [issue.message for issue in checks.run_checks(str(repo))]


def _has_error(repo: Path, needle: str) -> bool:
    return any(issue.is_error and needle in issue.message for issue in checks.run_checks(str(repo)))


def _has_warning(repo: Path, needle: str) -> bool:
    return any(
        not issue.is_error and needle in issue.message for issue in checks.run_checks(str(repo))
    )


def test_a_fresh_scaffold_has_no_errors_only_placeholder_warnings(repo: Path) -> None:
    _start(repo)
    issues = checks.run_checks(str(repo))
    assert issues
    assert all(not issue.is_error for issue in issues)
    assert any("placeholder" in issue.message for issue in issues)


def test_a_clean_memory_bank_passes(repo: Path) -> None:
    _start(repo)
    clean_memory_bank(repo)
    assert checks.run_checks(str(repo)) == []


def test_a_missing_file_is_an_error(repo: Path) -> None:
    _start(repo)
    clean_memory_bank(repo)
    (repo / "memory-bank" / "progress.md").unlink()
    assert _has_error(repo, "progress.md")


def test_a_missing_section_is_an_error(repo: Path) -> None:
    _start(repo)
    clean_memory_bank(repo)
    path = repo / "memory-bank" / "projectbrief.md"
    path.write_text(path.read_text().replace("## Constraints", "## Limits"), encoding="utf-8")
    assert _has_error(repo, "'## Constraints'")


def test_an_unfilled_placeholder_is_a_warning(repo: Path) -> None:
    _start(repo)
    clean_memory_bank(repo)
    path = repo / "memory-bank" / "progress.md"
    path.write_text(path.read_text() + "\n- _Feature or task_\n", encoding="utf-8")
    assert _has_warning(repo, "placeholder")


def test_an_old_instructions_file_is_a_warning(repo: Path) -> None:
    _start(repo)
    clean_memory_bank(repo)
    path = repo / "memory-bank" / "instructions.md"
    kept = [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if "memory-bank: instructions v" not in line
    ]
    path.write_text("\n".join(kept) + "\n", encoding="utf-8")
    assert _has_warning(repo, "older memory-bank version")


def test_the_current_instructions_template_is_not_reported(repo: Path) -> None:
    _start(repo)
    clean_memory_bank(repo)
    assert not _has_warning(repo, "older memory-bank version")


def test_an_unrendered_token_is_an_error(repo: Path) -> None:
    _start(repo)
    clean_memory_bank(repo)
    path = repo / "memory-bank" / "progress.md"
    path.write_text(path.read_text() + "\n{{DATE}}\n", encoding="utf-8")
    assert _has_error(repo, "{{DATE}}")


def test_too_many_recent_changes_is_a_warning(repo: Path) -> None:
    _start(repo)
    clean_memory_bank(repo)
    bullets = "\n".join(f"- 2026-11-{day:02d}: change {day}" for day in range(1, 9))
    path = repo / "memory-bank" / "activeContext.md"
    text = path.read_text()
    start = text.index("## Recent changes")
    end = text.index("## Next steps")
    path.write_text(text[:start] + f"## Recent changes\n\n{bullets}\n\n" + text[end:])
    assert _has_warning(repo, "recent changes")


def test_a_broken_file_reference_is_a_warning(repo: Path) -> None:
    _start(repo)
    clean_memory_bank(repo)
    path = repo / "memory-bank" / "activeContext.md"
    path.write_text(path.read_text() + "\nSee `docs/missing.md`.\n", encoding="utf-8")
    assert _has_warning(repo, "docs/missing.md")


def test_a_real_file_reference_is_not_reported(repo: Path) -> None:
    _start(repo)
    clean_memory_bank(repo)
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    path = repo / "memory-bank" / "activeContext.md"
    path.write_text(path.read_text() + "\nSee `README.md`.\n", encoding="utf-8")
    assert not _has_warning(repo, "README.md")


@pytest.mark.parametrize("marker", ["TODO", "FIXME", "XXX"])
def test_known_issues_none_with_code_markers_is_a_warning(repo: Path, marker: str) -> None:
    _start(repo)
    clean_memory_bank(repo)
    (repo / "main.py").write_text(f"# {marker}: later\n", encoding="utf-8")
    assert _has_warning(repo, "known issues")


def test_known_issues_can_list_a_problem(repo: Path) -> None:
    _start(repo)
    clean_memory_bank(repo)
    (repo / "main.py").write_text("# TODO: later\n", encoding="utf-8")
    path = repo / "memory-bank" / "progress.md"
    path.write_text(
        path.read_text().replace("## Known issues\n\n- None.", "## Known issues\n\n- Slow."),
        encoding="utf-8",
    )
    assert not _has_warning(repo, "known issues")


def test_a_missing_bridge_is_a_warning(repo: Path) -> None:
    _start(repo)
    clean_memory_bank(repo)
    (repo / "AGENTS.md").unlink()
    assert _has_warning(repo, "AGENTS.md")


def test_a_missing_bridge_is_reported_only_once(repo: Path) -> None:
    _start(repo)
    clean_memory_bank(repo)
    (repo / "AGENTS.md").unlink()
    mentions = [message for message in _messages(repo) if "AGENTS.md" in message]
    assert len(mentions) == 1


def test_a_foreign_bridge_is_a_warning(repo: Path) -> None:
    _start(repo)
    clean_memory_bank(repo)
    path = repo / "AGENTS.md"
    path.unlink()
    path.write_text("# my own rules\n", encoding="utf-8")
    assert _has_warning(repo, "not managed")


def test_an_obvious_secret_is_an_error(repo: Path) -> None:
    _start(repo)
    clean_memory_bank(repo)
    path = repo / "memory-bank" / "activeContext.md"
    token = "ghp_" + "a" * 30
    path.write_text(path.read_text() + f"\n{token}\n", encoding="utf-8")
    assert _has_error(repo, "secret")


def test_a_non_iso_date_is_a_warning(repo: Path) -> None:
    _start(repo)
    clean_memory_bank(repo)
    path = repo / "memory-bank" / "decisionLog.md"
    path.write_text(path.read_text().replace("2026-11-15", "15/11/2026"), encoding="utf-8")
    assert _has_warning(repo, "non-ISO")


def test_the_same_bad_date_is_reported_once(repo: Path) -> None:
    _start(repo)
    clean_memory_bank(repo)
    path = repo / "memory-bank" / "decisionLog.md"
    text = path.read_text().replace("2026-11-15", "15/11/2026")
    path.write_text(text + "\n" + text[text.index("## ADR-001") :], encoding="utf-8")
    mentions = [message for message in _messages(repo) if "non-ISO" in message]
    assert len(mentions) == 1


def test_errors_are_listed_before_warnings(repo: Path) -> None:
    _start(repo)
    clean_memory_bank(repo)
    (repo / "memory-bank" / "progress.md").unlink()
    issues = checks.run_checks(str(repo))
    assert issues[0].is_error
    assert any(not issue.is_error for issue in issues)


def test_messages_are_translated(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from conftest import set_language

    set_language(monkeypatch, "es")
    _start(repo)
    clean_memory_bank(repo)
    (repo / "AGENTS.md").unlink()
    assert any("Falta" in message for message in _messages(repo))
