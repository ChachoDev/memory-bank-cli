from __future__ import annotations

import string

import pytest

from memory_bank import i18n
from memory_bank.i18n import TRANSLATIONS, detect_language, t


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """No language variables and no system locale, so each test sets exactly what it needs."""
    monkeypatch.delenv("MEMORY_BANK_LANG", raising=False)
    monkeypatch.setattr(i18n, "_system_locale", lambda: None)
    detect_language.cache_clear()
    return monkeypatch


@pytest.mark.parametrize(
    ("var", "value", "expected"),
    [
        ("LC_ALL", "es_ES.UTF-8", "es"),
        ("LC_MESSAGES", "fr_FR.UTF-8", "fr"),
        ("LANG", "de_DE.UTF-8", "de"),
        ("LANG", "en_GB.UTF-8", "en"),
        ("LANGUAGE", "fr:en", "fr"),
        ("LANG", "de_AT@euro", "de"),
        ("LC_ALL", "it_IT.UTF-8", "en"),
        ("MEMORY_BANK_LANG", "fr", "fr"),
    ],
)
def test_detects_language_from_environment(
    clean_env: pytest.MonkeyPatch, var: str, value: str, expected: str
) -> None:
    clean_env.setenv(var, value)
    assert detect_language() == expected


def test_lc_all_overrides_lang(clean_env: pytest.MonkeyPatch) -> None:
    clean_env.setenv("LC_ALL", "es_ES.UTF-8")
    clean_env.setenv("LANG", "de_DE.UTF-8")
    assert detect_language() == "es"


def test_override_variable_wins_over_lc_all(clean_env: pytest.MonkeyPatch) -> None:
    clean_env.setenv("LC_ALL", "es_ES.UTF-8")
    clean_env.setenv("MEMORY_BANK_LANG", "de")
    assert detect_language() == "de"


def test_neutral_locale_falls_through_to_next_variable(clean_env: pytest.MonkeyPatch) -> None:
    clean_env.setenv("LC_ALL", "C")
    clean_env.setenv("LANG", "fr_FR.UTF-8")
    assert detect_language() == "fr"


def test_uses_system_locale_when_no_variable_is_set(clean_env: pytest.MonkeyPatch) -> None:
    clean_env.setattr(i18n, "_system_locale", lambda: "de_DE")
    assert detect_language() == "de"


def test_defaults_to_english_without_any_hint(clean_env: pytest.MonkeyPatch) -> None:
    assert detect_language() == "en"


def test_understands_windows_locale_names() -> None:
    assert i18n._language_code("Spanish_Spain") == "es"
    assert i18n._language_code("German_Germany.1252") == "de"


@pytest.mark.parametrize("language", ["es", "fr", "de"])
def test_every_language_has_the_same_keys_as_english(language: str) -> None:
    assert TRANSLATIONS[language].keys() == TRANSLATIONS["en"].keys()


def _fields(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


@pytest.mark.parametrize("language", ["es", "fr", "de"])
def test_every_translation_uses_the_english_placeholders(language: str) -> None:
    for key, english in TRANSLATIONS["en"].items():
        assert _fields(TRANSLATIONS[language][key]) == _fields(english), key


def test_t_formats_arguments() -> None:
    assert t("file_created", path="a.md") == "  + created a.md"


def test_t_translates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MEMORY_BANK_LANG", "es")
    detect_language.cache_clear()
    assert t("file_created", path="a.md") == "  + creado a.md"


def test_t_returns_the_key_when_unknown() -> None:
    assert t("no_such_key") == "no_such_key"
