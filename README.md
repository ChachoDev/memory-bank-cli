# memory-bank

[![CI](https://github.com/ChachoDev/memory-bank-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/ChachoDev/memory-bank-cli/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

A Python CLI utility for automating and managing persistent AI Memory Banks across multiple
IDEs and agents (Claude Code, Cursor, OpenCode, Pi), built for
[`uv`](https://docs.astral.sh/uv/). Its messages come in English,
Spanish, French and German, picked from your operating system's language.

The Memory Bank concept was created by [Nick Baumann](https://github.com/nickbaumann98) for
[Cline](https://cline.bot). This is an independent implementation of that idea for several
agents; see [Credits](#credits).

**Languages:** [English](#english) · [Español](#español) · [Français](#français) · [Deutsch](#deutsch)

---

## English

### What it is

AI agents forget everything between sessions, and each tool keeps its own private memory. The
Memory Bank is a `memory-bank/` folder of Markdown files, committed with your code, that every
agent reads before it starts and updates when it finishes.

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

### How it works

1. You install `memory-bank` once (globally, or per project) and run `memory-bank start` inside
   a Git repository.
2. It writes the six Markdown files above, links every agent's rules file to
   `memory-bank/instructions.md`, and configures the lifecycle hooks it can.
3. From then on, every agent session loads the memory bank before working.
4. When the agent changes code, the hooks (or the rules in `instructions.md`) make it update
   `activeContext.md` and `progress.md` before finishing.
5. You commit the result with the code. The next session, and your teammates, start with context.

### Requirements

- **Git.** Every command checks first that it runs inside a Git repository and stops otherwise.
- **uv** ([install it](https://docs.astral.sh/uv/getting-started/installation/)).
- Python 3.10 or newer (uv can install it for you).
- No third-party runtime dependencies and no network access when the CLI runs. It only calls
  `git` as an external command.

### Installation: global vs per project

Pick **one** of these. For normal use, the global install is the recommended one because the
agent hooks need to find the `memory-bank` command from any shell.

| Mode | Command | Where it lives | Best for |
|------|---------|----------------|----------|
| **Global** (recommended) | `uv tool install git+https://github.com/ChachoDev/memory-bank-cli` | Isolated env in `~/.local/share/uv/tools/memory-bank-cli`; command in `~/.local/bin` | Daily use in every repository; hooks always work |
| **Per project** | `uv add --dev git+https://github.com/ChachoDev/memory-bank-cli` | The repository's `.venv/`; pinned in `pyproject.toml` and `uv.lock` | Pinning the tool version in one repository or in CI |
| **Without installing** | `uvx --from git+https://github.com/ChachoDev/memory-bank-cli memory-bank start` | Temporary env in the uv cache | Trying it once, or generating the files in a sandbox |

#### Global install (recommended)

```bash
# straight from GitHub:
uv tool install git+https://github.com/ChachoDev/memory-bank-cli

# or from a local clone:
git clone https://github.com/ChachoDev/memory-bank-cli
cd memory-bank-cli && uv tool install .

# verify:
memory-bank --version
memory-bank help
```

`uv` creates an isolated environment, downloads only the package, and puts the `memory-bank`
command on your PATH. The package has no runtime dependencies. The hooks that `start` writes call
`memory-bank` directly, so a global install is what makes them work in every repository without
activating anything.

Upgrade after pulling new changes:

```bash
uv tool install --reinstall git+https://github.com/ChachoDev/memory-bank-cli
memory-bank sync            # refresh links and hooks in each repository
```

Uninstall (the generated files stay in your repositories):

```bash
uv tool uninstall memory-bank-cli
```

Development mode, where code changes apply immediately:

```bash
uv tool install --editable .
# or, inside a virtual environment:
uv venv && uv pip install -e .
# or run it without installing it globally:
uv run --no-dev memory-bank help
```

#### Per-project install

Use this when a repository must pin the exact tool version, for example in a monorepo or in CI:

```bash
cd my-repository
uv add --dev git+https://github.com/ChachoDev/memory-bank-cli
uv run memory-bank start
```

The command now lives in `my-repository/.venv/bin/memory-bank`, and `uv.lock` pins it. **Caveat:
the generated hooks call the bare `memory-bank` command.** They work if the environment that
launches your agent has `.venv/bin` on its PATH (for example, you opened the agent from a shell
where the venv is active). If you launch the agent from a desktop icon or an IDE that does not
activate the venv, the hook cannot find the command and Claude Code shows a non-blocking error.
In that case, install globally as well, or keep the venv active when you start the agent.

#### Try it without installing

```bash
uvx --from git+https://github.com/ChachoDev/memory-bank-cli memory-bank start
```

This generates the memory bank and the configuration, but the hooks will not find `memory-bank`
later. Use it to inspect the output or for a one-off run, not as your daily setup.

### Scenario 1: a brand-new project with no code

```bash
mkdir my-project
cd my-project
git init
memory-bank start
```

What happens:

1. `start` verifies that you are inside a Git repository.
2. It scans the repository. With no code, it reports
   `No existing code detected: starting from a blank project.`
3. It writes the six Markdown files under `memory-bank/`.
4. It creates the links to `instructions.md` and merges the hooks into `.claude/settings.json`
   and `opencode.json`.
5. It prints `Memory bank ready.`

Next steps:

```bash
# 1. Describe the project while it is still small
$EDITOR memory-bank/projectbrief.md      # scope, goals, requirements
$EDITOR memory-bank/productContext.md    # users and why the product exists

# 2. Commit the memory bank together with the first code
git add memory-bank CLAUDE.md .cursorrules .opencode .claude/settings.json opencode.json
git commit -m "chore: add memory bank"
```

As you build, the agent ticks off `progress.md`, keeps `activeContext.md` current and adds
decisions to `decisionLog.md`. You do not need to fill everything by hand.

### Scenario 2: an existing project that already has code

```bash
cd my-existing-repository
memory-bank start
```

What happens:

1. `start` runs from the Git root, even if you are in a subdirectory.
2. The scanner looks at the repository root and at source files up to three levels deep. It
   detects Node.js, TypeScript, Python, uv, Flutter/Dart, Rust, Go, Java, Kotlin, .NET, Ruby,
   PHP, Swift, Elixir, Docker, Terraform and more.
3. It prints the detected stack (for example `Existing code detected. Stack: Python, uv,
   Docker`), and writes it into the **Technology stack** section of `projectbrief.md`.
4. It writes the memory bank files, links and hooks exactly as in the blank-project case.

The detected stack is a starting point, not a verdict. Correct or complete it by hand in
`projectbrief.md`, then fill in the scope, goals and users. The agent uses those files as its map
of the project; the more accurate they are, the less you have to repeat yourself.

If the repository already has its own `CLAUDE.md`, `.cursorrules` or
`.opencode/rules/memory.md`, **memory-bank never overwrites them**. It reports the file as
foreign and leaves it alone. To wire it to the single source of truth:

- **Claude Code:** add the line `@memory-bank/instructions.md` to your `CLAUDE.md`. Claude Code
  imports it.
- **Cursor:** make `.cursorrules` a symlink to `memory-bank/instructions.md`, or copy its rules.
- **OpenCode:** add `"memory-bank/*.md"` to the `instructions` array in `opencode.json` (or
  `opencode.jsonc`, which memory-bank never edits).

### Scenario 3: the repository already has a memory bank

`start` refuses to run when `memory-bank/` already exists, so it cannot destroy notes:

```text
The memory bank already exists in /path/to/memory-bank.
Use 'memory-bank sync' to repair it or 'memory-bank reset' to start over.
```

- If the folder is an existing memory bank (from Cline or written by hand), run
  `memory-bank sync`. It keeps every existing note, adds only missing files, recreates missing
  links and fixes outdated hooks. Files with the same six standard names are respected as they
  are.
- If you want the standard layout from scratch, run `memory-bank reset`. It deletes the folder
  and rebuilds it, so commit or back up anything you care about first.

### `sync`: repair without losing your notes

Run `sync` whenever the generated setup may have drifted:

- after pulling changes made by a teammate;
- after upgrading `memory-bank` (`uv tool install --reinstall ...` then `memory-bank sync`);
- after adding a new agent or deleting its config file;
- when a link is missing, a copied rules file is stale, or a hook command is outdated;
- when `start` says the memory bank already exists and you only want it healthy.

```bash
memory-bank sync
```

What it does:

| Situation | `sync` behaviour |
|-----------|------------------|
| A note is missing | Creates it from the current template |
| A link is missing or broken | Recreates the relative symlink |
| A marked copy is outdated | Refreshes it from `instructions.md` |
| A hook command is outdated | Rewrites it to the current `memory-bank hook ...` |
| `opencode.json` lacks the instruction entry | Adds `"memory-bank/*.md"` |
| A note already exists | **Keeps it untouched** |
| `CLAUDE.md` or `.cursorrules` is foreign | Reports it, leaves it untouched |
| A JSON config is invalid | Reports it, leaves it untouched |
| `opencode.jsonc` is used | Skips it and asks you to add the entry manually |
| You added extra `.md` notes | Keeps them and loads them after the standard ones |

What it never does: overwrite or merge the content of existing notes, delete files, resolve
conflicts between your notes and the templates, or fix a foreign agent file for you.

### `reset`: start from scratch

```bash
memory-bank reset          # warns, then asks for confirmation
memory-bank reset --yes    # no prompt (CI, scripts)
```

It deletes `memory-bank/` and regenerates every file from the templates, including the detected
stack. Only Git history can bring back what it deletes. Links and hook configuration are rebuilt
too.

### What `start` creates

```text
your-repository/
├── memory-bank/
│   ├── projectbrief.md
│   ├── productContext.md
│   ├── activeContext.md
│   ├── progress.md
│   ├── decisionLog.md
│   └── instructions.md
├── CLAUDE.md -> memory-bank/instructions.md
├── .cursorrules -> memory-bank/instructions.md
├── .opencode/rules/memory.md -> memory-bank/instructions.md
├── .claude/settings.json      # hooks merged into your settings
└── opencode.json              # instructions merged into your config
```

Where the OS forbids symlinks (Windows without Developer Mode, some network drives and
sandboxes), memory-bank writes a copy that starts with a `<!-- memory-bank: copy ... -->` marker,
and `sync` keeps that copy up to date. An existing file at any of those paths is never
overwritten.

### Links to a single source of truth

`memory-bank/instructions.md` holds the agent rules. `start` links each tool's rules file to it:

| Link | Read by |
|------|---------|
| `CLAUDE.md` | Claude Code, Pi, and OpenCode as a fallback |
| `.cursorrules` | Cursor |
| `.opencode/rules/memory.md` | OpenCode |

The links are relative symlinks, so they survive moving or cloning the repository.

### Automatic hooks

| Moment | Claude Code | OpenCode | Cursor, Pi |
|--------|-------------|----------|------------|
| Session start | `SessionStart` hook runs `memory-bank hook session-start`; its output, the whole memory bank, goes into the context | `opencode.json` → `"instructions": ["memory-bank/*.md"]` loads every file | `.cursorrules` or `CLAUDE.md` tells the agent to read `memory-bank/` first |
| After code changes / session end | `Stop` hook runs `memory-bank hook stop`: if a changed file is newer than `activeContext.md` or `progress.md`, the agent is told to update them before it finishes | Rule in `instructions.md` | Rule in `instructions.md` |

Hook configuration is **merged** into existing `.claude/settings.json` and `opencode.json`; your
other settings are kept. If one of them is invalid JSON, it is left untouched and reported. If
you use `opencode.jsonc`, add `"memory-bank/*.md"` to its `instructions` yourself.

The `Stop` hook blocks at most once per turn (it respects `stop_hook_active`), so it cannot loop.
It ignores changes inside `memory-bank/` and the files memory-bank manages. It compares file
modification times using `git status`: if any changed code file is newer than either
`activeContext.md` or `progress.md`, it asks for an update.

The Claude Code hooks call the `memory-bank` command, so every teammate needs it installed
(`uv tool install`). When it is missing, Claude Code reports a non-blocking hook error and carries
on.

### Working in a team and in CI

Commit the generated files with your code:

```bash
git add memory-bank CLAUDE.md .cursorrules .opencode .claude/settings.json opencode.json
git commit -m "chore: add memory bank"
```

- **Every teammate** should install `memory-bank` globally if they want the hooks. Without it,
  the files still work as plain documentation and Claude Code only logs a non-blocking error.
- **After pulling**, run `memory-bank sync` if links, copies or hooks may have changed.
- **CI** does not need the memory bank to build your project. If you use the per-project install,
  keep the pinned version in `uv.lock`; do not run `reset` in CI, because it destroys notes.
- **Never commit** `.venv/` or the tool's cache. The generated files and configs are what you
  share.

### Language

The CLI language comes from `MEMORY_BANK_LANG`, then `LC_ALL`, `LC_MESSAGES`, `LANG`, `LANGUAGE`,
then the system locale. Supported: `en`, `es`, `fr`, `de`. Anything else falls back to English.

```bash
MEMORY_BANK_LANG=de memory-bank help
```

The templates stay in English because their main reader is the agent.

### Troubleshooting

| Message or symptom | Cause | Fix |
|--------------------|-------|-----|
| `Git is not installed or not on PATH` | Git is missing | Install Git and reopen the shell |
| `... is not inside a Git repository` | The folder has no `.git` | Run `git init` (or `cd` into the repository) |
| `The memory bank already exists` | `start` was run twice | Use `sync` to repair it or `reset` to start over |
| `There is no memory bank` on `sync` | `start` was never run | Run `memory-bank start` |
| `CLAUDE.md exists and is not managed` | You have your own file | Add `@memory-bank/instructions.md` to it, or link it yourself |
| `symlinks are not available` | OS or sandbox forbids them | Nothing to do: a marked copy was written; `sync` refreshes it |
| `opencode.jsonc found` | JSONC is not edited | Add `"memory-bank/*.md"` to its `instructions` by hand |
| `... is not valid JSON` | Broken config | Fix the JSON, then run `sync` |
| Hooks do nothing / `memory-bank: command not found` | Only a per-project install, venv not active | Install globally, or activate the venv before starting the agent |
| `This is not an interactive terminal` on `reset` | No TTY | Add `--yes` |
| Help appears in the wrong language | Locale detection | Set `MEMORY_BANK_LANG=en` (or `es`, `fr`, `de`) |
| OpenCode does not load the files | No `instructions` entry | Add `"memory-bank/*.md"` to `opencode.json` and restart the session |

### Command reference

```bash
memory-bank help            # usage, in your system's language
memory-bank start           # create memory-bank/, agent links and hooks
memory-bank sync            # repair missing files, broken links, outdated hooks; keeps notes
memory-bank reset           # delete memory-bank/ and regenerate it (asks first)
memory-bank reset --yes     # same, without the prompt (CI, scripts)
memory-bank hook session-start   # internal, called by the Claude Code SessionStart hook
memory-bank hook stop            # internal, called by the Claude Code Stop hook
```

Exit codes: `0` success, `1` error (no Git, already initialised, reset cancelled), `2` wrong
usage.

### Credits

The Memory Bank concept was created by **[Nick Baumann](https://github.com/nickbaumann98)** for
[Cline](https://cline.bot). His original instructions describe a `memory-bank/` folder of
Markdown documents that an agent reads at the start of every session and updates at the end.

This project is an independent, unofficial implementation of that idea: it extends the same file
layout to Claude Code, Cursor, OpenCode and Pi, and automates the links and lifecycle hooks with
a standard-library Python CLI. The concept and its vocabulary belong to Nick Baumann; the
automation, templates, translations and code in this repository are ours.

See [CREDITS.md](CREDITS.md) for the original sources and the full acknowledgements.

---

## Español

**Qué es.** Una carpeta `memory-bank/` de ficheros Markdown versionados con Git que todo agente de
IA lee antes de empezar y actualiza al terminar. Usa Markdown en Git en lugar de una base de datos
porque no necesita ningún servicio, se revisa en las merge requests y sigue a tus ramas.

| Fichero | Contiene |
|---------|----------|
| `projectbrief.md` | Alcance, objetivos, requisitos y stack detectado |
| `productContext.md` | Por qué existe el producto, usuarios y objetivos UX |
| `activeContext.md` | Enfoque actual, cambios recientes y próximos pasos |
| `progress.md` | Qué funciona, qué falta y la fase actual |
| `decisionLog.md` | Decisiones arquitectónicas (estilo ADR) |
| `instructions.md` | Las reglas que siguen los agentes: leer primero, actualizar al final |

**Requisitos:** Git (obligatorio: los comandos abortan fuera de un repositorio), `uv` y Python
3.10 o superior. El CLI no tiene dependencias de ejecución ni accede a la red: solo llama a `git`.

### Instalación: global o por proyecto

| Modo | Comando | Dónde queda | Cuándo usarlo |
|------|---------|-------------|---------------|
| **Global** (recomendado) | `uv tool install git+https://github.com/ChachoDev/memory-bank-cli` | Entorno aislado en `~/.local/share/uv/tools/memory-bank-cli`; comando en `~/.local/bin` | Uso diario en todos los repositorios; los hooks siempre funcionan |
| **Por proyecto** | `uv add --dev git+https://github.com/ChachoDev/memory-bank-cli` | El `.venv/` del repositorio; queda fijado en `pyproject.toml` y `uv.lock` | Fijar la versión en un repositorio concreto o en CI |
| **Sin instalar** | `uvx --from git+https://github.com/ChachoDev/memory-bank-cli memory-bank start` | Entorno temporal en la caché de uv | Probar una vez o generar los ficheros en un entorno aislado |

**Global (recomendado):**

```bash
uv tool install git+https://github.com/ChachoDev/memory-bank-cli
memory-bank --version
```

`uv` crea un entorno aislado, descarga solo el paquete y deja `memory-bank` en el PATH. No hay
dependencias de ejecución. Los hooks que escribe `start` llaman directamente a `memory-bank`, así
que la instalación global es la que hace que funcionen en cualquier repositorio sin activar nada.

Actualizar y desinstalar:

```bash
uv tool install --reinstall git+https://github.com/ChachoDev/memory-bank-cli
memory-bank sync                 # refresca enlaces y hooks en cada repositorio
uv tool uninstall memory-bank-cli
```

**Por proyecto:** útil para fijar la versión, pero ten en cuenta que los hooks ejecutan
`memory-bank` sin ruta absoluta. Funcionan si el entorno que lanza el agente tiene `.venv/bin` en
el PATH (por ejemplo, abriendo el agente desde una terminal con el venv activo). Si lo lanzas
desde el escritorio o un IDE que no activa el venv, el hook no encontrará el comando y Claude Code
mostrará un error no bloqueante: en ese caso instálalo también globalmente.

### Caso 1: proyecto nuevo, sin código

```bash
mkdir mi-proyecto
cd mi-proyecto
git init
memory-bank start
```

`start` comprueba que estás en un repositorio Git, no encuentra código
(`No existing code detected: starting from a blank project.`), crea los seis ficheros, los enlaces
y los hooks, y termina con `Memory bank ready.`

Después:

```bash
$EDITOR memory-bank/projectbrief.md      # alcance, objetivos, requisitos
$EDITOR memory-bank/productContext.md    # usuarios y motivo del producto
git add memory-bank CLAUDE.md .cursorrules .opencode .claude/settings.json opencode.json
git commit -m "chore: add memory bank"
```

A medida que construyas, el agente marca lo hecho en `progress.md`, mantiene `activeContext.md`
al día y añade decisiones a `decisionLog.md`.

### Caso 2: proyecto que ya tiene código

```bash
cd mi-repositorio-existente
memory-bank start
```

- Se ejecuta desde la raíz del repositorio aunque estés en un subdirectorio.
- El escáner mira la raíz y los ficheros fuente hasta tres niveles y detecta Node.js, TypeScript,
  Python, uv, Flutter/Dart, Rust, Go, Java, Kotlin, .NET, Ruby, PHP, Swift, Elixir, Docker,
  Terraform y más.
- Imprime el stack detectado (por ejemplo `Existing code detected. Stack: Python, uv, Docker`) y
  lo escribe en la sección **Technology stack** de `projectbrief.md`.
- Crea los ficheros, enlaces y hooks igual que en un proyecto vacío.

El stack detectado es una pista, no una verdad absoluta: corrígelo o complétalo a mano en
`projectbrief.md` y rellena el alcance, los objetivos y los usuarios.

Si ya tienes tu propio `CLAUDE.md`, `.cursorrules` o `.opencode/rules/memory.md`, **no se
sobrescribe nada**. Para conectarlo con la fuente única de reglas:

- **Claude Code:** añade `@memory-bank/instructions.md` a tu `CLAUDE.md`.
- **Cursor:** haz que `.cursorrules` sea un symlink a `memory-bank/instructions.md`, o copia sus
  reglas.
- **OpenCode:** añade `"memory-bank/*.md"` al array `instructions` de `opencode.json` (o de
  `opencode.jsonc`, que memory-bank nunca edita).

### Caso 3: el repositorio ya tiene un memory bank

`start` se niega a ejecutarse si `memory-bank/` ya existe, para no destruir notas:

- Si es un memory bank existente (de Cline o hecho a mano), usa `memory-bank sync`: conserva todas
  las notas, crea solo lo que falta, recrea enlaces rotos y corrige hooks desactualizados.
- Si quieres el formato estándar desde cero, usa `memory-bank reset`: borra la carpeta y la
  reconstruye. Haz commit o copia de seguridad antes.

### `sync`: reparar sin perder notas

Ejecútalo tras un `git pull`, tras actualizar la herramienta, al añadir un agente, si falta un
enlace, si una copia está desfasada o si un hook apunta a un comando antiguo.

| Situación | Qué hace `sync` |
|-----------|-----------------|
| Falta una nota | La crea desde la plantilla actual |
| Falta un enlace o está roto | Lo recrea como symlink relativo |
| Una copia marcada está desfasada | La refresca desde `instructions.md` |
| Un hook está desactualizado | Lo reescribe con el comando actual |
| `opencode.json` no tiene la entrada | Añade `"memory-bank/*.md"` |
| La nota ya existe | **No la toca** |
| `CLAUDE.md` o `.cursorrules` es ajeno | Lo reporta y no lo toca |
| Un JSON no es válido | Lo reporta y no lo toca |
| Se usa `opencode.jsonc` | Lo omite y te pide añadir la entrada a mano |
| Tienes notas `.md` adicionales | Las conserva y las carga después de las estándar |

Nunca sobrescribe ni mezcla el contenido de notas existentes, no borra ficheros, no resuelve
conflictos entre tus notas y las plantillas y no arregla por ti un fichero de agente ajeno.

### `reset`: empezar de cero

```bash
memory-bank reset          # avisa y pide confirmación
memory-bank reset --yes    # sin preguntar (CI, scripts)
```

Borra `memory-bank/`, lo regenera desde las plantillas (incluido el stack detectado) y reconstruye
enlaces y hooks. Solo el historial de Git puede recuperar lo borrado.

### Qué crea `start`

```text
tu-repositorio/
├── memory-bank/
│   ├── projectbrief.md
│   ├── productContext.md
│   ├── activeContext.md
│   ├── progress.md
│   ├── decisionLog.md
│   └── instructions.md
├── CLAUDE.md -> memory-bank/instructions.md
├── .cursorrules -> memory-bank/instructions.md
├── .opencode/rules/memory.md -> memory-bank/instructions.md
├── .claude/settings.json      # hooks mezclados con tus ajustes
└── opencode.json              # instructions mezcladas con tu configuración
```

Donde el sistema no permite symlinks (Windows sin Developer Mode, algunas unidades de red y
sandboxes), se escribe una copia marcada que `sync` mantiene al día. Un fichero propio en esas
rutas nunca se sobrescribe.

**Enlaces:** `CLAUDE.md`, `.cursorrules` y `.opencode/rules/memory.md` apuntan a
`memory-bank/instructions.md` mediante symlinks relativos, así que sobreviven a un clonado o a
mover el repositorio.

**Hooks:** en Claude Code, `SessionStart` carga el Memory Bank en el contexto y `Stop` obliga a
actualizar `activeContext.md` y `progress.md` tras cambiar código (bloquea como máximo una vez por
turno, así que no entra en bucle). En OpenCode, `opencode.json` carga `memory-bank/*.md` en cada
sesión. En Cursor y Pi, las reglas de `instructions.md`. La configuración se mezcla con la tuya;
un JSON inválido se deja intacto y se reporta.

### Equipo y CI

Haz commit de los ficheros generados con tu código:

```bash
git add memory-bank CLAUDE.md .cursorrules .opencode .claude/settings.json opencode.json
git commit -m "chore: add memory bank"
```

- Cada compañero debe instalar `memory-bank` globalmente si quiere los hooks. Sin él, los ficheros
  siguen sirviendo como documentación y Claude Code solo registra un error no bloqueante.
- Tras un `git pull`, ejecuta `memory-bank sync` si pueden haber cambiado enlaces, copias o hooks.
- CI no necesita el memory bank para compilar. Si usas la instalación por proyecto, mantén la
  versión fijada en `uv.lock`; no ejecutes `reset` en CI, porque borra notas.
- No hagas commit de `.venv/` ni de la caché de la herramienta.

### Idioma

Se detecta de `MEMORY_BANK_LANG`, luego `LC_ALL`, `LC_MESSAGES`, `LANG`, `LANGUAGE` y el locale del
sistema. Soportados: `en`, `es`, `fr`, `de`; el resto cae en inglés. Fuérzalo con
`MEMORY_BANK_LANG=es memory-bank help`. Las plantillas se quedan en inglés porque su lector
principal es el agente.

### Problemas habituales

| Mensaje o síntoma | Causa | Solución |
|-------------------|-------|----------|
| `Git is not installed or not on PATH` | Falta Git | Instálalo y abre de nuevo la terminal |
| `... is not inside a Git repository` | La carpeta no tiene `.git` | Ejecuta `git init` o entra en el repositorio |
| `The memory bank already exists` | `start` ejecutado dos veces | Usa `sync` para reparar o `reset` para empezar de cero |
| `There is no memory bank` en `sync` | Nunca se ejecutó `start` | Ejecuta `memory-bank start` |
| `CLAUDE.md exists and is not managed` | Tienes un fichero propio | Añade `@memory-bank/instructions.md` o enlázalo tú |
| `symlinks are not available` | El sistema no permite symlinks | No hagas nada: se escribió una copia marcada que `sync` refresca |
| `opencode.jsonc found` | JSONC no se edita | Añade `"memory-bank/*.md"` a `instructions` a mano |
| `... is not valid JSON` | Configuración rota | Corrige el JSON y ejecuta `sync` |
| Los hooks no hacen nada / `memory-bank: command not found` | Instalación solo por proyecto sin venv activo | Instala globalmente o activa el venv antes de abrir el agente |
| `This is not an interactive terminal` en `reset` | No hay TTY | Añade `--yes` |
| La ayuda sale en otro idioma | Detección del locale | Usa `MEMORY_BANK_LANG=es` (o `en`, `fr`, `de`) |
| OpenCode no carga los ficheros | Falta la entrada `instructions` | Añádela a `opencode.json` y reinicia la sesión |

### Comandos y códigos de salida

```bash
memory-bank help            # ayuda en el idioma del sistema
memory-bank start           # crea memory-bank/, los enlaces y los hooks
memory-bank sync            # repara lo que falta sin tocar tus notas
memory-bank reset           # borra y regenera memory-bank/ (pide confirmación)
memory-bank reset --yes     # lo mismo, sin preguntar (CI, scripts)
```

Códigos: `0` éxito, `1` error (sin Git, ya inicializado, reset cancelado), `2` uso incorrecto.

**Créditos:** la idea original del Memory Bank es de
[Nick Baumann](https://github.com/nickbaumann98), creada para [Cline](https://cline.bot). Este
proyecto es una implementación independiente de esa idea. Ver [CREDITS.md](CREDITS.md).

---

## Français

**Qu'est-ce que c'est.** Un dossier `memory-bank/` de fichiers Markdown versionnés avec Git, que
chaque agent IA lit avant de commencer et met à jour en fin de travail. Markdown dans Git plutôt
qu'une base de données : aucun service à faire tourner, relecture dans les merge requests, et la
mémoire suit vos branches.

| Fichier | Contient |
|---------|----------|
| `projectbrief.md` | Périmètre, objectifs, exigences et pile détectée |
| `productContext.md` | Pourquoi le produit existe, utilisateurs, objectifs UX |
| `activeContext.md` | Focus actuel, changements récents, prochaines étapes |
| `progress.md` | Ce qui fonctionne, ce qui reste, phase en cours |
| `decisionLog.md` | Décisions d'architecture (style ADR) |
| `instructions.md` | Les règles que suivent les agents : lire d'abord, mettre à jour à la fin |

**Prérequis :** Git (obligatoire : les commandes s'arrêtent hors d'un dépôt), `uv` et Python 3.10
ou plus. Aucune dépendance d'exécution, aucun accès réseau : le CLI appelle seulement `git`.

### Installation : globale ou par projet

| Mode | Commande | Emplacement | Usage |
|------|----------|-------------|-------|
| **Globale** (recommandée) | `uv tool install git+https://github.com/ChachoDev/memory-bank-cli` | Environnement isolé dans `~/.local/share/uv/tools/memory-bank-cli` ; commande dans `~/.local/bin` | Usage quotidien dans tous les dépôts ; les hooks fonctionnent toujours |
| **Par projet** | `uv add --dev git+https://github.com/ChachoDev/memory-bank-cli` | Le `.venv/` du dépôt ; version figée dans `pyproject.toml` et `uv.lock` | Figer la version dans un dépôt ou en CI |
| **Sans installer** | `uvx --from git+https://github.com/ChachoDev/memory-bank-cli memory-bank start` | Environnement temporaire du cache uv | Essayer une fois ou générer les fichiers dans un bac à sable |

Les hooks générés appellent la commande `memory-bank` sans chemin absolu : l'installation globale
est donc recommandée. En installation par projet, ils fonctionnent si l'environnement qui lance
l'agent a `.venv/bin` dans son PATH ; sinon Claude Code signale une erreur non bloquante.

### Projet vide et projet existant

```bash
# nouveau projet
mkdir mon-projet && cd mon-projet
git init
memory-bank start

# projet qui a déjà du code
cd mon-depot-existant
memory-bank start
```

`start` vérifie Git, scanne la racine et les fichiers source jusqu'à trois niveaux, puis écrit les
six fichiers Markdown, les liens et les hooks. Sur un projet vide il indique
`No existing code detected` ; sur un projet existant il affiche le stack détecté (Node.js,
TypeScript, Python, uv, Flutter/Dart, Rust, Go, Java, Kotlin, .NET, Ruby, PHP, Swift, Elixir,
Docker, Terraform, etc.) et l'écrit dans `projectbrief.md`.

Un `CLAUDE.md`, `.cursorrules` ou `.opencode/rules/memory.md` existant n'est **jamais**
écrasé. Pour le relier : ajoutez `@memory-bank/instructions.md` à `CLAUDE.md`, pointez
`.cursorrules` vers `memory-bank/instructions.md`, ou ajoutez `"memory-bank/*.md"` aux
`instructions` d'`opencode.json` (`opencode.jsonc` n'est jamais modifié).

Si `memory-bank/` existe déjà, `start` s'arrête. Utilisez `memory-bank sync` pour réparer sans
toucher aux notes, ou `memory-bank reset` pour tout recréer (destructif, confirmation demandée ;
`--yes` en CI).

### `sync` et `reset`

`sync` s'exécute après un `git pull`, une mise à jour de l'outil, l'ajout d'un agent, ou si un lien
ou un hook semble cassé :

- crée les fichiers manquants, recrée les liens et les copies marquées, corrige les hooks
  obsolètes et ajoute l'entrée OpenCode manquante ;
- **ne touche jamais** au contenu des notes existantes, aux fichiers d'agent étrangers, aux JSON
  invalides ni à `opencode.jsonc` ;
- conserve les notes `.md` supplémentaires.

`reset` supprime `memory-bank/` et le régénère depuis les modèles. Seul l'historique Git peut
restaurer les notes supprimées.

### Équipe et CI

Commitez `memory-bank/`, `CLAUDE.md`, `.cursorrules`, `.opencode/`, `.claude/settings.json` et
`opencode.json` avec le code. Chaque coéquipier installe l'outil globalement pour les hooks ; sans
lui, les fichiers restent utilisables et Claude Code affiche seulement une erreur non bloquante.
Après un `git pull`, lancez `memory-bank sync`. Ne commitez pas `.venv/` et ne lancez pas `reset`
en CI.

**Langue :** détectée depuis le système ; forcez-la avec `MEMORY_BANK_LANG=fr`. Les modèles
restent en anglais car leur lecteur principal est l'agent.

**Crédits :** l'idée originale du Memory Bank est de
[Nick Baumann](https://github.com/nickbaumann98), créée pour [Cline](https://cline.bot). Ce
projet est une implémentation indépendante de cette idée. Voir [CREDITS.md](CREDITS.md).

---

## Deutsch

**Was es ist.** Ein Ordner `memory-bank/` mit Markdown-Dateien in Git, den jeder KI-Agent vor dem
Start liest und am Ende aktualisiert. Markdown in Git statt einer Datenbank: kein Dienst nötig,
Review in Merge Requests, und das Gedächtnis folgt deinen Branches.

| Datei | Enthält |
|-------|---------|
| `projectbrief.md` | Umfang, Ziele, Anforderungen und erkannter Stack |
| `productContext.md` | Warum es das Produkt gibt, Nutzer, UX-Ziele |
| `activeContext.md` | Aktueller Fokus, letzte Änderungen, nächste Schritte |
| `progress.md` | Was funktioniert, was fehlt, aktuelle Phase |
| `decisionLog.md` | Architekturentscheidungen (ADR-Stil) |
| `instructions.md` | Die Regeln der Agenten: zuerst lesen, zuletzt aktualisieren |

**Voraussetzungen:** Git (Pflicht: außerhalb eines Repositorys brechen die Befehle ab), `uv` und
Python 3.10 oder neuer. Keine Laufzeitabhängigkeiten, kein Netzwerkzugriff: das CLI ruft nur `git`
auf.

### Installation: global oder pro Projekt

| Modus | Befehl | Speicherort | Wofür |
|-------|--------|-------------|-------|
| **Global** (empfohlen) | `uv tool install git+https://github.com/ChachoDev/memory-bank-cli` | Isolierte Umgebung in `~/.local/share/uv/tools/memory-bank-cli`; Befehl in `~/.local/bin` | Täglicher Einsatz in allen Repositorys; Hooks funktionieren immer |
| **Pro Projekt** | `uv add --dev git+https://github.com/ChachoDev/memory-bank-cli` | Das `.venv/` des Repositorys; Version in `pyproject.toml` und `uv.lock` fixiert | Version in einem Repository oder in CI fixieren |
| **Ohne Installation** | `uvx --from git+https://github.com/ChachoDev/memory-bank-cli memory-bank start` | Temporäre Umgebung im uv-Cache | Einmal ausprobieren oder Dateien in einer Sandbox erzeugen |

Die erzeugten Hooks rufen `memory-bank` ohne absoluten Pfad auf, deshalb ist die globale
Installation empfohlen. Bei einer Installation pro Projekt funktionieren sie nur, wenn die
Umgebung, die den Agenten startet, `.venv/bin` im PATH hat; sonst meldet Claude Code einen
nicht blockierenden Fehler.

### Leeres Projekt und bestehendes Projekt

```bash
# neues Projekt
mkdir mein-projekt && cd mein-projekt
git init
memory-bank start

# Projekt mit vorhandenem Code
cd mein-bestehendes-repo
memory-bank start
```

`start` prüft Git, durchsucht die Wurzel und Quelldateien bis zu drei Ebenen tief und schreibt
dann die sechs Markdown-Dateien, die Links und die Hooks. Bei einem leeren Projekt meldet es
`No existing code detected`; bei vorhandenem Code zeigt es den erkannten Stack (Node.js,
TypeScript, Python, uv, Flutter/Dart, Rust, Go, Java, Kotlin, .NET, Ruby, PHP, Swift, Elixir,
Docker, Terraform und mehr) und schreibt ihn in `projectbrief.md`.

Eine vorhandene `CLAUDE.md`, `.cursorrules` oder `.opencode/rules/memory.md` wird **niemals**
überschrieben. Zum Verbinden: `@memory-bank/instructions.md` in `CLAUDE.md` eintragen,
`.cursorrules` auf `memory-bank/instructions.md` zeigen lassen oder `"memory-bank/*.md"` zu den
`instructions` in `opencode.json` hinzufügen (`opencode.jsonc` wird nie bearbeitet).

Existiert `memory-bank/` bereits, bricht `start` ab. Nutze `memory-bank sync`, um ohne Änderung
der Notizen zu reparieren, oder `memory-bank reset`, um alles neu zu erzeugen (destruktiv,
Rückfrage; `--yes` für CI).

### `sync` und `reset`

`sync` läuft nach `git pull`, nach einem Update des Tools, beim Hinzufügen eines Agenten oder wenn
ein Link oder Hook defekt wirkt:

- erstellt fehlende Dateien, erneuert Links und markierte Kopien, korrigiert veraltete Hooks und
  ergänzt den fehlenden OpenCode-Eintrag;
- **ändert nie** den Inhalt vorhandener Notizen, fremder Agentendateien, ungültiger JSON-Dateien
  oder von `opencode.jsonc`;
- behält zusätzliche `.md`-Notizen.

`reset` löscht `memory-bank/` und erzeugt es aus den Vorlagen neu. Nur die Git-Historie kann
gelöschte Notizen wiederherstellen.

### Team und CI

Committe `memory-bank/`, `CLAUDE.md`, `.cursorrules`, `.opencode/`, `.claude/settings.json` und
`opencode.json` zusammen mit dem Code. Jedes Teammitglied installiert das Tool global für die
Hooks; ohne Installation bleiben die Dateien nutzbar und Claude Code meldet nur einen nicht
blockierenden Fehler. Nach `git pull` `memory-bank sync` ausführen. `.venv/` nicht committen und
`reset` nicht in CI ausführen.

**Sprache:** wird vom System erkannt; mit `MEMORY_BANK_LANG=de` erzwingen. Die Vorlagen bleiben
englisch, weil ihr Hauptleser der Agent ist.

**Danksagung:** Die ursprüngliche Memory-Bank-Idee stammt von
[Nick Baumann](https://github.com/nickbaumann98), entwickelt für [Cline](https://cline.bot).
Dieses Projekt ist eine unabhängige Umsetzung dieser Idee. Siehe [CREDITS.md](CREDITS.md).

---

## Contributing

Bug reports and pull requests are welcome. Before opening one:

```bash
uv sync --locked
uvx ruff check . && uvx ruff format --check .
uvx mypy --strict memory_bank
uv run pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide and [CHANGELOG.md](CHANGELOG.md)
for release notes. By taking part you agree to follow the
[Code of Conduct](CODE_OF_CONDUCT.md). To report a security issue, read [SECURITY.md](SECURITY.md)
instead of opening a public issue. The project is a standard-library-only Python package, so the
test suite runs without any external service.

## License

[MIT](LICENSE) © 2026 Victor M. Cañada Ojeda.
