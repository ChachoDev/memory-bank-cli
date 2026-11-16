"""Initial Markdown templates for the memory bank.

Templates are available in four languages (en, es, fr, de). Two placeholders are
filled in at generation time: ``{{DETECTED_STACK}}`` and ``{{DATE}}``.

``instructions.md`` carries a version marker so ``memory-bank check`` can tell a note written by
an older release (which ``sync`` never overwrites) from a current one. Bump
``INSTRUCTIONS_VERSION`` whenever the agent rules change in a way existing banks should adopt.
"""

from __future__ import annotations

from typing import Final

STACK_PLACEHOLDER: Final = "{{DETECTED_STACK}}"
DATE_PLACEHOLDER: Final = "{{DATE}}"

INSTRUCTIONS_FILE: Final = "instructions.md"

SUPPORTED_TEMPLATE_LANGS: Final[tuple[str, ...]] = ("en", "es", "fr", "de")

INSTRUCTIONS_VERSION: Final = "3"

# Order in which hooks inject the files into the agent's context.
READ_ORDER: Final[tuple[str, ...]] = (
    INSTRUCTIONS_FILE,
    "projectbrief.md",
    "productContext.md",
    "activeContext.md",
    "progress.md",
    "decisionLog.md",
)


# ---------------------------------------------------------------------------
# English templates (default)
# ---------------------------------------------------------------------------

_EN_PROJECT_BRIEF: Final = """# Project Brief

> Foundation document. Every other memory bank file builds on it.
> Keep it short and stable; change it only when the project's scope changes.

## Overview

_One paragraph: what this project is and who it is for._

## Goals

- _Goal 1: the main outcome the project must deliver._
- _Goal 2_
- _Goal 3_

## Core requirements

- [ ] _Requirement that must hold for the project to be useful._
- [ ] _Requirement_

## Out of scope

- _What this project deliberately does not do._

## Technology stack

Detected automatically when the memory bank was created:

{{DETECTED_STACK}}

_Correct or complete this list by hand; the agent will keep it up to date._

## Constraints

- _Deadlines, budgets, platforms, compliance or performance limits._
"""

_EN_PRODUCT_CONTEXT: Final = """# Product Context

> Why the project exists and how it should feel to use.

## Problem

_What problem does the product solve? What happens today without it?_

## Users

| User | Need | How the product helps |
|------|------|-----------------------|
| _Primary user_ | _Their need_ | _The answer_ |

## Value proposition

_One or two sentences on why users choose this product._

## User experience goals

- _Example: a new user completes the main task in under two minutes._
- _Example: every error message says what to do next._

## How it should work

_The main user flows, step by step._
"""

_EN_ACTIVE_CONTEXT: Final = """# Active Context

> What is happening right now. The agent updates this file at the end of every session
> that changes code. Keep it short: it describes the present, not history.

## Current focus

_Bootstrapping the memory bank ({{DATE}})._

## Recent changes

- {{DATE}}: memory bank created.

## Next steps

1. Fill in `projectbrief.md` and `productContext.md`.
2. _Next concrete task._

## Open questions and blockers

- _None yet._

## Active decisions and considerations

- _Trade-offs being weighed right now. Move settled ones to `decisionLog.md`._
"""

_EN_PROGRESS: Final = """# Progress

> Status of the build. The agent ticks items off and adds new ones as work lands.

## Current phase

**Phase 0: Setup** (since {{DATE}})

## What works

- [x] Memory bank initialised

## What is left to build

- [ ] _Feature or task_
- [ ] _Feature or task_

## Known issues

- _None yet._

## Milestones

| Phase | Goal | Status |
|-------|------|--------|
| 0. Setup | Repository, tooling and memory bank | In progress |
| 1. MVP | _Smallest useful release_ | Not started |
"""

_EN_DECISION_LOG: Final = """# Decision Log

> Architectural decisions, newest last. Never rewrite an entry to change its meaning: add a new one
> that supersedes it. Compression under the size budget (see `instructions.md`) is the only
> exception: the decision and its constraint stay, the deliberation goes to Git history.
> Format: context, decision, alternatives considered, consequences.

## ADR-001: Keep project memory in Markdown files versioned with Git

- **Date:** {{DATE}}
- **Status:** Accepted
- **Context:** AI coding agents lose their context between sessions and across tools
  (Claude Code, Cursor, OpenCode, Pi). They need a shared, durable memory of the project.
- **Decision:** Store that memory as plain Markdown files in `memory-bank/`, committed to Git.
  Every agent reads them at the start of a session and updates them at the end.
- **Alternatives considered:**
  - A vector or relational database: needs a running service, hides content from code review
    and ties the memory to one tool.
  - Each tool's private memory: not shared between tools or teammates.
- **Consequences:**
  - Memory is reviewable in merge requests, diffable and branch-aware.
  - Any tool that reads files can use it; no service to run.
  - Files must stay concise, because they are loaded into the agent's context window.

<!-- Next decision: copy the shape above, use the next ADR number and keep the newest last. -->
"""

_EN_INSTRUCTIONS: Final = """# Memory Bank Instructions for AI Agents

<!-- memory-bank: instructions v3 -->

> This is the single source of truth for agent rules in this repository.
> `AGENTS.md`, `CLAUDE.md`, `.cursorrules` and `.opencode/rules/memory.md` link to this file:
> edit `memory-bank/instructions.md`, never the links.

I am an AI coding agent whose memory resets between sessions. The `memory-bank/` folder is my
only memory of this project, so I rely on it completely.

## 1. Before doing anything: read the memory bank

At the start of every session, before answering the first message, I read every file in
`memory-bank/`, silently, in this order:

1. `projectbrief.md`: scope, goals and core requirements.
2. `productContext.md`: why the product exists and for whom.
3. `activeContext.md`: what is being worked on now and the next steps.
4. `progress.md`: what works, what is left and the current phase.
5. `decisionLog.md`: decisions already taken; I do not reopen them without a reason.
6. Any other `.md` file in `memory-bank/`.

If a hook has already injected the memory bank into my context, I do not read it again.
If the files contradict the code, the code is the truth: I say so and fix the memory bank.

## 2. While working

- I follow the decisions in `decisionLog.md`. When I take a new architectural decision
  (a library, a pattern, a data model, a trade-off), I append an entry there.
- I respect the scope in `projectbrief.md`. If a request falls outside it, I say so.

## 3. Before finishing: update the memory bank

After any significant change to the code, before ending my turn, I update:

- `activeContext.md`: current focus, recent changes (dated) and the next steps.
- `progress.md`: tick off what now works, add what is left, note new known issues.
- `decisionLog.md`: only if I took a decision worth recording.

When the user says **"update memory bank"**, I review every file and update all of them.

## 4. Rules for the files

- Concise and factual: these files are loaded into every session's context.
- `activeContext.md` describes the present; move history into `progress.md` or `decisionLog.md`.
- The bank stays small: it enters every session's context. When `memory-bank check` reports a
  note that is too large, I compress the oldest `decisionLog.md` entries to one line each:
  context, alternatives and consequences go; the decision and the constraint it imposes stay.
  Never a bare title, and the pointer `git log -p memory-bank/decisionLog.md` stays with it.
- Never write secrets, tokens, credentials or personal data in the memory bank.
- Dates in ISO format (YYYY-MM-DD).
- The memory bank is committed with the code it describes, in the same commit when possible.

## 5. Before finishing: consistency checklist

A code change is not finished until the memory bank and the docs tell the truth. I check:

- [ ] If I changed observable behaviour (CLI output, API, error messages), I updated the
  user-facing docs (README or equivalent) and their examples show the real output.
- [ ] Every file list, count and status I wrote is verified against the code, not guessed.
- [ ] `activeContext.md` describes the present and stays short; older history is in
  `progress.md` or `decisionLog.md`.
- [ ] "Known issues" in `progress.md` is true: I do not write "None" while I know of a problem.
- [ ] The bank is still small: I compressed old entries instead of letting a note grow.
- [ ] The memory bank uses one language consistently.
- [ ] If `memory-bank check` is available, I ran it and it passes, or I explained every warning.

## 6. If the project uses Spec-Driven Development (SDD)

Some projects keep a spec-driven workflow beside the code: a folder of specs and,
for each change, a proposal, a design and a task list. When that workflow exists,
I keep the two sources of truth apart:

- Specs, proposals, per-change design and task lists belong to the SDD workflow.
  I do not copy them into the memory bank.
- `decisionLog.md` holds only what is durable for the whole project: a decision
  that outlives the change that introduced it.
- `progress.md` is the project-wide status. When it disagrees with an SDD task
  list, the task list wins: it is more granular and stays current while the
  change is open.
- `activeContext.md` may point at the change in flight, so the next session knows
  where to resume.

If the project does not use SDD, this section does not apply and nothing changes.
"""


# ---------------------------------------------------------------------------
# Spanish templates
# ---------------------------------------------------------------------------

_ES_PROJECT_BRIEF: Final = """# Resumen del Proyecto

> Documento base. Todos los demás archivos del Memory Bank se construyen sobre él.
> Manténlo breve y estable; cámbialo solo cuando el alcance del proyecto cambie.

## Descripción general

_Un párrafo: qué es este proyecto y para quién está dirigido._

## Objetivos

- _Objetivo 1: el resultado principal que el proyecto debe entregar._
- _Objetivo 2_
- _Objetivo 3_

## Requisitos principales

- [ ] _Requisito que debe cumplirse para que el proyecto sea útil._
- [ ] _Requisito_

## Fuera de alcance

- _Lo que este proyecto deliberadamente no hace._

## Stack tecnológico

Detectado automáticamente al crear el Memory Bank:

{{DETECTED_STACK}}

_Corrija o complete esta lista a mano; el agente la mantendrá actualizada._

## Restricciones

- _Plazos, presupuestos, plataformas, cumplimiento normativo o límites de rendimiento._
"""

_ES_PRODUCT_CONTEXT: Final = """# Contexto del Producto

> Por qué existe el proyecto y cómo debería sentirse al usarlo.

## Problema

_¿Qué problema resuelve el producto? ¿Qué pasa hoy sin él?_

## Usuarios

| Usuario | Necesidad | Cómo ayuda el producto |
|---------|-----------|------------------------|
| _Usuario principal_ | _Su necesidad_ | _La respuesta_ |

## Propuesta de valor

_Una o dos frases sobre por qué los usuarios eligen este producto._

## Objetivos de experiencia de usuario

- _Ejemplo: un usuario nuevo completa la tarea principal en menos de dos minutos._
- _Ejemplo: cada mensaje de error indica qué hacer a continuación._

## Cómo debería funcionar

_Los flujos principales de usuario, paso a paso._
"""

_ES_ACTIVE_CONTEXT: Final = """# Contexto Activo

> Qué está pasando ahora mismo. El agente actualiza este archivo al final de cada sesión
> que modifica código. Manténlo breve: describe el presente, no el historial.

## Enfoque actual

_Inicializando el Memory Bank ({{DATE}})._

## Cambios recientes

- {{DATE}}: Memory Bank creado.

## Siguientes pasos

1. Completar `projectbrief.md` y `productContext.md`.
2. _Siguiente tarea concreta._

## Preguntas abiertas y bloqueos

- _Ninguno aún._

## Decisiones activas y consideraciones

- _Compromisos que se están evaluando ahora. Mover los resueltos a `decisionLog.md`._
"""

_ES_PROGRESS: Final = """# Progreso

> Estado del desarrollo. El agente marca lo completado y añade nuevos elementos a medida que avanza.

## Fase actual

**Fase 0: Configuración** (desde {{DATE}})

## Qué funciona

- [x] Memory Bank inicializado

## Qué falta por construir

- [ ] _Funcionalidad o tarea_
- [ ] _Funcionalidad o tarea_

## Problemas conocidos

- _Ninguno aún._

## Hitos

| Fase | Objetivo | Estado |
|------|----------|--------|
| 0. Configuración | Repositorio, herramientas y Memory Bank | En progreso |
| 1. MVP | _Lanzamiento mínimo útil_ | No iniciado |
"""

_ES_DECISION_LOG: Final = """# Registro de Decisiones

> Decisiones arquitectónicas, de más reciente a más antigua. Nunca reescribas una entrada para cambiar su significado: añade una nueva
> que la suplante. La compresión dentro del límite de tamaño (ver `instructions.md`) es la única
> excepción: la decisión y su restricción se quedan, la deliberación pasa al historial de Git.
> Formato: contexto, decisión, alternativas consideradas, consecuencias.

## ADR-001: Mantener la memoria del proyecto en archivos Markdown versionados con Git

- **Fecha:** {{DATE}}
- **Estado:** Aceptado
- **Contexto:** Los agentes de código IA pierden su contexto entre sesiones y entre herramientas
  (Claude Code, Cursor, OpenCode, Pi). Necesitan una memoria compartida y duradera del proyecto.
- **Decisión:** Almacenar esa memoria como archivos Markdown planos en `memory-bank/`, comprometidos en Git.
  Cada agente los lee al inicio de una sesión y los actualiza al final.
- **Alternativas consideradas:**
  - Una base de datos vectorial o relacional: requiere un servicio en ejecución, oculta el contenido en las revisiones de código
    y ata la memoria a una herramienta.
  - La memoria privada de cada herramienta: no se comparte entre herramientas o compañeros.
- **Consecuencias:**
  - La memoria es revisable en merge requests, difusable y consciente de ramas.
  - Cualquier herramienta que lea archivos puede usarla; no hay servicio que ejecutar.
  - Los archivos deben ser concisos, porque se cargan en la ventana de contexto del agente.

<!-- Siguiente decisión: copia la estructura anterior, usa el siguiente número ADR y mantén la más reciente al final. -->
"""

_ES_INSTRUCTIONS: Final = """# Instrucciones del Memory Bank para Agentes de IA

<!-- memory-bank: instructions v3 -->

> Este es el único origen de verdad para las reglas del agente en este repositorio.
> `AGENTS.md`, `CLAUDE.md`, `.cursorrules` y `.opencode/rules/memory.md` enlazan a este archivo:
> edita `memory-bank/instructions.md`, nunca los enlaces.

Soy un agente de código IA cuya memoria se reinicia entre sesiones. La carpeta `memory-bank/` es mi
única memoria de este proyecto, así que dependo de ella completamente.

## 1. Antes de hacer nada: lee el Memory Bank

Al inicio de cada sesión, antes de responder el primer mensaje, leo cada archivo en
`memory-bank/`, en silencio, en este orden:

1. `projectbrief.md`: alcance, objetivos y requisitos principales.
2. `productContext.md`: por qué existe el producto y para quién.
3. `activeContext.md`: en qué se está trabajando ahora y los siguientes pasos.
4. `progress.md`: qué funciona, qué falta y la fase actual.
5. `decisionLog.md`: decisiones ya tomadas; no las reabro sin motivo.
6. Cualquier otro archivo `.md` en `memory-bank/`.

Si un hook ya inyectó el Memory Bank en mi contexto, no lo leo de nuevo.
Si los archivos contradicen el código, el código es la verdad: lo indico y corrijo el Memory Bank.

## 2. Mientras trabajo

- Sigo las decisiones en `decisionLog.md`. Cuando tomo una nueva decisión arquitectónica
  (una librería, un patrón, un modelo de datos, un compromiso), añado una entrada allí.
- Respeto el alcance en `projectbrief.md`. Si una solicitud está fuera de él, lo indico.

## 3. Antes de terminar: actualiza el Memory Bank

Después de cualquier cambio significativo en el código, antes de terminar mi turno, actualizo:

- `activeContext.md`: enfoque actual, cambios recientes (con fecha) y siguientes pasos.
- `progress.md`: marcar lo que ahora funciona, añadir lo que falta, anotar nuevos problemas conocidos.
- `decisionLog.md`: solo si tomé una decisión que valga la pena registrar.

Cuando el usuario dice **"actualizar Memory Bank"**, reviso cada archivo y los actualizo todos.

## 4. Reglas para los archivos

- Conciso y factual: estos archivos se cargan en el contexto de cada sesión.
- `activeContext.md` describe el presente; mueve el historial a `progress.md` o `decisionLog.md`.
- El banco se mantiene pequeño: entra en el contexto de cada sesión. Cuando `memory-bank check` reporta
  que una nota es demasiado grande, comprimo las entradas más antiguas de `decisionLog.md` a una línea cada una:
  contexto, alternativas y consecuencias se van; la decisión y la restricción que impone se quedan.
  Nunca un título sin contenido, y el puntero `git log -p memory-bank/decisionLog.md` se mantiene con él.
- Nunca escribas secretos, tokens, credenciales o datos personales en el Memory Bank.
- Fechas en formato ISO (YYYY-MM-DD).
- El Memory Bank se compromete con el código que describe, en el mismo commit cuando sea posible.

## 5. Antes de terminar: checklist de consistencia

Un cambio de código no está terminado hasta que el Memory Bank y la documentación cuentan la verdad. Verifico:

- [ ] Si cambié el comportamiento observable (salida de CLI, API, mensajes de error), actualicé la
  documentación orientada al usuario (README o equivalente) y sus ejemplos muestran la salida real.
- [ ] Cada lista de archivos, conteo y estado que escribí está verificado contra el código, no adivinado.
- [ ] `activeContext.md` describe el presente y se mantiene breve; el historial más antiguo está en
  `progress.md` o `decisionLog.md`.
- [ ] "Problemas conocidos" en `progress.md` es cierto: no escribo "Ninguno" mientras sé de un problema.
- [ ] El banco sigue siendo pequeño: comprimí entradas antiguas en lugar de dejar que una nota crezca.
- [ ] El Memory Bank usa un idioma de forma consistente.
- [ ] Si `memory-bank check` está disponible, lo ejecuté y pasa, o expliqué cada advertencia.

## 6. Si el proyecto usa Desarrollo Guiado por Especificaciones (SDD)

Algunos proyectos mantienen un flujo basado en especificaciones junto al código: una carpeta de especificaciones y,
para cada cambio, una propuesta, un diseño y una lista de tareas. Cuando ese flujo existe,
mantengo las dos fuentes de verdad separadas:

- Las especificaciones, propuestas, diseño por cambio y listas de tareas pertenecen al flujo SDD.
  No los copio al Memory Bank.
- `decisionLog.md` contiene solo lo que es duradero para todo el proyecto: una decisión
  que sobrevive al cambio que la introdujo.
- `progress.md` es el estado de todo el proyecto. Cuando discrepa con una lista de tareas SDD,
  la lista de tareas gana: es más granular y se mantiene actualizada mientras el
  cambio está abierto.
- `activeContext.md` puede señalar el cambio en curso, para que la siguiente sesión sepa
  dónde reanudar.

Si el proyecto no usa SDD, esta sección no aplica y nada cambia.
"""


# ---------------------------------------------------------------------------
# French templates
# ---------------------------------------------------------------------------

_FR_PROJECT_BRIEF: Final = """# Résumé du Projet

> Document de base. Tous les autres fichiers du Memory Bank s'y appuient.
> Gardez-le court et stable ; modifiez-le uniquement lorsque la portée du projet change.

## Vue d'ensemble

_Un paragraphe : ce qu'est ce projet et pour qui il est destiné._

## Objectifs

- _Objectif 1 : le résultat principal que le projet doit livrer._
- _Objectif 2_
- _Objectif 3_

## Exigences principales

- [ ] _Exigence qui doit être remplie pour que le projet soit utile._
- [ ] _Exigence_

## Hors de portée

- _Ce que ce projet ne fait pas délibérément._

## Stack technologique

Détecté automatiquement lors de la création du Memory Bank :

{{DETECTED_STACK}}

_Corrigez ou complétez cette liste à la main ; l'agent la maintiendra à jour._

## Contraintes

- _Délais, budgets, plateformes, conformité ou limites de performance._
"""

_FR_PRODUCT_CONTEXT: Final = """# Contexte du Produit

> Pourquoi le projet existe et comment il devrait se sentir à utiliser.

## Problème

_Quel problème le produit résout-il ? Que se passe-t-il aujourd'hui sans lui ?_

## Utilisateurs

| Utilisateur | Besoin | Comment le produit aide |
|-------------|--------|-------------------------|
| _Utilisateur principal_ | _Son besoin_ | _La réponse_ |

## Proposition de valeur

_Un ou deux phrases sur pourquoi les utilisateurs choisissent ce produit._

## Objectifs d'expérience utilisateur

- _Exemple : un nouvel utilisateur termine la tâche principale en moins de deux minutes._
- _Exemple : chaque message d'erreur indique quoi faire ensuite._

## Comment ça devrait fonctionner

_Les principaux flux utilisateur, étape par étape._
"""

_FR_ACTIVE_CONTEXT: Final = """# Contexte Actif

> Ce qui se passe en ce moment. L'agent met à jour ce fichier à la fin de chaque session
> qui modifie du code. Gardez-le court : il décrit le présent, pas l'historique.

## Focus actuel

_Mise en place du Memory Bank ({{DATE}})._

## Changements récents

- {{DATE}} : Memory Bank créé.

## Prochaines étapes

1. Remplir `projectbrief.md` et `productContext.md`.
2. _Prochaine tâche concrète._

## Questions ouvertes et blocages

- _Aucune pour l'instant._

## Décisions actives et considérations

- _Compromis en cours d'évaluation. Déplacer les décisions tranchées vers `decisionLog.md`._
"""

_FR_PROGRESS: Final = """# Progression

> État de la construction. L'agent coche les éléments terminés et en ajoute de nouveaux au fur et à mesure.

## Phase actuelle

**Phase 0 : Configuration** (depuis {{DATE}})

## Ce qui fonctionne

- [x] Memory Bank initialisé

## Ce qui reste à construire

- [ ] _Fonctionnalité ou tâche_
- [ ] _Fonctionnalité ou tâche_

## Problèmes connus

- _Aucun pour l'instant._

## Jalons

| Phase | Objectif | Statut |
|-------|----------|--------|
| 0. Configuration | Dépôt, outils et Memory Bank | En cours |
| 1. MVP | _Plus petite version utile_ | Non démarré |
"""

_FR_DECISION_LOG: Final = """# Journal des Décisions

> Décisions architecturales, les plus récentes en premier. Ne réécrivez jamais une entrée pour changer son sens : ajoutez-en une nouvelle
> qui la remplace. La compression dans la limite de taille (voir `instructions.md`) est la seule
> exception : la décision et sa contrainte restent, la délibération passe à l'historique Git.
> Format : contexte, décision, alternatives considérées, conséquences.

## ADR-001: Conserver la mémoire du projet dans des fichiers Markdown versionnés avec Git

- **Date :** {{DATE}}
- **Statut :** Accepté
- **Contexte :** Les agents de code IA perdent leur contexte entre les sessions et entre les outils
  (Claude Code, Cursor, OpenCode, Pi). Ils ont besoin d'une mémoire partagée et durable du projet.
- **Décision :** Stocker cette mémoire sous forme de fichiers Markdown dans `memory-bank/`, commités dans Git.
  Chaque agent les lit au début d'une session et les met à jour à la fin.
- **Alternatives considérées :**
  - Une base de données vectorielle ou relationnelle : nécessite un service en cours d'exécution, cache le contenu des revues de code
    et lie la mémoire à un seul outil.
  - La mémoire privée de chaque outil : non partagée entre les outils ou les collègues.
- **Conséquences :**
  - La mémoire est révisable dans les merge requests, diffable et consciente des branches.
  - Tout outil qui lit des fichiers peut l'utiliser ; aucun service à exécuter.
  - Les fichiers doivent être concis, car ils sont chargés dans la fenêtre de contexte de l'agent.

<!-- Prochaine décision : copiez la structure ci-dessus, utilisez le prochain numéro ADR et gardez la plus récente en dernier. -->
"""

_FR_INSTRUCTIONS: Final = """# Instructions du Memory Bank pour les Agents IA

<!-- memory-bank: instructions v3 -->

> C'est la seule source de vérité pour les règles de l'agent dans ce dépôt.
> `AGENTS.md`, `CLAUDE.md`, `.cursorrules` et `.opencode/rules/memory.md` pointent vers ce fichier :
> modifiez `memory-bank/instructions.md`, jamais les liens.

Je suis un agent de code IA dont la mémoire se réinitialise entre les sessions. Le dossier `memory-bank/` est ma
seule mémoire de ce projet, donc j'en dépends entièrement.

## 1. Avant de faire quoi que ce soit : lisez le Memory Bank

Au début de chaque session, avant de répondre au premier message, je lis chaque fichier dans
`memory-bank/`, silencieusement, dans cet ordre :

1. `projectbrief.md` : portée, objectifs et exigences principales.
2. `productContext.md` : pourquoi le produit existe et pour qui.
3. `activeContext.md` : ce sur quoi on travaille maintenant et les prochaines étapes.
4. `progress.md` : ce qui fonctionne, ce qui reste et la phase actuelle.
5. `decisionLog.md` : décisions déjà prises ; je ne les rouvre pas sans raison.
6. Tout autre fichier `.md` dans `memory-bank/`.

Si un hook a déjà injecté le Memory Bank dans mon contexte, je ne le lis pas à nouveau.
Si les fichiers contredisent le code, le code est la vérité : je le signale et corrige le Memory Bank.

## 2. Pendant le travail

- Je suis les décisions dans `decisionLog.md`. Lorsque je prends une nouvelle décision architecturale
  (une bibliothèque, un motif, un modèle de données, un compromis), j'ajoute une entrée là-bas.
- Je respecte la portée dans `projectbrief.md`. Si une demande est hors de portée, je le signale.

## 3. Avant de terminer : mettez à jour le Memory Bank

Après tout changement significatif dans le code, avant de terminer mon tour, je mets à jour :

- `activeContext.md` : focus actuel, changements récents (datés) et prochaines étapes.
- `progress.md` : cocher ce qui fonctionne maintenant, ajouter ce qui reste, noter les nouveaux problèmes connus.
- `decisionLog.md` : uniquement si j'ai pris une décision qui vaut la peine d'être enregistrée.

Lorsque l'utilisateur dit **"mettre à jour le Memory Bank"**, je révise chaque fichier et les mets tous à jour.

## 4. Règles pour les fichiers

- Concis et factuel : ces fichiers sont chargés dans le contexte de chaque session.
- `activeContext.md` décrit le présent ; déplacez l'historique vers `progress.md` ou `decisionLog.md`.
- Le bank reste petit : il entre dans le contexte de chaque session. Lorsque `memory-bank check` signale
  qu'une note est trop volumineuse, je compresse les anciennes entrées de `decisionLog.md` en une ligne chacune :
  contexte, alternatives et conséquences partent ; la décision et la contrainte qu'elle impose restent.
  Jamais un titre nu, et le pointeur `git log -p memory-bank/decisionLog.md` reste avec elle.
- N'écrivez jamais de secrets, jetons, identifiants ou données personnelles dans le Memory Bank.
- Dates au format ISO (YYYY-MM-DD).
- Le Memory Bank est commité avec le code qu'il décrit, dans le même commit si possible.

## 5. Avant de terminer : liste de vérification de cohérence

Un changement de code n'est pas terminé tant que le Memory Bank et la documentation ne disent pas la vérité. Je vérifie :

- [ ] Si j'ai changé le comportement observable (sortie CLI, API, messages d'erreur), j'ai mis à jour la
  documentation utilisateur (README ou équivalent) et ses exemples montrent la sortie réelle.
- [ ] Chaque liste de fichiers, comptage et statut que j'ai écrit est vérifié contre le code, pas deviné.
- [ ] `activeContext.md` décrit le présent et reste court ; l'historique plus ancien est dans
  `progress.md` ou `decisionLog.md`.
- [ ] "Problèmes connus" dans `progress.md` est vrai : je n'écris pas "Aucun" quand je connais un problème.
- [ ] Le bank est toujours petit : j'ai compressé les anciennes entrées au lieu de laisser une note grandir.
- [ ] Le Memory Bank utilise une langue de manière cohérente.
- [ ] Si `memory-bank check` est disponible, je l'ai exécuté et il passe, ou j'ai expliqué chaque avertissement.

## 6. Si le projet utilise le Développement Piloté par Spécifications (SDD)

Certains projets maintiennent un flux piloté par les spécifications à côté du code : un dossier de spécifications et,
pour chaque changement, une proposition, une conception et une liste de tâches. Lorsque ce flux existe,
je garde les deux sources de vérité séparées :

- Les spécifications, propositions, conception par changement et listes de tâches appartiennent au flux SDD.
  Je ne les copie pas dans le Memory Bank.
- `decisionLog.md` contient uniquement ce qui est durable pour tout le projet : une décision
  qui survit au changement qui l'a introduite.
- `progress.md` est l'état de tout le projet. Lorsqu'il est en désaccord avec une liste de tâches SDD,
  la liste de tâches l'emporte : elle est plus granulaire et reste actuelle pendant que le
  changement est ouvert.
- `activeContext.md` peut pointer vers le changement en cours, afin que la session suivante sache
  où reprendre.

Si le projet n'utilise pas le SDD, cette section ne s'applique pas et rien ne change.
"""


# ---------------------------------------------------------------------------
# German templates
# ---------------------------------------------------------------------------

_DE_PROJECT_BRIEF: Final = """# Projektübersicht

> Grundlegendes Dokument. Alle anderen Memory-Bank-Dateien bauen darauf auf.
> Halte es kurz und stabil; ändere es nur, wenn sich der Projektumfang ändert.

## Übersicht

_Ein Absatz: was dieses Projekt ist und wofür es gedacht ist._

## Ziele

- _Ziel 1: das Hauptergebnis, das das Projekt liefern muss._
- _Ziel 2_
- _Ziel 3_

## Kernanforderungen

- [ ] _Anforderung, die erfüllt sein muss, damit das Projekt nützlich ist._
- [ ] _Anforderung_

## Außerhalb des Umfangs

- _Was dieses Projekt bewusst nicht tut._

## Technologie-Stack

Automatisch erkannt beim Erstellen der Memory Bank:

{{DETECTED_STACK}}

_Korrigiere oder ergänze diese Liste manuell; der Agent hält sie auf dem Laufenden._

## Einschränkungen

- _Fristen, Budgets, Plattformen, Compliance- oder Leistungsgrenzen._
"""

_DE_PRODUCT_CONTEXT: Final = """# Produktkontext

> Warum das Projekt existiert und wie es sich bei der Nutzung anfühlen sollte.

## Problem

_Welches Problem löst das Produkt? Was passiert heute ohne es?_

## Nutzer

| Nutzer | Bedarf | Wie das Produkt hilft |
|--------|--------|-----------------------|
| _Primärer Nutzer_ | _Ihr Bedarf_ | _Die Antwort_ |

## Wertversprechen

_Ein oder zwei Sätze darüber, warum Nutzer dieses Produkt wählen._

## Nutzererfahrungsziele

- _Beispiel: ein neuer Nutzer erledigt die Hauptaufgabe in unter zwei Minuten._
- _Beispiel: jede Fehlermeldung sagt, was als Nächstes zu tun ist._

## Wie es funktionieren sollte

_Die wichtigsten Nutzerabläufe, schrittweise._
"""

_DE_ACTIVE_CONTEXT: Final = """# Aktueller Kontext

> Was gerade passiert. Der Agent aktualisiert diese Datei am Ende jeder Sitzung,
> die Code ändert. Halte es kurz: es beschreibt die Gegenwart, nicht die Geschichte.

## Aktueller Fokus

_Memory Bank einrichten ({{DATE}})._

## Letzte Änderungen

- {{DATE}}: Memory Bank erstellt.

## Nächste Schritte

1. `projectbrief.md` und `productContext.md` ausfüllen.
2. _Nächste konkrete Aufgabe._

## Offene Fragen und Blockaden

- _Keine bisher._

## Aktive Entscheidungen und Überlegungen

- _Abwägungen, die gerade getroffen werden. Abgeschlossene nach `decisionLog.md` verschieben._
"""

_DE_PROGRESS: Final = """# Fortschritt

> Status der Entwicklung. Der Agent hakt ab, was fertig ist, und fügt neue Elemente hinzu.

## Aktuelle Phase

**Phase 0: Einrichtung** (seit {{DATE}})

## Was funktioniert

- [x] Memory Bank initialisiert

## Was noch zu bauen ist

- [ ] _Funktion oder Aufgabe_
- [ ] _Funktion oder Aufgabe_

## Bekannte Probleme

- _Keine bisher._

## Meilensteine

| Phase | Ziel | Status |
|-------|------|--------|
| 0. Einrichtung | Repository, Werkzeuge und Memory Bank | In Bearbeitung |
| 1. MVP | _Kleinste nutzbare Version_ | Nicht gestartet |
"""

_DE_DECISION_LOG: Final = """# Entscheidungsprotokoll

> Architekturentscheidungen, neueste zuerst. Schreibe niemals einen Eintrag um, um seine Bedeutung zu ändern: füge einen neuen hinzu,
> der ihn ersetzt. Komprimierung innerhalb des Größenlimits (siehe `instructions.md`) ist die einzige
> Ausnahme: die Entscheidung und ihre Einschränkung bleiben, die Überlegung geht in die Git-Historie.
> Format: Kontext, Entscheidung, betrachtete Alternativen, Konsequenzen.

## ADR-001: Projektgedächtnis in mit Git versionierten Markdown-Dateien speichern

- **Datum:** {{DATE}}
- **Status:** Akzeptiert
- **Kontext:** KI-Coding-Agenten verlieren ihren Kontext zwischen Sitzungen und über Tools hinweg
  (Claude Code, Cursor, OpenCode, Pi). Sie brauchen ein gemeinsames, dauerhaftes Gedächtnis des Projekts.
- **Entscheidung:** Dieses Gedächtnis als einfache Markdown-Dateien in `memory-bank/` speichern, in Git committen.
  Jeder Agent liest sie am Anfang einer Sitzung und aktualisiert sie am Ende.
- **Betrachtete Alternativen:**
  - Eine Vektor- oder relationale Datenbank: benötigt einen laufenden Dienst, verbirgt Inhalte vor Code-Reviews
    und bindet das Gedächtnis an ein Tool.
  - Der private Speicher jedes Tools: nicht zwischen Tools oder Teammitgliedern geteilt.
- **Konsequenzen:**
  - Das Gedächtnis ist in Merge-Requests überprüfbar, diffbar und branchenbewusst.
  - Jedes Tool, das Dateien liest, kann es nutzen; kein Dienst muss laufen.
  - Die Dateien müssen knapp sein, da sie in das Kontextfenster des Agents geladen werden.

<!-- Nächste Entscheidung: kopiere die obere Struktur, verwende die nächste ADR-Nummer und halte die neueste zuletzt. -->
"""

_DE_INSTRUCTIONS: Final = """# Memory-Bank-Anweisungen für KI-Agenten

<!-- memory-bank: instructions v3 -->

> Dies ist die einzige Quelle der Wahrheit für Agenten-Regeln in diesem Repository.
> `AGENTS.md`, `CLAUDE.md`, `.cursorrules` und `.opencode/rules/memory.md` verlinken auf diese Datei:
> bearbeite `memory-bank/instructions.md`, niemals die Links.

Ich bin ein KI-Coding-Agent, dessen Gedächtnis zwischen Sitzungen zurückgesetzt wird. Der Ordner `memory-bank/` ist mein
einziges Gedächtnis dieses Projekts, also verlasse ich mich vollständig darauf.

## 1. Bevor du irgendetwas tust: lies die Memory Bank

Am Anfang jeder Sitzung, bevor ich auf die erste Nachricht antworte, lese ich jede Datei in
`memory-bank/`, stillschweigend, in dieser Reihenfolge:

1. `projectbrief.md`: Umfang, Ziele und Kernanforderungen.
2. `productContext.md`: warum das Produkt existiert und für wen.
3. `activeContext.md`: woran gerade gearbeitet wird und die nächsten Schritte.
4. `progress.md`: was funktioniert, was fehlt und die aktuelle Phase.
5. `decisionLog.md`: bereits getroffene Entscheidungen; ich öffne sie nicht ohne Grund wieder.
6. Jede andere `.md`-Datei in `memory-bank/`.

Wenn ein Hook die Memory Bank bereits in meinen Kontext injiziert hat, lese ich sie nicht erneut.
Wenn die Dateien dem Code widersprechen, ist der Code die Wahrheit: ich sage es und repariere die Memory Bank.

## 2. Während der Arbeit

- Ich folge den Entscheidungen in `decisionLog.md`. Wenn ich eine neue architektonische Entscheidung treffe
  (eine Bibliothek, ein Muster, ein Datenmodell, einen Kompromiss), füge ich dort einen Eintrag hinzu.
- Ich respektiere den Umfang in `projectbrief.md`. Wenn eine Anfrage außerhalb liegt, sage ich es.

## 3. Bevor du aufhörst: aktualisiere die Memory Bank

Nach jeder signifikanten Code-Änderung, bevor ich meine Runde beende, aktualisiere ich:

- `activeContext.md`: aktueller Fokus, letzte Änderungen (datiert) und nächste Schritte.
- `progress.md`: abhaken, was jetzt funktioniert, hinzufügen, was fehlt, neue bekannte Probleme notieren.
- `decisionLog.md`: nur, wenn ich eine Entscheidung getroffen habe, die es wert ist, aufgezeichnet zu werden.

Wenn der Benutzer sagt **"Memory Bank aktualisieren"**, überprüfe ich jede Datei und aktualisiere alle.

## 4. Regeln für die Dateien

- Knapp und sachlich: diese Dateien werden in jede Sitzung geladen.
- `activeContext.md` beschreibt die Gegenwart; verschiebe Historie nach `progress.md` oder `decisionLog.md`.
- Die Bank bleibt klein: sie geht in jede Sitzung ein. Wenn `memory-bank check` meldet,
  dass eine Notiz zu groß ist, komprimiere ich die ältesten `decisionLog.md`-Einträge auf je eine Zeile:
  Kontext, Alternativen und Konsequenzen gehen; die Entscheidung und die Einschränkung, die sie auferlegt, bleiben.
  Niemals ein nackter Titel, und der Zeiger `git log -p memory-bank/decisionLog.md` bleibt dabei.
- Schreibe niemals Geheimnisse, Tokens, Zugangsdaten oder persönliche Daten in die Memory Bank.
- Daten im ISO-Format (YYYY-MM-DD).
- Die Memory Bank wird mit dem Code, den sie beschreibt, im selben Commit committet, wenn möglich.

## 5. Bevor du aufhörst: Konsistenz-Checkliste

Eine Code-Änderung ist nicht fertig, bis die Memory Bank und die Docs die Wahrheit sagen. Ich prüfe:

- [ ] Wenn ich das beobachtbare Verhalten geändert habe (CLI-Ausgabe, API, Fehlermeldungen), habe ich die
  nutzerorientierte Dokumentation (README oder Äquivalent) aktualisiert und ihre Beispiele zeigen die echte Ausgabe.
- [ ] Jede Dateiliste, Anzahl und Status, die ich geschrieben habe, ist gegen den Code verifiziert, nicht erraten.
- [ ] `activeContext.md` beschreibt die Gegenwart und bleibt kurz; ältere Historie ist in
  `progress.md` oder `decisionLog.md`.
- [ ] "Bekannte Probleme" in `progress.md` ist wahr: ich schreibe nicht "Keine", während ich von einem Problem weiß.
- [ ] Die Bank ist immer noch klein: ich habe alte Einträge komprimiert, anstatt eine Notiz wachsen zu lassen.
- [ ] Die Memory Bank verwendet eine Sprache konsistent.
- [ ] Wenn `memory-bank check` verfügbar ist, habe ich es ausgeführt und es besteht, oder ich habe jede Warnung erklärt.

## 6. Wenn das Projekt Spec-Driven Development (SDD) verwendet

Einige Projekte halten neben dem Code einen spec-gesteuerten Workflow: einen Ordner mit Specs und,
für jede Änderung, einen Vorschlag, ein Design und eine Aufgabenliste. Wenn dieser Workflow existiert,
halte ich die beiden Wahrheitsquellen getrennt:

- Specs, Vorschläge, Design pro Änderung und Aufgabenlisten gehören zum SDD-Workflow.
  Ich kopiere sie nicht in die Memory Bank.
- `decisionLog.md` enthält nur das, was für das gesamte Projekt dauerhaft ist: eine Entscheidung,
  die die Änderung, die sie eingeführt hat, überlebt.
- `progress.md` ist der projektweite Status. Wenn er mit einer SDD-Aufgabenliste widerspricht,
  gewinnt die Aufgabenliste: sie ist granularer und bleibt aktuell, während die
  Änderung offen ist.
- `activeContext.md` kann auf die laufende Änderung verweisen, damit die nächste Sitzung weiß,
  wo sie fortfahren soll.

Wenn das Projekt kein SDD verwendet, gilt dieser Abschnitt nicht und nichts ändert sich.
"""


# ---------------------------------------------------------------------------
# Template registry by language
# ---------------------------------------------------------------------------

_TEMPLATES_BY_LANG: Final[dict[str, dict[str, str]]] = {
    "en": {
        "projectbrief.md": _EN_PROJECT_BRIEF,
        "productContext.md": _EN_PRODUCT_CONTEXT,
        "activeContext.md": _EN_ACTIVE_CONTEXT,
        "progress.md": _EN_PROGRESS,
        "decisionLog.md": _EN_DECISION_LOG,
        INSTRUCTIONS_FILE: _EN_INSTRUCTIONS,
    },
    "es": {
        "projectbrief.md": _ES_PROJECT_BRIEF,
        "productContext.md": _ES_PRODUCT_CONTEXT,
        "activeContext.md": _ES_ACTIVE_CONTEXT,
        "progress.md": _ES_PROGRESS,
        "decisionLog.md": _ES_DECISION_LOG,
        INSTRUCTIONS_FILE: _ES_INSTRUCTIONS,
    },
    "fr": {
        "projectbrief.md": _FR_PROJECT_BRIEF,
        "productContext.md": _FR_PRODUCT_CONTEXT,
        "activeContext.md": _FR_ACTIVE_CONTEXT,
        "progress.md": _FR_PROGRESS,
        "decisionLog.md": _FR_DECISION_LOG,
        INSTRUCTIONS_FILE: _FR_INSTRUCTIONS,
    },
    "de": {
        "projectbrief.md": _DE_PROJECT_BRIEF,
        "productContext.md": _DE_PRODUCT_CONTEXT,
        "activeContext.md": _DE_ACTIVE_CONTEXT,
        "progress.md": _DE_PROGRESS,
        "decisionLog.md": _DE_DECISION_LOG,
        INSTRUCTIONS_FILE: _DE_INSTRUCTIONS,
    },
}

# Backward-compatible alias: English templates are the default.
TEMPLATES: Final[dict[str, str]] = _TEMPLATES_BY_LANG["en"]


def get_templates(lang: str) -> dict[str, str]:
    """Return the template dictionary for ``lang``.

    Falls back to English when ``lang`` is not supported.
    """
    return _TEMPLATES_BY_LANG.get(lang, _TEMPLATES_BY_LANG["en"])


def render(template: str, detected_stack: list[str], date: str) -> str:
    """Fill the placeholders of ``template``."""
    stack = "\n".join(f"- {item}" for item in detected_stack) or "- _Nothing detected yet._"
    return template.replace(STACK_PLACEHOLDER, stack).replace(DATE_PLACEHOLDER, date)
