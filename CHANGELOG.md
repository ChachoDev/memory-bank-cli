# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- GitHub Actions is back, with the linter and type checker pinned so a tool release cannot turn a
  green build red, plus a job that builds the wheel and runs the installed `memory-bank` binary.

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
