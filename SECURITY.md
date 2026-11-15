# Security Policy

## Supported versions

Only the latest released minor version receives security fixes.

| Version | Supported |
|---------|-----------|
| 1.x     | Yes       |

## Reporting a vulnerability

**Please do not report security issues in a public issue.**

Send an email to **elchachodev@gmail.com** with:

- A description of the problem and its impact.
- The steps to reproduce it, or a minimal repository that triggers it.
- The version of `memory-bank` (`memory-bank --version`), your Python version and your
  operating system.
- Any suggested fix, if you have one.

You will receive an acknowledgement within 7 days, and we will keep you informed while the issue
is investigated and fixed. Please give us a reasonable amount of time to release a fix before
disclosing the problem publicly.

## Scope

`memory-bank` runs locally, has no runtime dependencies and never sends data over the network. It
reads files from the repository where it runs and writes the generated memory bank plus agent
configuration files. The most relevant risks are therefore:

- Overwriting or deleting user content (`reset` is the only destructive command and asks for
  confirmation).
- Injecting unexpected values into `.claude/settings.json`, `opencode.json` or the generated
  Markdown files.
- Following a malicious symlink or path when writing a file.

The memory bank is plain text committed to Git: **never store secrets, tokens or credentials in
it**. The generated `instructions.md` already tells agents not to.
