# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Memory bank templates are always generated in English regardless of the user's system language.
  The CLI messages remain translated (English, Spanish, French, German). This avoids inconsistencies
  when multiple users with different system languages share the same repository.

### Removed

- Multilingual template variants (Spanish, French, German). Only English templates remain.

## [1.2.0] - 2026-11-16

### Added

- **Framework detection**: the scanner now reads dependency manifests (`package.json`,
  `pyproject.toml`, `requirements.txt`, `Cargo.toml`, `go.mod`, `build.gradle`) to detect
  frameworks such as React, Next.js, Vue, Express, Django, FastAPI, Flask, PyTorch, Actix,
  Rocket, Gin, Spring Boot, Ktor and many more. The detected stack now lists languages first,
  then frameworks.
- `start` installs a local `pre-commit` hook in `.git/hooks/` that runs `memory-bank check` and
  aborts the commit when `check` finds errors (never on warnings). The hook is read-only, silent
  unless it blocks, and does nothing when `memory-bank` is not on PATH or `memory-bank/` is
  missing. It never replaces a hook it did not create and never writes into a custom
  `core.hooksPath`.
- `memory-bank git-hooks install|uninstall`: install or remove only the managed hook. `sync` leaves
  Git hooks alone, so an explicit uninstall is respected. Git hooks are local and unversioned, so
  each clone installs its own; existing banks run `git-hooks install` once.

### Changed

- The `decisionLog.md` template now presents compression under the size budget as the only
  exception to "never rewrite an entry", so it no longer contradicts `instructions.md`. It also
  dropped the empty ADR-002 skeleton that `check` reported as an unfilled placeholder.
- The README says exactly what `check` can prove: dates are checked in `decisionLog.md`, and the
  CI note no longer claims it detects drift in the docs.

### Fixed

- `check` now recognizes "No known issues", "No problems" and their Spanish, French and German
  equivalents, so the TODO/FIXME contradiction is not missed.
- `hook session-start` skips a note that is not valid UTF-8 instead of failing the whole hook.

### Removed

- The Dependabot configuration. The checks listed in `CONTRIBUTING.md` run locally, so the
  project does not depend on GitHub automation.

## [1.1.0] - 2026-11-16

### Added

- `memory-bank check [--strict]`: a read-only consistency check for the memory bank. It reports
  missing files or sections, unfilled placeholders, unrendered tokens, changelog drift in
  `activeContext.md`, broken file references, "Known issues: None" contradicting TODO/FIXME
  markers in the code, broken agent links, non-ISO dates, obvious secrets and an `instructions.md`
  written by an older release. `--strict` also fails on warnings, so it can gate CI.
- The `Stop` hook reason and `memory-bank/instructions.md` now include a consistency checklist:
  update the docs when behaviour changes, verify every count, keep `activeContext.md` short, do
  not fake "Known issues: None", and run `memory-bank check`.
- `check` now guards the context budget: it warns when a note passes 12,000 characters (about 3k
  tokens) or the whole bank passes 40,000 (about 10k tokens), naming the size and the fix.
- `hook session-start` no longer repeats `memory-bank/instructions.md` when `CLAUDE.md` already
  points at it, saving about 1k tokens per Claude Code session.
- The `instructions.md` template (now v3) explains how to compress the decision log when `check`
  reports it: the decision and the constraint it imposes stay, the deliberation goes back to Git
  history, and the pointer `git log -p memory-bank/decisionLog.md` keeps the full text one
  command away. Banks written by an older template get the version warning from `check`.
- JetBrains Junie support: `start` now creates `AGENTS.md` as a link to
  `memory-bank/instructions.md`, the file Junie reads as project guidelines. The scanner ignores
  the `.junie/` folder.
- GitHub issue forms for bug reports and feature requests, a pull request template, a code of
  conduct, a security policy, and `.gitattributes`/`.editorconfig` files.
- `CREDITS.md` acknowledging Nick Baumann, creator of the Memory Bank concept, and Cline, the
  project it was originally designed for.

### Changed

- Rewrote the README as a detailed guide: global, per-project and ephemeral installation, a
  step-by-step walkthrough for new and existing repositories, what `start`, `sync`, `check` and
  `reset` do, the team/CI workflow, hook details and a troubleshooting table. It now credits the
  original Memory Bank idea in every language and links to `CREDITS.md`.

### Removed

- The GitHub Actions workflow. The checks listed in `CONTRIBUTING.md` run locally, so the project
  does not depend on Actions.

## [1.0.0] - 2026-11-09

### Added

- `memory-bank start` creates the `memory-bank/` folder of Markdown notes, detects the
  repository stack (Node.js, TypeScript, Python, Flutter/Dart, Rust, Go, Java, Kotlin, .NET,
  Ruby, PHP, Swift, Elixir, Docker, Terraform and more) and writes it into `projectbrief.md`.
- `memory-bank sync` repairs missing files, broken links and outdated hooks without ever
  overwriting an existing note.
- `memory-bank reset` deletes and regenerates the memory bank, asking for confirmation
  (`--yes` skips the prompt for CI and scripts).
- `memory-bank hook session-start` and `memory-bank hook stop` power the Claude Code hooks.
- Relative symlinks from `CLAUDE.md`, `.cursorrules` and `.opencode/rules/memory.md` to
  `memory-bank/instructions.md`, with a marked copy as a fallback where symlinks are not
  allowed. Existing files are never overwritten.
- Hook configuration merged into `.claude/settings.json` and `opencode.json`, keeping your
  other settings intact.
- Messages localised in English, Spanish, French and German, picked from the system locale
  and overridable with `MEMORY_BANK_LANG`.
- Exit codes: `0` success, `1` error, `2` wrong usage.
