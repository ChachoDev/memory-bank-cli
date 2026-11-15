# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- GitHub issue forms for bug reports and feature requests, a pull request template, a code of
  conduct, a security policy, and `.gitattributes`/`.editorconfig` files.
- `CREDITS.md` acknowledging Nick Baumann, creator of the Memory Bank concept, and Cline, the
  project it was originally designed for.

### Changed

- Rewrote the README as a detailed guide: global, per-project and ephemeral installation, a
  step-by-step walkthrough for new and existing repositories, what `start`, `sync` and `reset`
  do, the team/CI workflow, hook details and a troubleshooting table. It now credits the original
  Memory Bank idea in every language and links to `CREDITS.md`.

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
