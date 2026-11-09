from __future__ import annotations

from pathlib import Path

import pytest

from memory_bank.scanner import scan_project


def test_empty_project_has_no_code(tmp_path: Path) -> None:
    assert scan_project(str(tmp_path)) == {"has_code": False, "detected_stack": []}


@pytest.mark.parametrize(
    ("marker", "stack"),
    [
        ("package.json", "Node.js"),
        ("Cargo.toml", "Rust"),
        ("pyproject.toml", "Python"),
        ("requirements.txt", "Python"),
        ("go.mod", "Go"),
        ("pom.xml", "Java (Maven)"),
        ("Gemfile", "Ruby"),
        ("composer.json", "PHP"),
        ("Dockerfile", "Docker"),
        ("App.csproj", ".NET"),
        ("main.tf", "Terraform"),
    ],
)
def test_detects_stack_from_marker(tmp_path: Path, marker: str, stack: str) -> None:
    (tmp_path / marker).write_text("", encoding="utf-8")
    result = scan_project(str(tmp_path))
    assert result["has_code"] is True
    assert stack in result["detected_stack"]


def test_tells_flutter_from_plain_dart(tmp_path: Path) -> None:
    flutter, dart = tmp_path / "flutter", tmp_path / "dart"
    flutter.mkdir()
    dart.mkdir()
    (flutter / "pubspec.yaml").write_text("dependencies:\n  flutter:\n    sdk: flutter\n")
    (dart / "pubspec.yaml").write_text("name: tool\n")
    assert scan_project(str(flutter))["detected_stack"] == ["Flutter (Dart)"]
    assert scan_project(str(dart))["detected_stack"] == ["Dart"]


def test_lists_each_stack_once_in_detection_order(tmp_path: Path) -> None:
    for name in ("requirements.txt", "pyproject.toml", "package.json", "tsconfig.json"):
        (tmp_path / name).write_text("", encoding="utf-8")
    assert scan_project(str(tmp_path))["detected_stack"] == ["Node.js", "TypeScript", "Python"]


def test_source_files_mean_code_even_without_markers(tmp_path: Path) -> None:
    (tmp_path / "src" / "app").mkdir(parents=True)
    (tmp_path / "src" / "app" / "main.go").write_text("package main\n")
    assert scan_project(str(tmp_path)) == {"has_code": True, "detected_stack": []}


def test_ignores_dependency_and_memory_folders(tmp_path: Path) -> None:
    for folder in ("node_modules", ".venv", "memory-bank"):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "index.js").write_text("")
    assert scan_project(str(tmp_path))["has_code"] is False


def test_does_not_look_deeper_than_three_levels(tmp_path: Path) -> None:
    deep = tmp_path / "a" / "b" / "c" / "d"
    deep.mkdir(parents=True)
    (deep / "main.py").write_text("")
    assert scan_project(str(tmp_path))["has_code"] is False
