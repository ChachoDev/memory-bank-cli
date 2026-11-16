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

This project does not use GitHub Actions: the checks run locally and CI is not required. Run all
of them on Python 3.10 or newer before opening a pull request:

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
chore: refresh uv.lock
```

## Pull requests

1. Open an issue first for anything larger than a bug fix, so the approach can be agreed.
2. Keep one logical change per pull request.
3. Add or update tests for behaviour changes.
4. Update `CHANGELOG.md` under an `Unreleased` heading when the change is user-visible.
5. Make sure the checks above pass.

## Reporting bugs

Open an issue with the **Bug report** form and include the operating system, Python version, the
exact command, what you expected and what happened instead. If the problem involves generated
files, paste the relevant file or the output of `memory-bank sync`.

## Code of conduct

Everyone who takes part in this project is expected to follow the
[Code of Conduct](CODE_OF_CONDUCT.md). Report unacceptable behaviour to the address listed there.

## Security

Please do not open a public issue for security problems. Follow [SECURITY.md](SECURITY.md) and
send the details by email.

## Credits

The Memory Bank concept was created by Nick Baumann for Cline. See [CREDITS.md](CREDITS.md) for
the original sources and the full acknowledgements.

## License

By contributing you agree that your work is released under the [MIT License](LICENSE).
