# memory-bank

A Markdown **Memory Bank** for AI coding agents (Claude Code, Cursor, OpenCode, Pi), shipped
as a single CLI built for [`uv`](https://docs.astral.sh/uv/). Its messages come in English,
Spanish, French and German, picked from your operating system's language.

**Languages:** [English](#english) · [Español](#español) · [Français](#français) · [Deutsch](#deutsch)

---

## English

### What it is

AI agents forget everything between sessions, and each tool keeps its own private memory.
The Memory Bank is a `memory-bank/` folder of Markdown files, committed with your code, that every
agent reads before it starts and updates when it finishes:

| File | Holds |
|------|-------|
| `projectbrief.md` | Scope, goals, core requirements, detected stack |
| `productContext.md` | Why the product exists, users, UX goals |
| `activeContext.md` | Current focus, recent changes, next steps |
| `progress.md` | What works, what is left, current phase |
| `decisionLog.md` | Architectural decisions (ADR style) |
| `instructions.md` | The rules agents follow: read first, update last |

**Why Markdown in Git instead of a database?** It needs no service to run. Changes show up as
diffs in merge requests, the memory follows your branches, any tool that reads files can use it,
and teammates share it by pulling.

### Requirements

- **Git.** Every command checks first that it runs inside a Git repository and stops otherwise.
- **uv** ([install it](https://docs.astral.sh/uv/getting-started/installation/)).
- Python 3.10 or newer (uv can install it for you). There are no third-party dependencies.

### Installation

Global install, so `memory-bank` works in every repository:

```bash
cd memory-bank-skill
uv tool install .
# upgrade after pulling changes:
uv tool install --reinstall .
```

Development mode (code changes apply right away):

```bash
uv tool install --editable .
# or, inside a virtual environment:
uv venv && uv pip install -e .
# or without installing anything:
uv run memory-bank help
```

### Commands

```bash
memory-bank help            # usage, in your system's language
memory-bank start           # create memory-bank/, agent links and hooks
memory-bank sync            # repair missing files, broken links, outdated hooks; keeps notes
memory-bank reset           # delete memory-bank/ and regenerate it (asks first)
memory-bank reset --yes     # same, without the prompt (CI, scripts)
```

- **start** checks Git, stops if `memory-bank/` already exists, scans the repository for
  existing code (Node.js, TypeScript, Python, Flutter/Dart, Rust, Go, Java, Kotlin, .NET, Ruby,
  PHP, Swift, Elixir, Docker, Terraform and more), writes the templates with the detected stack in
  `projectbrief.md`, then creates the links and hooks.
- **sync** never overwrites a note. It writes only missing files, recreates missing links,
  refreshes fallback copies of `instructions.md` and fixes outdated hook commands.
- **reset** warns, asks for confirmation, then deletes `memory-bank/` and rebuilds it. Only Git
  history can restore what it deletes.

Exit codes: `0` success, `1` error (no Git, already initialised, reset cancelled), `2` wrong usage.

### Links to a single source of truth

`memory-bank/instructions.md` holds the agent rules. `start` links each tool's rules file to it:

| Link | Read by |
|------|---------|
| `CLAUDE.md` | Claude Code, Pi, and OpenCode as a fallback |
| `.cursorrules` | Cursor |
| `.opencode/rules/memory.md` | OpenCode |

The links are relative symlinks, so they survive a move or a clone. Where the OS forbids symlinks
(Windows without Developer Mode, some sandboxes), memory-bank writes a copy that starts with a
`<!-- memory-bank: copy ... -->` marker, and `memory-bank sync` refreshes it.

**An existing file is never overwritten.** If your repository already has a `CLAUDE.md` or a
`.cursorrules`, memory-bank leaves it alone and tells you. You can then add a line to it yourself,
for example `@memory-bank/instructions.md` in `CLAUDE.md`, which Claude Code imports.

### Automatic hooks

| Moment | Claude Code | OpenCode | Cursor, Pi |
|--------|-------------|----------|-----------|
| Session start | `SessionStart` hook runs `memory-bank hook session-start`; its output, the whole memory bank, goes into the context | `opencode.json` → `"instructions": ["memory-bank/*.md"]` loads every file | `.cursorrules` or `CLAUDE.md` tells the agent to read `memory-bank/` first |
| After code changes / session end | `Stop` hook runs `memory-bank hook stop`: if a changed file is newer than `activeContext.md` or `progress.md`, the agent is told to update them before it finishes | Rule in `instructions.md` | Rule in `instructions.md` |

Hook configuration is **merged** into existing `.claude/settings.json` and `opencode.json`; your
other settings are kept. If one of them is invalid JSON, it is left untouched and reported.
If you use `opencode.jsonc`, add `"memory-bank/*.md"` to its `instructions` yourself.

The `Stop` hook blocks at most once per turn (it respects `stop_hook_active`), so it cannot loop.
It ignores changes inside `memory-bank/` and the files memory-bank manages.

The Claude Code hooks call the `memory-bank` command, so every teammate needs it installed
(`uv tool install`). When it is missing, Claude Code reports a non-blocking hook error and carries
on.

### Language

The CLI language comes from `MEMORY_BANK_LANG`, then `LC_ALL`, `LC_MESSAGES`, `LANG`, `LANGUAGE`,
then the system locale. Supported: `en`, `es`, `fr`, `de`. Anything else falls back to English.

```bash
MEMORY_BANK_LANG=de memory-bank help
```

The templates stay in English because their main reader is the agent.

### Commit the result

```bash
git add memory-bank CLAUDE.md .cursorrules .opencode .claude/settings.json opencode.json
git commit -m "chore: add memory bank"
```

---

## Español

**Qué es.** Una carpeta `memory-bank/` de ficheros Markdown versionados con Git que todo agente de
IA lee antes de empezar y actualiza al terminar. Usa Markdown en Git en lugar de una base de datos
porque no necesita ningún servicio, se revisa en las merge requests y sigue a tus ramas.

**Requisitos:** Git (obligatorio: los comandos abortan fuera de un repositorio) y `uv`.

**Instalación:**

```bash
uv tool install .              # global
uv tool install --editable .   # desarrollo
uv venv && uv pip install -e . # desarrollo dentro de un entorno virtual
```

**Comandos:**

```bash
memory-bank start        # crea memory-bank/, los enlaces y los hooks
memory-bank sync         # repara lo que falta sin tocar tus notas
memory-bank reset        # borra y regenera memory-bank/ (pide confirmación; --yes para omitirla)
memory-bank help         # ayuda en el idioma del sistema
```

**Enlaces:** `CLAUDE.md`, `.cursorrules` y `.opencode/rules/memory.md` apuntan a
`memory-bank/instructions.md`. Si ya existe un fichero propio en esa ruta, no se toca.
Si el sistema no permite symlinks, se escribe una copia marcada que `sync` mantiene al día.

**Hooks:** en Claude Code, `SessionStart` carga el Memory Bank en el contexto y `Stop` obliga a
actualizar `activeContext.md` y `progress.md` tras cambiar código. En OpenCode, `opencode.json`
carga `memory-bank/*.md` en cada sesión. En Cursor y Pi, las reglas de `instructions.md`.

**Idioma:** se detecta del sistema; fuérzalo con `MEMORY_BANK_LANG=es`.

---

## Français

**Qu'est-ce que c'est.** Un dossier `memory-bank/` de fichiers Markdown versionnés avec Git, que
chaque agent IA lit avant de commencer et met à jour en fin de travail. Markdown dans Git plutôt
qu'une base de données : aucun service à faire tourner, relecture dans les merge requests, et la
mémoire suit vos branches.

**Prérequis :** Git (obligatoire : les commandes s'arrêtent hors d'un dépôt) et `uv`.

**Installation :**

```bash
uv tool install .              # globale
uv tool install --editable .   # développement
uv venv && uv pip install -e . # développement dans un environnement virtuel
```

**Commandes :**

```bash
memory-bank start        # crée memory-bank/, les liens et les hooks
memory-bank sync         # répare ce qui manque sans toucher à vos notes
memory-bank reset        # supprime et régénère memory-bank/ (confirmation ; --yes pour l'éviter)
memory-bank help         # aide dans la langue du système
```

**Liens :** `CLAUDE.md`, `.cursorrules` et `.opencode/rules/memory.md` pointent vers
`memory-bank/instructions.md`. Un fichier existant à cet emplacement n'est jamais modifié.
Sans liens symboliques, une copie marquée est écrite et `sync` la tient à jour.

**Hooks :** dans Claude Code, `SessionStart` charge le Memory Bank dans le contexte et `Stop` exige
la mise à jour de `activeContext.md` et `progress.md` après un changement de code. Dans OpenCode,
`opencode.json` charge `memory-bank/*.md` à chaque session. Dans Cursor et Pi, les règles
d'`instructions.md`.

**Langue :** détectée depuis le système ; forcez-la avec `MEMORY_BANK_LANG=fr`.

---

## Deutsch

**Was es ist.** Ein Ordner `memory-bank/` mit Markdown-Dateien in Git, den jeder KI-Agent vor dem
Start liest und am Ende aktualisiert. Markdown in Git statt einer Datenbank: kein Dienst nötig,
Review in Merge Requests, und das Gedächtnis folgt deinen Branches.

**Voraussetzungen:** Git (Pflicht: außerhalb eines Repositorys brechen die Befehle ab) und `uv`.

**Installation:**

```bash
uv tool install .              # global
uv tool install --editable .   # Entwicklung
uv venv && uv pip install -e . # Entwicklung in einer virtuellen Umgebung
```

**Befehle:**

```bash
memory-bank start        # legt memory-bank/, Links und Hooks an
memory-bank sync         # repariert Fehlendes, ohne Notizen zu ändern
memory-bank reset        # löscht und erzeugt memory-bank/ neu (mit Rückfrage; --yes überspringt sie)
memory-bank help         # Hilfe in der Systemsprache
```

**Links:** `CLAUDE.md`, `.cursorrules` und `.opencode/rules/memory.md` zeigen auf
`memory-bank/instructions.md`. Eine vorhandene eigene Datei an dieser Stelle bleibt unverändert.
Ohne Symlinks wird eine markierte Kopie geschrieben, die `sync` aktuell hält.

**Hooks:** In Claude Code lädt `SessionStart` die Memory Bank in den Kontext, und `Stop` verlangt
nach Codeänderungen ein Update von `activeContext.md` und `progress.md`. In OpenCode lädt
`opencode.json` in jeder Sitzung `memory-bank/*.md`. In Cursor und Pi gelten die Regeln aus
`instructions.md`.

**Sprache:** wird vom System erkannt; mit `MEMORY_BANK_LANG=de` erzwingen.
