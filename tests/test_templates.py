from __future__ import annotations

from memory_bank.templates import (
    DATE_PLACEHOLDER,
    READ_ORDER,
    STACK_PLACEHOLDER,
    TEMPLATES,
    render,
)

EXPECTED_FILES = {
    "projectbrief.md",
    "productContext.md",
    "activeContext.md",
    "progress.md",
    "decisionLog.md",
    "instructions.md",
}


def test_ships_the_six_core_files() -> None:
    assert set(TEMPLATES) == EXPECTED_FILES
    assert set(READ_ORDER) == EXPECTED_FILES


def test_every_template_starts_with_a_title() -> None:
    for name, template in TEMPLATES.items():
        assert template.startswith("# "), name


def test_render_fills_every_placeholder() -> None:
    for template in TEMPLATES.values():
        rendered = render(template, ["Rust", "Docker"], "2026-11-09")
        assert STACK_PLACEHOLDER not in rendered
        assert DATE_PLACEHOLDER not in rendered


def test_render_lists_the_stack() -> None:
    rendered = render(STACK_PLACEHOLDER, ["Rust", "Docker"], "2026-11-09")
    assert rendered == "- Rust\n- Docker"


def test_render_marks_an_empty_stack() -> None:
    assert render(STACK_PLACEHOLDER, [], "2026-11-09") == "- _Nothing detected yet._"


def test_instructions_tell_agents_to_read_first_and_update_last() -> None:
    instructions = TEMPLATES["instructions.md"]
    assert "Before doing anything: read the memory bank" in instructions
    assert "Before finishing: update the memory bank" in instructions
