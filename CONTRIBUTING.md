# Contributing

Thanks for taking the time to improve `memory-bank`. This guide covers the development
workflow; the [README](README.md) explains what the tool does and how to use it.

## Requirements

- Python 3.10 or newer
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Git

## Set up

```bash
git clone https://github.com/ChachoDev/memory-bank-cli
cd memory-bank-cli
uv sync --locked          # creates .venv and installs the dev tools
uv run pytest             # run the test suite
```

To try a change as if it were installed globally:

```bash
uv tool install --editable .
```

## Checks before opening a pull request

CI runs all of these on Python 3.10 and 3.13, so run them locally first:

```bash
uvx ruff check .
uvx ruff format --check .
uvx mypy --strict memory_bank
uv run pytest
```

Run `uvx ruff format .` to fix formatting instead of editing it by hand.

## Project layout

| Path | Role |
|------|------|
| `memory_bank/cli.py` | Argument parsing, command dispatch, exit codes |
| `memory_bank/scaffold.py` | Writes the memory bank, creates links and merges hooks |
| `memory_bank/scanner.py` | Detects the stack of the repository being initialised |
| `memory_bank/templates.py` | Contents of the generated Markdown files |
| `memory_bank/i18n.py` | English, Spanish, French and German messages |
| `tests/` | pytest suite covering every module and the CLI end to end |

There are no third-party runtime dependencies on purpose: the tool must run with nothing
but Python and Git, so keep new code on the standard library.

## Commit messages

Short imperative lines, optionally prefixed with a conventional type:

```
feat: add Dart stack detection
fix: do not overwrite an existing CLAUDE.md
docs: clarify the OpenCode hook section
test: cover reset in a non-Git directory
chore: bump the CI matrix
```

## Pull requests

1. Open an issue first for anything larger than a bug fix, so the approach can be agreed.
2. Keep one logical change per pull request.
3. Add or update tests for behaviour changes.
4. Update `CHANGELOG.md` under an `Unreleased` heading when the change is user-visible.
5. Make sure the checks above pass.

## Reporting bugs

Include the operating system, Python version, the exact command, what you expected and what
happened instead. If the problem involves generated files, paste the relevant file or the
output of `memory-bank sync`.

## License

By contributing you agree that your work is released under the [MIT License](LICENSE).
