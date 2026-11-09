"""Initial Markdown templates for the memory bank.

Templates are written in English because their main reader is the AI agent. Two placeholders are
filled in at generation time: ``{{DETECTED_STACK}}`` and ``{{DATE}}``.
"""

from __future__ import annotations

from typing import Final

STACK_PLACEHOLDER: Final = "{{DETECTED_STACK}}"
DATE_PLACEHOLDER: Final = "{{DATE}}"

INSTRUCTIONS_FILE: Final = "instructions.md"

PROJECT_BRIEF: Final = """# Project Brief

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

PRODUCT_CONTEXT: Final = """# Product Context

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

ACTIVE_CONTEXT: Final = """# Active Context

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

PROGRESS: Final = """# Progress

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

DECISION_LOG: Final = """# Decision Log

> Architectural decisions, newest last. Never rewrite an entry: add a new one that supersedes it.
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

## ADR-002: _Title_

- **Date:**
- **Status:** Proposed | Accepted | Superseded by ADR-xxx
- **Context:**
- **Decision:**
- **Alternatives considered:**
- **Consequences:**
"""

INSTRUCTIONS: Final = """# Memory Bank Instructions for AI Agents

> This is the single source of truth for agent rules in this repository.
> `CLAUDE.md`, `.cursorrules` and `.opencode/rules/memory.md` link to this file:
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
- Never write secrets, tokens, credentials or personal data in the memory bank.
- Dates in ISO format (YYYY-MM-DD).
- The memory bank is committed with the code it describes, in the same commit when possible.

## 5. If the project uses Spec-Driven Development (SDD)

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

TEMPLATES: Final[dict[str, str]] = {
    "projectbrief.md": PROJECT_BRIEF,
    "productContext.md": PRODUCT_CONTEXT,
    "activeContext.md": ACTIVE_CONTEXT,
    "progress.md": PROGRESS,
    "decisionLog.md": DECISION_LOG,
    INSTRUCTIONS_FILE: INSTRUCTIONS,
}

# Order in which hooks inject the files into the agent's context.
READ_ORDER: Final[tuple[str, ...]] = (
    INSTRUCTIONS_FILE,
    "projectbrief.md",
    "productContext.md",
    "activeContext.md",
    "progress.md",
    "decisionLog.md",
)


def render(template: str, detected_stack: list[str], date: str) -> str:
    """Fill the placeholders of ``template``."""
    stack = "\n".join(f"- {item}" for item in detected_stack) or "- _Nothing detected yet._"
    return template.replace(STACK_PLACEHOLDER, stack).replace(DATE_PLACEHOLDER, date)
