"""Verify that memory bank templates are always written in English, regardless of system language.

These tests simulate users with different system languages (Spanish, French, German) and verify
that the persisted memory bank files are always in English. They also test the scenario where
a user starts with one language and later switches to another.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import commit_all, set_language

from memory_bank import i18n, scaffold
from memory_bank.templates import TEMPLATES


# Headings that prove a file is in English
ENGLISH_HEADINGS = {
    "projectbrief.md": ["# Project Brief", "## Overview", "## Goals", "## Core requirements"],
    "productContext.md": ["# Product Context", "## Problem", "## Users", "## Value proposition"],
    "activeContext.md": ["# Active Context", "## Current focus", "## Recent changes", "## Next steps"],
    "progress.md": ["# Progress", "## Current phase", "## What works", "## Known issues"],
    "decisionLog.md": ["# Decision Log", "## ADR-001:"],
    "instructions.md": ["# Memory Bank Instructions for AI Agents"],
}

# Headings unique to Spanish templates (exclude ambiguous ones like ## Problem)
SPANISH_HEADINGS = {
    "projectbrief.md": ["# Resumen del Proyecto", "## Descripción general", "## Objetivos"],
    "productContext.md": ["# Contexto del Producto"],
    "activeContext.md": ["# Contexto Activo", "## Enfoque actual", "## Cambios recientes"],
    "progress.md": ["# Progreso", "## Fase actual", "## Qué funciona"],
    "decisionLog.md": ["# Registro de Decisiones"],
}

# Headings unique to French templates
FRENCH_HEADINGS = {
    "projectbrief.md": ["# Résumé du Projet", "## Vue d'ensemble", "## Objectifs"],
    "productContext.md": ["# Contexte du Produit"],
    "activeContext.md": ["# Contexte Actif", "## Focus actuel", "## Changements récents"],
    "progress.md": ["# Progression", "## Phase actuelle", "## Ce qui fonctionne"],
    "decisionLog.md": ["# Journal des Décisions"],
}

# Headings unique to German templates
GERMAN_HEADINGS = {
    "projectbrief.md": ["# Projektübersicht", "## Übersicht", "## Ziele"],
    "productContext.md": ["# Produktkontext"],
    "activeContext.md": ["# Aktiver Kontext", "## Aktueller Fokus", "## Letzte Änderungen"],
    "progress.md": ["# Fortschritt", "## Aktuelle Phase", "## Was funktioniert"],
    "decisionLog.md": ["# Entscheidungsprotokoll"],
}

NON_ENGLISH_HEADINGS = {**SPANISH_HEADINGS, **FRENCH_HEADINGS, **GERMAN_HEADINGS}


def _assert_all_english(root: Path) -> None:
    """Assert every memory bank file contains English headings and no non-English headings."""
    directory = root / "memory-bank"
    for name, english_headings in ENGLISH_HEADINGS.items():
        path = directory / name
        if not path.is_file():
            pytest.fail(f"{name} was not created")
        content = path.read_text(encoding="utf-8")
        for heading in english_headings:
            assert heading in content, (
                f"{name} is missing English heading '{heading}' — template may not be in English"
            )
        # Also assert no non-English headings appear
        non_en = NON_ENGLISH_HEADINGS.get(name, [])
        for heading in non_en:
            assert heading not in content, (
                f"{name} contains non-English heading '{heading}' — template is not in English"
            )


def test_start_with_spanish_system_language(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """User with Spanish system language creates a memory bank → files are in English."""
    set_language(monkeypatch, "es")
    scaffold.create_memory_bank(str(repo), ["Python"], log=lambda _: None)
    _assert_all_english(repo)


def test_start_with_french_system_language(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """User with French system language creates a memory bank → files are in English."""
    set_language(monkeypatch, "fr")
    scaffold.create_memory_bank(str(repo), ["Python"], log=lambda _: None)
    _assert_all_english(repo)


def test_start_with_german_system_language(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """User with German system language creates a memory bank → files are in English."""
    set_language(monkeypatch, "de")
    scaffold.create_memory_bank(str(repo), ["Python"], log=lambda _: None)
    _assert_all_english(repo)


def test_sync_after_language_change_keeps_english(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Simulate: User A (Spanish) creates the bank, commits. User B (French) pulls and runs sync.
    All files remain in English.
    """
    # User A: Spanish system
    set_language(monkeypatch, "es")
    scaffold.create_memory_bank(str(repo), ["Python"], log=lambda _: None)
    commit_all(repo)

    # Verify initial state is English
    _assert_all_english(repo)

    # User B: French system, runs sync
    set_language(monkeypatch, "fr")
    i18n.detect_language.cache_clear()
    scaffold.sync_memory_bank(str(repo), ["Python"], log=lambda _: None)

    # All files should still be in English
    _assert_all_english(repo)


def test_sync_creates_missing_files_in_english(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Simulate: A memory bank exists with some files missing. User with Spanish system runs sync.
    The missing files are created in English, not Spanish.
    """
    # Create the bank in English
    scaffold.create_memory_bank(str(repo), ["Python"], log=lambda _: None)
    commit_all(repo)

    # Remove some files to simulate missing files
    (repo / "memory-bank" / "progress.md").unlink()
    (repo / "memory-bank" / "decisionLog.md").unlink()

    # User with Spanish system runs sync
    set_language(monkeypatch, "es")
    i18n.detect_language.cache_clear()
    scaffold.sync_memory_bank(str(repo), ["Python"], log=lambda _: None)

    # The recreated files should be in English
    _assert_all_english(repo)


def test_reset_with_different_language_regenerates_english(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Simulate: Memory bank exists in English. User with French system runs reset.
    The regenerated bank is in English.
    """
    # Create the bank
    scaffold.create_memory_bank(str(repo), ["Python"], log=lambda _: None)
    commit_all(repo)

    # Switch to French and reset
    set_language(monkeypatch, "fr")
    i18n.detect_language.cache_clear()
    scaffold.reset_memory_bank(str(repo), ["Python"], log=lambda _: None)

    # Regenerated bank should be in English
    _assert_all_english(repo)


def test_multiple_language_switches_always_english(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Simulate: A user repeatedly changes system language and runs sync.
    The memory bank stays in English throughout.
    """
    languages = ["en", "es", "fr", "de", "es", "fr", "en"]
    scaffold.create_memory_bank(str(repo), ["Python"], log=lambda _: None)

    for lang in languages:
        set_language(monkeypatch, lang)
        i18n.detect_language.cache_clear()
        scaffold.sync_memory_bank(str(repo), ["Python"], log=lambda _: None)
        _assert_all_english(repo)


def test_cli_messages_still_translate(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Verify that CLI messages still respect the system language even though
    templates are always in English.
    """
    messages: list[str] = []

    def log(msg: str) -> None:
        messages.append(msg)

    # Spanish system
    set_language(monkeypatch, "es")
    scaffold.create_memory_bank(str(repo), ["Python"], log=log)

    # The log messages should be in Spanish (file_created, file_kept, etc.)
    # Check that at least one message is translated
    has_spanish = any("creado" in msg or "mantenido" in msg for msg in messages)
    assert has_spanish, (
        f"CLI messages should be in Spanish, got: {messages}"
    )

    # But the actual files should be in English
    _assert_all_english(repo)


def test_instructions_always_english_across_languages(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    The instructions.md file contains agent rules. It must always be in English
    because agents understand English best.
    """
    for lang in ["en", "es", "fr", "de"]:
        set_language(monkeypatch, lang)
        i18n.detect_language.cache_clear()

        # Create a fresh repo for each language
        fresh = repo.parent / f"fresh_{lang}"
        fresh.mkdir()
        from conftest import git as _git
        _git(fresh, "init", "-q")

        scaffold.create_memory_bank(str(fresh), [], log=lambda _: None)
        instructions = (fresh / "memory-bank" / "instructions.md").read_text()

        assert "# Memory Bank Instructions for AI Agents" in instructions
        assert "Before doing anything: read the memory bank" in instructions
        assert "Before finishing: update the memory bank" in instructions

        # No Spanish instructions
        assert "# Instrucciones del Memory Bank para Agentes de IA" not in instructions
        # No French instructions
        assert "# Instructions du Memory Bank pour les Agents IA" not in instructions
        # No German instructions
        assert "# Memory Bank-Anweisungen für KI-Agenten" not in instructions
