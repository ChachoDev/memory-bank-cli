"""Detect existing code and infer the technology stack of a project."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final, TypedDict


class ScanResult(TypedDict):
    has_code: bool
    detected_stack: list[str]


# Exact file names in the project root and the stack they reveal.
ROOT_MARKERS: Final[dict[str, str]] = {
    "package.json": "Node.js",
    "tsconfig.json": "TypeScript",
    "deno.json": "Deno",
    "deno.jsonc": "Deno",
    "bun.lockb": "Bun",
    "bun.lock": "Bun",
    "pyproject.toml": "Python",
    "requirements.txt": "Python",
    "setup.py": "Python",
    "Pipfile": "Python",
    "uv.lock": "uv",
    "Cargo.toml": "Rust",
    "go.mod": "Go",
    "pom.xml": "Java (Maven)",
    "build.gradle": "JVM (Gradle)",
    "build.gradle.kts": "Kotlin (Gradle)",
    "Gemfile": "Ruby",
    "composer.json": "PHP",
    "Package.swift": "Swift",
    "mix.exs": "Elixir",
    "CMakeLists.txt": "C/C++ (CMake)",
    "Makefile": "Make",
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
    "compose.yml": "Docker Compose",
    "compose.yaml": "Docker Compose",
}

# Glob patterns in the project root and the stack they reveal.
ROOT_GLOBS: Final[dict[str, str]] = {
    "*.csproj": ".NET",
    "*.sln": ".NET",
    "*.tf": "Terraform",
}

SOURCE_EXTENSIONS: Final = frozenset(
    {
        ".py",
        ".js",
        ".mjs",
        ".cjs",
        ".ts",
        ".tsx",
        ".jsx",
        ".dart",
        ".rs",
        ".go",
        ".java",
        ".kt",
        ".swift",
        ".rb",
        ".php",
        ".cs",
        ".c",
        ".h",
        ".cpp",
        ".hpp",
        ".ex",
        ".exs",
        ".scala",
        ".vue",
        ".svelte",
        ".sh",
        ".sql",
    }
)

IGNORED_DIRS: Final = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        "dist",
        "build",
        "target",
        ".dart_tool",
        ".idea",
        ".vscode",
        "memory-bank",
        ".opencode",
        ".claude",
        ".agents",
    }
)

MAX_DEPTH: Final = 3


def _pubspec_stack(pubspec: Path) -> str:
    try:
        content = pubspec.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "Dart"
    return "Flutter (Dart)" if "flutter:" in content else "Dart"


def _detect_stack(root: Path) -> list[str]:
    stack: list[str] = []

    def add(name: str) -> None:
        if name not in stack:
            stack.append(name)

    for marker, name in ROOT_MARKERS.items():
        if (root / marker).is_file():
            add(name)
    pubspec = root / "pubspec.yaml"
    if pubspec.is_file():
        add(_pubspec_stack(pubspec))
    for pattern, name in ROOT_GLOBS.items():
        if any(root.glob(pattern)):
            add(name)
    return stack


def _has_source_files(root: Path) -> bool:
    """Walk at most MAX_DEPTH levels and stop at the first source file."""
    root_depth = len(root.parts)
    for current, dirs, files in os.walk(root):
        depth = len(Path(current).parts) - root_depth
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and depth < MAX_DEPTH]
        if any(Path(name).suffix.lower() in SOURCE_EXTENSIONS for name in files):
            return True
    return False


def scan_project(project_root: str) -> ScanResult:
    """Inspect ``project_root`` and report whether it holds code and which stack it uses."""
    root = Path(project_root).resolve()
    stack = _detect_stack(root)
    return {"has_code": bool(stack) or _has_source_files(root), "detected_stack": stack}
