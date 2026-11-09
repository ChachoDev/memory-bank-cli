# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
