"""Translations and operating-system language detection.

Order of precedence: MEMORY_BANK_LANG, then the POSIX variables (LC_ALL, LC_MESSAGES, LANG,
LANGUAGE), then ``locale.getlocale()``. The first variable that names a real language decides;
an unsupported language falls back to English.
"""

from __future__ import annotations

import locale
import os
from functools import lru_cache

DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES: tuple[str, ...] = ("en", "es", "fr", "de")
_ENV_VARS: tuple[str, ...] = ("MEMORY_BANK_LANG", "LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE")
_NEUTRAL_LOCALES = frozenset({"", "c", "posix"})
# Windows reports locale names such as "Spanish_Spain".
_WINDOWS_NAMES = {"english": "en", "spanish": "es", "french": "fr", "german": "de"}

YES_ANSWERS = frozenset({"y", "yes", "s", "si", "sí", "o", "oui", "j", "ja"})

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "help": (
            "memory-bank {version} - Markdown memory bank for AI coding agents\n"
            "\n"
            "Usage: memory-bank <command> [options]\n"
            "\n"
            "Commands:\n"
            "  start          Create the memory bank, agent links and hooks in this Git repository\n"
            "  sync           Repair missing files, broken links and outdated hooks; keeps notes\n"
            "  check [--strict]  Validate the memory bank; --strict also fails on warnings\n"
            "  reset [--yes]  Delete memory-bank/ and regenerate it from scratch\n"
            "  help           Show this help\n"
            "\n"
            "Internal, called by agent hooks:\n"
            "  hook session-start  Print the memory bank so the agent loads it\n"
            "  hook stop           Ask the agent to update activeContext.md and progress.md\n"
            "\n"
            "The language comes from the system (LC_ALL, LC_MESSAGES, LANG).\n"
            "Set MEMORY_BANK_LANG=en|es|fr|de to override it."
        ),
        "git_missing": "Error: Git is not installed or not on PATH. The memory bank requires Git.",
        "not_git_repo": "Error: {path} is not inside a Git repository. Run 'git init' first.",
        "already_exists": (
            "The memory bank already exists in {path}. "
            "Use 'memory-bank sync' to repair it or 'memory-bank reset' to start over."
        ),
        "not_initialized": "There is no memory bank in {path}. Run 'memory-bank start' first.",
        "scanning": "Scanning {path} for existing code...",
        "stack_detected": "Existing code detected. Stack: {stack}",
        "code_no_stack": "Existing code detected, but no known stack marker was found.",
        "no_code": "No existing code detected: starting from a blank project.",
        "file_created": "  + created {path}",
        "file_kept": "  = kept {path}",
        "link_created": "  + linked {link} -> {target}",
        "link_ok": "  = {link} already points to {target}",
        "link_copied": "  + wrote {link} as a copy of {target} (symlinks are not available)",
        "link_refreshed": "  ~ refreshed the copy {link}",
        "link_foreign": (
            "  ! {link} exists and is not managed by memory-bank; left untouched. "
            "Point it at {target} yourself."
        ),
        "hooks_written": "  + hooks configured in {path}",
        "hooks_ok": "  = hooks up to date in {path}",
        "config_invalid": (
            "  ! {path} is not valid JSON or has an unexpected shape; left untouched. "
            "Fix it and run 'memory-bank sync'."
        ),
        "jsonc_skipped": '  ! {path} found: add "memory-bank/*.md" to its "instructions" yourself.',
        "start_done": (
            "Memory bank ready. Fill in memory-bank/projectbrief.md and commit the result."
        ),
        "sync_done": "Sync complete. Existing notes were kept.",
        "reset_warning": (
            "WARNING: this deletes {path} and every note in it. Only Git history can bring it back."
        ),
        "reset_confirm": "Continue? [y/N] ",
        "reset_aborted": "Reset cancelled. Nothing was deleted.",
        "reset_needs_yes": "This is not an interactive terminal: rerun with --yes to confirm.",
        "reset_done": "Memory bank regenerated from scratch.",
        "check_ok": "Memory bank looks consistent.",
        "check_error_label": "error",
        "check_warning_label": "warning",
        "check_summary": "{errors} error(s), {warnings} warning(s).",
        "check_missing_file": "{path} is missing. Run 'memory-bank sync'.",
        "check_missing_section": "{path} has no '{section}' section.",
        "check_outdated_template": (
            "{path} was written by an older memory-bank version and lacks the latest agent rules "
            "(for example the consistency checklist). Ask your agent to copy the new sections and "
            "the version marker from the current template; 'memory-bank sync' never overwrites "
            "your notes."
        ),
        "check_placeholder": "{path} still contains the template placeholder: {text}",
        "check_unrendered": "{path} still contains the unrendered token {token}.",
        "check_recent_changes": (
            "{path} lists {count} recent changes; keep it short (max {max}) and move history "
            "to progress.md."
        ),
        "check_broken_ref": "{path} mentions {ref}, which does not exist.",
        "check_known_issues": (
            "{path} says there are no known issues, but the code contains {count} "
            "TODO/FIXME marker(s)."
        ),
        "check_link": "{link} is missing or does not point to {target}. Run 'memory-bank sync'.",
        "check_foreign_link": (
            "{link} exists but is not managed by memory-bank; point it at {target} yourself."
        ),
        "check_secret": (
            "{path} looks like it contains a secret ({kind}). Remove it before committing."
        ),
        "check_date": "{path} has a non-ISO date: {value}",
        "check_large_note": (
            "{path} is {size} characters (~{tokens} tokens) and is loaded into every session. "
            "Keep it under {max}: move history to Git, compress old entries or split the file."
        ),
        "check_large_bank": (
            "The memory bank is {size} characters (~{tokens} tokens) and enters every session. "
            "Keep the whole bank under {max}: compress old entries and move history to Git."
        ),
        "unknown_command": "Unknown command: {command}. Run 'memory-bank help'.",
        "unknown_option": "Unknown option: {option}. Run 'memory-bank help'.",
    },
    "es": {
        "help": (
            "memory-bank {version} - Memory Bank en Markdown para agentes de IA\n"
            "\n"
            "Uso: memory-bank <comando> [opciones]\n"
            "\n"
            "Comandos:\n"
            "  start          Crea el Memory Bank, los enlaces y los hooks en este repositorio Git\n"
            "  sync           Repara ficheros que faltan, enlaces rotos y hooks desactualizados\n"
            "                 sin tocar tus notas\n"
            "  check [--strict]  Valida el Memory Bank; --strict también falla con avisos\n"
            "  reset [--yes]  Borra memory-bank/ y lo regenera desde cero\n"
            "  help           Muestra esta ayuda\n"
            "\n"
            "Internos, los llaman los hooks del agente:\n"
            "  hook session-start  Imprime el Memory Bank para que el agente lo cargue\n"
            "  hook stop           Pide al agente actualizar activeContext.md y progress.md\n"
            "\n"
            "El idioma se toma del sistema (LC_ALL, LC_MESSAGES, LANG).\n"
            "Usa MEMORY_BANK_LANG=en|es|fr|de para forzarlo."
        ),
        "git_missing": "Error: Git no está instalado o no está en el PATH. El Memory Bank requiere Git.",
        "not_git_repo": "Error: {path} no está dentro de un repositorio Git. Ejecuta antes 'git init'.",
        "already_exists": (
            "El Memory Bank ya existe en {path}. "
            "Usa 'memory-bank sync' para repararlo o 'memory-bank reset' para empezar de cero."
        ),
        "not_initialized": "No hay Memory Bank en {path}. Ejecuta antes 'memory-bank start'.",
        "scanning": "Analizando {path} en busca de código existente...",
        "stack_detected": "Se ha detectado código existente. Stack: {stack}",
        "code_no_stack": "Se ha detectado código existente, pero ningún marcador de stack conocido.",
        "no_code": "No se ha detectado código: se parte de un proyecto vacío.",
        "file_created": "  + creado {path}",
        "file_kept": "  = conservado {path}",
        "link_created": "  + enlazado {link} -> {target}",
        "link_ok": "  = {link} ya apunta a {target}",
        "link_copied": "  + escrito {link} como copia de {target} (no se pueden crear symlinks)",
        "link_refreshed": "  ~ actualizada la copia {link}",
        "link_foreign": (
            "  ! {link} existe y no lo gestiona memory-bank; no se ha tocado. "
            "Haz que apunte a {target} tú mismo."
        ),
        "hooks_written": "  + hooks configurados en {path}",
        "hooks_ok": "  = hooks al día en {path}",
        "config_invalid": (
            "  ! {path} no es JSON válido o tiene una forma inesperada; no se ha tocado. "
            "Corrígelo y ejecuta 'memory-bank sync'."
        ),
        "jsonc_skipped": (
            '  ! Encontrado {path}: añade "memory-bank/*.md" a sus "instructions" tú mismo.'
        ),
        "start_done": (
            "Memory Bank listo. Completa memory-bank/projectbrief.md y haz commit del resultado."
        ),
        "sync_done": "Sincronización completada. Se han conservado las notas existentes.",
        "reset_warning": (
            "AVISO: esto borra {path} y todas sus notas. "
            "Solo el historial de Git podrá recuperarlas."
        ),
        "reset_confirm": "¿Continuar? [s/N] ",
        "reset_aborted": "Reset cancelado. No se ha borrado nada.",
        "reset_needs_yes": "No es una terminal interactiva: vuelve a ejecutar con --yes para confirmar.",
        "reset_done": "Memory Bank regenerado desde cero.",
        "check_ok": "El Memory Bank parece coherente.",
        "check_error_label": "error",
        "check_warning_label": "aviso",
        "check_summary": "{errors} error(es), {warnings} aviso(s).",
        "check_missing_file": "Falta {path}. Ejecuta 'memory-bank sync'.",
        "check_missing_section": "{path} no tiene la sección '{section}'.",
        "check_outdated_template": (
            "{path} lo escribió una versión anterior de memory-bank y no incluye las reglas más "
            "recientes (por ejemplo, el checklist de consistencia). Pide a tu agente que copie las "
            "secciones nuevas y el marcador de versión de la plantilla actual; 'memory-bank sync' "
            "nunca sobrescribe tus notas."
        ),
        "check_placeholder": "{path} aún contiene el marcador de plantilla: {text}",
        "check_unrendered": "{path} aún contiene el token sin sustituir {token}.",
        "check_recent_changes": (
            "{path} enumera {count} cambios recientes; mantenlo corto (máx. {max}) y mueve el "
            "historial a progress.md."
        ),
        "check_broken_ref": "{path} menciona {ref}, que no existe.",
        "check_known_issues": (
            "{path} dice que no hay problemas conocidos, pero el código contiene {count} "
            "marcador(es) TODO/FIXME."
        ),
        "check_link": "Falta {link} o no apunta a {target}. Ejecuta 'memory-bank sync'.",
        "check_foreign_link": (
            "{link} existe pero no lo gestiona memory-bank; haz que apunte a {target} tú mismo."
        ),
        "check_secret": (
            "{path} parece contener un secreto ({kind}). Elimínalo antes de hacer commit."
        ),
        "check_date": "{path} tiene una fecha que no es ISO: {value}",
        "check_large_note": (
            "{path} ocupa {size} caracteres (~{tokens} tokens) y se carga en cada sesión. "
            "Mantenlo por debajo de {max}: mueve el historial a Git, comprime entradas antiguas "
            "o divide el fichero."
        ),
        "check_large_bank": (
            "El Memory Bank ocupa {size} caracteres (~{tokens} tokens) y entra en cada sesión. "
            "Mantén el banco entero por debajo de {max}: comprime entradas antiguas y mueve el "
            "historial a Git."
        ),
        "unknown_command": "Comando desconocido: {command}. Ejecuta 'memory-bank help'.",
        "unknown_option": "Opción desconocida: {option}. Ejecuta 'memory-bank help'.",
    },
    "fr": {
        "help": (
            "memory-bank {version} - Memory Bank en Markdown pour agents IA\n"
            "\n"
            "Usage : memory-bank <commande> [options]\n"
            "\n"
            "Commandes :\n"
            "  start          Crée le Memory Bank, les liens et les hooks dans ce dépôt Git\n"
            "  sync           Répare les fichiers manquants, les liens cassés et les hooks\n"
            "                 obsolètes sans toucher à vos notes\n"
            "  check [--strict]  Valide le Memory Bank ; --strict échoue aussi sur les avertissements\n"
            "  reset [--yes]  Supprime memory-bank/ et le régénère de zéro\n"
            "  help           Affiche cette aide\n"
            "\n"
            "Internes, appelées par les hooks de l'agent :\n"
            "  hook session-start  Affiche le Memory Bank pour que l'agent le charge\n"
            "  hook stop           Demande à l'agent de mettre à jour activeContext.md et progress.md\n"
            "\n"
            "La langue vient du système (LC_ALL, LC_MESSAGES, LANG).\n"
            "Définissez MEMORY_BANK_LANG=en|es|fr|de pour la forcer."
        ),
        "git_missing": (
            "Erreur : Git n'est pas installé ou absent du PATH. Le Memory Bank nécessite Git."
        ),
        "not_git_repo": (
            "Erreur : {path} n'est pas dans un dépôt Git. Exécutez d'abord 'git init'."
        ),
        "already_exists": (
            "Le Memory Bank existe déjà dans {path}. "
            "Utilisez 'memory-bank sync' pour le réparer ou 'memory-bank reset' pour repartir de zéro."
        ),
        "not_initialized": ("Aucun Memory Bank dans {path}. Exécutez d'abord 'memory-bank start'."),
        "scanning": "Analyse de {path} à la recherche de code existant...",
        "stack_detected": "Code existant détecté. Stack : {stack}",
        "code_no_stack": "Code existant détecté, mais aucun marqueur de stack connu.",
        "no_code": "Aucun code existant détecté : projet vierge.",
        "file_created": "  + créé {path}",
        "file_kept": "  = conservé {path}",
        "link_created": "  + lien {link} -> {target}",
        "link_ok": "  = {link} pointe déjà vers {target}",
        "link_copied": (
            "  + {link} écrit comme copie de {target} (liens symboliques indisponibles)"
        ),
        "link_refreshed": "  ~ copie {link} mise à jour",
        "link_foreign": (
            "  ! {link} existe et n'est pas géré par memory-bank ; laissé intact. "
            "Faites-le pointer vers {target} vous-même."
        ),
        "hooks_written": "  + hooks configurés dans {path}",
        "hooks_ok": "  = hooks à jour dans {path}",
        "config_invalid": (
            "  ! {path} n'est pas un JSON valide ou a une forme inattendue ; laissé intact. "
            "Corrigez-le puis exécutez 'memory-bank sync'."
        ),
        "jsonc_skipped": (
            '  ! {path} trouvé : ajoutez "memory-bank/*.md" à ses "instructions" vous-même.'
        ),
        "start_done": (
            "Memory Bank prêt. Complétez memory-bank/projectbrief.md et commitez le résultat."
        ),
        "sync_done": "Synchronisation terminée. Les notes existantes ont été conservées.",
        "reset_warning": (
            "ATTENTION : ceci supprime {path} et toutes ses notes. "
            "Seul l'historique Git pourra les restaurer."
        ),
        "reset_confirm": "Continuer ? [o/N] ",
        "reset_aborted": "Reset annulé. Rien n'a été supprimé.",
        "reset_needs_yes": (
            "Ce n'est pas un terminal interactif : relancez avec --yes pour confirmer."
        ),
        "reset_done": "Memory Bank régénéré de zéro.",
        "check_ok": "Le Memory Bank semble cohérent.",
        "check_error_label": "erreur",
        "check_warning_label": "avertissement",
        "check_summary": "{errors} erreur(s), {warnings} avertissement(s).",
        "check_missing_file": "{path} est absent. Exécutez 'memory-bank sync'.",
        "check_missing_section": "{path} n'a pas de section '{section}'.",
        "check_outdated_template": (
            "{path} a été écrit par une version plus ancienne de memory-bank et n'inclut pas les "
            "dernières règles (par exemple la checklist de cohérence). Demandez à votre agent de "
            "copier les nouvelles sections et le marqueur de version du modèle actuel ; "
            "'memory-bank sync' ne remplace jamais vos notes."
        ),
        "check_placeholder": "{path} contient encore le modèle de texte : {text}",
        "check_unrendered": "{path} contient encore le jeton non remplacé {token}.",
        "check_recent_changes": (
            "{path} liste {count} changements récents ; restez concis (max {max}) et déplacez "
            "l'historique dans progress.md."
        ),
        "check_broken_ref": "{path} mentionne {ref}, qui n'existe pas.",
        "check_known_issues": (
            "{path} indique qu'il n'y a pas de problème connu, mais le code contient {count} "
            "marqueur(s) TODO/FIXME."
        ),
        "check_link": "{link} est absent ou ne pointe pas vers {target}. Exécutez 'memory-bank sync'.",
        "check_foreign_link": (
            "{link} existe mais n'est pas géré par memory-bank ; faites-le pointer vers {target} "
            "vous-même."
        ),
        "check_secret": (
            "{path} semble contenir un secret ({kind}). Supprimez-le avant de committer."
        ),
        "check_date": "{path} contient une date non ISO : {value}",
        "check_large_note": (
            "{path} fait {size} caractères (~{tokens} jetons) et est chargé à chaque session. "
            "Gardez-le sous {max} : déplacez l'historique dans Git, compressez les anciennes "
            "entrées ou scindez le fichier."
        ),
        "check_large_bank": (
            "Le Memory Bank fait {size} caractères (~{tokens} jetons) et entre dans chaque "
            "session. Gardez l'ensemble sous {max} : compressez les anciennes entrées et "
            "déplacez l'historique dans Git."
        ),
        "unknown_command": "Commande inconnue : {command}. Exécutez 'memory-bank help'.",
        "unknown_option": "Option inconnue : {option}. Exécutez 'memory-bank help'.",
    },
    "de": {
        "help": (
            "memory-bank {version} - Markdown-Memory-Bank für KI-Coding-Agenten\n"
            "\n"
            "Verwendung: memory-bank <Befehl> [Optionen]\n"
            "\n"
            "Befehle:\n"
            "  start          Legt Memory Bank, Agenten-Links und Hooks in diesem Git-Repository an\n"
            "  sync           Repariert fehlende Dateien, defekte Links und veraltete Hooks,\n"
            "                 ohne Notizen zu verändern\n"
            "  check [--strict]  Prüft die Memory Bank; --strict schlägt auch bei Warnungen fehl\n"
            "  reset [--yes]  Löscht memory-bank/ und erzeugt es komplett neu\n"
            "  help           Zeigt diese Hilfe\n"
            "\n"
            "Intern, von Agenten-Hooks aufgerufen:\n"
            "  hook session-start  Gibt die Memory Bank aus, damit der Agent sie lädt\n"
            "  hook stop           Fordert den Agenten auf, activeContext.md und progress.md\n"
            "                      zu aktualisieren\n"
            "\n"
            "Die Sprache kommt vom System (LC_ALL, LC_MESSAGES, LANG).\n"
            "Mit MEMORY_BANK_LANG=en|es|fr|de lässt sie sich überschreiben."
        ),
        "git_missing": (
            "Fehler: Git ist nicht installiert oder nicht im PATH. Die Memory Bank benötigt Git."
        ),
        "not_git_repo": (
            "Fehler: {path} liegt in keinem Git-Repository. Führe zuerst 'git init' aus."
        ),
        "already_exists": (
            "Die Memory Bank existiert bereits in {path}. Nutze 'memory-bank sync' zum "
            "Reparieren oder 'memory-bank reset' für einen Neuanfang."
        ),
        "not_initialized": (
            "In {path} gibt es keine Memory Bank. Führe zuerst 'memory-bank start' aus."
        ),
        "scanning": "Durchsuche {path} nach vorhandenem Code...",
        "stack_detected": "Vorhandener Code erkannt. Stack: {stack}",
        "code_no_stack": "Vorhandener Code erkannt, aber kein bekannter Stack-Marker gefunden.",
        "no_code": "Kein vorhandener Code erkannt: Start mit einem leeren Projekt.",
        "file_created": "  + erstellt {path}",
        "file_kept": "  = behalten {path}",
        "link_created": "  + verlinkt {link} -> {target}",
        "link_ok": "  = {link} zeigt bereits auf {target}",
        "link_copied": ("  + {link} als Kopie von {target} geschrieben (Symlinks nicht verfügbar)"),
        "link_refreshed": "  ~ Kopie {link} aktualisiert",
        "link_foreign": (
            "  ! {link} existiert und wird nicht von memory-bank verwaltet; unverändert. "
            "Lass es selbst auf {target} zeigen."
        ),
        "hooks_written": "  + Hooks in {path} konfiguriert",
        "hooks_ok": "  = Hooks in {path} sind aktuell",
        "config_invalid": (
            "  ! {path} ist kein gültiges JSON oder unerwartet aufgebaut; unverändert. "
            "Korrigiere es und führe 'memory-bank sync' aus."
        ),
        "jsonc_skipped": (
            '  ! {path} gefunden: füge "memory-bank/*.md" selbst zu "instructions" hinzu.'
        ),
        "start_done": (
            "Memory Bank bereit. Fülle memory-bank/projectbrief.md aus und committe das Ergebnis."
        ),
        "sync_done": "Synchronisierung abgeschlossen. Vorhandene Notizen wurden behalten.",
        "reset_warning": (
            "WARNUNG: Dies löscht {path} mit allen Notizen. "
            "Nur die Git-Historie kann sie wiederherstellen."
        ),
        "reset_confirm": "Fortfahren? [j/N] ",
        "reset_aborted": "Reset abgebrochen. Nichts wurde gelöscht.",
        "reset_needs_yes": (
            "Kein interaktives Terminal: erneut mit --yes ausführen, um zu bestätigen."
        ),
        "reset_done": "Memory Bank komplett neu erzeugt.",
        "check_ok": "Die Memory Bank wirkt konsistent.",
        "check_error_label": "Fehler",
        "check_warning_label": "Warnung",
        "check_summary": "{errors} Fehler, {warnings} Warnung(en).",
        "check_missing_file": "{path} fehlt. Führe 'memory-bank sync' aus.",
        "check_missing_section": "{path} hat keinen Abschnitt '{section}'.",
        "check_outdated_template": (
            "{path} wurde von einer älteren memory-bank-Version geschrieben und enthält nicht "
            "die neuesten Regeln (zum Beispiel die Konsistenz-Checkliste). Lass deinen Agenten "
            "die neuen Abschnitte und den Versionsmarker aus der aktuellen Vorlage übernehmen; "
            "'memory-bank sync' überschreibt niemals deine Notizen."
        ),
        "check_placeholder": "{path} enthält noch den Vorlagenplatzhalter: {text}",
        "check_unrendered": "{path} enthält noch den nicht ersetzten Platzhalter {token}.",
        "check_recent_changes": (
            "{path} listet {count} letzte Änderungen; halte es kurz (max. {max}) und "
            "verschiebe die Historie nach progress.md."
        ),
        "check_broken_ref": "{path} nennt {ref}, aber die Datei existiert nicht.",
        "check_known_issues": (
            "{path} sagt, es gibt keine bekannten Probleme, aber der Code enthält {count} "
            "TODO/FIXME-Marker."
        ),
        "check_link": "{link} fehlt oder zeigt nicht auf {target}. Führe 'memory-bank sync' aus.",
        "check_foreign_link": (
            "{link} existiert, wird aber nicht von memory-bank verwaltet; lass es selbst auf "
            "{target} zeigen."
        ),
        "check_secret": (
            "{path} scheint ein Geheimnis zu enthalten ({kind}). Entferne es vor dem Commit."
        ),
        "check_date": "{path} enthält ein Datum, das nicht ISO ist: {value}",
        "check_large_note": (
            "{path} hat {size} Zeichen (~{tokens} Tokens) und wird in jeder Sitzung geladen. "
            "Halte die Datei unter {max}: verschiebe Historie nach Git, komprimiere alte "
            "Einträge oder teile die Datei."
        ),
        "check_large_bank": (
            "Die Memory Bank hat {size} Zeichen (~{tokens} Tokens) und geht in jede Sitzung ein. "
            "Halte die gesamte Bank unter {max}: komprimiere alte Einträge und verschiebe "
            "Historie nach Git."
        ),
        "unknown_command": "Unbekannter Befehl: {command}. Führe 'memory-bank help' aus.",
        "unknown_option": "Unbekannte Option: {option}. Führe 'memory-bank help' aus.",
    },
}


def _language_code(value: str | None) -> str | None:
    """Return the language part of a locale string, or None when it names no language."""
    if not value:
        return None
    for candidate in value.split(":"):  # LANGUAGE may hold a list such as "fr:en"
        name = candidate.strip().split(".")[0].split("@")[0].replace("-", "_")
        code = name.split("_")[0].lower()
        if code in _NEUTRAL_LOCALES:
            continue
        return _WINDOWS_NAMES.get(code, code)
    return None


def _system_locale() -> str | None:
    try:
        return locale.getlocale()[0]
    except ValueError:
        return None


@lru_cache(maxsize=1)
def detect_language() -> str:
    """Detect the user's language; fall back to English when it is not supported."""
    for var in _ENV_VARS:
        code = _language_code(os.environ.get(var))
        if code is not None:
            return code if code in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    code = _language_code(_system_locale())
    return code if code in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def t(key: str, **kwargs: object) -> str:
    """Translate ``key`` into the detected language, falling back to English, then the key."""
    catalog = TRANSLATIONS.get(detect_language(), TRANSLATIONS[DEFAULT_LANGUAGE])
    text = catalog.get(key) or TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)
    return text.format(**kwargs) if kwargs else text
