# Credits

`memory-bank-cli` is an independent implementation of the **Memory Bank** idea. It is not an
official product of Cline or its authors.

## The Memory Bank concept

The Memory Bank methodology was created by **Nick Baumann**
([@nickbaumann98](https://github.com/nickbaumann98)) for [Cline](https://cline.bot), the
open-source AI coding agent. His original instructions describe a `memory-bank/` folder of
Markdown documents that the agent reads at the start of every session and updates at the end, so
it never loses the project's context between sessions.

Original sources:

- [Memory Bank: How to Make Cline an AI Agent That Never Forgets](https://cline.bot/blog/memory-bank-how-to-make-cline-an-ai-agent-that-never-forgets),
  by Nick Baumann.
- [Cline's Memory Bank instructions](https://github.com/cline/prompts/blob/main/.clinerules/memory-bank.md).
- [Cline documentation: Memory Bank](https://docs.cline.bot/features/memory-bank).

This project takes that idea beyond Cline: it generates the same kind of Markdown memory for
Claude Code, Cursor, OpenCode and Pi, links every agent's rules file to a single
`instructions.md`, and installs lifecycle hooks, all through a small standard-library Python CLI.

The concept, its vocabulary and the original file layout belong to Nick Baumann. The automation,
templates, translations, hooks and code in this repository are ours.

## Acknowledgements

- **Nick Baumann** and the **Cline** community, for creating, documenting and popularising the
  Memory Bank pattern.
- The Claude Code, Cursor, OpenCode and Pi teams, for their hook and instruction-file APIs.
