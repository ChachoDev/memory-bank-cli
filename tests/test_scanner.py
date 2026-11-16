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


@pytest.mark.parametrize("folder", [".claude", ".opencode", ".agents", ".junie"])
def test_ignores_tool_generated_folders(tmp_path: Path, folder: str) -> None:
    """Skills and hooks written by agents are not project code."""
    skill = tmp_path / folder / "skills" / "some-skill"
    skill.mkdir(parents=True)
    (skill / "helper.py").write_text("")
    assert scan_project(str(tmp_path)) == {"has_code": False, "detected_stack": []}


def test_does_not_look_deeper_than_three_levels(tmp_path: Path) -> None:
    deep = tmp_path / "a" / "b" / "c" / "d"
    deep.mkdir(parents=True)
    (deep / "main.py").write_text("")
    assert scan_project(str(tmp_path))["has_code"] is False


# ---------------------------------------------------------------------------
# Framework detection
# ---------------------------------------------------------------------------


def test_detects_react_from_package_json(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"react": "^18.0", "react-dom": "^18.0"}}',
        encoding="utf-8",
    )
    stack = scan_project(str(tmp_path))["detected_stack"]
    assert "Node.js" in stack
    assert "React" in stack


def test_detects_next_js_from_package_json(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"next": "^14.0"}}',
        encoding="utf-8",
    )
    stack = scan_project(str(tmp_path))["detected_stack"]
    assert "Next.js" in stack


def test_detects_express_from_package_json(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"express": "^4.0"}}',
        encoding="utf-8",
    )
    stack = scan_project(str(tmp_path))["detected_stack"]
    assert "Express" in stack


def test_detects_vue_from_package_json(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"vue": "^3.0"}}',
        encoding="utf-8",
    )
    stack = scan_project(str(tmp_path))["detected_stack"]
    assert "Vue" in stack


def test_detects_tailwind_from_dev_dependencies(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        '{"devDependencies": {"tailwindcss": "^3.0"}}',
        encoding="utf-8",
    )
    stack = scan_project(str(tmp_path))["detected_stack"]
    assert "Tailwind CSS" in stack


def test_detects_django_from_pyproject_toml(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\ndependencies = [\n  "django>=4.2",\n  "celery>=5.0",\n]\n',
        encoding="utf-8",
    )
    stack = scan_project(str(tmp_path))["detected_stack"]
    assert "Python" in stack
    assert "Django" in stack
    assert "Celery" in stack


def test_detects_fastapi_from_requirements_txt(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text(
        "fastapi>=0.100\nuvicorn>=0.20\npydantic>=2.0\n",
        encoding="utf-8",
    )
    stack = scan_project(str(tmp_path))["detected_stack"]
    assert "FastAPI" in stack
    assert "Uvicorn" in stack
    assert "Pydantic" in stack


def test_detects_flask_from_requirements_txt(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text(
        "flask>=2.0\nsqlalchemy>=2.0\n",
        encoding="utf-8",
    )
    stack = scan_project(str(tmp_path))["detected_stack"]
    assert "Flask" in stack
    assert "SQLAlchemy" in stack


def test_detects_pytorch_from_pyproject_toml(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\ndependencies = [\n  "torch>=2.0",\n  "pandas>=2.0",\n]\n',
        encoding="utf-8",
    )
    stack = scan_project(str(tmp_path))["detected_stack"]
    assert "PyTorch" in stack
    assert "Pandas" in stack


def test_detects_actix_from_cargo_toml(tmp_path: Path) -> None:
    (tmp_path / "Cargo.toml").write_text(
        '[package]\nname = "app"\n\n[dependencies]\nactix-web = "4"\ntokio = { version = "1", features = ["full"] }\nserde = "1"\n',
        encoding="utf-8",
    )
    stack = scan_project(str(tmp_path))["detected_stack"]
    assert "Rust" in stack
    assert "Actix Web" in stack
    assert "Tokio" in stack
    assert "Serde" in stack


def test_detects_rocket_from_cargo_toml(tmp_path: Path) -> None:
    (tmp_path / "Cargo.toml").write_text(
        '[package]\nname = "app"\n\n[dependencies]\nrocket = "0.5"\ndiesel = "2"\n',
        encoding="utf-8",
    )
    stack = scan_project(str(tmp_path))["detected_stack"]
    assert "Rocket" in stack
    assert "Diesel" in stack


def test_detects_gin_from_go_mod(tmp_path: Path) -> None:
    (tmp_path / "go.mod").write_text(
        'module example.com/app\n\ngo 1.21\n\nrequire (\n\tgithub.com/gin-gonic/gin v1.9.0\n\tgorm.io/gorm v1.25.0\n)\n',
        encoding="utf-8",
    )
    stack = scan_project(str(tmp_path))["detected_stack"]
    assert "Go" in stack
    assert "Gin" in stack
    assert "GORM" in stack


def test_detects_spring_boot_from_gradle(tmp_path: Path) -> None:
    (tmp_path / "build.gradle").write_text(
        'plugins { id "java" }\n\ndependencies {\n    implementation "org.springframework.boot:spring-boot-starter-web"\n    implementation "org.springframework.boot:spring-boot-starter-data-jpa"\n    testImplementation "org.junit.jupiter:junit-jupiter"\n}\n',
        encoding="utf-8",
    )
    stack = scan_project(str(tmp_path))["detected_stack"]
    assert "Spring Boot" in stack
    assert "JUnit 5" in stack


def test_detects_ktor_from_gradle_kts(tmp_path: Path) -> None:
    (tmp_path / "build.gradle.kts").write_text(
        'plugins { kotlin("jvm") version "1.9.0" }\n\ndependencies {\n    implementation("io.ktor:ktor-server-core")\n    implementation("io.ktor:ktor-client-core")\n}\n',
        encoding="utf-8",
    )
    stack = scan_project(str(tmp_path))["detected_stack"]
    assert "Kotlin (Gradle)" in stack
    assert "Ktor" in stack


def test_no_framework_when_no_framework_deps(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"unknown-pkg": "^1.0"}}',
        encoding="utf-8",
    )
    stack = scan_project(str(tmp_path))["detected_stack"]
    assert "Node.js" in stack
    # No framework should appear
    assert all(fw not in stack for fw in ("React", "Vue", "Express", "Angular"))


def test_frameworks_appear_after_languages(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"react": "^18.0", "express": "^4.0"}}',
        encoding="utf-8",
    )
    stack = scan_project(str(tmp_path))["detected_stack"]
    node_idx = stack.index("Node.js")
    react_idx = stack.index("React")
    express_idx = stack.index("Express")
    assert node_idx < react_idx
    assert node_idx < express_idx


def test_deduplicates_frameworks(tmp_path: Path) -> None:
    """react and react-dom both map to React; should appear once."""
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"react": "^18.0", "react-dom": "^18.0"}}',
        encoding="utf-8",
    )
    stack = scan_project(str(tmp_path))["detected_stack"]
    assert stack.count("React") == 1
