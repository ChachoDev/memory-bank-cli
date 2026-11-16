from __future__ import annotations

import pytest

from memory_bank.templates import (
    DATE_PLACEHOLDER,
    INSTRUCTIONS_VERSION,
    READ_ORDER,
    STACK_PLACEHOLDER,
    SUPPORTED_TEMPLATE_LANGS,
    TEMPLATES,
    get_templates,
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


def test_instructions_draw_a_boundary_with_sdd_without_naming_tools() -> None:
    instructions = TEMPLATES["instructions.md"]
    assert "Spec-Driven Development (SDD)" in instructions
    # The boundary must not mention a specific SDD tool: it applies to any of them.
    for tool in ("OpenSpec", "spec-kit", "Kiro", "BMAD"):
        assert tool not in instructions
    # Without SDD the section is inert, so it has to say so explicitly.
    assert "does not apply" in instructions


def test_instructions_carry_a_version_marker() -> None:
    instructions = TEMPLATES["instructions.md"]
    assert f"<!-- memory-bank: instructions v{INSTRUCTIONS_VERSION} -->" in instructions


def test_instructions_explain_how_to_compress_the_decision_log() -> None:
    instructions = TEMPLATES["instructions.md"]
    assert "compress the oldest `decisionLog.md` entries" in instructions
    assert "git log -p memory-bank/decisionLog.md" in instructions
    assert "Never a bare title" in instructions


def test_decision_log_ships_one_filled_example_and_no_empty_entry() -> None:
    decision_log = TEMPLATES["decisionLog.md"]
    assert "## ADR-001:" in decision_log
    assert "## ADR-002" not in decision_log
    assert "_Title_" not in decision_log


def test_decision_log_allows_compression_but_not_rewriting_meaning() -> None:
    decision_log = TEMPLATES["decisionLog.md"]
    assert "Never rewrite an entry to change its meaning" in decision_log
    assert "Compression under the size budget" in decision_log


def test_instructions_include_a_consistency_checklist() -> None:
    instructions = TEMPLATES["instructions.md"]
    assert "Before finishing: consistency checklist" in instructions
    for item in ("README", "count", "activeContext.md", "Known issues", "memory-bank check"):
        assert item in instructions


# ---------------------------------------------------------------------------
# Multilingual templates
# ---------------------------------------------------------------------------


def test_supported_langs_match_i18n() -> None:
    assert SUPPORTED_TEMPLATE_LANGS == ("en", "es", "fr", "de")


def test_get_templates_returns_six_files_for_each_lang() -> None:
    for lang in SUPPORTED_TEMPLATE_LANGS:
        templates = get_templates(lang)
        assert set(templates) == EXPECTED_FILES, lang


def test_get_templates_falls_back_to_english() -> None:
    unknown = get_templates("xx")
    assert unknown is TEMPLATES


def test_every_lang_template_starts_with_a_title() -> None:
    for lang in SUPPORTED_TEMPLATE_LANGS:
        templates = get_templates(lang)
        for name, template in templates.items():
            assert template.startswith("# "), f"{lang} / {name}"


def test_render_fills_placeholders_in_every_lang() -> None:
    for lang in SUPPORTED_TEMPLATE_LANGS:
        templates = get_templates(lang)
        for template in templates.values():
            rendered = render(template, ["Rust", "Docker"], "2026-11-09")
            assert STACK_PLACEHOLDER not in rendered, f"{lang} stack placeholder"
            assert DATE_PLACEHOLDER not in rendered, f"{lang} date placeholder"


def test_instructions_version_marker_in_every_lang() -> None:
    for lang in SUPPORTED_TEMPLATE_LANGS:
        templates = get_templates(lang)
        instructions = templates["instructions.md"]
        assert f"<!-- memory-bank: instructions v{INSTRUCTIONS_VERSION} -->" in instructions, lang


def test_decision_log_has_adr_in_every_lang() -> None:
    for lang in SUPPORTED_TEMPLATE_LANGS:
        templates = get_templates(lang)
        decision_log = templates["decisionLog.md"]
        assert "## ADR-001:" in decision_log, lang


@pytest.mark.parametrize(
    ("lang", "marker"),
    [
        ("en", "Project Brief"),
        ("es", "Resumen del Proyecto"),
        ("fr", "Résumé du Projet"),
        ("de", "Projektübersicht"),
    ],
)
def test_project_brief_title_matches_language(lang: str, marker: str) -> None:
    templates = get_templates(lang)
    assert f"# {marker}" in templates["projectbrief.md"]


@pytest.mark.parametrize(
    ("lang", "marker"),
    [
        ("en", "Product Context"),
        ("es", "Contexto del Producto"),
        ("fr", "Contexte du Produit"),
        ("de", "Produktkontext"),
    ],
)
def test_product_context_title_matches_language(lang: str, marker: str) -> None:
    templates = get_templates(lang)
    assert f"# {marker}" in templates["productContext.md"]


@pytest.mark.parametrize(
    ("lang", "marker"),
    [
        ("en", "Active Context"),
        ("es", "Contexto Activo"),
        ("fr", "Contexte Actif"),
        ("de", "Aktueller Kontext"),
    ],
)
def test_active_context_title_matches_language(lang: str, marker: str) -> None:
    templates = get_templates(lang)
    assert f"# {marker}" in templates["activeContext.md"]


@pytest.mark.parametrize(
    ("lang", "marker"),
    [
        ("en", "Progress"),
        ("es", "Progreso"),
        ("fr", "Progression"),
        ("de", "Fortschritt"),
    ],
)
def test_progress_title_matches_language(lang: str, marker: str) -> None:
    templates = get_templates(lang)
    assert f"# {marker}" in templates["progress.md"]


@pytest.mark.parametrize(
    ("lang", "marker"),
    [
        ("en", "Decision Log"),
        ("es", "Registro de Decisiones"),
        ("fr", "Journal des Décisions"),
        ("de", "Entscheidungsprotokoll"),
    ],
)
def test_decision_log_title_matches_language(lang: str, marker: str) -> None:
    templates = get_templates(lang)
    assert f"# {marker}" in templates["decisionLog.md"]


@pytest.mark.parametrize(
    ("lang", "marker"),
    [
        ("en", "Memory Bank Instructions for AI Agents"),
        ("es", "Instrucciones del Memory Bank para Agentes de IA"),
        ("fr", "Instructions du Memory Bank pour les Agents IA"),
        ("de", "Memory-Bank-Anweisungen für KI-Agenten"),
    ],
)
def test_instructions_title_matches_language(lang: str, marker: str) -> None:
    templates = get_templates(lang)
    assert f"# {marker}" in templates["instructions.md"]
